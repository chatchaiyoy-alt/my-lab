import os
import telebot
import google.generativeai as genai
import asyncio
import aiohttp

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

bot = telebot.TeleBot(TELEGRAM_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-1.5-flash')

async def ask_gemini(prompt):
    try:
        response = await asyncio.to_thread(gemini_model.generate_content, prompt)
        return f"🤖 **Gemini:**\n{response.text}"
    except: return "🤖 **Gemini:** Error"

async def ask_claude(prompt):
    if not CLAUDE_API_KEY: return "🧠 **Claude:** ยังไม่ได้ใส่ Key"
    url = "https://api.anthropic.com/v1/messages"
    headers = {"x-api-key": CLAUDE_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"}
    data = {"model": "claude-3-haiku-20240307", "max_tokens": 1024, "messages": [{"role": "user", "content": prompt}]}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as resp:
                r = await resp.json()
                return f"🧠 **Claude:**\n{r['content'][0]['text']}"
    except: return "🧠 **Claude:** Error"

async def ask_gpt(prompt):
    if not OPENAI_API_KEY: return "💡 **GPT:** ยังไม่ได้ใส่ Key"
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    data = {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}]}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as resp:
                r = await resp.json()
                return f"💡 **GPT:**\n{r['choices'][0]['message']['content']}"
    except: return "💡 **GPT:** Error"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "สวัสดีครับท่าน ผมบอท 3 สมอง พร้อมให้ Gemini + Claude + GPT ช่วยกันคิดแล้ว")

@bot.message_handler(func=lambda message: True)
def handle_all(message):
    bot.send_chat_action(message.chat.id, 'typing')
    msg = bot.reply_to(message, "ให้ AI 3 ตัวประชุมกันแปป...")
    try:
        tasks = [ask_gemini(message.text), ask_claude(message.text), ask_gpt(message.text)]
        results = asyncio.run(asyncio.gather(*tasks))
        final = "\n\n---\n\n".join(results)
        bot.edit_message_text(final, message.chat.id, msg.message_id, parse_mode='Markdown')
    except Exception as e:
        bot.edit_message_text(f"สภาล่ม: {e}", message.chat.id, msg.message_id)

if __name__ == '__main__':
    print("Multi-AI Bot is running...")
    bot.polling()
