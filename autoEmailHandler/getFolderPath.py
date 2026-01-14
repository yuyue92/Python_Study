INBOX_ENUM = 6  # olFolderInbox

def _resolve_folder(namespace, folder_path: str):
    """
    支持:
      - "Inbox" 或 "Inbox\\Sub1\\Sub2"
      - "Online-Archive - Yu,Yue\\Survey" （Store显示名\\子文件夹）
    return: Outlook Folder 对象（与原函数一致）
    """
    # 1) 空路径：默认主邮箱 Inbox
    if not folder_path:
        return namespace.GetDefaultFolder(INBOX_ENUM)

    parts = [p for p in folder_path.split("\\") if p]
    if not parts:
        return namespace.GetDefaultFolder(INBOX_ENUM)

    first = parts[0].strip()

    # 2) 主邮箱 Inbox 分支（保持你原来的逻辑）
    if first.lower() == "inbox":
        cur = namespace.GetDefaultFolder(INBOX_ENUM)
        for p in parts[1:]:
            cur = cur.Folders[p]
        return cur

    # 3) 其它：把第一段当作 Store.DisplayName（例如 "Online-Archive - Yu,Yue"）
    store = None
    for st in namespace.Stores:
        if (st.DisplayName or "").strip().lower() == first.lower():
            store = st
            break

    if store is None:
        # 兜底：有些环境也能从 namespace.Folders[...] 取到“顶层邮箱”，但不如 Stores 稳
        # 保持与原函数的容错思路一致：先尝试 namespace.Folders[first]
        root = namespace.Folders[first]
        cur = root
        for p in parts[1:]:
            cur = cur.Folders[p]
        return cur

    # 4) 从该 Store 的根开始往下走
    cur = store.GetRootFolder()

    # 可选：如果你写成 "Online-Archive - Yu,Yue\\Inbox\\Sub1"
    # 建议用 GetDefaultFolder(INBOX_ENUM) 而不是 cur.Folders["Inbox"]（避免语言差异）
    idx = 1
    if len(parts) >= 2 and parts[1].strip().lower() == "inbox":
        cur = store.GetDefaultFolder(INBOX_ENUM)
        idx = 2

    for p in parts[idx:]:
        cur = cur.Folders[p]

    return cur


使用方法：
folder = _resolve_folder(ns, r"Online-Archive - Yu,Yue\Survey")
print(folder.FolderPath)   # 输出解析后的完整 FolderPath（Outlook 内部路径）
