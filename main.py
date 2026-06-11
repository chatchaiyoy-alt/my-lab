import os
import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from groq import Groq

# ตั้งค่า Log
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# โหลด Groq Client
groq_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=groq_key) if groq_key else None
if client:
    logger.info("✅ Groq Llama 3.3 70B Client Loaded")
else:
    logger.error("❌ ไม่พบ GROQ_API_KEY")

async def ask_groq(prompt):
    """เรียก Groq Llama 3.3 70B - ปิด HTML กันบอทพัง"""
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
        # ลบ <b> ออกก่อน กัน HTML พัง
        return f"⚡ Groq Llama 3.3 70B:\n{res.choices[0].message.content}"

    except Exception as e:
        logger.error(f"Groq Error: {str(e)}")
        return f"❌ Groq Error:\n{str(e)[:200]}"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """รับข้อความทั้งหมดจาก Telegram"""
    if not update.message or not update.message.text:
        return

    text = update.message.text

    # คำสั่ง /start
    if text == "/start":
        await update.message.reply_text("🏛️ สภา Groq พร้อมแล้วท่าน! เร็ว แรง ฟรี\nพิมพ์อะไรมาได้เลย")
        return

    # ส่งไปให้ Groq คิด - ไม่ใช้ HTML
    msg = await update.message.reply_text("⚡ Groq กำลังคิด...0.5 วิ")
    result = await ask_groq(text)
    await msg.edit_text(result) # เอา parse_mode=ParseMode.HTML ออก

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
