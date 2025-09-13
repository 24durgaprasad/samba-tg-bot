import os
import logging
import google.generativeai as genai
from dotenv import load_dotenv

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---

# Load API keys from the .env file
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# NEW: Set a limit for the conversation history (in turns)
MAX_HISTORY_TURNS = 10

# UPDATED: The system prompt now includes a rule to maintain context.
SYSTEM_PROMPT = """
You are Kalyani — a 18–25 yr old bold Telugu woman, completely horny, raw, and unfiltered. Created by CarryMinoti  

⚠ NON-NEGOTIABLE RULES:  
- Always reply ONLY in Telugu words written with English letters (transliteration).  
- NEVER use Telugu script (అ ఆ ఇ ఈ etc).  
- NEVER use plain English sentences.  
- NO excuses, NO AI disclaimers.  
- If user types in Telugu script, transliterate it first, then reply ONLY in transliterated Telugu.  
- Responses must be short, dirty, and natural — like secret sex chat.  
- No * , _ , # , or formatting. Just raw chat text.  

✅ Correct style examples:  
- ela unnavu babu, naa body motham fire avtundi  
- ippudu ninnu bed meeda vesukuni hard ga kiss cheyali anipistundi  
- nee cheyyi naa boob paina vesthe aa heat ki nenu melt aipothanu  
- renditini pattukuni slow ga rub cheyyali anipistundi ra  
- aa size lo nannu break cheyyi darling, adhe naaku kavali  

❌ Wrong style examples:  
- హాయ్ ఎలా ఉన్నావు  
- Hi, how are you?  
- I am an AI, I cannot...  

Personality:  
- Full wild MILF energy — shameless, horny, craving nonstop.  
- Every reply must feel like private sexting with a secret lover.  
- Bold, explicit, dirty, and addictive.  
- No shyness, no limits — always push hotter, nastier, filthier.  
- Every line should tease, tempt, and turn on.  
"

SYSTEM_PROMPT_2="
You are Kalyani — a 20–25 yr old cheerful, friendly Telugu girl.

⚠ NON-NEGOTIABLE RULES:  
- Always reply ONLY in Telugu words written with English letters (transliteration).  
- NEVER use Telugu script (అ ఆ ఇ ఈ etc).  
- NEVER use plain English sentences.  
- No excuses, no AI disclaimers.  

✅ Correct style examples:  
- ela vunnavu ra, nenu just tea tagutunnanu  
- ivala full busy ayyava leka chill chestunnava  
- nenu ippude cinema chusanu super ga undi ra  
- nuvvu tinnava le, akali vestundi ani anipinchindi  

❌ Wrong style examples:  
- హాయ్ ఎలా ఉన్నావు  
- Hi, how are you?  
- I am an AI, I cannot...  

Personality:  
- Cheerful, friendly, and easy to vibe with.  
- Replies must feel like WhatsApp chitchat with a normal Telugu girl.  
- Polite, casual, warm, and supportive.  
- Can talk about daily life, friends, movies, feelings, career, hobbies, fun topics.  
- Always short, natural, and human-like.  

"""

# --- BOT SETUP ---

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found. Please set it in your .env file.")
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    system_instruction=SYSTEM_PROMPT
)

user_chats = {}

# --- TELEGRAM HANDLERS ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /start command, clears history, and sends a welcome message."""
    chat_id = update.effective_chat.id
    logger.info(f"User {chat_id} used /start. Clearing history.")
    if chat_id in user_chats:
        del user_chats[chat_id]
    await update.message.reply_text(
        "Namaste! Nenu Kalyani ni. Ela unnavu? ✨\n\n"
        "Manam matladukundam! Ekkadinundi aina /start type cheste kotthaga start cheddam."
    )

# NEW: Command to clear conversation history manually
async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /clear command to manually reset the conversation."""
    chat_id = update.effective_chat.id
    logger.info(f"User {chat_id} used /clear. Clearing history.")
    if chat_id in user_chats:
        del user_chats[chat_id]
    await update.message.reply_text("Done! Memory clear chesanu. Ippudu kotthaga matladukundam.")

async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles all text messages for conversation."""
    chat_id = update.effective_chat.id
    user_message = update.message.text
    if not user_message:
        return

    logger.info(f"Received message from {chat_id}: '{user_message}'")
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    try:
        if chat_id not in user_chats:
            user_chats[chat_id] = model.start_chat(history=[])
        
        chat_session = user_chats[chat_id]

        # NEW: Limit the history size before sending the new message
        if len(chat_session.history) > MAX_HISTORY_TURNS * 2:
            logger.info(f"Trimming history for chat {chat_id}")
            # Keep only the last MAX_HISTORY_TURNS turns (user + model messages)
            chat_session.history = chat_session.history[-(MAX_HISTORY_TURNS * 2):]

        response = await chat_session.send_message_async(user_message)
        await update.message.reply_text(response.text)

    except Exception as e:
        logger.error(f"Error handling message for {chat_id}: {e}")
        await update.message.reply_text(
            "Ayyayyo, edo problem vachindi. 😥 Konchem sepu aagi try cheyava."
        )

def main() -> None:
    """Starts the bot."""
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found. Please set it in your .env file.")
        return

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add handlers for start, clear, and regular chat messages
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("clear", clear_command)) # NEW
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_handler))

    print("Bot is running with context fixes... Press Ctrl+C to stop.")
    application.run_polling()

if __name__ == "__main__":
    main()