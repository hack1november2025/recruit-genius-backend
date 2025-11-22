"""Drop unused agent_executions table

Revision ID: 6b6c9713cb1a
Revises: 821fa5ff6a79
Create Date: 2025-11-22 10:16:08.000897+00:00

This migration removes the agent_executions table which was never used
in the application. Agent execution tracking is handled by LangGraph's
built-in checkpointer system instead.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '6b6c9713cb1a'
down_revision = '821fa5ff6a79'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Drop the unused agent_executions table and its enums.
    """
    # Drop indexes first
    op.drop_index('ix_agent_executions_thread_id', table_name='agent_executions')
    op.drop_index('ix_agent_executions_status', table_name='agent_executions')
    op.drop_index('ix_agent_executions_id', table_name='agent_executions')
    op.drop_index('ix_agent_executions_agent_type', table_name='agent_executions')
    
    # Drop table
    op.drop_table('agent_executions')
    
    # Drop enum types (PostgreSQL specific)
    op.execute('DROP TYPE IF EXISTS executionstatus')
    op.execute('DROP TYPE IF EXISTS agenttype')


def downgrade() -> None:
    """
    Recreate agent_executions table if needed for rollback.
    Note: This will not restore any data that was in the table.
    """
    # Recreate enum types
    op.execute("CREATE TYPE agenttype AS ENUM ('RESUME_ANALYZER', 'JOB_MATCHER', 'INTERVIEWER')")
    op.execute("CREATE TYPE executionstatus AS ENUM ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED')")
    
    # Recreate table
    op.create_table(
        'agent_executions',
        sa.Column('agent_type', postgresql.ENUM('RESUME_ANALYZER', 'JOB_MATCHER', 'INTERVIEWER', name='agenttype'), nullable=False),
        sa.Column('thread_id', sa.String(length=255), nullable=False),
        sa.Column('input_data', sa.JSON(), nullable=False),
        sa.Column('output_data', sa.JSON(), nullable=True),
        sa.Column('status', postgresql.ENUM('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', name='executionstatus'), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('execution_metadata', sa.JSON(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Recreate indexes
    op.create_index('ix_agent_executions_agent_type', 'agent_executions', ['agent_type'])
    op.create_index('ix_agent_executions_id', 'agent_executions', ['id'])
    op.create_index('ix_agent_executions_status', 'agent_executions', ['status'])
    op.create_index('ix_agent_executions_thread_id', 'agent_executions', ['thread_id'])
