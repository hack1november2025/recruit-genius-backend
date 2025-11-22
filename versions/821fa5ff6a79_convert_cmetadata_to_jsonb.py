"""convert_cmetadata_to_jsonb

Revision ID: 821fa5ff6a79
Revises: e34c136a9313
Create Date: 2025-11-22 09:30:10.320492+00:00

Convert JSON columns to JSONB in LangChain tables for proper filter support.
LangChain's PGVector requires JSONB for jsonb_path_match operations.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = '821fa5ff6a79'
down_revision = 'e34c136a9313'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Convert JSON columns to JSONB for LangChain compatibility."""
    
    # Convert langchain_pg_collection.cmetadata from JSON to JSONB
    op.execute("""
        ALTER TABLE langchain_pg_collection 
        ALTER COLUMN cmetadata TYPE JSONB USING cmetadata::TEXT::JSONB
    """)
    
    # Convert langchain_pg_embedding.cmetadata from JSON to JSONB
    op.execute("""
        ALTER TABLE langchain_pg_embedding 
        ALTER COLUMN cmetadata TYPE JSONB USING cmetadata::TEXT::JSONB
    """)


def downgrade() -> None:
    """Convert JSONB columns back to JSON."""
    
    op.execute("""
        ALTER TABLE langchain_pg_collection 
        ALTER COLUMN cmetadata TYPE JSON USING cmetadata::TEXT::JSON
    """)
    
    op.execute("""
        ALTER TABLE langchain_pg_embedding 
        ALTER COLUMN cmetadata TYPE JSON USING cmetadata::TEXT::JSON
    """)
