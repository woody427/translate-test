import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai

app = Flask(__name__)

# 環境變數設定
line_bot_api = LineBotApi(os.environ["LINE_CHANNEL_ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["LINE_CHANNEL_SECRET"])
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
                translated = translate_with_gpt(content)
            except Exception as e:
                translated = f"⚠️ 翻譯錯誤：{str(e)}"
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=translated)
            )

def contains_chinese(text):
    return any('\u4e00' <= ch <= '\u9fff' for ch in text)

def translate_with_gpt(text):
    target_lang = "英文" if contains_chinese(text) else "繁體中文"
    prompt = f"請將以下文字翻譯為{target_lang}：\n{text}"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )
    return response.choices[0].message.content.strip()

if __name__ == "__main__":
    app.run()
