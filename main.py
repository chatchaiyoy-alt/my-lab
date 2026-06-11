import os
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
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
def setup_clients():
    clients = {}
    if GEMINI_API_KEY:
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            # แก้ไขตรงนี้: ใช้ชื่อโมเดลมาตรฐานที่เสถียรที่สุด
            clients['gemini'] = genai.GenerativeModel('gemini-1.5-flash')
        except Exception as e:
            logger.error(f"Gemini setup error: {e}")
            clients['gemini'] = None
    if OPENAI_API_KEY:
        clients['gpt'] = OpenAI(api_key=OPENAI_API_KEY)
    if ANTHROPIC_API_KEY:
        clients['claude'] = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return clients

ai_clients = setup_clients()

# --- AI Call Functions ---
async def get_gemini_response(prompt):
    model = ai_clients.get('gemini')
    if not model: return "❌ ไม่ได้ตั้งค่า Gemini API Key"
    try:
        # ใช้ asyncio.to_thread เพื่อไม่ให้บล็อกการทำงานหลัก
        response = await asyncio.to_thread(model.generate_content, prompt)
        return response.text
    except Exception as e:
        logger.error(f"Gemini Error: {e}")
        return f"❌ Gemini Error: {str(e)}"

async def get_gpt_response(prompt):
    client = ai_clients.get('gpt')
    if not client: return "❌ ไม่ได้ตั้งค่า OpenAI API Key"
    try:
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ GPT Error: {str(e)}"

async def get_claude_response(prompt):
    client = ai_clients.get('claude')
    if not client: return "❌ ไม่ได้ตั้งค่า Anthropic API Key"
    try:
        response = await asyncio.to_thread(
            client.messages.create,
            model="claude-3-5-sonnet-20240620",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        return f"❌ Claude Error: {str(e)}"

# --- Logic for Processing Commands ---
async def handle_ai_request(update: Update, cmd: str, prompt: str):
    if not prompt:
        await update.message.reply_text("ใช้คำสั่ง: gemini, claude, gpt, all ตามด้วยคำถาม")
        return

    if cmd == "gemini":
        res = await get_gemini_response(prompt)
        await update.message.reply_text(f"<b>♊ Gemini:</b>\n{res}", parse_mode='HTML')
    elif cmd == "gpt":
        res = await get_gpt_response(prompt)
        await update.message.reply_text(f"<b>🤖 GPT-4o:</b>\n{res}", parse_mode='HTML')
    elif cmd == "claude":
        res = await get_claude_response(prompt)
        await update.message.reply_text(f"<b>🎭 Claude:</b>\n{res}", parse_mode='HTML')
    elif cmd == "all":
        msg = await update.message.reply_text("⏳ สภา 3 สมองกำลังประชุม... โปรดรอสักครู่")
        res_gemini, res_gpt, res_claude = await asyncio.gather(
            get_gemini_response(prompt),
            get_gpt_response(prompt),
            get_claude_response(prompt)
        )
        final_text = (
            f"<b>🏛️ มติสภา 3 สมอง</b>\n\n"
            f"<b>♊ Gemini:</b>\n{res_gemini}\n\n"
            f"<b>🤖 GPT-4o:</b>\n{res_gpt}\n\n"
            f"<b>🎭 Claude:</b>\n{res_claude}"
        )
        await msg.edit_text(final_text, parse_mode='HTML')

# --- Telegram Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_html("<b>สภา 3 สมอง พร้อมรับคำสั่ง!</b> 🏛️\nลองพิมพ์: <code>all ทดสอบ</code>")

async def message_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text: return
    text = update.message.text.strip()
    parts = text.split(maxsplit=1)
    first_word = parts[0].lower().replace("/", "")
    prompt = parts[1] if len(parts) > 1 else ""
    valid_cmds = ["gemini", "gpt", "claude", "all"]
    if first_word in valid_cmds:
        await handle_ai_request(update, first_word, prompt)

def main() -> None:
    if not TELEGRAM_BOT_TOKEN: return
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_router))
    app.add_handler(MessageHandler(filters.COMMAND, message_router))
    app.run_polling()

if __name__ == "__main__":
    main()
