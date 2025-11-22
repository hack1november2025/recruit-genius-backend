import logging
from openai import OpenAI
import asyncio
import io
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
)
from telegram.ext import filters
from app.services.chat_orchestrator import ChatOrchestrator
from app.schemas.chat import ChatQueryRequest
from app.db.session import AsyncSessionLocal
from app.core.config import get_settings

logger = logging.getLogger(__name__)


async def chat_with_ai(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Only process text messages
    if not (update.message and update.message.text):
        return

    # Show typing status
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    except Exception:
        logger.debug("Failed to send typing action", exc_info=True)

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


async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Handle Telegram voice (OGG/OPUS)
    if not (update.message and update.message.voice):
        return

    # Show bot is recording/processing audio
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="record_audio")
    except Exception:
        logger.debug("Failed to send record_audio action", exc_info=True)

    telegram_user_id = update.message.from_user.id
    thread_id = f"telegram_{telegram_user_id}"

    file_id = update.message.voice.file_id
    file = await context.bot.get_file(file_id)
    audio_bytes = await file.download_as_bytearray()

    settings = get_settings()
    openai_key = settings.openai_api_key
    if not openai_key:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Sorry, transcription service is not configured."
        )
        return

    # Transcribe using OpenAI whisper SDK
    try:
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "voice.ogg"
        audio_file.seek(0)

        client = OpenAI(api_key=openai_key)

        def transcribe_sync():
            return client.audio.transcriptions.create(model="whisper-1", file=audio_file)

        trans_resp = await asyncio.to_thread(transcribe_sync)
        transcription = trans_resp.get("text") if isinstance(trans_resp, dict) else getattr(trans_resp, "text", None)
    except Exception as e:
        logging.exception("Transcription failed")
        short = f"{e.__class__.__name__}: {str(e)}"
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Sorry, I couldn't understand what you said. ({short})"
        )
        return

    if not transcription:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Transcription was empty."
        )
        return

    # Build chat request using the transcription
    chat_request = ChatQueryRequest(
        query=transcription,
        thread_id=thread_id,
        user_identifier=f"telegram_{telegram_user_id}"
    )

    async with AsyncSessionLocal() as db:
        orchestrator = ChatOrchestrator(db)
        result = await orchestrator.process_query(chat_request)

    # Send both the transcription and AI response
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=result.response_text
    )

def main() -> None:
    # Prefer loading via application settings so the project's `.env` is respected
    settings = get_settings()
    token = settings.telegram_bot_token

    if not token:
        raise EnvironmentError("TELEGRAM_BOT_TOKEN environment variable not set")

    app = ApplicationBuilder().token(token).build()


    # Route voice notes to the voice handler
    app.add_handler(MessageHandler(filters.VOICE & ~filters.COMMAND, handle_voice_message))

    # Route non-command messages to the chat handler (text)
    app.add_handler(MessageHandler(~filters.COMMAND, chat_with_ai))

    # Start the Bot (runs until Ctrl-C)
    app.run_polling()


if __name__ == '__main__':
    main()