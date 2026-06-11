import os
import logging
import asyncio
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import anthropic

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

anthropic_key = os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=anthropic_key) if anthropic_key else None
if client: logger.info("✅ Claude Sonnet 4.5 Client Loaded")

async def ask_claude(prompt):
    try:
        if not client: return "❌ ลืมใส่ ANTHROPIC_API_KEY ใน Railway Variables"
        res = await asyncio.to_thread(
            client.messages.create,
            model="claude-sonnet-4-5",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        return f"<b>🎭 Claude Sonnet 4.5:</b>\n{res.content[0].text}"
    except Exception as e:
        logger.error(f"Claude Error: {str(e)}")
        return f"<b>❌ Claude Error:</b>\n<code>{str(e)[:200]}</code>"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏛️ สภา Claude พร้อมแล้วท่าน! พิมพ์อะไรมาได้เลย")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    if update.message.text.startswith('/start'):
        await start(update, context)
        return

    msg = await update.message.reply_text("⏳ Claude กำลังคิด...")
    result = await ask_claude(update.message.text)
    await msg.edit_text(result, parse_mode=ParseMode.HTML)

if __name__ == '__main__':
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("❌ ไม่พบ TELEGRAM_BOT_TOKEN")
    else:
        app = ApplicationBuilder().token(token).build()
        app.add_handler(CommandHandler("start", handle_message))
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        logger.info("🚀 บอท Claude เริ่มทำงาน...")
        app.run_polling(drop_pending_updates=True)
