import os
import logging
import asyncio
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI
import anthropic

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def get_clients():
    clients = {}
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        clients['gpt'] = OpenAI(api_key=openai_key)
        logger.info("✅ GPT-4o Client Loaded")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        clients['claude'] = anthropic.Anthropic(api_key=anthropic_key)
        logger.info("✅ Claude Sonnet 4.5 Client Loaded")
    return clients

AI_CLIENTS = get_clients()

async def ask_ai(target, prompt):
    try:
        if target == 'gpt' and 'gpt' in AI_CLIENTS:
            res = await asyncio.to_thread(
                AI_CLIENTS['gpt'].chat.completions.create,
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}]
            )
            return f"<b>🧠 GPT-4o:</b>\n{res.choices[0].message.content}"
        elif target == 'claude' and 'claude' in AI_CLIENTS:
            res = await asyncio.to_thread(
                AI_CLIENTS['claude'].messages.create,
                model="claude-sonnet-4-5",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            return f"<b>🎭 Claude Sonnet 4.5:</b>\n{res.content[0].text}"
        return f"❌ {target} is not configured."
    except Exception as e:
        logger.error(f"Error calling {target}: {str(e)}")
        return f"<b>❌ {target} Error:</b>\n<code>{str(e)[:200]}...</code>"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    full_text = update.message.text.strip()
    parts = full_text.split(maxsplit=1)
    cmd = parts[0].lower().replace('/', '')
    prompt = parts[1] if len(parts) > 1 else ""

    if cmd == 'all':
        if not prompt:
            await update.message.reply_text("กรุณาใส่คำถาม เช่น: all วิเคราะห์เศรษฐกิจโลก")
            return
        msg = await update.message.reply_text("⏳ สภา 2 สมองกำลังประมวลผล...")
        results = await asyncio.gather(ask_ai('gpt', prompt), ask_ai('claude', prompt))
        header = "<b>🏛️ มติสภา 2 สมอง</b>\n\n"
        final_text = header + "\n\n".join(results)
        if len(final_text) > 4090:
            final_text = final_text[:4090] + "\n\n<i>...ข้อความถูกตัดเพราะยาวเกินไป...</i>"
        await msg.edit_text(final_text, parse_mode=ParseMode.HTML)
    elif cmd in ['gpt', 'claude']:
        if not prompt: return
        result = await ask_ai(cmd, prompt)
        await update.message.reply_text(result, parse_mode=ParseMode.HTML)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏛️ สภา 2 สมอง GPT + Claude พร้อมแล้ว!\nใช้คำสั่ง 'all [คำถาม]' เพื่อเริ่มประชุมครับ")

if __name__ == '__main__':
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("❌ ไม่พบ TELEGRAM_BOT_TOKEN")
    else:
        app = ApplicationBuilder().token(token).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        for c in ['all', 'gpt', 'claude']:
            app.add_handler(CommandHandler(c, handle_message))
        logger.info("🚀 บอท 2 สมองเริ่มทำงาน...")
        app.run_polling(drop_pending_updates=True)
