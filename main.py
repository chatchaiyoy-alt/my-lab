import os
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
from openai import OpenAI
import anthropic

# Logging setup
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Config - ดึงจาก Railway Variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

def setup_clients():
    clients = {}
    if GEMINI_API_KEY:
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            clients['gemini'] = genai.GenerativeModel('gemini-1.5-flash')
        except:
            clients['gemini'] = None
    if OPENAI_API_KEY:
        clients['gpt'] = OpenAI(api_key=OPENAI_API_KEY)
    if ANTHROPIC_API_KEY:
        clients['claude'] = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return clients

ai_clients = setup_clients()

async def get_ai_res(name, prompt):
    try:
        if name == 'gemini' and ai_clients.get('gemini'):
            res = await asyncio.to_thread(ai_clients['gemini'].generate_content, prompt)
            return res.text
        if name == 'gpt' and ai_clients.get('gpt'):
            res = await asyncio.to_thread(ai_clients['gpt'].chat.completions.create, model="gpt-4o", messages=[{"role":"user","content":prompt}])
            return res.choices[0].message.content
        if name == 'claude' and ai_clients.get('claude'):
            res = await asyncio.to_thread(ai_clients['claude'].messages.create, model="claude-3-5-sonnet-20240620", max_tokens=1024, messages=[{"role":"user","content":prompt}])
            return res.content[0].text
        return "❌ ไม่ได้ตั้งค่า API Key ตัวนี้"
    except Exception as e:
        return f"❌ Error: {str(e)}"

async def handle_request(update: Update, cmd: str, prompt: str):
    if not prompt:
        await update.message.reply_html(
            f"<b>วิธีใช้:</b> พิมพ์ <code>{cmd} [คำถาม]</code>\n"
            f"ตัวอย่าง: <code>{cmd} สรุปข่าววันนี้ให้หน่อย</code>"
        )
        return

    if cmd == "all":
        msg = await update.message.reply_text("⏳ สภา 3 สมองกำลังประชุม...")
        results = await asyncio.gather(get_ai_res('gemini', prompt), get_ai_res('gpt', prompt), get_ai_res('claude', prompt))
        text = f"<b>🏛️ มติสภา 3 สมอง</b>\n\n<b>♊ Gemini:</b>\n{results[0]}\n\n<b>🤖 GPT-4o:</b>\n{results[1]}\n\n<b>🎭 Claude:</b>\n{results[2]}"
        await msg.edit_text(text, parse_mode='HTML')
    else:
        res = await get_ai_res(cmd, prompt)
        name_tag = {"gemini":"♊ Gemini", "gpt":"🤖 GPT-4o", "claude":"🎭 Claude"}[cmd]
        await update.message.reply_text(f"<b>{name_tag}:</b>\n{res}", parse_mode='HTML')

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text = update.message.text.strip()
    parts = text.split(maxsplit=1)
    cmd = parts[0].lower().replace("/", "")
    prompt = parts[1] if len(parts) > 1 else ""

    if cmd in ["gemini", "gpt", "claude", "all"]:
        await handle_request(update, cmd, prompt)

def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ ไม่พบ TELEGRAM_BOT_TOKEN")
        return
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", lambda u,c: u.message.reply_text("สภา 3 สมอง พร้อม! ลองพิมพ์ 'all สวัสดี'")))
    app.add_handler(MessageHandler(filters.TEXT, on_message))
    app.run_polling()

if __name__ == "__main__":
    main()
