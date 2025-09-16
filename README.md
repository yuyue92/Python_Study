🐍 Python 开发详细指南（由浅入深）

**1. 环境与基础**
- 安装：推荐 Python 官网 或 pyenv/conda 管理多版本。
- 包管理：用 pip / pipx / conda。
- 虚拟环境：python -m venv venv && source venv/bin/activate。
- 编辑器：VSCode + Pylance 插件 / PyCharm。
- 👉 练习：写一个脚本，读取 .txt 文件，统计单词出现频率。

**2. 语法核心**
- 数据类型
- 数字、字符串、列表、元组、集合、字典
- 不可变 vs 可变对象
- 深浅拷贝：copy / deepcopy

- 控制流
- if/elif/else
- for + enumerate / zip
- while
- 推导式（list/dict/set comprehensions）
- 👉 练习：实现一个九九乘法表打印。

函数与作用域
- 默认参数、关键字参数、解包 *args / **kwargs
- 闭包与 nonlocal
- 装饰器（函数型编程常用）
- 👉 练习：实现一个计时器装饰器 @timeit。

类与对象
- 基础 OOP：__init__、实例属性、类属性
- 继承、多态
- 特殊方法（__str__, __repr__, __len__, __iter__ 等）
- 数据类 @dataclass
- 👉 练习：写一个 Vector 类，支持 +、-、len()。

包管理与项目结构
```
myproject/
  ├── mypackage/
  │     ├── __init__.py
  │     ├── module1.py
  │     └── module2.py
  ├── tests/
  ├── requirements.txt
  ├── pyproject.toml (推荐)
  └── main.py
```


常用第三方库：
- 数据处理：numpy, pandas
- 网络请求：requests, httpx
- Web 开发：flask, fastapi, django
- 数据库：sqlalchemy, peewee, pymongo
- 爬虫：scrapy, beautifulsoup4
- 可视化：matplotlib, seaborn, plotly
- 工具：click (命令行), typer, rich (美化输出)



学习进阶路线
- 脚本小工具：命令行工具、文件处理
- Web 开发：Flask/FastAPI 做 REST API
- 数据分析：用 Pandas 处理 CSV/Excel
- 并发 & 网络：写爬虫、并发任务
- 大型工程：模块化、测试、CI/CD
- AI & 数据科学：机器学习、深度学习
