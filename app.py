import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai

app = Flask(__name__)

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
    text = event.message.text
    if text.lower().startswith("@t"):
        content = text[2:].strip()
        if content:
            try:
                translated = translate_with_openai(content)
                line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(text=translated)
                )
            except Exception as e:
                error_msg = f"⚠️ 翻譯錯誤：\n{str(e)}"
                line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(text=error_msg)
                )

def translate_with_openai(text):
    is_chinese = any('\u4e00' <= ch <= '\u9fff' for ch in text)
    prompt = f"請將以下句子翻譯成{'英文' if is_chinese else '中文'}：\n{text}"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "你是一個翻譯機器人，請根據使用者語言將輸入翻譯成目標語言。"},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

if __name__ == "__main__":
    app.run()
