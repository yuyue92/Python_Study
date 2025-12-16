#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Outlook Feedback Export + Mail Sender (Win32 Dispatch / MAPI)
- Fetch emails from local Outlook (filter by subject/sender)
- Parse survey text into structured data
- Export Excel report as report.xlsx
- Send report via Outlook with one-time token
- Self-check:
  1) Whether fetch/parse produces data
  2) Whether Excel is successfully generated (exists and non-empty)
  3) Whether email is sent successfully (verify in "Sent Items" by Subject Token)

Note:
- Requires local Outlook client installed and logged in
- Uses win32com (pywin32) to drive Outlook MAPI
"""

# ========================== Configuration Section (Modify as needed) ==========================
# Read location: supports "Inbox" or "Inbox\\Sub1\\Sub2"
OUTLOOK_FOLDER_PATH = "Inbox\\survey feedback"
# Maximum number of emails to process (from most recent backwards)
SHOW_LIMIT = 500
# Filter unread emails only [true: only unread, false: all emails]
FILTER_UNREAD=False
# Mark unread emails as read [true: mark as read, false: don't mark]
SET_READED=False
# Start and end date range
DATE_FROM = "2025-12-01"
DATE_TO = "2025-12-21"
# Subject keywords (lowercase matching)
SUBJECT_KEYWORDS = ["feedback", "survey"]
# Sender whitelist (empty = no restriction), e.g.: ["noreply@typeform.com"]
SURVEY_SENDERS = []

# Exported Excel filename
REPORT_XLSX = "report.xlsx"

# Email configuration for sending report
# TARGET_TO = ["Mandy.MT.Kwok@pccw.com"]
TARGET_TO = ["Peng.Huang@pccw.com" ]   # Recipients
TARGET_CC = []
TARGET_BCC = []
MAIL_SUBJECT_PREFIX = "[Feedback Report]"
MAIL_BODY_TEXT = (
    "Hi,\n\n"
    "Please find attached the latest feedback report exported from Outlook.\n"
    "This email was sent automatically by the local script.\n\n"
    "Regards,\nAutomated Reporter"
)

# Timeout for checking "Sent Items" after sending (seconds)
SENT_CHECK_TIMEOUT = 45
SENT_CHECK_INTERVAL = 3

# ========================== Dependencies & Imports ==========================
import os
import re
import sys
import time
import uuid
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Iterable
import pandas as pd

# ========================== Logging Configuration (Fix Chinese encoding) ==========================
import logging
import logging.config

def setup_logging():
    """Setup UTF-8 encoded logging configuration"""
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        },
        'handlers': {
            'file': {
                'class': 'logging.FileHandler',
                'level': 'DEBUG',
                'formatter': 'standard',
                'filename': 'app.log',
                'encoding': 'utf-8',  # Key: specify UTF-8 encoding
                'mode': 'a'
            },
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'standard',
                'stream': sys.stdout
            }
        },
        'loggers': {
            '__main__': {
                'level': 'DEBUG',
                'handlers': ['file', 'console'],
                'propagate': False
            }
        }
    }
    
    logging.config.dictConfig(logging_config)

# Call at script start
setup_logging()
logger = logging.getLogger(__name__)

# win32 related imports
try:
    import win32com.client as win32
except Exception:
    print("Please install pywin32 first: pip install pywin32")
    raise

import pywintypes
import pythoncom

# ========================== Utility Functions (Decode/Extract/Filter) ==========================
# Define report column headers
REPORT_COLUMNS = [
    "Ref ID",
    "Q1 Score",
    "Q1 Text",
    "Q2 Score",
    "Q2 Text",
    "Q3 Score",
    "Q3 Text",
    "Q4 Text",
    "Q5 Score",
    "Q5 Text",
    "Submit Date",
    "Submit Time",
]


def _strip_html(html: str) -> str:
    """Strip HTML tags and normalize whitespace"""
    text = re.sub(r"<[^>]+>", " ", html or "")
    return re.sub(r"\s+", " ", text).strip()


def subject_sender_filter(subj: str, frm: str) -> bool:
    """Filter emails by subject keywords and sender whitelist"""
    s = (subj or "").lower()
    f = (frm or "").lower()
    if SUBJECT_KEYWORDS:
        if not any(k in s for k in SUBJECT_KEYWORDS):
            return False
    if SURVEY_SENDERS:
        if f and not any(f.endswith(x.lower()) for x in SURVEY_SENDERS):
            return False
    return True

# ========================== Parse Survey Text ==========================
# Support two formats: number+letter or just number 4
RE_QA = re.compile(
    r'^(?P<num>\d+)(?P<sub>[a-z])?[\.\s]*[:：]\s*(?P<val>.*)$',
    re.IGNORECASE
)

# Regex for submit date/time
RE_SUBMIT = re.compile(
    r"eForm Submit Date\s*[:：]?\s*(?P<date>\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s*-\s*(?P<time>\d{1,2}:\d{2})",
    re.IGNORECASE,
)
# Regex for reference ID
RE_REFID = re.compile(r"Ref(?:erence)?\s*ID\s*[:：]\s*(?P<id>\S+)", re.IGNORECASE)


def _parse_submit_block(text: str) -> Tuple[str, str]:
    """Parse submit date and time from email body"""
    m = RE_SUBMIT.search(text or "")
    if not m:
        return "", ""
    raw_date, raw_time = m.group("date").strip(), m.group("time").strip()
    d, mn, y = re.split(r"[/-]", raw_date)
    if len(y) == 2:
        y = "20" + y
    d, mn = d.zfill(2), mn.zfill(2)
    try:
        _ = int(y)
        _ = int(d)
        _ = int(mn)
        std_date = f"{d}/{mn}/{y}"
    except Exception:
        std_date = raw_date
    hh, mm = raw_time.split(":")
    return std_date, f"{hh.zfill(2)}:{mm.zfill(2)}"


def _parse_refid(text: str) -> str:
    """Extract reference ID from email body"""
    m = RE_REFID.search(text or "")
    return m.group("id").strip() if m else ""

def _parse_answers(text: str) -> Dict[str, str]:
    """Parse answers, supporting two formats:
    1. Standard format: number+letter (e.g. '1a', '2b')
    2. Special format: only number 4 (treat as '4b')
    """
    ans = {}
    
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
            
        m = RE_QA.match(line)
        if not m:
            continue
            
        # Get matched groups
        val = m.group("val") or ""
        
        # Determine which matching pattern
        # Pattern 1: Standard format (number+letter)
        if m.group("sub"):  
            num = m.group("num") or ""
            sub = m.group("sub") or ""
            
            if num and sub:
                k = f"{num.lower()}{sub.lower()}"
                ans[k] = val.strip()
                
        # Pattern 2: Special format (only number 4, treat as 4b)
        else:
            num = m.group("num") or ""
            if num == "4":  # Only handle special case of number 4
                ans["4b"] = val.strip()
            # Other numbers without letters can be ignored or handled as needed
            # else:
            #     logger.debug(f"Ignore number-only line: {line}")
    
    return ans

def parse_single_body(body: str) -> Dict[str, str]:
    """Parse a single email body into structured data"""
    ref_id = _parse_refid(body)
    if not ref_id:
        return {}
    sdate, stime = _parse_submit_block(body)
    ans = _parse_answers(body)
    return {
        "Ref ID": ref_id,
        "Q1 Score": ans.get("1a", ""),
        "Q1 Text": ans.get("1b", ""),
        "Q2 Score": ans.get("2a", ""),
        "Q2 Text": ans.get("2b", ""),
        "Q3 Score": ans.get("3a", ""),
        "Q3 Text": ans.get("3b", ""),
        "Q4 Text": ans.get("4b", ""),
        "Q5 Score": ans.get("5a", ""),
        "Q5 Text": ans.get("5b", ""),
        "Submit Date": sdate,
        "Submit Time": stime,
    }


# ========================== MAPI: Constants & Safe COM Calls ==========================
INBOX_ENUM = 6  # Inbox constant


def safe_com_call(func, *args, retries: int = 3, delay: float = 1.0, **kwargs):
    """
    Retry mechanism for COM calls, prioritizing handling 'Call was rejected by callee' (RPC_E_CALL_REJECTED).
    """
    last_exc = None
    for i in range(retries):
        try:
            return func(*args, **kwargs)
        except pywintypes.com_error as e:
            hresult = e.args[0] if e.args else None
            if hresult == -2147418111:  # RPC_E_CALL_REJECTED
                logger.warning(
                    f"COM call rejected by Outlook (RPC_E_CALL_REJECTED), attempt {i+1}/{retries}, retrying..."
                )
                last_exc = e
                if i < retries - 1:
                    time.sleep(delay)
                    continue
            # Not this error or retries exhausted
            last_exc = e
            break
        except Exception as e:
            last_exc = e
            break
    # All retries failed
    raise last_exc


def _resolve_folder(namespace, folder_path: str):
    """
    Support paths like "Inbox" or "Inbox\\Sub1\\Sub2".
    """
    if not folder_path:
        return namespace.GetDefaultFolder(INBOX_ENUM)
    parts = folder_path.split("\\")
    root = namespace.GetDefaultFolder(INBOX_ENUM) if parts[0].lower() == "inbox" else namespace.Folders[parts[0]]
    cur = root
    for p in parts[1:]:
        cur = cur.Folders[p]
    return cur


def _ensure_dt(v):
    """Convert various date formats to datetime object"""
    if v is None or v == "":
        return None
    if isinstance(v, datetime):
        return v
    if isinstance(v, (int, float)):
        return datetime.fromtimestamp(v)
    if isinstance(v, str):
        v = v.strip()
        if not v:
            return None
        for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                return datetime.strptime(v, fmt)
            except Exception:
                pass
    return None


def _fmt_ol_datetime(dt: datetime) -> str:
    """
    Format datetime for Outlook Restrict query.
    Usually 'YYYY-MM-DD HH:MM' works.
    """
    return dt.strftime("%Y-%m-%d %H:%M")


def _any_match(text: str, patterns: Iterable[str], ci: bool = True) -> bool:
    """Check if text matches any pattern"""
    text = text or ""
    if ci:
        text = text.lower()
        patterns = [p.lower() for p in patterns]
    return any(p in text for p in patterns)


def _none_match(text: str, patterns: Iterable[str], ci: bool = True) -> bool:
    """Check if text matches none of the patterns"""
    return not _any_match(text, patterns, ci)


def create_outlook_instance(max_retries: int = 3, retry_delay: float = 2.0):
    """
    Create robust Outlook instance with multiple connection methods and retry mechanism.

    Args:
        max_retries: Maximum retry attempts
        retry_delay: Retry delay (seconds)

    Returns:
        Outlook Application object
    """
    last_exception = None

    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to connect to Outlook (attempt {attempt + 1})...")

            # Method 1: Try direct connection (fastest)
            if attempt == 0:
                try:
                    outlook = safe_com_call(win32.Dispatch, "Outlook.Application")
                    logger.info("Connected successfully using Dispatch")
                    return outlook
                except Exception as e:
                    last_exception = e
                    logger.warning(f"Dispatch connection failed: {e}")

            # Method 2: Use EnsureDispatch (more stable)
            if attempt <= 1:
                try:
                    outlook = safe_com_call(
                        win32.gencache.EnsureDispatch, "Outlook.Application"
                    )
                    logger.info("Connected successfully using EnsureDispatch")
                    return outlook
                except Exception as e:
                    last_exception = e
                    logger.warning(f"EnsureDispatch connection failed: {e}")

            # Method 3: Use dynamic dispatch (best compatibility)
            try:
                outlook = safe_com_call(
                    win32.dynamic.Dispatch, "Outlook.Application"
                )
                logger.info("Connected successfully using dynamic.Dispatch")
                return outlook
            except Exception as e:
                last_exception = e
                logger.warning(f"dynamic.Dispatch connection failed: {e}")

            # If not last attempt, wait before retrying
            if attempt < max_retries - 1:
                logger.info(f"Waiting {retry_delay} seconds before retrying Outlook connection...")
                time.sleep(retry_delay)

        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                logger.info(
                    f"Connection attempt {attempt + 1} failed, waiting before retry..."
                )
                time.sleep(retry_delay)

    # All attempts failed
    error_msg = (
        f"Unable to connect to Outlook, all {max_retries} attempts failed. Last error: {last_exception}"
    )
    logger.error(error_msg)
    raise Exception(error_msg)


def fetch_outlook_messages(
    limit: int = 500,
    folder_path: str = "Inbox",
    # New filter conditions:
    date_from=None,  # 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM' or datetime
    date_to=None,  # Same as above
    senders: Optional[List[str]] = None,
    exclude_senders: Optional[List[str]] = None,
    subject_keywords: Optional[List[str]] = None,
    exclude_subject_keywords: Optional[List[str]] = None,
    body_keywords: Optional[List[str]] = None,
    exclude_body_keywords: Optional[List[str]] = None,
    case_insensitive: bool = True,
) -> List[str]:
    """
    Fetch email bodies from Outlook (returns list of plain text bodies), supports multiple filter conditions.
    - Time range preferably uses Items.Restrict (better performance)
    - Subject/sender/body inclusion/exclusion filtered on Python side
    """
    # Create Outlook instance
    outlook = create_outlook_instance()
    # outlook = win32.Dispatch("Outlook.Application")
    namespace = safe_com_call(outlook.GetNamespace, "MAPI")
    folder = safe_com_call(_resolve_folder, namespace, folder_path)

    items = safe_com_call(lambda: folder.Items)
    items.IncludeRecurrences = True
    # Sort by received time descending
    safe_com_call(items.Sort, "[ReceivedTime]", True)
    logger.info(f"Total emails in folder: {len(items)}" )

    # ---------- Time filtering (using Restrict) ----------
    df = _ensure_dt(date_from)
    dt = _ensure_dt(date_to)
    restricted = items
    filter_parts = []
    if FILTER_UNREAD:
        filter_parts.append("[UnRead] = True")
    if df:
        filter_parts.append(f"[ReceivedTime] >= '{_fmt_ol_datetime(df)}'")
    if dt:
        filter_parts.append(f"[ReceivedTime] <= '{_fmt_ol_datetime(dt)}'")
    if filter_parts:
        restriction = " AND ".join(filter_parts)
        try:
            restricted = safe_com_call(items.Restrict, restriction)
        except Exception as e:
            # If Restrict fails in some locales, fallback to full scan with Python-side filtering (worse performance)
            restricted = items
            logger.warning(f"Warning: Outlook Restrict time filter failed, fallback to local filtering. Error: {e}")

    # ---------- Iterate and apply keyword/sender filters ----------
    bodies: List[str] = []
    taken = 0
    # If subject_keywords not passed, use default SUBJECT_KEYWORDS from script top
    default_subject_kw = (
        subject_keywords
        if subject_keywords is not None
        else (globals().get("SUBJECT_KEYWORDS") or [])
    )
    count = len(restricted)
    logger.info(f'After condition filtering, total emails: {count}')
    for idx in range(1, count + 1):  # Outlook collections are 1-based
        if limit and taken >= limit:
            break

        try:
            item = safe_com_call(restricted.Item, idx)
        except Exception as e:
            logger.warning(f"Failed to read email #{idx}: {e}")
            continue

        if getattr(item, "Class", None) != 43:  # 43 = olMail
            continue

        subj = getattr(item, "Subject", "") or ""
        frm = (
            getattr(item, "SenderEmailAddress", "")
            or getattr(item, "SenderName", "")
            or ""
        )
        # Python-side sender and subject filtering (inclusion + exclusion)
        if senders and not _any_match(frm, senders, case_insensitive):
            continue
        if exclude_senders and not _none_match(
            frm, exclude_senders, case_insensitive
        ):
            continue

        # Subject inclusion/exclusion
        if default_subject_kw and not _any_match(
            subj, default_subject_kw, case_insensitive
        ):
            continue
        if exclude_subject_keywords and not _none_match(
            subj, exclude_subject_keywords, case_insensitive
        ):
            continue
        # Mark unread emails as read if configured
        if SET_READED and item.Unread:
            item.UnRead=False
            item.Save()
        # Get body (prefer plain text), fallback to stripping HTML if needed
        body = (getattr(item, "Body", None) or "").strip()
        if not body:
            html = getattr(item, "HTMLBody", None) or ""
            body = _strip_html(html)

        if not body:
            continue

        # Body keyword inclusion/exclusion
        if body_keywords and not _any_match(
            body, body_keywords, case_insensitive
        ):
            continue
        if exclude_body_keywords and not _none_match(
            body, exclude_body_keywords, case_insensitive
        ):
            continue

        bodies.append(body)
        taken += 1

    return bodies


# ========================== Export to Excel ==========================
def build_report_from_texts(texts: List[str], out_xlsx: str) -> pd.DataFrame:
    """Build Excel report from parsed email bodies"""
    rows = []
    for body in texts:
        try:
            txt_body = parse_single_body(body)
            if txt_body:
                rows.append(txt_body)
            else:
                rows.append({})
        except Exception as e:
            ref_id = _parse_refid(body)
            logger.warning(f"refID: {ref_id}, error getting email content: {e}")
            sdate, stime = _parse_submit_block(body)
            rows.append(
                {
                    "Ref ID": ref_id,
                    "Q1 Score": "",
                    "Q1 Text": "",
                    "Q2 Score": "",
                    "Q2 Text": "",
                    "Q3 Score": "",
                    "Q3 Text": "",
                    "Q4 Text": "",
                    "Q5 Score": "",
                    "Q5 Text": "",
                    "Submit Date": sdate,
                    "Submit Time": stime,
                }
            )

    filtered_rows = [row for row in rows if row]        # Filter out completely empty dictionaries
    logger.info(f'Total with headers: {len(rows)}, after removing empty: {len(filtered_rows)}' )
    logger.info(f"Matched {len(filtered_rows)} emails (after subject/sender filtering). Generating report...")
    df = pd.DataFrame(filtered_rows, columns=REPORT_COLUMNS)
    df.to_excel(out_xlsx, index=False)
    return df


# ========================== Send Report (Outlook MAPI) ==========================
def send_report_via_outlook(
    report_path: str,
    to: List[str],
    cc: List[str],
    bcc: List[str],
    subject_prefix: str,
    body_text: str,
) -> Tuple[str, str]:
    """
    Send report using Outlook, with one-time token in subject.
    Returns (subject, token)
    """
    outlook = create_outlook_instance()
    namespace = safe_com_call(outlook.GetNamespace, "MAPI")

    mail = safe_com_call(outlook.CreateItem, 0)  # 0 = olMailItem
    token = str(uuid.uuid4())[:8]
    subject = f"{subject_prefix} [{token}]"

    mail.Subject = subject
    mail.Body = body_text

    if to:
        mail.To = ";".join(to)
    if cc:
        mail.CC = ";".join(cc)
    if bcc:
        mail.BCC = ";".join(bcc)

    # Attachment
    if report_path and os.path.exists(report_path):
        mail.Attachments.Add(os.path.abspath(report_path))

    mail.Send()
    return subject, token


def _find_recent_sent_by_token(namespace, token: str) -> bool:
    """Search for email containing token in Sent Items."""
    sent_folder = namespace.GetDefaultFolder(5)  # 5 = olFolderSentMail
    items = sent_folder.Items
    items.Sort("[SentOn]", True)
    checked = 0
    for item in items:
        if getattr(item, "Class", None) != 43:
            continue
        subj = getattr(item, "Subject", "") or ""
        if token in subj:
            return True
        checked += 1
        if checked >= 100:  # Only check most recent 100
            break
    return False


def wait_sent_verification(token: str) -> bool:
    """
    After sending, wait up to SENT_CHECK_TIMEOUT seconds in "Sent Items" to confirm email with token exists.
    """
    outlook = create_outlook_instance()
    namespace = safe_com_call(outlook.GetNamespace, "MAPI")

    start_ts = time.time()
    while True:
        if _find_recent_sent_by_token(namespace, token):
            return True
        if time.time() - start_ts > SENT_CHECK_TIMEOUT:
            return False
        time.sleep(SENT_CHECK_INTERVAL)

# ========================== New: Cache Cleanup Function ==========================
def clear_win32com_cache():
    """
    Clear win32com generated cache to resolve CLSIDToClassMap errors
    """
    try:
        # Get gen_py directory path
        gen_py_path = os.path.join(os.path.expanduser("~"), 
                                  "AppData", "Local", "Temp", "gen_py")
        
        # For Python 3.9+, path might be in another location
        if not os.path.exists(gen_py_path):
            gen_py_path = os.path.join(os.environ.get("TEMP", ""), "gen_py")
        
        if os.path.exists(gen_py_path):
            import shutil
            logger.info(f"Clearing win32com cache: {gen_py_path}")
            shutil.rmtree(gen_py_path, ignore_errors=True)
            logger.info("win32com cache cleared successfully")
        else:
            logger.info("win32com cache directory not found, no cleanup needed")
            
    except Exception as e:
        logger.warning(f"Error clearing cache (can be ignored): {e}")

# ========================== Main Process ==========================
def main():
    logger.info("************ Outlook Feedback Export + Mail Sender (win32/MAPI) ************")
    # Clear cache at start
    clear_win32com_cache()
    
    # 1) Fetch emails
    try:
        texts = fetch_outlook_messages(
            limit=SHOW_LIMIT,
            folder_path=OUTLOOK_FOLDER_PATH,
            date_from=DATE_FROM,
            date_to=DATE_TO,
        )
    except pywintypes.com_error as e:
        hresult = e.args[0] if e.args else None
        if hresult == -2147418111:
            logger.warning("Fetch failed: Outlook currently rejects external access (Call was rejected by callee).")
            logger.warning("Possible reasons: Outlook is showing a dialog/frozen/not responding, please verify:")
            logger.warning("  - Using classic desktop Outlook (not 'new Outlook')")
            logger.warning("  - Outlook is properly opened without any popups")
            logger.warning("  - Wait a few seconds and retry the script")
        else:
            logger.warning(f"Fetch failed (COM error): {e}" )
        sys.exit(2)
    except Exception as e:
        logger.info(f"Fetch failed: {e}" )
        sys.exit(2)

    if not texts:
        logger.info("No matching emails found (subject must contain feedback/survey).")
        sys.exit(1)

    # 2) Generate report
    df = build_report_from_texts(texts, REPORT_XLSX)
    rows = len(df)
    logger.info(f"Export complete: {REPORT_XLSX} ({rows} rows)")

    # 3) Self-check (export)
    file_ok = (
        os.path.exists(REPORT_XLSX)
        and os.path.getsize(REPORT_XLSX) > 0
        and rows > 0
    )
    logger.info(f'Self-check[Export]: {"PASS ✅" if file_ok else "FAIL ❌"}')
    if not file_ok:
        sys.exit(3)

    # 4) Send report
    try:
        subject, token = send_report_via_outlook(
            report_path=REPORT_XLSX,
            to=TARGET_TO,
            cc=TARGET_CC,
            bcc=TARGET_BCC,
            subject_prefix=MAIL_SUBJECT_PREFIX,
            body_text=MAIL_BODY_TEXT,
        )
        logger.info(f"Submitted for sending: {subject}")
    except Exception as e:
        logger.warning(f"Send failed: {e}")
        sys.exit(4)

    # 5) Self-check (verify sent)
    ok_sent = wait_sent_verification(token)
    logger.info(f'Self-check[Mail Sent]: {"PASS ✅" if ok_sent else "FAIL ❌"}')

    overall_ok = file_ok and ok_sent
    logger.info(f'Overall: {"PASS ✅" if overall_ok else "PARTIAL ⚠️"}')
    sys.exit(0 if overall_ok else 5)


if __name__ == "__main__":
    # Initialize COM library for Windows
    pythoncom.CoInitialize()
    try:
        main()
    finally:
        # Clean up COM library
        pythoncom.CoUninitialize()