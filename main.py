import os
import telebot
import google.generativeai as genai

# ใส่ Token กับ API Key ใน Environment ของ Render นะท่าน
BOT_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

bot = telebot.TeleBot(BOT_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "สวัสดีครับท่าน ผมบอท Gemini ฟรี พร้อมใช้งานแล้ว")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    try:
        response = model.generate_content(message.text)
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, f"เกิดข้อผิดพลาด: {e}")

if __name__ == '__main__':
    print("Bot is running...")
    bot.polling()
