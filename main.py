import os
import logging
import asyncio
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
from openai import OpenAI
import anthropic

# 1. ตั้งค่า Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# 2. ฟังก์ชันโหลด Clients
def get_clients():
    clients = {}

    # Gemini Setup: ใช้ 2.0-flash-exp ตัวใหม่สุด กัน 404
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        try:
            genai.configure(api_key=gemini_key)
            clients['gemini'] = genai.GenerativeModel('gemini-2.0-flash-exp')
            logger.info("✅ Gemini 2.0 Client Loaded")
        except Exception as e: logger.error(f"❌ Gemini Error: {e}")

    # GPT Setup
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        clients['gpt'] = OpenAI(api_key=openai_key)
        logger.info("✅ GPT-4o Client Loaded")

    # Claude Setup
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        clients['claude'] = anthropic.Anthropic(api_key=anthropic_key)
        logger.info("✅ Claude Sonnet 4.5 Client Loaded")

    return clients

AI_CLIENTS = get_clients()

# 3. ฟังก์ชันเรียก AI กันพังทุกเคส
async def ask_ai(target, prompt):
    try:
        if target == 'gemini' and 'gemini' in AI_CLIENTS:
            res = await asyncio.to_thread(AI_CLIENTS['gemini'].generate_content, prompt)
            # ดัก Safety Filter + res.text เป็น None
            if not res.parts:
                return "<b>🏛️ Gemini 2.0:</b>\n⚠️ ถูกบล็อกโดยระบบความปลอดภัย"
            text = res.text if res.text else "⚠️ ไม่ได้รับคำตอบ"
            return f"<b>🏛️ Gemini 2.0:</b>\n{text}"

        elif target == 'gpt' and 'gpt' in AI_CLIENTS:
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

# 4. จัดการข้อความ
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
        msg = await update.message.reply_text("⏳ สภา 3 สมองกำลังประมวลผล...")

        results = await asyncio.gather(
            ask_ai('gemini', prompt),
            ask_ai('gpt', prompt),
            ask_ai('claude', prompt)
        )

        # กัน MessageTooLong + ใช้ HTML ให้สวย
        header = "<b>🏛️ มติสภา 3 สมอง</b>\n\n"
        final_text = header + "\n\n".join(results)
        if len(final_text) > 4090:
            final_text = final_text[:4090] + "\n\n<i>...ข้อความถูกตัดเพราะยาวเกินไป...</i>"

        await msg.edit_text(final_text, parse_mode=ParseMode.HTML)

    elif cmd in ['gemini', 'gpt', 'claude']:
        if not prompt: return
        result = await ask_ai(cmd, prompt)
        await update.message.reply_text(result, parse_mode=ParseMode.HTML)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏛️ สภา 3 สมอง (High Performance) พร้อมแล้ว!\nใช้คำสั่ง 'all [คำถาม]' เพื่อเริ่มประชุมครับ")

if __name__ == '__main__':
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("❌ ไม่พบ TELEGRAM_BOT_TOKEN")
    else:
        app = ApplicationBuilder().token(token).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        for c in ['all', 'gemini', 'gpt', 'claude']:
            app.add_handler(CommandHandler(c, handle_message))

        logger.info("🚀 บอทเริ่มทำงานในโหมด Non-blocking...")
        app.run_polling(drop_pending_updates=True)
