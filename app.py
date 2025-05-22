import os
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from openai import OpenAI, OpenAIError

app = Flask(__name__)

line_bot_api = LineBotApi(os.environ["LINE_CHANNEL_ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["LINE_CHANNEL_SECRET"])
openai_api_key = os.environ.get("OPENAI_API_KEY")

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
                translated = translate(content)
            except Exception as e:
                translated = f"\ud83d\uded1 翻譯錯誤：\n{e}"
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=translated)
            )

def translate(text):
    try:
        return openai_translate(text)
    except Exception:
        return libretranslate(text)

def openai_translate(text):
    import openai
    openai.api_key = openai_api_key
    prompt = f"Translate this into {'English' if contains_chinese(text) else 'Traditional Chinese'}: {text}"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        timeout=10
    )
    return response.choices[0].message.content.strip()

def libretranslate(text):
    url = "https://libretranslate.de/translate"
    source = "zh" if contains_chinese(text) else "en"
    target = "en" if source == "zh" else "zh"
    payload = {
        "q": text,
        "source": source,
        "target": target,
        "format": "text"
    }
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    return response.json()["translatedText"]

def contains_chinese(text):
    return any('\u4e00' <= char <= '\u9fff' for char in text)

if __name__ == "__main__":
    app.run()
