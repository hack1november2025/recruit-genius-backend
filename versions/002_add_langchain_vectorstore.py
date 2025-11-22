"""Add LangChain PGVector tables for RAG

Revision ID: 002_langchain_vector
Revises: effc88337b9a
Create Date: 2025-11-22 00:00:00.000000

This migration creates the standard LangChain PGVector table structure
for storing CV embeddings following LangChain's native schema pattern.
"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision = 'b012abfb93ba'
down_revision = 'effc88337b9a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create LangChain-compatible vector store tables.
    
    This follows the standard LangChain PGVector schema:
    - langchain_pg_collection: Collections of documents
    - langchain_pg_embedding: Document embeddings with metadata
    """
    
    # Create collection table
    op.create_table(
        'langchain_pg_collection',
        sa.Column('uuid', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('cmetadata', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('uuid')
    )
    
    # Create embedding table with vector column
    op.create_table(
        'langchain_pg_embedding',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('collection_id', sa.UUID(), nullable=True),
        sa.Column('embedding', Vector(1536), nullable=True),  # OpenAI text-embedding-3-small dimension
        sa.Column('document', sa.String(), nullable=True),
        sa.Column('cmetadata', sa.JSON(), nullable=True),
        sa.Column('custom_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['collection_id'], ['langchain_pg_collection.uuid'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index(
        'ix_langchain_pg_embedding_collection_id',
        'langchain_pg_embedding',
        ['collection_id']
    )
    
    # Create custom_id index for looking up by CV ID
    op.create_index(
        'ix_langchain_pg_embedding_custom_id',
        'langchain_pg_embedding',
        ['custom_id']
    )
    
    # Create vector index using HNSW for fast similarity search
    # This is critical for performance on large datasets
    op.execute(
        """
        CREATE INDEX ix_langchain_pg_embedding_vector 
        ON langchain_pg_embedding 
        USING hnsw (embedding vector_cosine_ops)
        """
    )


def downgrade() -> None:
    """Remove LangChain vector store tables."""
    op.drop_table('langchain_pg_embedding')
    op.drop_table('langchain_pg_collection')
