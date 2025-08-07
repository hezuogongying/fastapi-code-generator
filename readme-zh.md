# fastapi-代码生成器

此代码生成器从 openapi 文件创建 FastAPI 应用程序。

[![PyPI version](https://badge.fury.io/py/fastapi-code-generator.svg)](https://pypi.python.org/pypi/fastapi-code-generator)
[![Downloads](https://pepy.tech/badge/fastapi-code-generator/month)](https://pepy.tech/project/fastapi-code-generator)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/fastapi-code-generator)](https://pypi.python.org/pypi/fastapi-code-generator)
[![codecov](https://codecov.io/gh/koxudaxi/fastapi-code-generator/branch/master/graph/badge.svg)](https://codecov.io/gh/koxudaxi/fastapi-code-generator)
![license](https://img.shields.io/github/license/koxudaxi/fastapi-code-generator.svg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)


## 此项目处于实验阶段。

fastapi-code-generator 使用 [datamodel-code-generator](https://github.com/koxudaxi/datamodel-code-generator) 生成 pydantic 模型。

## 帮助
更多详情请参阅[文档](https://koxudaxi.github.io/fastapi-code-generator)。


## 安装

安装 `fastapi-code-generator`：
```sh
$ pip install fastapi-code-generator
```

## 使用方法

`fastapi-code-generator` 命令：
```
用法: fastapi-codegen [选项]

选项:
  -i, --input 文件名     [必需]
  -o, --output 路径        [必需]
  -t, --template-dir 路径
  -m, --model-file         指定生成的模型文件路径+名称，如果未指定则默认为 models.py
  -r, --generate-routers   使用 RouterAPI 生成具有多个路由器的模块化 API（适用于较大的应用程序）。
  --specify-tags           与 --generate-routers 一起使用，从给定的标签列表中生成特定的路由器。
  -c, --custom-visitors    路径 - 添加变量到模板的自定义访问器。
  -d, --output-model-type  指定要使用的 Pydantic 基本模型（参见 [datamodel-code-generator](https://github.com/koxudaxi/datamodel-code-generator)；默认为 `pydantic.BaseModel`）。
  -p, --python-version     指定目标 Python 版本（默认为 `3.9`）。
  --install-completion     为当前 shell 安装自动补全。
  --show-completion        显示当前 shell 的自动补全，以便复制或自定义安装。
  --help                   显示此消息并退出。
```

### Pydantic 2 支持

在命令行中指定 Pydantic 2 `BaseModel` 版本，例如：

```sh
$ fastapi-codegen --input api.yaml --output app --output-model-type pydantic_v2.BaseModel
```

## 示例
### OpenAPI
```sh
$ fastapi-codegen --input api.yaml --output app
```

<details>
<summary>api.yaml</summary>
<pre>
<code>
openapi: "3.0.0"
info:
  version: 1.0.0
  title: Swagger Petstore
  license:
    name: MIT
servers:
  - url: http://petstore.swagger.io/v1
paths:
  /pets:
    get:
      summary: List all pets
      operationId: listPets
      tags:
        - pets
      parameters:
        - name: limit
          in: query
          description: How many items to return at one time (max 100)
          required: false
          schema:
            type: integer
            format: int32
      responses:
        '200':
          description: A paged array of pets
          headers:
            x-next:
              description: A link to the next page of responses
              schema:
                type: string
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Pets"
        default:
          description: unexpected error
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
                x-amazon-apigateway-integration:
                  uri:
                    Fn::Sub: arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${PythonVersionFunction.Arn}/invocations
                  passthroughBehavior: when_no_templates
                  httpMethod: POST
                  type: aws_proxy
    post:
      summary: Create a pet
      operationId: createPets
      tags:
        - pets
      responses:
        '201':
          description: Null response
        default:
          description: unexpected error
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
                x-amazon-apigateway-integration:
                  uri:
                    Fn::Sub: arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${PythonVersionFunction.Arn}/invocations
                  passthroughBehavior: when_no_templates
                  httpMethod: POST
                  type: aws_proxy
  /pets/{petId}:
    get:
      summary: Info for a specific pet
      operationId: showPetById
      tags:
        - pets
      parameters:
        - name: petId
          in: path
          required: true
          description: The id of the pet to retrieve
          schema:
            type: string
      responses:
        '200':
          description: Expected response to a valid request
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Pets"
        default:
          description: unexpected error
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
    x-amazon-apigateway-integration:
      uri:
        Fn::Sub: arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${PythonVersionFunction.Arn}/invocations
      passthroughBehavior: when_no_templates
      httpMethod: POST
      type: aws_proxy
components:
  schemas:
    Pet:
      required:
        - id
        - name
      properties:
        id:
          type: integer
          format: int64
        name:
          type: string
        tag:
          type: string
    Pets:
      type: array
      description: list of pet
      items:
        $ref: "#/components/schemas/Pet"
    Error:
      required:
        - code
        - message
      properties:
        code:
          type: integer
          format: int32
        message:
          type: string
</code>
</pre>
</details>


`app/main.py`:
```python
# generated by fastapi-codegen:
#   filename:  api.yaml
#   timestamp: 2020-06-14T10:45:22+00:00

from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, Query

from .models import Pets

app = FastAPI(version="1.0.0", title="Swagger Petstore", license="{'name': 'MIT'}",)


@app.get('/pets', response_model=Pets)
def list_pets(limit: Optional[int] = None) -> Pets:
    """
    List all pets
    """
    pass


@app.post('/pets', response_model=None)
def create_pets() -> None:
    """
    Create a pet
    """
    pass


@app.get('/pets/{pet_id}', response_model=Pets)
def show_pet_by_id(pet_id: str = Query(..., alias='petId')) -> Pets:
    """
    Info for a specific pet
    """
    pass

```

`app/models.py`:
```python
# generated by datamodel-codegen:
#   filename:  api.yaml
#   timestamp: 2020-06-14T10:45:22+00:00

from typing import List, Optional

from pydantic import BaseModel, Field


class Pet(BaseModel):
    id: int
    name: str
    tag: Optional[str] = None


class Pets(BaseModel):
    __root__: List[Pet] = Field(..., description='list of pet')


class Error(BaseModel):
    code: int
    message: str
```

## 自定义模板
如果您想生成自定义的 `*.py` 文件，可以通过命令的 `-t` 或 `--template-dir` 选项为 fastapi-code-generator 提供一个自定义模板目录。

fastapi-code-generator 将在给定的模板目录中搜索 [jinja2](https://jinja.palletsprojects.com/) 模板文件，例如 `some_jinja_templates/list_pets.py`。

```bash
fastapi-code-generator --template-dir some_jinja_templates --output app --input api.yaml
```

这些文件将被渲染并写入输出目录。此外，生成的文件名将使用模板名称和 `*.py` 扩展名创建，例如 `app/list_pets.py` 将是从 jinja 模板生成的单独文件，与默认的 `app/main.py` 一起生成。

### 变量
您可以在 jinja2 模板中使用以下变量：

- `imports`  所有导入语句
- `info`  所有信息语句
- `operations` `operations` 是 `operation` 的列表
  - `operation.type` HTTP 方法
  - `operation.path` 路径
  - `operation.snake_case_path` 蛇形命名法的路径
  - `operation.response` 响应对象
  - `operation.function_name` 函数名称由 `operationId` 或 `方法` + `路径` 创建
  - `operation.snake_case_arguments` 蛇形命名法的函数参数
  - `operation.security` [安全认证](https://swagger.io/docs/specification/authentication/)
  - `operation.summary` 摘要
  - `operation.tags` [标签](https://swagger.io/docs/specification/grouping-operations-with-tags/)

### 默认模板
`main.jinja2`
```jinja2
from __future__ import annotations

from fastapi import FastAPI

{{imports}}

app = FastAPI(
    {% if info %}
    {% for key,value in info.items() %}
    {{ key }} = "{{ value }}",
    {% endfor %}
    {% endif %}
    )


{% for operation in operations %}
@app.{{operation.type}}('{{operation.snake_case_path}}', response_model={{operation.response}})
def {{operation.function_name}}({{operation.snake_case_arguments}}) -> {{operation.response}}:
    {%- if operation.summary %}
    """
    {{ operation.summary }}
    """
    {%- endif %}
    pass
{% endfor %}

```

### 模块化模板
`modular_template/main.jinja2`:
```jinja
from __future__ import annotations

from fastapi import FastAPI

from .routers import {{ routers | join(", ") }}

app = FastAPI(
    {% if info %}
    {% for key,value in info.items() %}
    {% set info_value= value.__repr__() %}
    {{ key }} = {{info_value}},
    {% endfor %}
    {% endif %}
    )

{% for router in routers -%}
app.include_router({{router}}.router)
{% endfor -%}

@app.get("/")
async def root():
    return {"message": "Gateway of the App"}
```

`modular_template/routers.jinja2`:
```jinja
from __future__ import annotations

from fastapi import APIRouter
from fastapi import FastAPI

from ..dependencies import *

router = APIRouter(
    tags=['{{tag}}']
    )

{% for operation in operations %}
{% if operation.tags[0] == tag %}
@router.{{operation.type}}('{{operation.snake_case_path}}', response_model={{operation.response}}
    {% if operation.additional_responses %}
        , responses={
            {% for status_code, models in operation.additional_responses.items() %}
                '{{ status_code }}': {
                {% for key, model in models.items() %}
                    '{{ key }}': {{ model }}{% if not loop.last %},{% endif %}
                {% endfor %}
                }{% if not loop.last %},{% endif %}
            {% endfor %}
        }
    {% endif %}
    {% if operation.tags%}
    , tags={{operation.tags}}
    {% endif %})
def {{operation.function_name}}({{operation.snake_case_arguments}}) -> {{operation.return_type}}:
    {%- if operation.summary %}
    """
    {{ operation.summary }}
    """
    {%- endif %}
    pass
{% endif %}
{% endfor %}
```

`modular_template/dependencies.jinja2`:
```jinja
{{imports}}
```

## 自定义访问器
