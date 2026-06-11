import os
import logging
import asyncio
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from groq import Groq

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

groq_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=groq_key) if groq_key else None
if client:
    logger.info("✅ Groq Llama 3.3 70B Client Loaded")
else:
    logger.error("❌ ไม่พบ GROQ_API_KEY")

async def ask_groq(prompt):
    try:
        if not client:
            return "❌ ลืมใส่ GROQ_API_KEY ใน Railway Variables"
        res = await asyncio.to_thread(
            client.chat.completions.create,
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2048
        )
        return f"<b>⚡ Groq Llama 3.3 70B:</b>\n{res.choices[0].message.content}"
    except Exception as e:
        logger.error(f"Groq Error: {str(e)}")
        return f"<b>❌ Groq Error:</b>\n<code>{str(e)[:200]}</code>"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text

    if text == "/start":
        await update.message.reply_text("🏛️ สภา Groq พร้อมแล้วท่าน! เร็ว แรง ฟรี\nพิมพ์อะไรมาได้เลย")
        return

    msg = await update.message.reply_text("⚡ Groq กำลังคิด...0.5 วิ")
    result = await ask_groq(text)
    await msg.edit_text(result, parse_mode=ParseMode.HTML)

if __name__ == '__main__':
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("❌ ไม่พบ TELEGRAM_BOT_TOKEN")
    else:
        app = ApplicationBuilder().token(token).build()
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        app.add_handler(MessageHandler(filters.COMMAND, handle_message))
        logger.info("🚀 บอท Groq เริ่มทำงาน...")
        app.run_polling(drop_pending_updates=True)
