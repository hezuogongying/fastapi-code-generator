import sys
from pathlib import Path
import subprocess
import sys
import shutil

def run_gen(python_executable, input_json_path, output_path, template_dir):
    # 清理并确保输出目录状态
    if output_path.exists():
        print(f"Cleaning up existing output directory: {output_path}")
        # shutil is now imported at the top
        shutil.rmtree(output_path)
    output_path.mkdir(parents=True, exist_ok=False) # 要求目录不存在，由 mkdir 创建

    # 新增：复制 req_api_tpl.py 到目标目录
    # 从 input_json_path 推断 script_dir，因为 script_dir 不是直接传递给此函数的
    # input_json_path = script_dir / 'apifox_aihub_json' / 'amap.json'
    script_dir_derived = input_json_path.parent.parent
    source_req_api_path = script_dir_derived / 'req_api_tpl.py'
    dest_req_api_path = output_path / 'req_api.py'
    if source_req_api_path.exists():
        print(f"Copying {source_req_api_path} to {dest_req_api_path}")
        shutil.copy2(source_req_api_path, dest_req_api_path) # copy2 尝试保留更多元数据
    else:
        print(f"Warning: Source file {source_req_api_path} not found. Skipping copy.", file=sys.stderr)
    
    cmd = [
        str(python_executable),
        '-m',
        'fastapi_code_generator',
        '--input', str(input_json_path),
        '--output', str(output_path),
        '--template-dir', str(template_dir) # 恢复自定义模板
    ]
    print(f"Running command: {' '.join(cmd)}")
    try:
        # 使用 capture_output 获取 stdout/stderr 以便更好地调试
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8')
        print("代码生成成功!")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("代码生成失败:", file=sys.stderr)
        print(f"返回代码: {e.returncode}", file=sys.stderr)
        print(f"Stdout: {e.stdout}", file=sys.stderr)
        print(f"Stderr: {e.stderr}", file=sys.stderr)
        raise # 重新引发异常以便外部捕获


def main():
    # 脚本位于 '.../fastapi-code-generator/'
    script_dir = Path(__file__).parent
    # venv 位于 '.../ai_code_tools/'，即上一级目录
    project_root = script_dir.parent
    
    # 构建到虚拟环境 Python 解释器的路径
    python_executable = project_root / 'venv' / 'Scripts' / 'python.exe'
    
    if not python_executable.exists():
        print(f"错误: 在 {python_executable} 未找到 Python 解释器", file=sys.stderr)
        sys.exit(1)

    input_json_path = script_dir / 'apifox_aihub_json' / 'amap_api_template' / 'amap.json'  # 使用不含中文的文件名
    output_path = script_dir / 'apifox_aihub_json' / 'amap_api'
    template_dir = script_dir / 'apifox_aihub_json' / 'amap_api_template'
    
    print(f"Using Python from: {python_executable}")
    run_gen(python_executable, input_json_path, output_path, template_dir)


if __name__ == "__main__":
    main()
