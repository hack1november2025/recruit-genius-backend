"""Embedding service for generating and managing vector embeddings."""
import tiktoken
from typing import List
from langchain_openai import OpenAIEmbeddings
from app.core.config import get_settings
from app.core.errors import EmbeddingGenerationError
from app.core.logging import rag_logger


class EmbeddingService:
    """Service for generating embeddings using OpenAI."""
    
    def __init__(self):
        settings = get_settings()
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=settings.openai_api_key
        )
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Split text into overlapping chunks based on token count.
        
        Args:
            text: Text to chunk
            chunk_size: Maximum tokens per chunk
            overlap: Token overlap between chunks
            
        Returns:
            List of text chunks
        """
        tokens = self.tokenizer.encode(text)
        chunks = []
        
        start = 0
        while start < len(tokens):
            end = start + chunk_size
            chunk_tokens = tokens[start:end]
            chunk_text = self.tokenizer.decode(chunk_tokens)
            chunks.append(chunk_text)
            start = end - overlap
        
        rag_logger.info(f"Chunked text into {len(chunks)} chunks")
        return chunks
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
            
        Raises:
            EmbeddingGenerationError: If embedding generation fails
        """
        try:
            embedding = await self.embeddings.aembed_query(text)
            rag_logger.debug(f"Generated embedding of dimension {len(embedding)}")
            return embedding
        except Exception as e:
            rag_logger.error(f"Failed to generate embedding: {str(e)}")
            raise EmbeddingGenerationError(f"Failed to generate embedding: {str(e)}")
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
            
        Raises:
            EmbeddingGenerationError: If embedding generation fails
        """
        try:
            embeddings = await self.embeddings.aembed_documents(texts)
            rag_logger.info(f"Generated {len(embeddings)} embeddings")
            return embeddings
        except Exception as e:
            rag_logger.error(f"Failed to generate embeddings: {str(e)}")
            raise EmbeddingGenerationError(f"Failed to generate embeddings: {str(e)}")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.tokenizer.encode(text))
