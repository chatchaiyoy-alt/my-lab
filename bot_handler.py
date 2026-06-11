import nest_asyncio
nest_asyncio.apply()
import os
import asyncio
import google.generativeai as genai
import anthropic
import openai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ดึง Token จาก Environment Variables ใน Railway
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Setup API Clients
genai.configure(api_key=GEMINI_API_KEY)
claude_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("สวัสดีครับท่าน บอท 3 สมอง Gemini+Claude+GPT ออนไลน์แล้ว")

async def ask_gemini(prompt):
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = await model.generate_content_async(prompt)
    return response.text

async def ask_claude(prompt):
    msg = await asyncio.to_thread(
        claude_client.messages.create,
        model="claude-3-haiku-20240307",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    return msg.content[0].text

async def ask_gpt(prompt):
    res = await asyncio.to_thread(
        openai_client.chat.completions.create,
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return res.choices[0].message.content

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    try:
        if text.startswith("claude "):
            reply = await ask_claude(text[7:])
            await update.message.reply_text(f"Claude: {reply}")
        elif text.startswith("gemini "):
            reply = await ask_gemini(text[7:])
            await update.message.reply_text(f"Gemini: {reply}")
        elif text.startswith("gpt "):
            reply = await ask_gpt(text[4:])
            await update.message.reply_text(f"GPT: {reply}")
        elif text.startswith("all "):
            prompt = text[4:]
            await update.message.reply_text("รับทราบ... 3 สมองกำลังประมวลผลทีละตัว แก้สภาล่มแล้ว")
            g = await ask_gemini(prompt)
            await update.message.reply_text(f"Gemini: {g}")
            c = await ask_claude(prompt)
            await update.message.reply_text(f"Claude: {c}")
            o = await ask_gpt(prompt)
            await update.message.reply_text(f"GPT: {o}")
        else:
            await update.message.reply_text("ใช้คำสั่ง: gemini, claude, gpt, all ตามด้วยคำถาม")
    except Exception as e:
        await update.message.reply_text(f"เกิดข้อผิดพลาด: {str(e)}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    # สำคัญมาก: close_loop=False แก้บัคสภาล่มบน Railway
    app.run_polling(close_loop=False)

if __name__ == '__main__':
    main()
