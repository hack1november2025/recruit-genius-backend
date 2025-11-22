"""Translation service for converting CV text to English."""
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.config import get_settings
from app.core.logging import llm_logger
from app.core.langfuse_config import get_langfuse_callbacks
from langdetect import detect, LangDetectException


class TranslationService:
    """Service for translating CV text to English."""
    
    def __init__(self):
        settings = get_settings()
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=0.3,
            openai_api_key=settings.openai_api_key
        )
    
    def detect_language(self, text: str) -> str:
        """
        Detect language of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            ISO 639-1 language code (e.g., "en", "es", "fr")
        """
        try:
            lang = detect(text)
            llm_logger.debug(f"Detected language: {lang}")
            return lang
        except LangDetectException as e:
            llm_logger.warning(f"Could not detect language: {e}")
            return "unknown"
    
    async def translate_to_english(self, text: str, source_lang: str | None = None) -> dict:
        """
        Translate CV text to English.
        
        Args:
            text: CV text to translate
            source_lang: Source language code (auto-detected if not provided)
            
        Returns:
            Dictionary with translated_text and detected_language
        """
        # Detect language if not provided
        if not source_lang:
            source_lang = self.detect_language(text)
        
        # Skip translation if already in English
        if source_lang == "en":
            llm_logger.info("Text is already in English, skipping translation")
            return {
                "translated_text": text,
                "original_language": "en",
                "was_translated": False
            }
        
        # Translate using LLM
        llm_logger.info(f"Translating CV from {source_lang} to English")
        
        system_prompt = """You are a professional translator specializing in CV/résumé translation.
Translate the following CV text to English while:
1. Preserving all technical terms, job titles, and company names
2. Maintaining the original structure and formatting
3. Keeping dates, numbers, and proper nouns intact
4. Ensuring professional tone and clarity

Provide ONLY the translated text, without any additional commentary."""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Translate this CV to English:\n\n{text}")
        ]
        
        try:
            # Get Langfuse callbacks for LLM tracking
            callbacks = get_langfuse_callbacks(
                trace_name="cv_translation",
                tags=["translation", "cv_parser"],
                metadata={
                    "source_language": source_lang,
                    "text_length": len(text)
                }
            )
            
            response = await self.llm.ainvoke(messages, config={"callbacks": callbacks})
            translated_text = response.content
            
            llm_logger.info(f"Successfully translated CV ({len(text)} -> {len(translated_text)} chars)")
            
            return {
                "translated_text": translated_text,
                "original_language": source_lang,
                "was_translated": True
            }
        except Exception as e:
            llm_logger.error(f"Translation failed: {str(e)}")
            return {
                "translated_text": text,
                "original_language": source_lang,
                "was_translated": False,
                "error": str(e)
            }
