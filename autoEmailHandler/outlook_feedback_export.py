#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Outlook Feedback Export (Win32 Dispatch / MAPI) — 拉取 Outlook 邮件 → 解析（1a..5b）→ 导出 report.xlsx → 自检

- 使用本地 Outlook 客户端（win32com Dispatch）读取邮件，而非 IMAP/POP3
- 过滤规则：主题包含 "feedback" 或 "survey"（不区分大小写），可选发件人白名单
- 解析规则保持与 survey_report_builder.py 一致：
  Ref ID | Q1 Score | Q1 Text | Q2 Score | Q2 Text | Q3 Score | Q3 Text | Q4 Score | Q4 Text | Q5 Score | Q5 Text | Submit Date | Submit Time
"""

# ========================== 配置区（按需修改） ==========================
# 读取位置：
# - 默认读取当前默认帐户的 Inbox；若要读收件箱下子文件夹，形如 "Inbox\\Survey"
OUTLOOK_FOLDER_PATH = "Inbox"     # 支持 "Inbox" 或 "Inbox\\Sub1\\Sub2"
SHOW_LIMIT = 500                  # 最多处理多少封（从最近往前数）
SUBJECT_KEYWORDS = ["feedback", "survey"]  # 主题关键词（小写匹配）
SURVEY_SENDERS = []               # 发件人白名单（可留空=不限制），如 ["noreply@typeform.com"]

# 导出
REPORT_XLSX = "report.xlsx"

# ========================== 依赖与导入 ==========================
import re
import sys
from typing import List, Dict, Tuple
import pandas as pd

# win32 相关
try:
    import win32com.client as win32
    from win32com.client import constants
except Exception as e:
    print("请先安装 pywin32： pip install pywin32")
    raise

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

def _strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html or "")
    return re.sub(r"\s+", " ", text).strip()

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
    try:
        _ = int(y); _ = int(d); _ = int(mn)
        std_date = f"{d}/{mn}/{y}"
    except Exception:
        std_date = raw_date
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

# ========================== 核心：使用 win32 Dispatch 抓取 Outlook 邮件 ==========================
def _resolve_folder(namespace, path: str):
    """
    解析类似 'Inbox' 或 'Inbox\\Sub1\\Sub2' 的路径到 MAPIFolder。
    从默认帐户的 Inbox 起步向下找子文件夹（常见需求够用）。
    """
    # 6 = olFolderInbox
    folder = namespace.GetDefaultFolder(constants.olFolderInbox)
    if not path or path.lower() == "inbox":
        return folder

    # 去掉前缀 "inbox\"，按子层级遍历
    parts = [p for p in path.split("\\") if p]
    if parts and parts[0].lower() == "inbox":
        parts = parts[1:]

    for name in parts:
        folder = folder.Folders.Item(name)
    return folder

def fetch_outlook_messages(limit: int = SHOW_LIMIT, folder_path: str = OUTLOOK_FOLDER_PATH) -> List[str]:
    """
    使用 Outlook MAPI 读取邮件正文（返回纯文本 body 列表）
    - 从最近邮件往前遍历，命中过滤规则则加入结果，直到 limit
    - 优先取 MailItem.Body（纯文本）；若为空再用 HTMLBody 去标签
    """
    outlook = win32.Dispatch("Outlook.Application")
    namespace = outlook.GetNamespace("MAPI")
    folder = _resolve_folder(namespace, folder_path)

    # Items 集合：按接收时间倒序
    items = folder.Items
    items.IncludeRecurrences = True
    items.Sort("[ReceivedTime]", True)

    bodies: List[str] = []
    taken = 0
    # Outlook Items 是 COM 集合，for 循环枚举从最新到更早
    for item in items:
        # 43 = olMail
        if getattr(item, "Class", None) != 43:
            continue

        subj = getattr(item, "Subject", "") or ""
        frm  = getattr(item, "SenderEmailAddress", "") or getattr(item, "SenderName", "") or ""

        if not subject_sender_filter(subj, frm):
            continue

        # 抽正文：优先 Body（纯文本），否则 HTMLBody 去标签
        body = (getattr(item, "Body", None) or "").strip()
        if not body:
            html = getattr(item, "HTMLBody", None) or ""
            body = _strip_html(html)

        if body:
            bodies.append(body)
            taken += 1
            if taken >= limit:
                break

    return bodies

# ========================== 导出 Excel + 自检 ==========================
def build_report_from_texts(texts: List[str], out_xlsx: str) -> pd.DataFrame:
    rows=[]
    for body in texts:
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
    print("== Outlook Feedback Export (win32/MAPI) ==")
    try:
        texts = fetch_outlook_messages(limit=SHOW_LIMIT, folder_path=OUTLOOK_FOLDER_PATH)
    except Exception as e:
        print("拉取失败：", e)
        sys.exit(2)

    print(f"匹配到 {len(texts)} 封（按主题/发件人过滤后）。正在生成报表…")
    if not texts:
        print("没有符合条件的邮件（主题需包含 feedback/survey）。")
        sys.exit(1)

    df = build_report_from_texts(texts, REPORT_XLSX)
    rows = len(df)
    print(f"导出完成：{REPORT_XLSX}（{rows} 行）")

    # 自检：至少 1 行
    ok = rows > 0
    print("Self-check:", "PASS ✅" if ok else "FAIL ❌")
    sys.exit(0 if ok else 3)

if __name__ == "__main__":
    main()
