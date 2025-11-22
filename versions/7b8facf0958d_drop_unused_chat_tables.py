"""Drop unused chat_sessions and chat_messages tables

Revision ID: 7b8facf0958d
Revises: 6b6c9713cb1a
Create Date: 2025-11-22 10:21:02.028595+00:00

These tables were replaced by LangGraph's built-in checkpointer system
which handles all conversation state and history automatically per thread_id.
The checkpointer stores data in: checkpoints, checkpoint_writes, checkpoint_blobs.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '7b8facf0958d'
down_revision = '6b6c9713cb1a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Drop unused chat tables.
    LangGraph's checkpointer handles conversation persistence.
    """
    # Drop chat_messages first (has foreign key to chat_sessions)
    op.drop_index('ix_chat_messages_id', table_name='chat_messages')
    op.drop_index('ix_chat_messages_session_id', table_name='chat_messages')
    op.drop_table('chat_messages')
    
    # Drop chat_sessions
    op.drop_index('ix_chat_sessions_id', table_name='chat_sessions')
    op.drop_table('chat_sessions')


def downgrade() -> None:
    """
    Recreate chat tables if needed for rollback.
    Note: This will not restore any data.
    """
    # Recreate chat_sessions
    op.create_table(
        'chat_sessions',
        sa.Column('thread_id', sa.String(length=255), nullable=False, unique=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_chat_sessions_id', 'chat_sessions', ['id'])
    
    # Recreate chat_messages
    op.create_table(
        'chat_messages',
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_chat_messages_id', 'chat_messages', ['id'])
    op.create_index('ix_chat_messages_session_id', 'chat_messages', ['session_id'])
