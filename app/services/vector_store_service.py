"""LangChain-based vector store service for RAG operations."""
from typing import List
from langchain_core.documents import Document
from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
from app.core.config import get_settings
from app.core.logging import rag_logger


class VectorStoreService:
    """
    LangChain-based vector store service for semantic search.
    
    Uses LangChain's native PGVector implementation with standard schema:
    - langchain_pg_collection: Document collections
    - langchain_pg_embedding: Embeddings with metadata
    """
    
    def __init__(self):
        """Initialize vector store with OpenAI embeddings."""
        settings = get_settings()
        
        # Initialize OpenAI embeddings
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=settings.openai_api_key
        )
        
        # Use plain postgresql:// connection string for langchain-postgres
        # Remove SQLAlchemy dialect prefix (postgresql+asyncpg://)
        self.connection_string = settings.database_url.replace(
            "postgresql+asyncpg://",
            "postgresql://"
        )
        
        # Collection name for all documents (CVs and jobs)
        # Note: Keep name as cv_documents for backward compatibility
        self.collection_name = "cv_documents"
        
        rag_logger.info("VectorStoreService initialized with LangChain PGVector")
    
    def get_vector_store(self) -> PGVector:
        """
        Get configured PGVector store instance using LangChain's native schema.
        
        Returns:
            Configured PGVector instance
        """
        try:
            vector_store = PGVector(
                embeddings=self.embeddings,
                collection_name=self.collection_name,
                connection=self.connection_string,
                use_jsonb=True,
            )
            
            rag_logger.debug("Created PGVector instance")
            return vector_store
            
        except Exception as e:
            rag_logger.error(f"Error creating vector store: {str(e)}")
            raise
    
    async def similarity_search(
        self,
        query: str,
        k: int = 10,
        filter_dict: dict = None
    ) -> List[Document]:
        """
        Perform similarity search using LangChain's vector store.
        
        Args:
            query: Search query text
            k: Number of results to return
            filter_dict: Optional metadata filters
            
        Returns:
            List of Document objects with page_content and metadata
        """
        try:
            vector_store = self.get_vector_store()
            
            # Use sync method in async context (runs in executor)
            # PGVector is initialized with sync connection, so we must use sync methods
            import asyncio
            if filter_dict:
                documents = await asyncio.to_thread(
                    vector_store.similarity_search,
                    query,
                    k=k,
                    filter=filter_dict
                )
            else:
                documents = await asyncio.to_thread(
                    vector_store.similarity_search,
                    query,
                    k=k
                )
            
            rag_logger.info(f"Found {len(documents)} documents for query: {query[:100]}")
            return documents
            
        except Exception as e:
            rag_logger.error(f"Error in similarity search: {str(e)}")
            raise
    
    async def similarity_search_with_score(
        self,
        query: str,
        k: int = 10,
        filter_dict: dict = None
    ) -> List[tuple[Document, float]]:
        """
        Perform similarity search with relevance scores.
        
        Args:
            query: Search query text
            k: Number of results to return
            filter_dict: Optional metadata filters
            
        Returns:
            List of tuples (Document, similarity_score)
        """
        try:
            vector_store = self.get_vector_store()
            
            # Use sync method in async context (runs in executor)
            # PGVector is initialized with sync connection, so we must use sync methods
            import asyncio
            if filter_dict:
                results = await asyncio.to_thread(
                    vector_store.similarity_search_with_score,
                    query,
                    k=k,
                    filter=filter_dict
                )
            else:
                results = await asyncio.to_thread(
                    vector_store.similarity_search_with_score,
                    query,
                    k=k
                )
            
            rag_logger.info(
                f"Found {len(results)} documents with scores for query: {query[:100]}"
            )
            return results
            
        except Exception as e:
            rag_logger.error(f"Error in similarity search with score: {str(e)}")
            raise
    
    def as_retriever(self, search_kwargs: dict = None):
        """
        Get a LangChain Retriever instance.
        
        Args:
            search_kwargs: Arguments for retriever (k, filter, etc.)
            
        Returns:
            Configured Retriever instance
        """
        vector_store = self.get_vector_store()
        
        if search_kwargs is None:
            search_kwargs = {"k": 10}
        
        retriever = vector_store.as_retriever(search_kwargs=search_kwargs)
        
        rag_logger.debug(f"Created retriever with kwargs: {search_kwargs}")
        return retriever
    
    async def add_documents(
        self,
        documents: List[Document]
    ) -> List[str]:
        """
        Add documents to the vector store (async wrapper for sync operation).
        LangChain will automatically generate UUIDs for document IDs.
        Custom IDs should be stored in document metadata.
        
        Args:
            documents: List of Document objects to add
            
        Returns:
            List of generated document IDs (UUIDs)
        """
        try:
            vector_store = self.get_vector_store()
            
            # add_documents is synchronous in PGVector - run in thread pool
            # Don't pass ids parameter - let LangChain generate UUIDs
            import asyncio
            document_ids = await asyncio.to_thread(
                vector_store.add_documents,
                documents
            )
            
            rag_logger.info(f"Added {len(documents)} documents to vector store")
            return document_ids
            
        except Exception as e:
            rag_logger.error(f"Error adding documents: {str(e)}")
            raise


# Singleton instance
_vector_store_service = None


def get_vector_store_service() -> VectorStoreService:
    """Get or create singleton VectorStoreService instance."""
    global _vector_store_service
    if _vector_store_service is None:
        _vector_store_service = VectorStoreService()
    return _vector_store_service
