"""
AI编程Agent - 最小可用版本
完整实现：上下文收集、Function Calling、Diff应用
"""

import os
import json
import subprocess
import difflib
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


# ============================================================================
# 第一部分：工具函数层 (Tools Layer)
# ============================================================================

class ToolKit:
    """提供给AI的工具集"""
    
    @staticmethod
    def read_file(file_path: str) -> Dict[str, Any]:
        """读取文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {
                'success': True,
                'content': content,
                'lines': len(content.split('\n')),
                'size': len(content)
            }
        except FileNotFoundError:
            return {'success': False, 'error': f'文件不存在: {file_path}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def write_file(file_path: str, content: str) -> Dict[str, Any]:
        """写入文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                'success': True,
                'message': f'成功写入 {file_path}',
                'bytes_written': len(content)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def list_files(directory: str = '.', pattern: str = '*') -> Dict[str, Any]:
        """列出目录下的文件"""
        try:
            import glob
            files = glob.glob(os.path.join(directory, pattern))
            
            return {
                'success': True,
                'files': files,
                'count': len(files)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def run_command(command: str, timeout: int = 30) -> Dict[str, Any]:
        """执行终端命令"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': f'命令超时 (>{timeout}s)'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_tool_definitions() -> List[Dict[str, Any]]:
        """返回所有工具的JSON Schema定义（供AI理解）"""
        return [
            {
                "name": "read_file",
                "description": "读取指定文件的完整内容，用于查看代码或配置文件",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "文件路径，如 'src/main.py'"
                        }
                    },
                    "required": ["file_path"]
                }
            },
            {
                "name": "write_file",
                "description": "创建新文件或完全覆盖现有文件的内容",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "目标文件路径"
                        },
                        "content": {
                            "type": "string",
                            "description": "要写入的完整文本内容"
                        }
                    },
                    "required": ["file_path", "content"]
                }
            },
            {
                "name": "list_files",
                "description": "列出目录中的文件，支持通配符",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "目录路径，默认为当前目录"
                        },
                        "pattern": {
                            "type": "string",
                            "description": "文件匹配模式，如 '*.py'"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "run_command",
                "description": "在终端执行shell命令，用于运行测试、安装依赖等",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "要执行的命令，如 'python test.py'"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "超时时间（秒），默认30秒"
                        }
                    },
                    "required": ["command"]
                }
            },
            {
                "name": "apply_diff",
                "description": "以diff格式精确修改文件的特定行，比全文替换更安全",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "要修改的文件路径"
                        },
                        "diff_content": {
                            "type": "string",
                            "description": "unified diff格式的修改内容"
                        }
                    },
                    "required": ["file_path", "diff_content"]
                }
            }
        ]


# ============================================================================
# 第二部分：上下文收集器 (Context Collector)
# ============================================================================

@dataclass
class FileContext:
    """文件上下文信息"""
    path: str
    content: str
    language: str
    line_count: int
    is_modified: bool = False


@dataclass
class ProjectContext:
    """项目上下文"""
    root_dir: str
    files: List[str]
    structure: Dict[str, Any]


class ContextCollector:
    """收集编程环境的上下文信息"""
    
    def __init__(self, project_root: str = '.'):
        self.project_root = project_root
        self.toolkit = ToolKit()
    
    def collect_full_context(self, 
                            focus_file: Optional[str] = None,
                            include_files: List[str] = None) -> Dict[str, Any]:
        """收集完整的上下文信息"""
        
        context = {
            'timestamp': datetime.now().isoformat(),
            'project_root': os.path.abspath(self.project_root),
            
            # 1. 项目结构
            'project_structure': self._scan_project_structure(),
            
            # 2. 焦点文件（用户正在编辑的）
            'focus_file': self._get_file_context(focus_file) if focus_file else None,
            
            # 3. 相关文件
            'related_files': [
                self._get_file_context(f) for f in (include_files or [])
            ],
            
            # 4. Git信息（如果是git仓库）
            'git_info': self._get_git_info(),
            
            # 5. 最近的命令输出
            'recent_commands': self._get_recent_commands()
        }
        
        return context
    
    def _scan_project_structure(self, max_depth: int = 3) -> Dict[str, Any]:
        """扫描项目文件结构"""
        structure = {
            'files': [],
            'directories': [],
            'file_count': 0
        }
        
        try:
            for root, dirs, files in os.walk(self.project_root):
                # 跳过隐藏目录和常见的忽略目录
                dirs[:] = [d for d in dirs if not d.startswith('.') 
                          and d not in ['node_modules', '__pycache__', 'venv']]
                
                depth = root.replace(self.project_root, '').count(os.sep)
                if depth >= max_depth:
                    dirs.clear()
                    continue
                
                rel_root = os.path.relpath(root, self.project_root)
                structure['directories'].append(rel_root)
                
                for file in files:
                    if not file.startswith('.'):
                        rel_path = os.path.join(rel_root, file)
                        structure['files'].append(rel_path)
                        structure['file_count'] += 1
        
        except Exception as e:
            structure['error'] = str(e)
        
        return structure
    
    def _get_file_context(self, file_path: str) -> Optional[FileContext]:
        """获取单个文件的详细信息"""
        result = self.toolkit.read_file(file_path)
        
        if not result['success']:
            return None
        
        # 推断文件语言
        ext = os.path.splitext(file_path)[1]
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust'
        }
        language = language_map.get(ext, 'text')
        
        return FileContext(
            path=file_path,
            content=result['content'],
            language=language,
            line_count=result['lines']
        )
    
    def _get_git_info(self) -> Dict[str, Any]:
        """获取Git仓库信息"""
        if not os.path.exists(os.path.join(self.project_root, '.git')):
            return {'is_git_repo': False}
        
        # 获取当前分支
        branch_result = self.toolkit.run_command('git branch --show-current')
        
        # 获取最近的提交
        log_result = self.toolkit.run_command(
            'git log -1 --pretty=format:"%H|%an|%s|%ar"'
        )
        
        info = {'is_git_repo': True}
        
        if branch_result['success']:
            info['branch'] = branch_result['stdout'].strip()
        
        if log_result['success']:
            parts = log_result['stdout'].split('|')
            if len(parts) == 4:
                info['last_commit'] = {
                    'hash': parts[0][:8],
                    'author': parts[1],
                    'message': parts[2],
                    'time': parts[3]
                }
        
        return info
    
    def _get_recent_commands(self) -> List[Dict[str, Any]]:
        """获取最近执行的命令（简化版，实际需要从终端历史读取）"""
        # 这里只是示例，实际应该从终端集成中获取
        return [
            {
                'command': 'python main.py',
                'timestamp': datetime.now().isoformat(),
                'output': '(命令历史需要终端集成)'
            }
        ]


# ============================================================================
# 第三部分：Diff处理器 (Diff Processor)
# ============================================================================

class DiffProcessor:
    """处理代码的Diff格式修改"""
    
    @staticmethod
    def apply_diff(file_path: str, diff_content: str) -> Dict[str, Any]:
        """应用unified diff到文件"""
        
        # 1. 读取原文件
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_lines = f.readlines()
        except FileNotFoundError:
            return {
                'success': False,
                'error': f'文件不存在: {file_path}'
            }
        
        # 2. 解析diff
        try:
            hunks = DiffProcessor._parse_unified_diff(diff_content)
        except Exception as e:
            return {
                'success': False,
                'error': f'Diff解析失败: {str(e)}'
            }
        
        # 3. 验证diff（确保原文件内容匹配）
        for hunk in hunks:
            if not DiffProcessor._validate_hunk(original_lines, hunk):
                return {
                    'success': False,
                    'error': f'Diff验证失败：第{hunk["old_start"]}行内容不匹配。'
                           f'文件可能已被修改，请重新生成diff。'
                }
        
        # 4. 应用修改
        new_lines = original_lines.copy()
        
        # 从后往前应用，避免行号偏移
        for hunk in reversed(hunks):
            start = hunk['old_start'] - 1  # 转为0索引
            end = start + len(hunk['old_lines'])
            new_lines[start:end] = [line + '\n' for line in hunk['new_lines']]
        
        # 5. 写回文件
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            
            return {
                'success': True,
                'message': f'成功应用diff到 {file_path}',
                'changes': len(hunks)
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'写入文件失败: {str(e)}'
            }
    
    @staticmethod
    def _parse_unified_diff(diff_content: str) -> List[Dict[str, Any]]:
        """解析unified diff格式"""
        lines = diff_content.split('\n')
        hunks = []
        current_hunk = None
        
        for line in lines:
            # 跳过文件头
            if line.startswith('---') or line.startswith('+++'):
                continue
            
            # 新的hunk开始
            if line.startswith('@@'):
                if current_hunk:
                    hunks.append(current_hunk)
                
                # 解析 @@ -10,5 +10,6 @@ 格式
                parts = line.split('@@')[1].strip().split()
                old_info = parts[0].split(',')
                new_info = parts[1].split(',')
                
                current_hunk = {
                    'old_start': int(old_info[0].replace('-', '')),
                    'old_lines': [],
                    'new_lines': []
                }
                continue
            
            if current_hunk is None:
                continue
            
            # 删除的行
            if line.startswith('-'):
                current_hunk['old_lines'].append(line[1:])
            # 添加的行
            elif line.startswith('+'):
                current_hunk['new_lines'].append(line[1:])
            # 上下文行（同时加到old和new）
            else:
                if line.startswith(' '):
                    line = line[1:]
                current_hunk['old_lines'].append(line)
                current_hunk['new_lines'].append(line)
        
        if current_hunk:
            hunks.append(current_hunk)
        
        return hunks
    
    @staticmethod
    def _validate_hunk(file_lines: List[str], hunk: Dict[str, Any]) -> bool:
        """验证hunk是否匹配文件内容"""
        start = hunk['old_start'] - 1
        end = start + len(hunk['old_lines'])
        
        if end > len(file_lines):
            return False
        
        actual_lines = [line.rstrip('\n') for line in file_lines[start:end]]
        expected_lines = [line.rstrip('\n') for line in hunk['old_lines']]
        
        return actual_lines == expected_lines
    
    @staticmethod
    def generate_diff(file_path: str, new_content: str) -> str:
        """生成unified diff格式"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_lines = f.readlines()
        except FileNotFoundError:
            original_lines = []
        
        new_lines = new_content.split('\n')
        if new_lines and not new_lines[-1].endswith('\n'):
            new_lines[-1] += '\n'
        new_lines = [line + '\n' if not line.endswith('\n') else line 
                     for line in new_lines]
        
        diff = difflib.unified_diff(
            original_lines,
            new_lines,
            fromfile=file_path,
            tofile=file_path,
            lineterm=''
        )
        
        return '\n'.join(diff)


# ============================================================================
# 第四部分：大语言模型接口 (LLM Interface)
# ============================================================================

class LLMInterface:
    """与大语言模型的接口（模拟版）"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.conversation_history = []
    
    def call_llm(self, 
                 prompt: str, 
                 tools: List[Dict[str, Any]] = None,
                 system_prompt: str = None) -> Dict[str, Any]:
        """
        调用大语言模型
        
        实际使用时，这里应该调用真实的API（如OpenAI、Anthropic）
        这里我们返回模拟的响应
        """
        
        # 记录对话历史
        self.conversation_history.append({
            'role': 'user',
            'content': prompt
        })
        
        # ===== 这里是模拟的AI响应 =====
        # 实际应该调用：
        # response = openai.ChatCompletion.create(...)
        # 或
        # response = anthropic.messages.create(...)
        
        mock_response = self._generate_mock_response(prompt, tools)
        
        self.conversation_history.append({
            'role': 'assistant',
            'content': mock_response
        })
        
        return mock_response
    
    def _generate_mock_response(self, prompt: str, tools: List[Dict]) -> Dict[str, Any]:
        """生成模拟的AI响应（实际使用时删除此方法）"""
        
        # 检测用户意图
        prompt_lower = prompt.lower()
        
        # 意图1：读取文件
        if 'read' in prompt_lower or '查看' in prompt_lower or '读取' in prompt_lower:
            return {
                'type': 'function_call',
                'function': 'read_file',
                'arguments': {
                    'file_path': 'example.py'  # 实际AI会从prompt提取
                },
                'reasoning': '用户想查看文件内容'
            }
        
        # 意图2：创建文件
        elif 'create' in prompt_lower or '创建' in prompt_lower or '新建' in prompt_lower:
            return {
                'type': 'function_call',
                'function': 'write_file',
                'arguments': {
                    'file_path': 'new_file.py',
                    'content': '# 这是一个新文件\nprint("Hello, World!")'
                },
                'reasoning': '用户想创建新文件'
            }
        
        # 意图3：修改文件（生成diff）
        elif 'modify' in prompt_lower or '修改' in prompt_lower or '优化' in prompt_lower:
            return {
                'type': 'function_call',
                'function': 'apply_diff',
                'arguments': {
                    'file_path': 'example.py',
                    'diff_content': '''--- example.py
+++ example.py
@@ -1,3 +1,4 @@
 def hello():
-    print("Hello")
+    # 优化后的版本
+    print("Hello, World!")
 '''
                },
                'reasoning': '用户想修改文件内容'
            }
        
        # 意图4：运行命令
        elif 'run' in prompt_lower or '运行' in prompt_lower or '执行' in prompt_lower:
            return {
                'type': 'function_call',
                'function': 'run_command',
                'arguments': {
                    'command': 'python example.py'
                },
                'reasoning': '用户想执行命令'
            }
        
        # 默认：纯文本回复
        else:
            return {
                'type': 'text',
                'content': f'我理解您的需求。请提供更多细节，我可以帮您：\n'
                          f'- 读取和查看文件\n'
                          f'- 创建新文件\n'
                          f'- 修改现有代码\n'
                          f'- 运行命令和测试'
            }


# ============================================================================
# 第五部分：AI编程Agent主控制器
# ============================================================================

class AICodingAgent:
    """AI编程助手的主控制器"""
    
    def __init__(self, project_root: str = '.', api_key: str = None):
        self.project_root = project_root
        
        # 初始化各个组件
        self.toolkit = ToolKit()
        self.context_collector = ContextCollector(project_root)
        self.diff_processor = DiffProcessor()
        self.llm = LLMInterface(api_key)
        
        # 对话历史
        self.conversation_history = []
    
    def process_request(self, 
                       user_request: str,
                       focus_file: Optional[str] = None,
                       related_files: List[str] = None) -> Dict[str, Any]:
        """
        处理用户请求的主流程
        
        Args:
            user_request: 用户的自然语言请求
            focus_file: 用户当前关注的文件
            related_files: 相关的文件列表
            
        Returns:
            处理结果
        """
        
        print(f"\n{'='*60}")
        print(f"用户请求: {user_request}")
        print(f"{'='*60}\n")
        
        # 第1步：收集上下文
        print("📊 收集上下文信息...")
        context = self.context_collector.collect_full_context(
            focus_file=focus_file,
            include_files=related_files or []
        )
        
        # 第2步：构建发送给LLM的完整Prompt
        full_prompt = self._build_prompt(user_request, context)
        
        # 第3步：调用LLM获取响应
        print("🤖 调用AI模型分析...")
        llm_response = self.llm.call_llm(
            prompt=full_prompt,
            tools=self.toolkit.get_tool_definitions(),
            system_prompt=self._get_system_prompt()
        )
        
        # 第4步：执行AI返回的操作
        result = self._execute_llm_response(llm_response)
        
        # 第5步：记录历史并返回
        self.conversation_history.append({
            'user_request': user_request,
            'llm_response': llm_response,
            'execution_result': result
        })
        
        return result
    
    def _build_prompt(self, user_request: str, context: Dict[str, Any]) -> str:
        """构建发送给LLM的完整prompt"""
        
        prompt_parts = [
            "# 用户请求",
            user_request,
            "",
            "# 项目上下文",
            ""
        ]
        
        # 添加项目结构
        if context.get('project_structure'):
            structure = context['project_structure']
            prompt_parts.extend([
                "## 项目结构",
                f"文件总数: {structure.get('file_count', 0)}",
                f"主要文件: {', '.join(structure.get('files', [])[:10])}",
                ""
            ])
        
        # 添加焦点文件内容
        if context.get('focus_file'):
            file_ctx = context['focus_file']
            prompt_parts.extend([
                f"## 当前文件: {file_ctx.path}",
                f"语言: {file_ctx.language}",
                f"行数: {file_ctx.line_count}",
                "",
                "```" + file_ctx.language,
                file_ctx.content,
                "```",
                ""
            ])
        
        # 添加Git信息
        if context.get('git_info', {}).get('is_git_repo'):
            git = context['git_info']
            prompt_parts.extend([
                "## Git状态",
                f"分支: {git.get('branch', 'unknown')}",
                ""
            ])
        
        return '\n'.join(prompt_parts)
    
    def _get_system_prompt(self) -> str:
        """返回系统提示词"""
        return """你是一个专业的AI编程助手。

你的职责：
1. 理解用户的编程需求
2. 分析项目上下文
3. 选择合适的工具完成任务
4. 生成高质量、可维护的代码

可用工具：
- read_file: 读取文件内容
- write_file: 创建或覆盖文件
- apply_diff: 使用diff格式精确修改文件
- run_command: 执行终端命令
- list_files: 列出目录文件

重要原则：
- 修改现有文件时优先使用apply_diff（更安全）
- 生成的代码要有适当的注释
- 考虑错误处理和边界情况
- 运行命令前检查依赖是否安装

响应格式：
- 如需调用工具，返回function_call格式
- 纯文本回复时要清晰、友好
"""
    
    def _execute_llm_response(self, llm_response: Dict[str, Any]) -> Dict[str, Any]:
        """执行LLM返回的操作"""
        
        response_type = llm_response.get('type')
        
        # 情况1：纯文本回复（不需要执行工具）
        if response_type == 'text':
            print(f"💬 AI回复: {llm_response.get('content')}")
            return {
                'success': True,
                'type': 'text_response',
                'content': llm_response.get('content')
            }
        
        # 情况2：需要调用工具
        elif response_type == 'function_call':
            function_name = llm_response.get('function')
            arguments = llm_response.get('arguments', {})
            reasoning = llm_response.get('reasoning', '')
            
            print(f"🔧 执行工具: {function_name}")
            print(f"📝 原因: {reasoning}")
            print(f"📋 参数: {json.dumps(arguments, indent=2, ensure_ascii=False)}")
            
            # 调用对应的工具函数
            result = self._call_tool(function_name, arguments)
            
            # 打印执行结果
            if result.get('success'):
                print(f"✅ 执行成功")
                if result.get('message'):
                    print(f"   {result['message']}")
            else:
                print(f"❌ 执行失败: {result.get('error')}")
            
            return result
        
        else:
            return {
                'success': False,
                'error': f'未知的响应类型: {response_type}'
            }
    
    def _call_tool(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用具体的工具函数"""
        
        if function_name == 'read_file':
            return self.toolkit.read_file(arguments['file_path'])
        
        elif function_name == 'write_file':
            return self.toolkit.write_file(
                arguments['file_path'],
                arguments['content']
            )
        
        elif function_name == 'apply_diff':
            return self.diff_processor.apply_diff(
                arguments['file_path'],
                arguments['diff_content']
            )
        
        elif function_name == 'run_command':
            return self.toolkit.run_command(
                arguments['command'],
                arguments.get('timeout', 30)
            )
        
        elif function_name == 'list_files':
            return self.toolkit.list_files(
                arguments.get('directory', '.'),
                arguments.get('pattern', '*')
            )
        
        else:
            return {
                'success': False,
                'error': f'未知的工具函数: {function_name}'
            }
    
    def chat(self, message: str):
        """简化的交互接口"""
        return self.process_request(message)


# ============================================================================
# 第六部分：使用示例
# ============================================================================

def demo():
    """演示AI编程Agent的使用"""
    
    print("\n" + "="*60)
    print("AI编程Agent - 演示程序")
    print("="*60 + "\n")
    
    # 创建Agent实例
    agent = AICodingAgent(project_root='.')
    
    print("📌 演示场景1：创建新文件")
    print("-" * 60)
    result1 = agent.chat("创建一个名为hello.py的文件，包含一个打印Hello World的函数")
    print(f"\n结果: {json.dumps(result1, indent=2, ensure_ascii=False)}")
    
    print("\n\n📌 演示场景2：读取文件")
    print("-" * 60)
    result2 = agent.chat("读取hello.py文件的内容")
    print(f"\n结果: {json.dumps(result2, indent=2, ensure_ascii=False)}")
    
    print("\n\n📌 演示场景3：修改文件（使用Diff）")
    print("-" * 60)
    result3 = agent.chat("优化hello.py，添加文档字符串和类型注解")
    print(f"\n结果: {json.dumps(result3, indent=2, ensure_ascii=False)}")
    
    print("\n\n📌 演示场景4：执行命令")
    print("-" * 60)
    result4 = agent.chat("运行hello.py文件")
    print(f"\n结果: {json.dumps(result4, indent=2, ensure_ascii=False)}")
    
    print("\n" + "="*60)
    print("演示完成！")
    print("="*60)


def interactive_mode():
    """交互式命令行模式"""
    
    print("\n" + "="*60)
    print("AI编程Agent - 交互模式")
    print("="*60)
    print("\n可用命令:")
    print("  - 输入任何编程请求（如：创建文件、修改代码等）")
    print("  - 输入 'exit' 或 'quit' 退出")
    print("  - 输入 'history' 查看对话历史")
    print("  - 输入 'clear' 清空历史")
    print("-" * 60 + "\n")
    
    agent = AICodingAgent(project_root='.')
    
    while True:
        try:
            # 获取用户输入
            user_input = input("\n💬 你: ").strip()
            
            if not user_input:
                continue
            
            # 处理特殊命令
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\n👋 再见！")
                break
            
            elif user_input.lower() == 'history':
                print("\n📜 对话历史:")
                for i, record in enumerate(agent.conversation_history, 1):
                    print(f"\n[{i}] 用户: {record['user_request']}")
                    print(f"    结果: {record['execution_result'].get('message', 'N/A')}")
                continue
            
            elif user_input.lower() == 'clear':
                agent.conversation_history.clear()
                print("\n✅ 历史已清空")
                continue
            
            # 处理普通请求
            print("\n🤖 Agent处理中...")
            result = agent.chat(user_input)
            
            # 显示结果
            if result.get('success'):
                print(f"\n✅ 完成！")
                if result.get('content'):
                    print(f"\n{result['content']}")
            else:
                print(f"\n❌ 失败: {result.get('error')}")
        
        except KeyboardInterrupt:
            print("\n\n👋 收到中断信号，退出...")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {str(e)}")


def advanced_demo():
    """高级演示：多步骤任务"""
    
    print("\n" + "="*60)
    print("高级演示：构建一个完整的Web API项目")
    print("="*60 + "\n")
    
    agent = AICodingAgent(project_root='./demo_project')
    
    # 步骤1：创建项目结构
    print("📁 步骤1：创建项目结构")
    print("-" * 60)
    agent.chat("列出当前目录的所有文件")
    
    # 步骤2：创建main.py
    print("\n\n📝 步骤2：创建Flask应用主文件")
    print("-" * 60)
    agent.process_request("""
创建一个main.py文件，包含：
1. Flask应用初始化
2. 一个GET /api/hello端点，返回JSON
3. 运行在5000端口
""")
    
    # 步骤3：创建requirements.txt
    print("\n\n📦 步骤3：创建依赖文件")
    print("-" * 60)
    agent.chat("创建requirements.txt，包含Flask和常用依赖")
    
    # 步骤4：创建README
    print("\n\n📖 步骤4：创建项目文档")
    print("-" * 60)
    agent.chat("创建README.md，说明项目的安装和使用方法")
    
    # 步骤5：运行项目
    print("\n\n🚀 步骤5：安装依赖并测试")
    print("-" * 60)
    agent.chat("安装requirements.txt中的依赖")
    
    print("\n" + "="*60)
    print("项目构建完成！文件已保存到 ./demo_project/")
    print("="*60)


def test_diff_functionality():
    """测试Diff功能的专项演示"""
    
    print("\n" + "="*60)
    print("Diff功能测试")
    print("="*60 + "\n")
    
    # 1. 创建测试文件
    print("📝 创建测试文件...")
    test_content = """def calculate(a, b):
    result = a + b
    return result

def main():
    x = 10
    y = 20
    print(calculate(x, y))
"""
    
    with open('test_diff.py', 'w') as f:
        f.write(test_content)
    print("✅ 创建完成: test_diff.py")
    
    # 2. 生成Diff
    print("\n📊 生成修改方案（Diff）...")
    new_content = """def calculate(a: int, b: int) -> int:
    \"\"\"计算两个数的和\"\"\"
    result = a + b
    return result

def main():
    x = 10
    y = 20
    print(f"结果: {calculate(x, y)}")

if __name__ == '__main__':
    main()
"""
    
    diff = DiffProcessor.generate_diff('test_diff.py', new_content)
    print(f"生成的Diff:\n{diff}")
    
    # 3. 应用Diff
    print("\n🔧 应用Diff到文件...")
    result = DiffProcessor.apply_diff('test_diff.py', diff)
    print(f"结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # 4. 验证修改
    print("\n✅ 验证修改后的文件内容:")
    with open('test_diff.py', 'r') as f:
        print(f.read())
    
    # 5. 清理
    import os
    os.remove('test_diff.py')
    print("\n🧹 清理测试文件完成")


def benchmark_context_collection():
    """性能测试：上下文收集速度"""
    
    print("\n" + "="*60)
    print("性能测试：上下文收集")
    print("="*60 + "\n")
    
    import time
    
    collector = ContextCollector('.')
    
    # 测试1：扫描项目结构
    print("📊 测试1：扫描项目结构")
    start = time.time()
    structure = collector._scan_project_structure(max_depth=3)
    elapsed = time.time() - start
    print(f"   文件数: {structure['file_count']}")
    print(f"   耗时: {elapsed:.3f}秒")
    
    # 测试2：读取文件内容
    if structure['files']:
        print("\n📊 测试2：读取文件内容")
        test_file = structure['files'][0]
        start = time.time()
        file_ctx = collector._get_file_context(test_file)
        elapsed = time.time() - start
        print(f"   文件: {test_file}")
        print(f"   行数: {file_ctx.line_count if file_ctx else 'N/A'}")
        print(f"   耗时: {elapsed:.3f}秒")
    
    # 测试3：完整上下文收集
    print("\n📊 测试3：完整上下文收集")
    start = time.time()
    full_context = collector.collect_full_context()
    elapsed = time.time() - start
    print(f"   耗时: {elapsed:.3f}秒")
    print(f"   上下文大小: ~{len(str(full_context)) / 1024:.1f} KB")


# ============================================================================
# 主入口
# ============================================================================

if __name__ == '__main__':
    import sys
    
    print("""
╔════════════════════════════════════════════════════════════╗
║          AI 编程 Agent - 最小可用版本                       ║
║          Minimal Viable AI Coding Agent                    ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    # 命令行参数处理
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        
        if mode == 'demo':
            demo()
        elif mode == 'interactive':
            interactive_mode()
        elif mode == 'advanced':
            advanced_demo()
        elif mode == 'test-diff':
            test_diff_functionality()
        elif mode == 'benchmark':
            benchmark_context_collection()
        else:
            print(f"❌ 未知模式: {mode}")
            print("\n可用模式:")
            print("  python agent.py demo          # 基础演示")
            print("  python agent.py interactive   # 交互模式")
            print("  python agent.py advanced      # 高级演示")
            print("  python agent.py test-diff     # 测试Diff功能")
            print("  python agent.py benchmark     # 性能测试")
    else:
        # 默认运行交互模式
        print("提示：可以添加参数运行不同模式")
        print("例如: python agent.py demo\n")
        
        choice = input("请选择模式 [1]演示 [2]交互 [3]高级 [4]测试Diff [5]性能测试: ").strip()
        
        if choice == '1':
            demo()
        elif choice == '2':
            interactive_mode()
        elif choice == '3':
            advanced_demo()
        elif choice == '4':
            test_diff_functionality()
        elif choice == '5':
            benchmark_context_collection()
        else:
            print("使用交互模式...")
            interactive_mode()