import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from openai import OpenAI

app = Flask(__name__)

# 初始化 LINE Bot API
line_bot_api = LineBotApi(os.environ.get("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.environ.get("LINE_CHANNEL_SECRET"))

# 初始化 OpenAI
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text
    if text.lower().startswith("@t"):
        content = text[2:].strip()
        if content:
            try:
                reply = translate_with_openai(content)
            except Exception as e:
                reply = f"\ud83d\udea8 翻譯錯誤\uff1a\n{str(e)}"
        else:
            reply = "\u8acb\u5728 @T \u5f8c\u8cbc\u4e0a\u60f3\u7ffb\u8b6f\u7684\u6587\u5b57"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply)
        )

def translate_with_openai(content):
    system_prompt = "You are a translation assistant. Translate between Chinese and English depending on input."
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ]
    )
    return response.choices[0].message.content.strip()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
