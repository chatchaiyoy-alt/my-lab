import nest_asyncio
nest_asyncio.apply()
import os
import asyncio
import google.generativeai as genai
import anthropic
import openai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
claude_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("สวัสดีครับท่าน บอท 3 สมอง พร้อมรับใช้")

async def ask_gemini(prompt):
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = await model.generate_content_async(prompt)
    return response.text

async def ask_claude(prompt):
    loop = asyncio.get_event_loop()
    def sync_claude():
        msg = claude_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text
    return await loop.run_in_executor(None, sync_claude)

async def ask_gpt(prompt):
    loop = asyncio.get_event_loop()
    def sync_gpt():
        res = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return res.choices[0].message.content
    return await loop.run_in_executor(None, sync_gpt)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()
    original_text = update.message.text
    try:
        if text.startswith("claude"):
            prompt = original_text[6:].strip()
            if not prompt: prompt = "สวัสดี"
            reply = await ask_claude(prompt)
            await update.message.reply_text(f"Claude: {reply}")
        elif text.startswith("gemini"):
            prompt = original_text[6:].strip()
            if not prompt: prompt = "สวัสดี"
            reply = await ask_gemini(prompt)
            await update.message.reply_text(f"Gemini: {reply}")
        elif text.startswith("gpt"):
            prompt = original_text[3:].strip()
            if not prompt: prompt = "สวัสดี"
            reply = await ask_gpt(prompt)
            await update.message.reply_text(f"GPT: {reply}")
        elif text.startswith("all"):
            prompt = original_text[3:].strip()
            if not prompt: prompt = "สวัสดี"
            await update.message.reply_text("รับทราบ... 3 สมองกำลังประมวลผล")
            g = await ask_gemini(prompt)
            await update.message.reply_text(f"Gemini: {g}")
            c = await ask_claude(prompt)
            await update.message.reply_text(f"Claude: {c}")
            o = await ask_gpt(prompt)
            await update.message.reply_text(f"GPT: {o}")
        else:
            await update.message.reply_text("ใช้คำสั่ง: gemini, claude, gpt, all ตามด้วยคำถาม")
    except Exception as e:
        await update.message.reply_text(f"สภาล่ม: {str(e)}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling(close_loop=False)

if __name__ == '__main__':
    main()
