import os
import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ตั้งค่าโมเดล AI
import google.generativeai as genai
from openai import OpenAI
import anthropic

# 1. ตั้งค่า Logging เพื่อดูสถานะใน Railway
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 2. ดึง API Keys จาก Variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# 3. ฟังก์ชันเรียก AI แต่ละตัว
async def ask_gemini(prompt):
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(prompt)
        return f"🏛️ **Gemini 2.0:**\n{response.text}\n"
    except Exception as e:
        return f"❌ **Gemini Error:** {str(e)}"

async def ask_gpt(prompt):
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return f"🧠 **GPT-4o:**\n{response.choices[0].message.content}\n"
    except Exception as e:
        return f"❌ **GPT Error:** {str(e)}"

async def ask_claude(prompt):
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        return f"🎨 **Claude 3.5:**\n{response.content[0].text}\n"
    except Exception as e:
        return f"❌ **Claude Error:** {str(e)}"

# 4. ฟังก์ชันจัดการคำสั่ง /all หรือ 'all'
async def handle_all(update: Update, context: ContextTypes.DEFAULT_TYPE, prompt: str):
    if not prompt:
        await update.message.reply_text("กรุณาใส่คำถามด้วยครับ เช่น 'all วันนี้อากาศดีไหม'")
        return
    
    status_msg = await update.message.reply_text("⏳ สภา 3 สมองกำลังประมวลผล...")
    
    # รันพร้อมกันทั้ง 3 ตัวเพื่อความเร็ว
    results = await asyncio.gather(
        ask_gemini(prompt),
        ask_gpt(prompt),
        ask_claude(prompt)
    )
    
    final_response = "🏛️ **มติสภา 3 สมอง** 🏛️\n\n" + "\n".join(results)
    await status_msg.edit_text(final_response, parse_mode='Markdown')

# 5. ตัวรับข้อความปกติ (เพื่อรองรับการพิมพ์โดยไม่มี /)
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()
    
    if text.startswith('all'):
        prompt = text[3:].strip()
        await handle_all(update, context, prompt)
    elif text.startswith('gemini'):
        prompt = text[6:].strip()
        await update.message.reply_text(await ask_gemini(prompt), parse_mode='Markdown')
    elif text.startswith('gpt'):
        prompt = text[3:].strip()
        await update.message.reply_text(await ask_gpt(prompt), parse_mode='Markdown')
    elif text.startswith('claude'):
        prompt = text[6:].strip()
        await update.message.reply_text(await ask_claude(prompt), parse_mode='Markdown')

# 6. คำสั่ง /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏛️ **ยินดีต้อนรับสู่สภา 3 สมอง!**\n\n"
        "ท่านสามารถสั่งการได้ดังนี้:\n"
        "• `all [คำถาม]` - ถามทั้ง 3 AI พร้อมกัน\n"
        "• `gemini [คำถาม]` - ถาม Gemini 2.0\n"
        "• `gpt [คำถาม]` - ถาม GPT-4o\n"
        "• `claude [คำถาม]` - ถาม Claude 3.5\n"
        "(รองรับทั้งแบบพิมพ์ปกติและใส่ / นำหน้าครับ)",
        parse_mode='Markdown'
    )

# 7. เริ่มต้นบอท
if __name__ == '__main__':
    if not TELEGRAM_TOKEN:
        logger.error("❌ ไม่พบ TELEGRAM_BOT_TOKEN ใน Variables!")
    else:
        logger.info("🚀 สภาเปิดประชุมแล้ว...")
        app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        
        # เพิ่ม Handler
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))
        
        # รันบอท
        app.run_
      polling()
