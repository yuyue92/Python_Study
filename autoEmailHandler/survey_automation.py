#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化调查问卷报表系统 - 一体化脚本
功能：从源邮箱读取调查反馈 → 生成Excel报表 → 发送到目标邮箱

使用说明：
1. 在源邮箱和目标邮箱后台开启SMTP/IMAP服务，获取授权码
2. 修改下方 CONFIG 区域的配置
3. 运行：python survey_automation.py
"""

# ========================================
# 配置区域 - 请根据实际情况修改
# ========================================
class CONFIG:
    # 源邮箱配置（读取调查反馈）
    SOURCE_EMAIL = "yy18825237023@126.com"
    SOURCE_PASSWORD = ""  # ← 必填：授权码
    SOURCE_IMAP_HOST = "imap.126.com"
    SOURCE_POP3_HOST = "pop.126.com"
    
    # 目标邮箱配置（发送报表）
    TARGET_EMAIL = "18825237023@163.com"  # 接收报表的邮箱
    
    # 发件邮箱配置（SMTP）
    SMTP_EMAIL = "yy18825237023@126.com"
    SMTP_PASSWORD = ""  # ← 必填：授权码
    SMTP_HOST = "smtp.126.com"
    SMTP_PORT = 465  # 465=SSL, 587=STARTTLS
    SMTP_USE_SSL = True  # 465端口用True，587端口用False
    SMTP_USE_TLS = False  # 587端口用True，465端口用False
    
    # 报表配置
    FETCH_EMAIL_LIMIT = 11  # 读取最近N封邮件
    REPORT_FILENAME = "survey_report.xlsx"
    EMAIL_SUBJECT_FILTER = "Customer Feedback Survey"  # 只处理包含此关键词的邮件
    
    # 发送报表的邮件配置
    REPORT_EMAIL_SUBJECT = "调查问卷自动报表 - {date}"
    REPORT_EMAIL_BODY = """
<div style="font-family: Arial, sans-serif; line-height: 1.6;">
    <h2>调查问卷数据报表</h2>
    <p>您好，</p>
    <p>这是系统自动生成的调查问卷数据报表，详见附件Excel文件。</p>
    <p><strong>报表统计：</strong></p>
    <ul>
        <li>数据条数：{count} 条</li>
        <li>生成时间：{datetime}</li>
    </ul>
    <p>如有疑问，请联系系统管理员。</p>
    <hr style="border: none; border-top: 1px solid #ddd;">
    <p style="color: #666; font-size: 12px;">此邮件由系统自动发送，请勿直接回复。</p>
</div>
"""

# ========================================
# 依赖库导入
# ========================================
import imaplib
import poplib
import email
import re
import sys
import ssl
import time
import smtplib
from datetime import datetime
from email.header import decode_header
from email import policy
from email.parser import BytesParser
from email.message import EmailMessage
from email.utils import formatdate
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Pandas 导入（如果没有安装，提示用户）
try:
    import pandas as pd
    from openpyxl import Workbook
except ImportError:
    print("错误：缺少必要的依赖库。请安装：")
    print("  pip install pandas openpyxl")
    sys.exit(1)

# ========================================
# 邮件读取模块
# ========================================
def decode_header_value(raw):
    """解码邮件头部"""
    if not raw:
        return ""
    parts = decode_header(raw)
    out = []
    for part, enc in parts:
        if isinstance(part, bytes):
            try:
                out.append(part.decode(enc or "utf-8", errors="ignore"))
            except Exception:
                out.append(part.decode("utf-8", errors="ignore"))
        else:
            out.append(part)
    return "".join(out)

def extract_body(msg):
    """提取邮件正文"""
    def strip_html(html):
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_maintype() == "multipart":
                continue
            if part.get_content_disposition() == "attachment":
                continue
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True) or b""
                charset = part.get_content_charset() or "utf-8"
                try:
                    return payload.decode(charset, errors="ignore").strip()
                except Exception:
                    return payload.decode("utf-8", errors="ignore").strip()
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                payload = part.get_payload(decode=True) or b""
                charset = part.get_content_charset() or "utf-8"
                try:
                    html = payload.decode(charset, errors="ignore")
                except Exception:
                    html = payload.decode("utf-8", errors="ignore")
                return strip_html(html)
        return ""
    else:
        payload = msg.get_payload(decode=True) or b""
        charset = msg.get_content_charset() or "utf-8"
        try:
            text = payload.decode(charset, errors="ignore")
        except Exception:
            text = payload.decode("utf-8", errors="ignore")
        if text.strip().startswith("<"):
            return strip_html(text)
        return text.strip()

def try_imap_fetch(user, pwd, host, limit):
    """尝试通过IMAP获取邮件"""
    ctx = ssl.create_default_context()
    with imaplib.IMAP4_SSL(host=host, port=993, ssl_context=ctx) as conn:
        conn.login(user, pwd)
        typ, data = conn.select("INBOX", readonly=True)
        if typ != "OK":
            conn.select("INBOX", readonly=False)
        
        typ, ids = conn.search(None, "ALL")
        if typ != "OK":
            raise RuntimeError("IMAP search failed")
        id_list = ids[0].split()
        if not id_list:
            return []
        
        msgs = []
        for eid in id_list[-limit:]:
            typ, raw = conn.fetch(eid, "(RFC822)")
            if typ == "OK" and raw and isinstance(raw[0], tuple):
                msg = email.message_from_bytes(raw[0][1], policy=policy.default)
                msgs.append(msg)
        return msgs

def try_pop3_fetch(user, pwd, host, limit, max_fetch=200):
    """POP3备用方案"""
    pop = None
    try:
        pop = poplib.POP3_SSL(host, 995, timeout=30)
        pop.user(user)
        pop.pass_(pwd)
    except Exception:
        if pop:
            try: pop.quit()
            except Exception: pass
        try:
            pop = poplib.POP3(host, 110, timeout=30)
            pop.user(user)
            pop.pass_(pwd)
            try:
                pop.stls()
            except Exception:
                pass
        except Exception as e:
            raise RuntimeError(f"POP3连接失败：{e}")
    
    try:
        count, _ = pop.stat()
        if count <= 0:
            return []
        
        start = max(1, count - max_fetch + 1)
        last_indices = list(range(max(start, count - limit + 1), count + 1))
        
        msgs = []
        for i in last_indices:
            resp, lines, octets = pop.retr(i)
            raw = b"\r\n".join(lines)
            msg = BytesParser(policy=policy.default).parsebytes(raw)
            msgs.append(msg)
        return msgs
    finally:
        if pop:
            try:
                pop.quit()
            except Exception:
                pass

def fetch_survey_emails():
    """从源邮箱获取调查反馈邮件"""
    print(f"\n[1/4] 正在从 {CONFIG.SOURCE_EMAIL} 读取邮件...")
    
    # 尝试IMAP
    try:
        msgs = try_imap_fetch(
            CONFIG.SOURCE_EMAIL,
            CONFIG.SOURCE_PASSWORD,
            CONFIG.SOURCE_IMAP_HOST,
            CONFIG.FETCH_EMAIL_LIMIT
        )
        source = "IMAP"
    except Exception as e:
        print(f"  IMAP失败: {e}")
        print("  切换到POP3...")
        msgs = try_pop3_fetch(
            CONFIG.SOURCE_EMAIL,
            CONFIG.SOURCE_PASSWORD,
            CONFIG.SOURCE_POP3_HOST,
            CONFIG.FETCH_EMAIL_LIMIT
        )
        source = "POP3"
    
    # 筛选符合条件的邮件
    survey_bodies = []
    for msg in msgs:
        subject = decode_header_value(msg.get("Subject"))
        if subject and CONFIG.EMAIL_SUBJECT_FILTER in subject:
            body = extract_body(msg)
            if body:
                survey_bodies.append(body)
    
    print(f"  ✓ 通过{source}获取到 {len(msgs)} 封邮件")
    print(f"  ✓ 筛选出 {len(survey_bodies)} 封调查反馈")
    return survey_bodies

# ========================================
# 报表生成模块
# ========================================
REPORT_COLUMNS = [
    "Ref ID",
    "Q1 Score", "Q1 Text",
    "Q2 Score", "Q2 Text",
    "Q3 Score", "Q3 Text",
    "Q4 Score", "Q4 Text",
    "Q5 Score", "Q5 Text",
    "Submit Date", "Submit Time"
]

RE_SUBMIT = re.compile(
    r"submit\s*date\s*:\s*(?P<date>\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s*[-–—]\s*(?P<time>\d{1,2}:\d{2})",
    re.IGNORECASE
)
RE_REFID = re.compile(r"ref\s*id\s*[:#-]?\s*(?P<id>[A-Za-z0-9_-]+)", re.IGNORECASE)
RE_QA = re.compile(
    r"^(?:Q\s*)?(?P<num>[1-5])\s*(?P<sub>[ab])\s*[:\-\)\.]\s*(?P<val>.+?)\s*$",
    re.IGNORECASE
)

def parse_submit(line: str) -> Optional[Tuple[str, str]]:
    """解析提交日期时间"""
    m = RE_SUBMIT.search(line)
    if not m:
        return None
    raw_date = m.group("date").strip()
    raw_time = m.group("time").strip()
    
    day, month, year = re.split(r"[/-]", raw_date)
    if len(year) == 2:
        year = "20" + year
    day = day.zfill(2)
    month = month.zfill(2)
    
    try:
        _ = datetime(int(year), int(month), int(day))
        std_date = f"{day}/{month}/{year}"
    except ValueError:
        std_date = raw_date
    
    hh, mm = raw_time.split(":")
    std_time = f"{hh.zfill(2)}:{mm.zfill(2)}"
    
    return std_date, std_time

def parse_refid(text: str) -> Optional[str]:
    """解析Ref ID"""
    m = RE_REFID.search(text)
    return m.group("id").strip() if m else None

def parse_answers(text: str) -> Dict[str, str]:
    """解析问卷答案"""
    answers: Dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        m = RE_QA.match(line)
        if m:
            k = f"{m.group('num').lower()}{m.group('sub').lower()}"
            v = m.group("val").strip()
            answers[k] = v
    return answers

def parse_single_email(body: str) -> Dict[str, str]:
    """解析单封邮件内容"""
    ref_id = parse_refid(body) or ""
    submit_dt = parse_submit(body) or ("", "")
    submit_date, submit_time = submit_dt
    
    answers = parse_answers(body)
    
    return {
        "Ref ID": ref_id,
        "Q1 Score": answers.get("1a", ""),
        "Q1 Text": answers.get("1b", ""),
        "Q2 Score": answers.get("2a", ""),
        "Q2 Text": answers.get("2b", ""),
        "Q3 Score": answers.get("3a", ""),
        "Q3 Text": answers.get("3b", ""),
        "Q4 Score": answers.get("4a", ""),
        "Q4 Text": answers.get("4b", ""),
        "Q5 Score": answers.get("5a", ""),
        "Q5 Text": answers.get("5b", ""),
        "Submit Date": submit_date,
        "Submit Time": submit_time,
    }

def build_report(texts: List[str], out_xlsx: str) -> pd.DataFrame:
    """生成Excel报表"""
    print(f"\n[2/4] 正在生成报表...")
    
    rows = []
    for body in texts:
        try:
            rows.append(parse_single_email(body))
        except Exception as e:
            print(f"  警告：解析单封邮件失败 - {e}")
            ref_id = parse_refid(body) or ""
            dt = parse_submit(body) or ("", "")
            rows.append({
                "Ref ID": ref_id,
                "Q1 Score": "", "Q1 Text": "",
                "Q2 Score": "", "Q2 Text": "",
                "Q3 Score": "", "Q3 Text": "",
                "Q4 Score": "", "Q4 Text": "",
                "Q5 Score": "", "Q5 Text": "",
                "Submit Date": dt[0], "Submit Time": dt[1],
            })
    
    df = pd.DataFrame(rows, columns=REPORT_COLUMNS)
    
    # 去重
    df = df.drop_duplicates(subset=["Ref ID", "Submit Date", "Submit Time"], keep="first")
    
    # 转换评分为数值
    for col in ["Q1 Score", "Q2 Score", "Q3 Score", "Q4 Score", "Q5 Score"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    # 导出Excel
    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Survey")
    
    print(f"  ✓ 报表已生成：{out_xlsx}")
    print(f"  ✓ 数据条数：{len(df)} 条")
    return df

# ========================================
# 邮件发送模块
# ========================================
def send_report_email(xlsx_path: str, record_count: int):
    """发送报表邮件"""
    print(f"\n[3/4] 正在发送报表到 {CONFIG.TARGET_EMAIL}...")
    
    # 准备邮件内容
    now = datetime.now()
    subject = CONFIG.REPORT_EMAIL_SUBJECT.format(date=now.strftime("%Y-%m-%d"))
    html_body = CONFIG.REPORT_EMAIL_BODY.format(
        count=record_count,
        datetime=now.strftime("%Y-%m-%d %H:%M:%S")
    )
    
    # 创建邮件
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = CONFIG.SMTP_EMAIL
    msg["To"] = CONFIG.TARGET_EMAIL
    msg["Date"] = formatdate(localtime=True)
    
    # 设置正文
    text_body = re.sub(r"<[^>]+>", "", html_body)
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")
    
    # 添加附件
    xlsx_file = Path(xlsx_path)
    if not xlsx_file.exists():
        raise FileNotFoundError(f"报表文件不存在：{xlsx_path}")
    
    with xlsx_file.open("rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=xlsx_file.name
        )
    
    # 发送邮件
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if CONFIG.SMTP_USE_SSL:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(CONFIG.SMTP_HOST, CONFIG.SMTP_PORT, context=context)
            else:
                server = smtplib.SMTP(CONFIG.SMTP_HOST, CONFIG.SMTP_PORT)
                server.ehlo()
                if CONFIG.SMTP_USE_TLS:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                    server.ehlo()
            
            server.login(CONFIG.SMTP_EMAIL, CONFIG.SMTP_PASSWORD)
            server.sendmail(CONFIG.SMTP_EMAIL, [CONFIG.TARGET_EMAIL], msg.as_string())
            server.quit()
            
            print(f"  ✓ 邮件发送成功")
            return
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"  重试 {attempt + 1}/{max_retries}...")
            time.sleep(2 ** attempt)

# ========================================
# 主流程
# ========================================
def validate_config():
    """验证配置"""
    print("\n[0/4] 检查配置...")
    errors = []
    
    if not CONFIG.SOURCE_PASSWORD:
        errors.append("  ✗ SOURCE_PASSWORD（源邮箱授权码）未设置")
    if not CONFIG.SMTP_PASSWORD:
        errors.append("  ✗ SMTP_PASSWORD（发件邮箱授权码）未设置")
    
    if errors:
        print("\n配置错误：")
        for err in errors:
            print(err)
        print("\n请在脚本顶部 CONFIG 类中填写必要的配置信息。")
        return False
    
    print("  ✓ 配置检查通过")
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("自动化调查问卷报表系统")
    print("=" * 60)
    
    # 验证配置
    if not validate_config():
        sys.exit(1)
    
    try:
        # 步骤1：读取邮件
        survey_bodies = fetch_survey_emails()
        if not survey_bodies:
            print("\n未找到调查反馈邮件。")
            sys.exit(0)
        
        # 步骤2：生成报表
        df = build_report(survey_bodies, CONFIG.REPORT_FILENAME)
        
        # 步骤3：发送报表
        send_report_email(CONFIG.REPORT_FILENAME, len(df))
        
        # 完成
        print("\n[4/4] 任务完成！")
        print("=" * 60)
        print(f"✓ 共处理 {len(survey_bodies)} 封反馈邮件")
        print(f"✓ 生成 {len(df)} 条有效记录")
        print(f"✓ 报表已发送至 {CONFIG.TARGET_EMAIL}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 错误：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()