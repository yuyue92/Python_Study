import re
import os
from datetime import datetime
from typing import List, Optional, Iterable

import win32com.client as win32

# === 常量：使用数值枚举更稳（避免 constants 取值失败） ===
INBOX_ENUM = 6  # Inbox

def _strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html or "")
    return re.sub(r"\s+", " ", text).strip()

def _resolve_folder(namespace, path: str):
    """
    解析 'Inbox' 或 'Inbox\\Sub1\\Sub2' 到 MAPIFolder。
    使用枚举值 INBOX_ENUM 获取默认收件箱，兼容不同语言显示名。
    """
    try:
        root_inbox = namespace.GetDefaultFolder(INBOX_ENUM)
    except Exception as e:
        raise RuntimeError(
            "无法获取默认收件箱。请确认使用 Classic Outlook（桌面版）、Outlook 已登录，且 Python 位数与 Outlook 位数一致。"
            f" 原始错误：{e}"
        )

    if not path or path.strip().lower() == "inbox":
        return root_inbox

    parts = [p for p in path.split("\\") if p]
    if parts and parts[0].lower() == "inbox":
        parts = parts[1:]

    folder = root_inbox
    for name in parts:
        try:
            folder = folder.Folders.Item(name)
        except Exception:
            available = [f.Name for f in folder.Folders]
            raise RuntimeError(
                f"子文件夹不存在：{name}。当前层可用子文件夹：{available}。"
                " 请检查 OUTLOOK_FOLDER_PATH 配置。"
            )
    return folder

# ---------- 新增：时间 & 关键字工具 ----------

def _ensure_dt(dt_like) -> Optional[datetime]:
    """将 str/datetime 转为 datetime；支持 'YYYY-MM-DD' 或 'YYYY-MM-DD HH:MM'。"""
    if dt_like is None:
        return None
    if isinstance(dt_like, datetime):
        return dt_like
    s = str(dt_like).strip()
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    raise ValueError(f"无法解析日期时间：{dt_like}（支持 YYYY-MM-DD 或 YYYY-MM-DD HH:MM）")

def _fmt_ol_datetime(dt: datetime) -> str:
    """
    Outlook Restrict 对日期过滤通常要求美国格式字符串：
    'MM/DD/YYYY HH:MM AM/PM'
    注：我们按本地时间构造，避免时区歧义。
    """
    return dt.strftime("%m/%d/%Y %I:%M %p")

def _any_match(text: str, needles: Iterable[str], ci: bool = True) -> bool:
    if not needles:
        return True
    if text is None:
        return False
    hay = text.lower() if ci else text
    for n in needles:
        if not n:
            continue
        nn = n.lower() if ci else n
        if nn in hay:
            return True
    return False

def _none_match(text: str, needles: Iterable[str], ci: bool = True) -> bool:
    """若 needles 中任一命中，则返回 False；全部不命中返回 True。"""
    if not needles:
        return True
    if text is None:
        # 若无文本而需排除关键字，视为通过（不存在即不命中排除词）
        return True
    hay = text.lower() if ci else text
    for n in needles:
        if not n:
            continue
        nn = n.lower() if ci else n
        if nn in hay:
            return False
    return True

# ---------- 这里是你要替换的抓取方法（增强版） ----------

def fetch_outlook_messages(
    limit: int = 500,
    folder_path: str = "Inbox",
    # 新增过滤条件：
    date_from=None,                    # 'YYYY-MM-DD' 或 'YYYY-MM-DD HH:MM' 或 datetime
    date_to=None,                      # 同上
    senders: Optional[List[str]] = None,
    exclude_senders: Optional[List[str]] = None,
    subject_keywords: Optional[List[str]] = None,
    exclude_subject_keywords: Optional[List[str]] = None,
    body_keywords: Optional[List[str]] = None,
    exclude_body_keywords: Optional[List[str]] = None,
    case_insensitive: bool = True,
) -> List[str]:
    """
    从 Outlook 读取邮件正文（返回纯文本 body 列表），支持多种过滤条件。
    - 时间范围优先用 Items.Restrict 实现（性能更好）
    - 主题/发件人/正文的包含/排除在 Python 侧过滤
    """
    outlook = win32.Dispatch("Outlook.Application")
    namespace = outlook.GetNamespace("MAPI")
    folder = _resolve_folder(namespace, folder_path)

    items = folder.Items
    items.IncludeRecurrences = True
    # 先按接收时间降序
    items.Sort("[ReceivedTime]", True)

    # ---------- 时间过滤（使用 Restrict） ----------
    df = _ensure_dt(date_from)
    dt = _ensure_dt(date_to)
    restricted = items
    filter_parts = []
    if df:
        filter_parts.append(f"[ReceivedTime] >= '{_fmt_ol_datetime(df)}'")
    if dt:
        filter_parts.append(f"[ReceivedTime] <= '{_fmt_ol_datetime(dt)}'")
    if filter_parts:
        restriction = " AND ".join(filter_parts)
        try:
            restricted = items.Restrict(restriction)
        except Exception as e:
            # 若 Restrict 在个别区域设置下异常，降级为全量后Python侧过滤（但性能较差）
            restricted = items
            print(f"警告：Outlook Restrict 时间过滤失败，已降级为本地过滤。错误：{e}")

    # ---------- 迭代并做关键词/发件人过滤 ----------
    bodies: List[str] = []
    taken = 0
    # 若未传 subject_keywords，则允许兼容你脚本顶部默认 SUBJECT_KEYWORDS
    default_subject_kw = subject_keywords if subject_keywords is not None else (globals().get("SUBJECT_KEYWORDS") or [])

    for item in restricted:
        if getattr(item, "Class", None) != 43:  # 43 = olMail
            continue

        subj = getattr(item, "Subject", "") or ""
        frm  = getattr(item, "SenderEmailAddress", "") or getattr(item, "SenderName", "") or ""

        # Python 侧的发件人与主题过滤（包含 + 排除）
        if senders and not _any_match(frm, senders, case_insensitive):
            continue
        if exclude_senders and not _none_match(frm, exclude_senders, case_insensitive):
            continue

        if default_subject_kw and not _any_match(subj, default_subject_kw, case_insensitive):
            continue
        if exclude_subject_keywords and not _none_match(subj, exclude_subject_keywords, case_insensitive):
            continue

        # 取正文（优先纯文本），必要时从 HTML 去标签
        body = (getattr(item, "Body", None) or "").strip()
        if not body:
            html = getattr(item, "HTMLBody", None) or ""
            body = _strip_html(html)

        if not body:
            continue

        # 正文包含/排除词
        if body_keywords and not _any_match(body, body_keywords, case_insensitive):
            continue
        if exclude_body_keywords and not _none_match(body, exclude_body_keywords, case_insensitive):
            continue

        bodies.append(body)
        taken += 1
        if limit and taken >= limit:
            break

    return bodies
