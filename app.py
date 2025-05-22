import os
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

line_bot_api = LineBotApi(os.environ["LINE_CHANNEL_ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["LINE_CHANNEL_SECRET"])

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    print(f"[Webhook] Received body: {body}")  # 除錯用，可觀察 Render Logs

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("[Webhook] ❌ Invalid signature.")
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()

    # 支援 @T / @t 開頭
    if text.lower().startswith("@t"):
        content = text[2:].strip()
        if content:
            translated = translate(content)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=translated)
            )

def contains_chinese(text):
    return any('\u4e00' <= char <= '\u9fff' for char in text)

def translate(text):
    """
    使用 LibreTranslate.com API 進行免費翻譯
    中文 → 英文、英文 → 中文
    """
    if contains_chinese(text):
        source = "zh"
        target = "en"
    else:
        source = "en"
        target = "zh"

    try:
        response = requests.post(
            "https://libretranslate.com/translate",
            headers={"Content-Type": "application/json"},
            json={
                "q": text,
                "source": source,
                "target": target,
                "format": "text"
            },
            timeout=10
        )
        if response.status_code == 200:
            return response.json()["translatedText"]
        else:
            return f"翻譯失敗，狀態碼 {response.status_code}"
    except Exception as e:
        return f"⚠️翻譯錯誤：{str(e)}"


if __name__ == "__main__":
    app.run()
