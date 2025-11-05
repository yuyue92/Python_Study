import win32com.client as win32
from datetime import datetime, timedelta

# 连接到运行中的 Outlook（也会自动拉起）
outlook = win32.Dispatch("Outlook.Application").GetNamespace("MAPI")

# 1) 取默认帐户的收件箱
inbox = outlook.GetDefaultFolder(6)  # 6 = olFolderInbox
items = inbox.Items
items.Sort("[ReceivedTime]", True)    # 按接收时间倒序

# 2) 仅取最近7天且未读
since = (datetime.now() - timedelta(days=7)).strftime("%m/%d/%Y %H:%M %p")  # 注意是 MM/DD/YYYY
restriction = f"[Unread] = True AND [ReceivedTime] >= '{since}'"
filtered = items.Restrict(restriction)

print(f"未读近7天: {len(filtered)} 封")
for mail in filtered:
    # 有些项目不是 MailItem（会议、回执等），可加类型判断
    if mail.Class == 43:  # 43 = olMail
        print("———")
        print("主题:", mail.Subject)
        print("发件人:", getattr(mail, "SenderEmailAddress", ""))
        print("时间:", mail.ReceivedTime)
        # 预览正文（Body/HTMLBody），注意可能很长
        print("正文预览:", (mail.Body or "").strip()[:120])
