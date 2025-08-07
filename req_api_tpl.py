# d:\project\python\ai_code_tools\fastapi-code-generator\apifox_aihub_json\amap_api\req_api.py

import requests
import time
import os
from dotenv import load_dotenv
import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException, Request # 新增导入

# --- 日志配置 ---
# 配置日志记录器，用于记录API调用过程中的信息和错误
# 日志级别设置为 INFO，格式包含时间戳、日志级别和消息内容
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__) # 获取当前模块的日志记录器

# --- 环境变量加载 ---
# 尝试从当前目录的 .env 文件或上一级目录的 .env 文件加载环境变量
# 主要用于加载 BASE_URL
ENV_PATH_CURRENT_DIR = os.path.join(os.path.dirname(__file__), '.env')
ENV_PATH_PARENT_DIR = os.path.join(os.path.dirname(__file__), '..', '.env')

if os.path.exists(ENV_PATH_CURRENT_DIR):
    load_dotenv(dotenv_path=ENV_PATH_CURRENT_DIR)
    logger.debug(f"从 {ENV_PATH_CURRENT_DIR} 加载 .env 文件")
elif os.path.exists(ENV_PATH_PARENT_DIR):
    load_dotenv(dotenv_path=ENV_PATH_PARENT_DIR)
    logger.debug(f"从 {ENV_PATH_PARENT_DIR} 加载 .env 文件")
else:
    logger.warning(f"在 {ENV_PATH_CURRENT_DIR} 或 {ENV_PATH_PARENT_DIR} 未找到 .env 文件。将使用默认配置（如果定义了）。")

# 从环境变量中获取高德地图 API 的基础 URL，如果未设置，则使用默认值
BASE_URL: Optional[str] = os.getenv("BASE_URL", "https://restapi.amap.com")
if not BASE_URL: # 确保 BASE_URL 有一个有效值
    logger.error("BASE_URL 环境变量未设置，且没有提供默认值。API 调用将失败。")
    # 实际应用中，这里可能需要更强的错误处理，例如启动时就失败

# --- 自定义异常 ---
class ApiError(Exception):
    """
    API 调用特定异常。
    当 API 调用在经过重试后仍然失败，或发生不可重试的客户端错误时抛出。
    """
    def __init__(self, message: str, status_code: Optional[int] = None, original_exception: Optional[Exception] = None):
        """
        初始化 ApiError。

        参数:
            message (str): 错误描述信息。
            status_code (Optional[int]): HTTP 状态码（如果适用）。
            original_exception (Optional[Exception]): 触发此错误的原始异常（如果适用）。
        """
        super().__init__(message)
        self.status_code = status_code
        self.original_exception = original_exception
        logger.error(f"ApiError: {message} (Status Code: {status_code})", exc_info=original_exception if logger.isEnabledFor(logging.DEBUG) else False)

# --- API 调用核心函数 ---
def call_api(
    endpoint_path: str,
    params: Dict[str, Any],
    max_retries: int = 3,
    initial_backoff: float = 1.0, # 初始等待时间（秒）
    max_backoff: float = 16.0,    # 最大等待时间（秒）
    timeout: int = 10             # 单次请求超时时间（秒）
) -> Dict[str, Any]:
    """
    调用高德地图 API 的通用函数，包含错误处理和指数回退重试逻辑。

    参数:
        endpoint_path (str): API 的端点路径 (例如: '/v5/place/text')。
        params (Dict[str, Any]): 请求的查询参数字典。
        max_retries (int): 对于可重试错误（如网络问题、5xx服务器错误）的最大重试次数。
        initial_backoff (float): 指数回退的初始等待时间（秒）。
        max_backoff (float): 指数回退的最大等待时间（秒）。
        timeout (int): 单次 HTTP 请求的超时时间（秒）。

    返回:
        Dict[str, Any]: API 成功响应的 JSON 数据 (已解析为字典)。

    抛出:
        ApiError: 如果 API 调用在所有重试尝试后仍然失败，或者发生不可重试的错误。
        ValueError: 如果 BASE_URL 未正确配置。
    """
    if not BASE_URL:
        # 这个检查确保基础 URL 配置正确，否则无法进行任何 API 调用
        logger.error("BASE_URL 未配置。无法执行 API 调用。")
        raise ValueError("高德 API 基础 URL (BASE_URL) 未在环境变量中配置。")

    # 构造完整的 API 请求 URL
    api_url: str = f"{BASE_URL.rstrip('/')}/{endpoint_path.lstrip('/')}" # 确保 URL 格式正确

    # 确保 'key' 参数存在，高德 API 通常强制要求
    if 'key' not in params or not params['key']:
        # 根据具体需求，这里可以选择记录警告并继续（让高德API返回错误），或者直接抛出客户端错误
        logger.warning(f"调用端点 {endpoint_path} 时，请求参数中缺少高德 API 密钥 ('key')。")
        # raise GaodeApiError("请求参数中缺少高德 API 密钥 ('key')。", status_code=400) # 或者选择不在这里抛出

    current_backoff = initial_backoff # 当前回退等待时间

    for attempt in range(max_retries + 1): # 尝试次数包括首次尝试 (attempt 0) 和 max_retries 次重试
        log_params_display = {k: v for k, v in params.items() if k != 'key'} # 日志中不显示 key
        logger.info(f"尝试第 {attempt + 1} 次调用高德 API: {api_url}, 参数 (部分): {log_params_display}")

        try:
            response = requests.get(api_url, params=params, timeout=timeout)
            
            # 检查 HTTP 状态码，对于非 2xx 的成功状态码，requests 不会主动抛出异常
            # raise_for_status() 会对 4xx (客户端错误) 和 5xx (服务器错误) 状态码抛出 HTTPError
            response.raise_for_status()

            # 如果请求成功 (2xx 状态码)
            logger.info(f"成功调用高德 API 端点: {endpoint_path}。状态码: {response.status_code}")
            return response.json() # 解析 JSON 响应并返回

        except requests.exceptions.Timeout as e:
            # 请求超时是典型的可重试错误
            logger.warning(f"调用 {api_url} 超时 (尝试 {attempt + 1}/{max_retries + 1})。错误: {e}")
            if attempt == max_retries: # 如果是最后一次尝试
                raise ApiError(f"调用高德 API 超时，已达到最大重试次数 ({max_retries + 1})。", original_exception=e)
        
        except requests.exceptions.ConnectionError as e:
            # 连接错误 (例如 DNS 解析失败、连接被拒绝) 通常也是可重试的
            logger.warning(f"调用 {api_url} 发生连接错误 (尝试 {attempt + 1}/{max_retries + 1})。错误: {e}")
            if attempt == max_retries:
                raise ApiError(f"调用高德 API 发生连接错误，已达到最大重试次数 ({max_retries + 1})。", original_exception=e)

        except requests.exceptions.HTTPError as e:
            # HTTPError 包含了 4xx 和 5xx 状态码
            status_code = e.response.status_code
            logger.error(f"调用 {api_url} 发生 HTTP 错误。状态码: {status_code}, 响应: {e.response.text[:200]} (尝试 {attempt + 1}/{max_retries + 1})", exc_info=True)
            
            if 500 <= status_code <= 599: # 5xx 服务器错误，通常是可重试的
                if attempt == max_retries:
                    raise ApiError(f"高德 API 返回服务器错误 (状态码: {status_code})，已达到最大重试次数。", status_code=status_code, original_exception=e)
            elif 400 <= status_code <= 499: # 4xx 客户端错误，通常不可重试 (例如参数错误、认证失败)
                # 对于特定的4xx错误，如429 (Too Many Requests)，有时也可以考虑重试，但这里简化处理为不可重试
                error_message = f"高德 API 返回客户端错误 (状态码: {status_code})。请检查请求参数或API密钥。"
                try:
                    # 尝试解析高德返回的错误信息
                    error_content = e.response.json()
                    error_message += f" 详细信息: {error_content}"
                except ValueError: # 如果响应不是JSON
                    error_message += f" 原始响应: {e.response.text[:200]}"
                raise ApiError(error_message, status_code=status_code, original_exception=e)
            else: 
                # 其他未明确处理的 HTTPError (理论上 raise_for_status 只处理 4xx/5xx)
                if attempt == max_retries:
                    raise ApiError(f"调用高德 API 发生未分类的 HTTP 错误 (状态码: {status_code})，已达到最大重试次数。", status_code=status_code, original_exception=e)
        
        except requests.exceptions.RequestException as e:
            # 捕获其他所有 'requests' 库可能抛出的基类异常 (如 SSLError 等)
            logger.error(f"调用 {api_url} 发生未预期的请求相关错误 (尝试 {attempt + 1}/{max_retries + 1})。错误: {e}", exc_info=True)
            if attempt == max_retries:
                raise ApiError(f"调用高德 API 发生未预期的请求错误，已达到最大重试次数。", original_exception=e)
        
        except ValueError as e: # requests.json() 可能抛出此异常如果响应体不是有效的JSON
            logger.error(f"解析来自 {api_url} 的响应时发生 JSON 解码错误 (尝试 {attempt + 1}/{max_retries + 1})。错误: {e}。响应文本: {response.text[:200] if 'response' in locals() else 'N/A'}", exc_info=True)
            # JSON解码错误通常意味着API行为异常或响应损坏，可能不适合重试，或者取决于具体情况
            # 这里我们选择不重试，直接抛出错误
            raise ApiError(f"高德 API 响应无法解析为 JSON。", original_exception=e)

        # 如果不是最后一次尝试，则进行等待
        if attempt < max_retries:
            wait_time = min(current_backoff, max_backoff) # 确保等待时间不超过最大值
            logger.info(f"等待 {wait_time:.2f} 秒后重试...")
            time.sleep(wait_time)
            current_backoff *= 2 # 指数增加回退时间 (简单实现，可以加入随机抖动)
    
    # 理论上，如果循环正常结束而没有返回或抛出异常，是不应该发生的
    # 但为保险起见，添加一个最终的错误抛出
    final_error_message = "调用高德 API 失败，所有重试尝试均告失败，且未捕获到特定原因。"
    logger.critical(final_error_message) # 使用 CRITICAL 级别，因为这表示逻辑可能存在问题
    raise ApiError(final_error_message)

# --- 新增：FastAPI 端点调用的包装函数 ---
def handel_api(
    request: Request,  # 接受 FastAPI Request 对象
    max_retries: int = 3,
    initial_backoff: float = 1.0,
    max_backoff: float = 16.0,
    timeout: int = 10
) -> Dict[str, Any]:
    """
    从 FastAPI Request 对象自动提取参数和端点路径，
    调用核心 API 函数 (call_api) 并统一处理 ApiError 和 ValueError，
    将它们转换为 FastAPI 的 HTTPException。

    参数:
        request (Request): FastAPI 的请求对象。
        max_retries (int): 最大重试次数。
        initial_backoff (float): 初始回退等待时间（秒）。
        max_backoff (float): 最大回退等待时间（秒）。
        timeout (int): 请求超时时间（秒）。

    返回:
        Dict[str, Any]: API 成功响应的 JSON 数据。

    抛出:
        HTTPException: 如果发生 ApiError 或 ValueError，则转换为相应的 HTTPException。
    """
    try:
        # 从 request 对象中获取端点路径 (不含查询参数)
        endpoint_path_from_request = request.scope['route'].path

        # 从 request 对象中获取所有路径参数和查询参数
        # request.path_params 是一个字典, e.g., {'adcode': '110000'}
        # request.query_params 是一个 MultiDict, 转换为普通字典
        # FastAPI 会自动处理参数的类型转换和别名，所以这里的键名已经是API期望的（或别名后的）
        all_params = {**request.path_params, **dict(request.query_params)}

        # 调用核心的 API 请求函数
        # call_api 内部会处理 None值的过滤 和 'Key' -> 'key' 的转换
        response_data = call_api(
            endpoint_path=endpoint_path_from_request,
            params=all_params,
            max_retries=max_retries,
            initial_backoff=initial_backoff,
            max_backoff=max_backoff,
            timeout=timeout
        )
        return response_data
    except ApiError as e:
        # 日志记录已在 call_api 或 ApiError 构造函数中完成
        # 此处仅转换异常类型
        status_code = e.status_code if e.status_code and 400 <= e.status_code < 600 else 503
        # logger.warning(f"API调用失败，将转换为HTTPException: {str(e)} (status: {status_code})")
        raise HTTPException(status_code=status_code, detail=str(e))
    except ValueError as e:
        # 通常是配置错误，例如 BASE_URL 未设置
        # logger.error(f"配置错误导致API调用失败: {str(e)}", exc_info=True) # 记录完整堆栈
        raise HTTPException(status_code=500, detail=f"服务器内部配置错误: {str(e)}")

    except Exception as e:
        # 捕获其他所有未预料到的异常，防止服务崩溃
        logger.critical(f"在 call_api_and_handle_errors 中发生意外错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"处理请求时发生意外的内部服务器错误。")
