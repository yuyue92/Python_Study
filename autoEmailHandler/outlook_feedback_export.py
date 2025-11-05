#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Outlook Feedback Export — 拉取 Outlook 邮件 → 解析（1a..5b）→ 导出 report.xlsx → 自检

过滤规则：主题包含 "feedback" 或 "survey"（不区分大小写）。
输出列顺序（与 survey_report_builder.py 一致）：
Ref ID | Q1 Score | Q1 Text | Q2 Score | Q2 Text | Q3 Score | Q3 Text | Q4 Score | Q4 Text | Q5 Score | Q5 Text | Submit Date | Submit Time
"""

# ========================== 配置区（请填写你的 Outlook 账号） ==========================
IMAP_HOST = "outlook.office365.com"  # Outlook/Office 365 IMAP
IMAP_PORT_SSL = 993
IMAP_USER = "your_outlook@outlook.com"     # 你的 Outlook/Office365 邮箱
IMAP_PASS = "YOUR_APP_PASSWORD_OR_PASSWORD"  # 若组织强制现代认证，需改用 APP 密码或 OAuth（见备注）

# 抓取范围
SHOW_LIMIT = 500        # 最多处理多少封（从最后往前取）
FOLDER = "INBOX"        # 读取文件夹（默认 INBOX，大小写不敏感）

# 过滤：主题关键词（小写匹配），发件人白名单可留空
SUBJECT_KEYWORDS = ["feedback", "survey"]
SURVEY_SENDERS = []  # 例如：["noreply@typeform.com", "forms@yourco.com"]

# 导出
REPORT_XLSX = "report.xlsx"

# ========================== 依赖与导入 ==========================
import imaplib, email, ssl, re, sys
from email import policy
from email.header import decode_header
import pandas as pd
from typing import List, Dict, Tuple

# ========================== 工具函数（解码/抽正文/过滤） ==========================
REPORT_COLUMNS = [
    "Ref ID",
    "Q1 Score","Q1 Text",
    "Q2 Score","Q2 Text",
    "Q3 Score","Q3 Text",
    "Q4 Score","Q4 Text",
    "Q5 Score","Q5 Text",
    "Submit Date","Submit Time"
]

def _decode_header_value(raw: str) -> str:
    if not raw: return ""
    parts = decode_header(raw); out=[]
    for part, enc in parts:
        if isinstance(part, bytes):
            try: out.append(part.decode(enc or "utf-8", errors="ignore"))
            except Exception: out.append(part.decode("utf-8", errors="ignore"))
        else:
            out.append(part)
    return "".join(out)

def _strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html or "")
    return re.sub(r"\s+", " ", text).strip()

def extract_plain_text(msg: email.message.Message) -> str:
    """优先 text/plain；否则取 html 并去标签"""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_maintype()=="multipart": continue
            if part.get_content_disposition()=="attachment": continue
            if part.get_content_type()=="text/plain":
                payload = part.get_payload(decode=True) or b""
                charset = part.get_content_charset() or "utf-8"
                try: return payload.decode(charset, errors="ignore").strip()
                except Exception: return payload.decode("utf-8", errors="ignore").strip()
        for part in msg.walk():
            if part.get_content_type()=="text/html":
                payload = part.get_payload(decode=True) or b""
                charset = part.get_content_charset() or "utf-8"
                try: html = payload.decode(charset, errors="ignore")
                except Exception: html = payload.decode("utf-8", errors="ignore")
                return _strip_html(html)
        return ""
    else:
        payload = msg.get_payload(decode=True) or b""
        charset = msg.get_content_charset() or "utf-8"
        try: text = payload.decode(charset, errors="ignore")
        except Exception: text = payload.decode("utf-8", errors="ignore")
        return _strip_html(text) if text.strip().startswith("<") else text.strip()

def subject_sender_filter(subj: str, frm: str) -> bool:
    s = (subj or "").lower()
    f = (frm or "").lower()
    subject_hit = any(k in s for k in SUBJECT_KEYWORDS) if SUBJECT_KEYWORDS else True
    sender_hit = True if not SURVEY_SENDERS else any(x in f for x in SURVEY_SENDERS)
    return subject_hit and sender_hit

# ========================== 解析规则（沿用 survey_report_builder） ==========================
RE_SUBMIT = re.compile(
    r"submit\s*date\s*:\s*(?P<date>\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s*[-–—]\s*(?P<time>\d{1,2}:\d{2})",
    re.IGNORECASE
)
RE_REFID  = re.compile(r"ref\s*id\s*[:#-]?\s*(?P<id>[A-Za-z0-9_-]+)", re.IGNORECASE)
RE_QA     = re.compile(r"^(?:Q\s*)?(?P<num>[1-5])\s*(?P<sub>[ab])\s*[:\-\)\.]\s*(?P<val>.+?)\s*$", re.IGNORECASE)

def _parse_submit_block(text: str) -> Tuple[str,str]:
    m = RE_SUBMIT.search(text or "")
    if not m: return "",""
    raw_date, raw_time = m.group("date").strip(), m.group("time").strip()
    d,mn,y = re.split(r"[/-]", raw_date)
    if len(y)==2: y="20"+y
    d,mn = d.zfill(2), mn.zfill(2)
    try: _=int(y); _=int(d); _=int(mn); std_date=f"{d}/{mn}/{y}"
    except Exception: std_date=raw_date
    hh,mm = raw_time.split(":")
    return std_date, f"{hh.zfill(2)}:{mm.zfill(2)}"

def _parse_refid(text: str) -> str:
    m = RE_REFID.search(text or "")
    return m.group("id").strip() if m else ""

def _parse_answers(text: str) -> Dict[str,str]:
    ans={}
    for raw in (text or "").splitlines():
        line=raw.strip()
        if not line: continue
        m=RE_QA.match(line)
        if m:
            k=f"{m.group('num').lower()}{m.group('sub').lower()}"
            ans[k]=m.group("val").strip()
    return ans

def parse_single_body(body: str) -> Dict[str,str]:
    ref_id=_parse_refid(body)
    sdate, stime=_parse_submit_block(body)
    ans=_parse_answers(body)
    return {
        "Ref ID": ref_id,
        "Q1 Score": ans.get("1a",""), "Q1 Text": ans.get("1b",""),
        "Q2 Score": ans.get("2a",""), "Q2 Text": ans.get("2b",""),
        "Q3 Score": ans.get("3a",""), "Q3 Text": ans.get("3b",""),
        "Q4 Score": ans.get("4a",""), "Q4 Text": ans.get("4b",""),
        "Q5 Score": ans.get("5a",""), "Q5 Text": ans.get("5b",""),
        "Submit Date": sdate, "Submit Time": stime,
    }

# ========================== IMAP 拉取（Outlook） ==========================
def fetch_outlook_messages(limit: int = SHOW_LIMIT, folder: str = FOLDER) -> List[email.message.Message]:
    ctx = ssl.create_default_context()
    with imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT_SSL, ssl_context=ctx) as conn:
        conn.login(IMAP_USER, IMAP_PASS)
        # 选择文件夹（Outlook 大小写不敏感；若失败可试 "Inbox"）
        typ, _ = conn.select(folder, readonly=True)
        if typ != "OK":
            typ, _ = conn.select("Inbox", readonly=True)
            if typ != "OK":
                raise RuntimeError("Cannot select INBOX on Outlook IMAP")

        typ, ids = conn.search(None, "ALL")
        if typ != "OK":
            raise RuntimeError("IMAP search failed")

        id_list = ids[0].split()
        if not id_list: return []

        msgs=[]
        # 从最后往前取 limit 封
        for eid in id_list[-limit:]:
            typ, raw = conn.fetch(eid, "(RFC822)")
            if typ=="OK" and raw and isinstance(raw[0], tuple):
                msg = email.message_from_bytes(raw[0][1], policy=policy.default)
                subj=_decode_header_value(msg.get("Subject"))
                frm = msg.get("From") or ""
                if subject_sender_filter(subj, frm):
                    msgs.append(msg)
        return msgs

# ========================== 导出 Excel + 自检 ==========================
def build_report_from_messages(msgs: List[email.message.Message], out_xlsx: str) -> pd.DataFrame:
    rows=[]
    for m in msgs:
        body = extract_plain_text(m)
        try:
            rows.append(parse_single_body(body))
        except Exception:
            # 容错：至少带上 ref 与提交时间
            ref_id=_parse_refid(body)
            sdate,stime=_parse_submit_block(body)
            rows.append({
                "Ref ID": ref_id,
                "Q1 Score":"","Q1 Text":"",
                "Q2 Score":"","Q2 Text":"",
                "Q3 Score":"","Q3 Text":"",
                "Q4 Score":"","Q4 Text":"",
                "Q5 Score":"","Q5 Text":"",
                "Submit Date": sdate, "Submit Time": stime
            })

    df = pd.DataFrame(rows, columns=REPORT_COLUMNS)
    # 去重（Ref ID + 提交时间）
    df = df.drop_duplicates(subset=["Ref ID","Submit Date","Submit Time"], keep="first")
    # 评分转数值（便于后续统计）
    for col in ["Q1 Score","Q2 Score","Q3 Score","Q4 Score","Q5 Score"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="Survey")
    return df

# ========================== 主流程 ==========================
def main():
    print("== Outlook Feedback Export ==")
    try:
        msgs = fetch_outlook_messages(limit=SHOW_LIMIT, folder=FOLDER)
    except Exception as e:
        print("拉取失败：", e)
        sys.exit(2)

    print(f"匹配到 {len(msgs)} 封（按主题/发件人过滤后）。正在生成报表…")
    if not msgs:
        print("没有符合条件的邮件（主题需包含 feedback/survey）。")
        sys.exit(1)

    df = build_report_from_messages(msgs, REPORT_XLSX)
    rows = len(df)
    print(f"导出完成：{REPORT_XLSX}（{rows} 行）")

    # 自检：至少 1 行
    ok = rows > 0
    print("Self-check:", "PASS ✅" if ok else "FAIL ❌")
    sys.exit(0 if ok else 3)

if __name__ == "__main__":
    if not IMAP_USER or not IMAP_PASS:
        print("请在脚本顶部配置 IMAP_USER / IMAP_PASS")
        sys.exit(2)
    main()
