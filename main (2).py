import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import google.generativeai as genai

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Add placeholders for other AI API keys if needed for '3 brains'
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Configure Gemini API
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    logger.error("GEMINI_API_KEY is not set.")
    gemini_model = None

# Define command handlers
async def start(update: Update, context) -> None:
    """Sends a welcome message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"สวัสดีครับ {user.mention_html()}!\nผมคือบอทสภา 3 สมอง ยินดีให้บริการครับ\nคุณสามารถใช้คำสั่ง /all ตามด้วยข้อความ เพื่อให้ผมและสมองอื่นๆ ช่วยตอบคำถามได้ครับ"
    )

async def all_command(update: Update, context) -> None:
    """Handles the 'all' command to query multiple AI models."""
    if not context.args:
        await update.message.reply_text("กรุณาพิมพ์ /all ตามด้วยคำถามของคุณครับ เช่น /all วิธีทำไข่เจียว")
        return

    prompt = " ".join(context.args)
    await update.message.reply_text(f"กำลังให้สภา 3 สมองพิจารณาคำถาม: '{prompt}' โปรดรอสักครู่ครับ...")

    responses = []

    # Gemini 1.5 Flash response
    if gemini_model:
        try:
            gemini_response = gemini_model.generate_content(prompt)
            responses.append(f"**Gemini 1.5 Flash:**\n{gemini_response.text}")
        except Exception as e:
            logger.error(f"Error from Gemini 1.5 Flash: {e}")
            responses.append(f"**Gemini 1.5 Flash:** เกิดข้อผิดพลาดในการตอบคำถาม: {e}")
    else:
        responses.append("**Gemini 1.5 Flash:** ไม่ได้ตั้งค่า API Key หรือเกิดข้อผิดพลาด")

    # Placeholder for other AI models (e.g., OpenAI, etc.)
    # if OPENAI_API_KEY:
    #     try:
    #         # Integrate OpenAI or other models here
    #         openai_response = "Response from OpenAI"
    #         responses.append(f"**OpenAI:**\n{openai_response}")
    #     except Exception as e:
    #         logger.error(f"Error from OpenAI: {e}")
    #         responses.append(f"**OpenAI:** เกิดข้อผิดพลาดในการตอบคำถาม: {e}")

    final_response = "\n\n".join(responses)
    await update.message.reply_text(final_response)

async def echo(update: Update, context) -> None:
    """Echoes the user message."""
    await update.message.reply_text(update.message.text)

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # On different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("all", all_command))

    # On non command messages - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set. Please set the environment variable.")
    else:
        main()
