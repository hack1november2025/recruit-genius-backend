import logging
import os

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from telegram.ext import filters
from app.services.chat_orchestrator import ChatOrchestrator
from app.schemas.chat import ChatQueryRequest
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def chat_with_ai(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Only process text messages
    if not (update.message and update.message.text):
        return

    telegram_user_id = update.message.from_user.id
    thread_id = f"telegram_{telegram_user_id}"

    # Build standard chat request
    chat_request = ChatQueryRequest(
        query=update.message.text,
        thread_id=thread_id,
        user_identifier=f"telegram_{telegram_user_id}"
    )

    # Run orchestrator with an async DB session
    async with AsyncSessionLocal() as db:
        orchestrator = ChatOrchestrator(db)
        result = await orchestrator.process_query(chat_request)

    # Send the response text back to Telegram
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=result.response_text
    )

def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "8182925635:AAFZQjzyJApN8JMYFQL5lPvlNKEbihwsHyM")

    app = ApplicationBuilder().token(token).build()


    # Route non-command messages to the chat handler
    app.add_handler(MessageHandler(~filters.COMMAND, chat_with_ai))

    # Start the Bot (runs until Ctrl-C)
    app.run_polling()


if __name__ == '__main__':
    main()