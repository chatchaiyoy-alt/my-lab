import os
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import google.generativeai as genai
from openai import OpenAI
import anthropic

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# --- AI Client Setup ---

# Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    gemini_model = None

# OpenAI
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Anthropic
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

# --- AI Call Functions ---

async def get_gemini_response(prompt):
    if not gemini_model: return "❌ ไม่ได้ตั้งค่า Gemini API Key"
    try:
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ Gemini Error: {str(e)}"

async def get_gpt_response(prompt):
    if not openai_client: return "❌ ไม่ได้ตั้งค่า OpenAI API Key"
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ GPT Error: {str(e)}"

async def get_claude_response(prompt):
    if not anthropic_client: return "❌ ไม่ได้ตั้งค่า Anthropic API Key"
    try:
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        return f"❌ Claude Error: {str(e)}"

# --- Telegram Command Handlers ---

async def start(update: Update, context) -> None:
    await update.message.reply_html(
        "<b>ยินดีต้อนรับสู่สภา 3 สมอง!</b> 🏛️\n\n"
        "<b>คำสั่งที่ใช้งานได้:</b>\n"
        "🔹 <code>/gemini [คำถาม]</code> - ถาม Gemini 1.5 Flash\n"
        "🔹 <code>/gpt [คำถาม]</code> - ถาม GPT-4o\n"
        "🔹 <code>/claude [คำถาม]</code> - ถาม Claude 3.5 Sonnet\n"
        "🔹 <code>/all [คำถาม]</code> - ถามทั้ง 3 สมองพร้อมกัน\n\n"
        "ลองเลย! เช่น <code>/all วิธีทำไข่เจียวให้กรอบ</code>"
    )

async def gemini_cmd(update: Update, context) -> None:
    prompt = " ".join(context.args)
    if not prompt: return await update.message.reply_text("กรุณาใส่คำถามด้วยครับ")
    res = await get_gemini_response(prompt)
    await update.message.reply_text(f"<b>♊ Gemini:</b>\n{res}", parse_mode='HTML')

async def gpt_cmd(update: Update, context) -> None:
    prompt = " ".join(context.args)
    if not prompt: return await update.message.reply_text("กรุณาใส่คำถามด้วยครับ")
    res = await get_gpt_response(prompt)
    await update.message.reply_text(f"<b>🤖 GPT-4o:</b>\n{res}", parse_mode='HTML')

async def claude_cmd(update: Update, context) -> None:
    prompt = " ".join(context.args)
    if not prompt: return await update.message.reply_text("กรุณาใส่คำถามด้วยครับ")
    res = await get_claude_response(prompt)
    await update.message.reply_text(f"<b>🎭 Claude:</b>\n{res}", parse_mode='HTML')

async def all_cmd(update: Update, context) -> None:
    prompt = " ".join(context.args)
    if not prompt: return await update.message.reply_text("กรุณาใส่คำถามด้วยครับ")
    
    msg = await update.message.reply_text("⏳ สภา 3 สมองกำลังประชุม... โปรดรอสักครู่")
    
    # Run all requests concurrently
    gemini_task = get_gemini_response(prompt)
    gpt_task = get_gpt_response(prompt)
    claude_task = get_claude_response(prompt)
    
    res_gemini, res_gpt, res_claude = await asyncio.gather(gemini_task, gpt_task, claude_task)
    
    final_text = (
        f"<b>🏛️ มติสภา 3 สมอง</b>\n\n"
        f"<b>♊ Gemini:</b>\n{res_gemini}\n\n"
        f"<b>🤖 GPT-4o:</b>\n{res_gpt}\n\n"
        f"<b>🎭 Claude:</b>\n{res_claude}"
    )
    
    await msg.edit_text(final_text, parse_mode='HTML')

def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        logger.error("Missing TELEGRAM_BOT_TOKEN")
        return

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gemini", gemini_cmd))
    app.add_handler(CommandHandler("gpt", gpt_cmd))
    app.add_handler(CommandHandler("claude", claude_cmd))
    app.add_handler(CommandHandler("all", all_cmd))

    app.run_polling()

if __name__ == "__main__":
    main()
