import os
import logging
import asyncio
import traceback
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
from openai import OpenAI
import anthropic

# 1. ตั้งค่า Logging ให้ละเอียดที่สุด
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 2. โหลดค่าจาก Variables
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
GPT_KEY = os.getenv("OPENAI_API_KEY")
CLAUDE_KEY = os.getenv("ANTHROPIC_API_KEY")

# 3. เตรียม AI Clients แบบปลอดภัย
def get_clients():
    c = {}
    try:
        if GEMINI_KEY:
            genai.configure(api_key=GEMINI_KEY)
            c['gemini'] = genai.GenerativeModel('gemini-1.5-flash')
        if GPT_KEY: c['gpt'] = OpenAI(api_key=GPT_KEY)
        if CLAUDE_KEY: c['claude'] = anthropic.Anthropic(api_key=CLAUDE_KEY)
    except Exception as e:
        logger.error(f"Setup Error: {e}")
    return c

clients = get_clients()

# 4. ฟังก์ชันเรียก AI แบบไม่ยอมให้บอทพัง
async def ask_ai(name, prompt):
    try:
        if name == 'gemini' and clients.get('gemini'):
            # แก้ปัญหา 404 และ Safety Filter
            res = await asyncio.to_thread(clients['gemini'].generate_content, prompt)
            return res.text if res.text else "⚠️ ไม่มีคำตอบ (อาจติดระบบความปลอดภัย)"
        
        if name == 'gpt' and clients.get('gpt'):
            res = await asyncio.to_thread(clients['gpt'].chat.completions.create, model="gpt-4o", messages=[{"role":"user","content":prompt}])
            return res.choices[0].message.content
            
        if name == 'claude' and clients.get('claude'):
            res = await asyncio.to_thread(clients['claude'].messages.create, model="claude-3-5-sonnet-20240620", max_tokens=1024, messages=[{"role":"user","content":prompt}])
            return res.content[0].text
            
        return "❌ ยังไม่ได้ตั้งค่า API ตัวนี้"
    except Exception as e:
        err_msg = str(e)
        logger.error(f"Error in {name}: {traceback.format_exc()}")
        return f"❌ {name} Error: {err_msg[:100]}..."

# 5. จัดการคำสั่ง
async def on_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    text = update.message.text.strip()
    parts = text.split(maxsplit=1)
    cmd = parts[0].lower().replace("/", "")
    prompt = parts[1] if len(parts) > 1 else ""
    
    if cmd in ["gemini", "gpt", "claude", "all"]:
        if not prompt:
            await update.message.reply_text(f"พิมพ์ {cmd} ตามด้วยคำถามครับ")
            return
            
        if cmd == "all":
            m = await update.message.reply_text("⏳ สภา 3 สมองกำลังประชุม...")
            r = await asyncio.gather(ask_ai('gemini', prompt), ask_ai('gpt', prompt), ask_ai('claude', prompt))
            out = f"<b>🏛️ มติสภา 3 สมอง</b>\n\n<b>♊ Gemini:</b>\n{r[0]}\n\n<b>🤖 GPT-4o:</b>\n{r[1]}\n\n<b>🎭 Claude:</b>\n{r[2]}"
            await m.edit_text(out, parse_mode='HTML')
        else:
            res = await ask_ai(cmd, prompt)
            await update.message.reply_text(f"<b>ผลลัพธ์จาก {cmd}:</b>\n{res}", parse_mode='HTML')

# 6. รันบอท
def main():
    if not TOKEN:
        logger.error("❌ ลืมใส่ TELEGRAM_BOT_TOKEN!")
        return
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", lambda u,c: u.message.reply_text("บอทสภา 3 สมอง พร้อม! ลองพิมพ์ 'all สวัสดี'")))
    app.add_handler(MessageHandler(filters.TEXT, on_msg))
    logger.info("🚀 สภาเปิดประชุมแล้ว...")
    app.run_polling()

if __name__ == "__main__":
   
  main()
