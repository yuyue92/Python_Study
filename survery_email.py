import imaplib
import email
from email.header import decode_header
import logging
import getpass

import re
import sys

# --- IMAP Modified UTF-7 helpers ---
def imap_decode(name: str) -> str:
    """服务器返回的邮箱名（Modified UTF-7） -> Python 字符串"""
    try:
        return name.encode('ascii').decode('imap4-utf-7')
    except Exception:
        return name  # 失败就原样返回

def imap_encode(name: str) -> bytes:
    """Python 字符串 -> Modified UTF-7（给 select 使用）"""
    try:
        return name.encode('imap4-utf-7')
    except Exception:
        return name.encode()

LIST_MAILBOX_RE = re.compile(r'^[\(\)\\A-Za-z0-9\s]*"[^"]*"\s+"([^"]+)"$')

import time

def _send_imap_id(m):
    # 发送 RFC2971 ID，部分网易服务端需要此信息才放行
    try:
        typ, caps = m.capability()
        cap_bytes = b" ".join(caps or [])
        if b"ID" in cap_bytes.upper():
            # 示例ID字段，可按需调整
            args = '("name" "SurveyBot" "version" "1.0" "vendor" "YourCompany" "support" "support@yourco.com")'
            typ, resp = m._simple_command("ID", args)
            m._get_response()  # 取回OK
    except Exception as e:
        logger.debug(f"发送 IMAP ID 时忽略异常: {e}")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EmailReader:
    def __init__(self, email_config):
        self.email_config = email_config
        self.mail = None
        
    def connect_email(self):
        """连接到邮箱服务器并测试可用文件夹"""
        try:
            logger.info(f"正在连接邮箱服务器: {self.email_config['imap_server']}")
            self.mail = imaplib.IMAP4_SSL(self.email_config['imap_server'])
            self.mail.login(self.email_config['email'], self.email_config['password'])

            # 关键：登录后立即发送 ID
            _send_imap_id(self.mail)
            time.sleep(0.2)

            # 列出文件夹
            logger.info("获取可用邮箱文件夹...")
            status, folders = self.mail.list()
            mailbox_names_raw = []
            mailbox_names_decoded = []

            if status == 'OK' and folders:
                logger.info("可用的邮箱文件夹:")
                for raw in folders:
                    line = raw.decode('utf-8', errors='ignore')
                    logger.info(f"  {line}")
                    # 正确抓取引号里的邮箱名
                    m = LIST_MAILBOX_RE.match(line.strip())
                    if m:
                        raw_name = m.group(1)
                    else:
                        # 兼容一些变体：最后一对引号里的内容
                        parts = line.split('"')
                        raw_name = parts[-2] if len(parts) >= 3 else line.rsplit(' ', 1)[-1]

                    decoded_name = imap_decode(raw_name)
                    mailbox_names_raw.append(raw_name)
                    mailbox_names_decoded.append(decoded_name)
                    logger.info(f"    解析出的文件夹名(raw): '{raw_name}' -> decoded: '{decoded_name}'")
            else:
                logger.warning("无法获取文件夹列表")

            # 直接尝试选择 INBOX（只读更稳妥）
            logger.info("直接选择 INBOX 文件夹...")
            status, data = self.mail.select("INBOX", readonly=True)
            if status == 'OK':
                logger.info("✅ 成功选择 INBOX")
            else:
                # 打印服务端具体原因
                reason = (data[0].decode(errors='ignore') if data and isinstance(data[0], (bytes, bytearray)) else str(data))
                logger.error(f"选择 INBOX 失败: {status} | {reason}")

                # 回退1：尝试小写/不同大小写
                for cand in ("Inbox", "inbox"):
                    status, data = self.mail.select(cand, readonly=True)
                    if status == 'OK':
                        logger.info(f"✅ 成功选择 {cand}")
                        break
                # 回退2：遍历 LIST 里的原样名字（用 UTF-7 编码传给服务器）
                if status != 'OK':
                    logger.info("尝试用 LIST 返回的文件夹名逐个选择（含 UTF-7）...")
                    for raw_name, dec_name in zip(mailbox_names_raw, mailbox_names_decoded):
                        # 优先挑看起来是 INBOX 的
                        if dec_name.upper() == "INBOX" or raw_name.upper() == "INBOX":
                            try_names = [raw_name, dec_name]
                        else:
                            # 也可尝试其他文件夹，至少保证能选中一个
                            try_names = [raw_name]

                        for name in try_names:
                            # 用字节（UTF-7）尝试
                            status, data = self.mail.select(imap_encode(name), readonly=True)
                            if status == 'OK':
                                logger.info(f"✅ 成功选择文件夹: {name}")
                                break
                        if status == 'OK':
                            break

                if status != 'OK':
                    reason = (data[0].decode(errors='ignore') if data and isinstance(data[0], (bytes, bytearray)) else str(data))
                    logger.error(f"最终仍无法选择任何文件夹: {status} | {reason}")
                    return False

            # 走到这里说明已选中某个文件夹，继续统计
            status, messages = self.mail.search(None, "ALL")
            if status == 'OK':
                email_ids = messages[0].split()
                logger.info(f"📧 当前文件夹中有 {len(email_ids)} 封邮件")
                return True
            else:
                logger.error(f"搜索邮件失败: {status}")
                return False

        except Exception as e:
            logger.error(f"❌ 连接邮箱失败: {e}")
            return False

    def test_search_all_emails(self):
        """测试搜索所有邮件"""
        try:
            if not self.mail:
                logger.error("邮箱未连接")
                return []
                
            # 搜索所有邮件
            logger.info("搜索所有邮件...")
            status, messages = self.mail.search(None, "ALL")
            
            if status != 'OK':
                logger.error(f"搜索失败: {status}")
                return []
                
            email_ids = messages[0].split()
            logger.info(f"✅ 找到 {len(email_ids)} 封邮件")
            return email_ids
            
        except Exception as e:
            logger.error(f"❌ 搜索邮件失败: {e}")
            return []
    
    def get_email_content(self, email_id):
        """获取邮件内容"""
        try:
            logger.info(f"获取邮件内容: {email_id}")
            
            # 使用不同的fetch命令
            status, msg_data = self.mail.fetch(email_id, "(BODY.PEEK[])")
            if status != 'OK':
                # 尝试另一种方式
                status, msg_data = self.mail.fetch(email_id, "(RFC822)")
                if status != 'OK':
                    logger.warning(f"获取邮件 {email_id} 内容失败")
                    return None
                
            # 处理响应数据
            if isinstance(msg_data[0], tuple):
                msg_bytes = msg_data[0][1]
            else:
                msg_bytes = msg_data[0]
                
            msg = email.message_from_bytes(msg_bytes)
            
            # 解析邮件基本信息
            subject = "无主题"
            if msg["Subject"]:
                decoded_parts = decode_header(msg["Subject"])
                subject_parts = []
                for part, encoding in decoded_parts:
                    if isinstance(part, bytes):
                        try:
                            decoded_part = part.decode(encoding if encoding else 'utf-8', errors='ignore')
                            subject_parts.append(decoded_part)
                        except:
                            subject_parts.append(str(part))
                    else:
                        subject_parts.append(part)
                subject = ''.join(subject_parts)
            
            from_header = msg["From"] or "未知发件人"
            date = msg["Date"] or "未知日期"
            
            # 提取邮件正文
            body = self._extract_email_body(msg)
            
            return {
                'id': email_id.decode() if isinstance(email_id, bytes) else str(email_id),
                'subject': subject,
                'from': from_header,
                'date': date,
                'body': body
            }
            
        except Exception as e:
            logger.error(f"获取邮件内容失败: {e}")
            return None
    
    def _extract_email_body(self, msg):
        """提取邮件正文内容"""
        body = ""
        try:
            if msg.is_multipart():
                logger.info("邮件是多部分的，遍历各部分...")
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition", ""))
                    
                    logger.info(f"处理部分: {content_type}, {content_disposition}")
                    
                    # 跳过附件
                    if "attachment" in content_disposition:
                        logger.info("跳过附件")
                        continue
                    
                    if content_type == "text/plain":
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or 'utf-8'
                            try:
                                body = payload.decode(charset, errors='ignore')
                                logger.info(f"成功提取纯文本内容，长度: {len(body)}")
                                if body.strip():  # 如果有内容就停止
                                    break
                            except (UnicodeDecodeError, LookupError):
                                body = payload.decode('utf-8', errors='ignore')
                                logger.info(f"使用utf-8解码纯文本内容，长度: {len(body)}")
                                if body.strip():
                                    break
                    elif content_type == "text/html" and not body:
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or 'utf-8'
                            try:
                                body = payload.decode(charset, errors='ignore')
                                logger.info(f"提取HTML内容，长度: {len(body)}")
                            except (UnicodeDecodeError, LookupError):
                                body = payload.decode('utf-8', errors='ignore')
                                logger.info(f"使用utf-8解码HTML内容，长度: {len(body)}")
            else:
                logger.info("邮件是单部分的")
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or 'utf-8'
                    try:
                        body = payload.decode(charset, errors='ignore')
                        logger.info(f"成功解码单部分内容，长度: {len(body)}")
                    except (UnicodeDecodeError, LookupError):
                        body = payload.decode('utf-8', errors='ignore')
                        logger.info(f"使用utf-8解码单部分内容，长度: {len(body)}")
            
            # 如果是HTML，简单清理
            if body and body.strip().startswith('<'):
                import re
                logger.info("清理HTML标签...")
                body = re.sub(r'<[^>]+>', ' ', body)
                body = re.sub(r'\s+', ' ', body).strip()
                logger.info(f"清理HTML后长度: {len(body)}")
                
        except Exception as e:
            logger.error(f"提取邮件正文时出错: {e}")
            
        return body
    
    def test_read_emails(self, limit=3):
        """测试读取邮件内容"""
        if not self.connect_email():
            return False
        
        email_ids = self.test_search_all_emails()
        
        if not email_ids:
            logger.error("没有找到任何邮件")
            self._safe_logout()
            return False
        
        # 只读取前几封邮件进行测试
        test_ids = email_ids[:limit] if len(email_ids) > limit else email_ids
        logger.info(f"测试读取 {len(test_ids)} 封邮件")
        
        successful_reads = 0
        for i, email_id in enumerate(test_ids, 1):
            logger.info(f"\n{'='*50}")
            logger.info(f"处理第 {i}/{len(test_ids)} 封邮件")
            
            email_content = self.get_email_content(email_id)
            if email_content:
                self._print_email_summary(email_content)
                if email_content['body']:
                    successful_reads += 1
            else:
                logger.warning(f"无法获取邮件 {email_id} 的内容")
        
        logger.info(f"成功读取 {successful_reads}/{len(test_ids)} 封邮件的内容")
        self._safe_logout()
        return successful_reads > 0
    
    def _print_email_summary(self, email_content):
        """打印邮件摘要"""
        print(f"\n📧 邮件ID: {email_content['id']}")
        print(f"📋 主题: {email_content['subject']}")
        print(f"👤 发件人: {email_content['from']}")
        print(f"📅 日期: {email_content['date']}")
        if email_content['body']:
            preview = email_content['body'][:200] + ('...' if len(email_content['body']) > 200 else '')
            print(f"📝 正文预览: {preview}")
            print(f"📊 正文长度: {len(email_content['body'])} 字符")
        else:
            print("📝 正文: [空]")
        print("-" * 50)

    def _safe_logout(self):
        """安全地关闭邮箱连接"""
        try:
            if self.mail:
                try:
                    # 有些服务器在未选中任何邮箱时调用 close() 会报错
                    self.mail.close()
                except Exception as e:
                    logger.debug(f"close() 忽略的异常: {e}")
                try:
                    self.mail.logout()
                finally:
                    logger.info("✅ 邮箱连接已安全关闭")
        except Exception as e:
            logger.warning(f"关闭邮箱连接时出现警告: {e}")

def get_email_config():
    """安全地获取邮箱配置"""
    print("请输入邮箱配置:")
    
    email_config = {
        'imap_server': 'imap.126.com',
        'email': 'yy18825237023@126.com',
        'password': getpass.getpass("请输入邮箱密码: ")
    }
    # EDuaH3BumbLK7HEi
    return email_config

def main():
    """主函数"""
    print("邮件内容读取测试")
    print("=" * 40)
    
    # 获取配置
    email_config = get_email_config()
    
    # 创建阅读器
    reader = EmailReader(email_config)
    
    # 测试读取邮件
    print("\n开始测试读取邮件内容...", email_config)
    success = reader.test_read_emails(limit=3)
    
    if success:
        print("\n✅ 测试完成！邮件内容读取成功")
    else:
        print("\n❌ 测试失败")

if __name__ == "__main__":

    main()
