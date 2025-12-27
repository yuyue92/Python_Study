# AI编程Agent - 交互式运行演示

## 场景：创建一个Web爬虫项目

---

### 启动Agent

```bash
$ python agent.py interactive
```

```
╔════════════════════════════════════════════════════════════╗
║          AI 编程 Agent - 最小可用版本                       ║
║          Minimal Viable AI Coding Agent                    ║
╚════════════════════════════════════════════════════════════╝

============================================================
AI编程Agent - 交互模式
============================================================

可用命令:
  - 输入任何编程请求（如：创建文件、修改代码等）
  - 输入 'exit' 或 'quit' 退出
  - 输入 'history' 查看对话历史
  - 输入 'clear' 清空历史
------------------------------------------------------------
```

---

### 第1轮对话：创建爬虫脚本

```
💬 你: 创建一个爬取豆瓣电影Top250的Python爬虫

🤖 Agent处理中...

============================================================
用户请求: 创建一个爬取豆瓣电影Top250的Python爬虫
============================================================

📊 收集上下文信息...
🤖 调用AI模型分析...
🔧 执行工具: write_file
📝 原因: 用户想创建新的爬虫脚本文件
📋 参数: {
  "file_path": "douban_spider.py",
  "content": "#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n\"\"\"\n豆瓣电影Top250爬虫\n\"\"\"\n\nimport requests\nfrom bs4 import BeautifulSoup\nimport time\nimport json\n\n\nclass DoubanSpider:\n    \"\"\"豆瓣电影爬虫类\"\"\"\n    \n    def __init__(self):\n        self.base_url = 'https://movie.douban.com/top250'\n        self.headers = {\n            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'\n        }\n        self.movies = []\n    \n    def fetch_page(self, start: int = 0) -> str:\n        \"\"\"获取页面内容\"\"\"\n        params = {'start': start, 'filter': ''}\n        try:\n            response = requests.get(\n                self.base_url, \n                headers=self.headers, \n                params=params,\n                timeout=10\n            )\n            response.raise_for_status()\n            return response.text\n        except requests.RequestException as e:\n            print(f'请求失败: {e}')\n            return ''\n    \n    def parse_page(self, html: str) -> list:\n        \"\"\"解析页面，提取电影信息\"\"\"\n        soup = BeautifulSoup(html, 'html.parser')\n        items = soup.find_all('div', class_='item')\n        \n        movies = []\n        for item in items:\n            try:\n                # 排名\n                rank = item.find('em').text\n                \n                # 标题\n                title = item.find('span', class_='title').text\n                \n                # 评分\n                rating = item.find('span', class_='rating_num').text\n                \n                # 评价人数\n                people = item.find('div', class_='star').find_all('span')[-1].text\n                people = people.replace('人评价', '')\n                \n                # 引言\n                inq = item.find('span', class_='inq')\n                quote = inq.text if inq else ''\n                \n                movies.append({\n                    'rank': rank,\n                    'title': title,\n                    'rating': rating,\n                    'people': people,\n                    'quote': quote\n                })\n            except Exception as e:\n                print(f'解析出错: {e}')\n                continue\n        \n        return movies\n    \n    def crawl_all(self):\n        \"\"\"爬取所有250部电影\"\"\"\n        print('开始爬取豆瓣电影Top250...')\n        \n        # 共10页，每页25部\n        for page in range(10):\n            start = page * 25\n            print(f'正在爬取第 {page + 1}/10 页...')\n            \n            html = self.fetch_page(start)\n            if html:\n                movies = self.parse_page(html)\n                self.movies.extend(movies)\n                print(f'  ✓ 成功获取 {len(movies)} 部电影')\n            else:\n                print(f'  ✗ 第 {page + 1} 页获取失败')\n            \n            # 礼貌延迟，避免被封\n            time.sleep(1)\n        \n        print(f'\\n爬取完成！共获取 {len(self.movies)} 部电影')\n    \n    def save_to_json(self, filename: str = 'douban_top250.json'):\n        \"\"\"保存到JSON文件\"\"\"\n        with open(filename, 'w', encoding='utf-8') as f:\n            json.dump(self.movies, f, ensure_ascii=False, indent=2)\n        print(f'数据已保存到: {filename}')\n\n\nif __name__ == '__main__':\n    spider = DoubanSpider()\n    spider.crawl_all()\n    spider.save_to_json()\n    \n    # 显示前5部电影\n    print('\\n前5部电影:')\n    for movie in spider.movies[:5]:\n        print(f\"{movie['rank']}. {movie['title']} - {movie['rating']}分\")\n"
}
✅ 执行成功
   成功写入 douban_spider.py

✅ 完成！
```

---

### 第2轮对话：创建依赖文件

```
💬 你: 创建requirements.txt，包含这个爬虫需要的依赖

🤖 Agent处理中...

============================================================
用户请求: 创建requirements.txt，包含这个爬虫需要的依赖
============================================================

📊 收集上下文信息...
🤖 调用AI模型分析...
🔧 执行工具: write_file
📝 原因: 创建Python项目依赖文件
📋 参数: {
  "file_path": "requirements.txt",
  "content": "# 豆瓣爬虫依赖\nrequests>=2.31.0\nbeautifulsoup4>=4.12.0\nlxml>=4.9.0\n"
}
✅ 执行成功
   成功写入 requirements.txt

✅ 完成！
```

---

### 第3轮对话：添加错误处理优化

```
💬 你: 优化爬虫，添加重试机制和更好的错误处理

🤖 Agent处理中...

============================================================
用户请求: 优化爬虫，添加重试机制和更好的错误处理
============================================================

📊 收集上下文信息...
🤖 调用AI模型分析...
🔧 执行工具: apply_diff
📝 原因: 用户想修改现有代码，使用diff更安全
📋 参数: {
  "file_path": "douban_spider.py",
  "diff_content": "--- douban_spider.py\n+++ douban_spider.py\n@@ -5,6 +5,7 @@\n \n import requests\n from bs4 import BeautifulSoup\n+from requests.adapters import HTTPAdapter\n+from requests.packages.urllib3.util.retry import Retry\n import time\n import json\n \n@@ -17,17 +18,34 @@\n             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'\n         }\n         self.movies = []\n+        self.session = self._create_session()\n+    \n+    def _create_session(self) -> requests.Session:\n+        \"\"\"创建带重试机制的会话\"\"\"\n+        session = requests.Session()\n+        \n+        # 配置重试策略\n+        retry_strategy = Retry(\n+            total=3,  # 最多重试3次\n+            backoff_factor=1,  # 重试间隔递增\n+            status_forcelist=[429, 500, 502, 503, 504],\n+            method_whitelist=['GET']\n+        )\n+        \n+        adapter = HTTPAdapter(max_retries=retry_strategy)\n+        session.mount('http://', adapter)\n+        session.mount('https://', adapter)\n+        \n+        return session\n     \n     def fetch_page(self, start: int = 0) -> str:\n         \"\"\"获取页面内容\"\"\"\n         params = {'start': start, 'filter': ''}\n         try:\n-            response = requests.get(\n+            response = self.session.get(\n                 self.base_url, \n                 headers=self.headers, \n                 params=params,\n                 timeout=10\n             )\n             response.raise_for_status()\n             return response.text\n"
}
✅ 执行成功
   成功应用diff到 douban_spider.py

✅ 完成！
```

---

### 第4轮对话：查看文件内容

```
💬 你: 读取douban_spider.py的前50行，让我确认一下

🤖 Agent处理中...

============================================================
用户请求: 读取douban_spider.py的前50行，让我确认一下
============================================================

📊 收集上下文信息...
🤖 调用AI模型分析...
🔧 执行工具: read_file
📝 原因: 用户想查看文件内容
📋 参数: {
  "file_path": "douban_spider.py"
}
✅ 执行成功

✅ 完成！

💬 AI回复: 已读取文件 douban_spider.py (共 158 行，6.8 KB)

前50行内容：
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
豆瓣电影Top250爬虫
"""

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import time
import json


class DoubanSpider:
    """豆瓣电影爬虫类"""
    
    def __init__(self):
        self.base_url = 'https://movie.douban.com/top250'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.movies = []
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """创建带重试机制的会话"""
        session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=3,  # 最多重试3次
            backoff_factor=1,  # 重试间隔递增
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=['GET']
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        return session
    
    def fetch_page(self, start: int = 0) -> str:
        """获取页面内容"""
        params = {'start': start, 'filter': ''}
        try:
            response = self.session.get(
                self.base_url, 
                headers=self.headers, 
...
```
```

---

### 第5轮对话：运行测试

```
💬 你: 安装依赖并运行爬虫测试

🤖 Agent处理中...

============================================================
用户请求: 安装依赖并运行爬虫测试
============================================================

📊 收集上下文信息...
🤖 调用AI模型分析...

[第1个工具调用]
🔧 执行工具: run_command
📝 原因: 安装Python依赖
📋 参数: {
  "command": "pip install -r requirements.txt"
}
✅ 执行成功

输出:
Collecting requests>=2.31.0
  Using cached requests-2.31.0-py3-none-any.whl (62 kB)
Collecting beautifulsoup4>=4.12.0
  Using cached beautifulsoup4-4.12.2-py3-none-any.whl (142 kB)
Collecting lxml>=4.9.0
  Using cached lxml-4.9.3-cp39-cp39-macosx_11_0_x86_64.whl (7.8 MB)
Installing collected packages: requests, beautifulsoup4, lxml
Successfully installed beautifulsoup4-4.12.2 lxml-4.9.3 requests-2.31.0


[第2个工具调用]
🔧 执行工具: run_command
📝 原因: 运行爬虫脚本进行测试
📋 参数: {
  "command": "python douban_spider.py",
  "timeout": 60
}
✅ 执行成功

输出:
开始爬取豆瓣电影Top250...
正在爬取第 1/10 页...
  ✓ 成功获取 25 部电影
正在爬取第 2/10 页...
  ✓ 成功获取 25 部电影
正在爬取第 3/10 页...
  ✓ 成功获取 25 部电影
...
正在爬取第 10/10 页...
  ✓ 成功获取 25 部电影

爬取完成！共获取 250 部电影
数据已保存到: douban_top250.json

前5部电影:
1. 肖申克的救赎 - 9.7分
2. 霸王别姬 - 9.6分
3. 阿甘正传 - 9.5分
4. 泰坦尼克号 - 9.4分
5. 这个杀手不太冷 - 9.4分

✅ 完成！
```

---

### 查看对话历史

```
💬 你: history

📜 对话历史:

[1] 用户: 创建一个爬取豆瓣电影Top250的Python爬虫
    结果: 成功写入 douban_spider.py

[2] 用户: 创建requirements.txt，包含这个爬虫需要的依赖
    结果: 成功写入 requirements.txt

[3] 用户: 优化爬虫，添加重试机制和更好的错误处理
    结果: 成功应用diff到 douban_spider.py

[4] 用户: 读取douban_spider.py的前50行，让我确认一下
    结果: N/A

[5] 用户: 安装依赖并运行爬虫测试
    结果: N/A
```

---

### 退出

```
💬 你: exit

👋 再见！
```

---

## 总结

### ✅ 完成的任务
1. ✅ 创建了完整的爬虫脚本（158行代码）
2. ✅ 生成了依赖文件
3. ✅ 使用Diff精确优化代码（添加重试机制）
4. ✅ 查看文件内容验证
5. ✅ 自动安装依赖并运行测试

### 🎯 展示的核心功能
- **上下文理解**：Agent理解用户的渐进式需求
- **Function Calling**：自动选择合适的工具
- **Diff机制**：安全地修改现有代码
- **多步骤执行**：一次请求完成安装+运行
- **对话历史**：记录所有操作

### 💡 实际价值
这个演示展示了AI编程Agent如何在**几分钟内**完成传统需要**30-60分钟**的开发任务：
- 编写爬虫逻辑
- 配置依赖
- 添加错误处理
- 测试运行

全程用户只需用自然语言描述需求！