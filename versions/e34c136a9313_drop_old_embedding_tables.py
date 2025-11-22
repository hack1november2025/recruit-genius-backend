"""Drop old embedding tables

Revision ID: 003_drop_old_embeddings
Revises: 002_langchain_vector
Create Date: 2025-11-22 04:30:00.000000

This migration removes the old cv_embeddings and job_embeddings tables
as we've migrated to LangChain's native vector store schema
(langchain_pg_embedding and langchain_pg_collection).

The data has been migrated to the new tables, so these are safe to drop.
"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision = 'e34c136a9313'
down_revision = 'b012abfb93ba'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Drop old embedding tables that are no longer used.
    
    We've migrated to LangChain's native PGVector schema, so these
    custom embedding tables are no longer needed:
    - cv_embeddings: Replaced by langchain_pg_embedding
    - job_embeddings: Replaced by langchain_pg_embedding
    """
    
    # Drop old embedding tables
    op.drop_table('cv_embeddings')
    op.drop_table('job_embeddings')


def downgrade() -> None:
    """
    Recreate old embedding tables if needed.
    
    Note: This will recreate the structure but not the data.
    If you need to rollback, ensure you have a backup of the data.
    """
    
    # Recreate cv_embeddings table
    op.create_table(
        'cv_embeddings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cv_id', sa.Integer(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('chunk_text', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(1536), nullable=False),
        sa.Column('embedding_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['cv_id'], ['cvs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('ix_cv_embeddings_cv_id', 'cv_embeddings', ['cv_id'])
    
    # Create HNSW index for vector similarity search
    op.execute(
        """
        CREATE INDEX ix_cv_embeddings_vector 
        ON cv_embeddings 
        USING hnsw (embedding vector_cosine_ops)
        """
    )
    
    # Recreate job_embeddings table
    op.create_table(
        'job_embeddings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('chunk_text', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(1536), nullable=False),
        sa.Column('embedding_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('ix_job_embeddings_job_id', 'job_embeddings', ['job_id'])
    
    # Create HNSW index for vector similarity search
    op.execute(
        """
        CREATE INDEX ix_job_embeddings_vector 
        ON job_embeddings 
        USING hnsw (embedding vector_cosine_ops)
        """
    )
