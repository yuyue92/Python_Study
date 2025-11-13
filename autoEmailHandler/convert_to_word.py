import win32com.client as win32
import os

def create_word_doc_from_markdown(md_file_path, docx_file_path):
    """
    使用win32com直接创建Word文档（无需python-docx）
    """
    try:
        # 读取Markdown文件
        with open(md_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 启动Word应用
        word = win32.Dispatch("Word.Application")
        word.Visible = False  # 后台运行
        
        # 创建新文档
        doc = word.Documents.Add()
        
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                # 空行
                word.Selection.TypeParagraph()
                continue
                
            # 处理标题
            if line.startswith('### '):
                word.Selection.Style = doc.Styles("Heading 3")
                word.Selection.TypeText(line[4:])
            elif line.startswith('## '):
                word.Selection.Style = doc.Styles("Heading 2")
                word.Selection.TypeText(line[3:])
            elif line.startswith('# '):
                word.Selection.Style = doc.Styles("Heading 1")
                word.Selection.TypeText(line[2:])
                
            # 处理列表项
            elif line.startswith('- ') or line.startswith('* '):
                word.Selection.Style = doc.Styles("Normal")
                word.Selection.TypeText("• " + line[2:])
                
            # 处理普通段落
            else:
                word.Selection.Style = doc.Styles("Normal")
                # 简单处理加粗
                if '**' in line:
                    parts = line.split('**')
                    for i, part in enumerate(parts):
                        if i % 2 == 1:  # 加粗部分
                            word.Selection.Font.Bold = True
                            word.Selection.TypeText(part)
                            word.Selection.Font.Bold = False
                        else:
                            word.Selection.TypeText(part)
                else:
                    word.Selection.TypeText(line)
            
            word.Selection.TypeParagraph()
        
        # 保存文档
        doc.SaveAs(os.path.abspath(docx_file_path))
        doc.Close()
        word.Quit()
        
        print(f"文档已成功保存为: {docx_file_path}")
        
    except Exception as e:
        print(f"创建Word文档时出错: {e}")

# 使用示例
if __name__ == "__main__":
    create_word_doc_from_markdown('fetch_feedback_and_send_spec_en.md', 'Technical_Specification.docx')
