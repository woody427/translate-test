import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai

app = Flask(__name__)

# LINE credentials
line_bot_api = LineBotApi(os.environ["LINE_CHANNEL_ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["LINE_CHANNEL_SECRET"])

# OpenAI API key
openai.api_key = os.environ["OPENAI_API_KEY"]

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()

    if text.lower().startswith("@t"):
        content = text[2:].strip()
        if content:
            try:
                translated = translate(content)
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=translated)
                )
            except Exception as e:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=f"⚠️ 翻譯錯誤：\n{str(e)}")
                )

def translate(text):
    if contains_chinese(text):
        prompt = f"Translate the following text to English:\n{text}"
    else:
        prompt = f"請將以下內容翻譯成繁體中文：\n{text}"

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "你是一個翻譯助手。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=1000
    )
    return response["choices"][0]["message"]["content"].strip()

def contains_chinese(text):
    return any('\u4e00' <= c <= '\u9fff' for c in text)

if __name__ == "__main__":
    app.run()
