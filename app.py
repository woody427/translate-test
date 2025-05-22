import os
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
    
    print(f"[Webhook] Received body: {body}")
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text
    if text.startswith("@T"):
        content = text[2:].strip()
        if content:
            translated = translate(content)
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text=translated)
            )

def translate(text):
    if contains_chinese(text):
        return "This is a simulated English translation."
    else:
        return "這是模擬的中文翻譯。"

def contains_chinese(text):
    return any('\u4e00' <= char <= '\u9fff' for char in text)

if __name__ == "__main__":
    app.run()
