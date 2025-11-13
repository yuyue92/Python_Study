import logging
# 新增：
import pywintypes

def main():
    print("== Outlook Feedback Export + Mail Sender (win32/MAPI) ==")

    # 1) 抓取
    try:
        texts = fetch_outlook_messages(
            limit=SHOW_LIMIT,
            folder_path=OUTLOOK_FOLDER_PATH,
            date_from=DATE_FROM,
            date_to=DATE_TO
        )
    except pywintypes.com_error as e:
        hresult = e.args[0] if e.args else None
        if hresult == -2147418111:
            print("拉取失败：Outlook 当前拒绝外部访问（Call was rejected by callee）。")
            print("可能原因：Outlook 正在弹出对话框/卡死/未响应，请确认：")
            print("  - 使用的是经典桌面版 Outlook（不是 '新 Outlook' ）")
            print("  - Outlook 已正常打开且没有任何弹窗")
            print("  - 稍等几秒钟再重试脚本")
        else:
            print("拉取失败（COM 错误）：", e)
        sys.exit(2)
    except Exception as e:
        print("拉取失败：", e)
        sys.exit(2)
