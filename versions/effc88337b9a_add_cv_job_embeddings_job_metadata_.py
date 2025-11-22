"""add cv job_embeddings job_metadata refactor cv_relations

Revision ID: effc88337b9a
Revises: 4165a975d65b
Create Date: 2025-11-21 23:23:04.006906+00:00

"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision = 'effc88337b9a'
down_revision = '4165a975d65b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create CVs table
    op.create_table(
        'cvs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('candidate_id', sa.Integer(), nullable=False),
        sa.Column('original_text', sa.Text(), nullable=False),
        sa.Column('translated_text', sa.Text(), nullable=True),
        sa.Column('original_language', sa.String(10), nullable=True),
        sa.Column('file_name', sa.String(255), nullable=True),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('extracted_name', sa.String(255), nullable=True),
        sa.Column('extracted_email', sa.String(255), nullable=True),
        sa.Column('extracted_phone', sa.String(50), nullable=True),
        sa.Column('structured_metadata', sa.JSON(), nullable=True),
        sa.Column('is_processed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_translated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cvs_id'), 'cvs', ['id'], unique=False)
    op.create_index(op.f('ix_cvs_candidate_id'), 'cvs', ['candidate_id'], unique=False)
    
    # Create job_embeddings table
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
    op.create_index(op.f('ix_job_embeddings_id'), 'job_embeddings', ['id'], unique=False)
    op.create_index(op.f('ix_job_embeddings_job_id'), 'job_embeddings', ['job_id'], unique=False)
    
    # Create job_metadata table
    op.create_table(
        'job_metadata',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('required_skills', sa.JSON(), nullable=True),
        sa.Column('preferred_skills', sa.JSON(), nullable=True),
        sa.Column('min_experience_years', sa.Integer(), nullable=True),
        sa.Column('max_experience_years', sa.Integer(), nullable=True),
        sa.Column('required_education', sa.String(100), nullable=True),
        sa.Column('preferred_education', sa.String(100), nullable=True),
        sa.Column('remote_type', sa.String(50), nullable=True),
        sa.Column('locations', sa.JSON(), nullable=True),
        sa.Column('seniority_level', sa.String(50), nullable=True),
        sa.Column('role_type', sa.String(50), nullable=True),
        sa.Column('min_salary', sa.Float(), nullable=True),
        sa.Column('max_salary', sa.Float(), nullable=True),
        sa.Column('currency', sa.String(10), nullable=True),
        sa.Column('required_certifications', sa.JSON(), nullable=True),
        sa.Column('preferred_certifications', sa.JSON(), nullable=True),
        sa.Column('responsibilities', sa.JSON(), nullable=True),
        sa.Column('benefits', sa.JSON(), nullable=True),
        sa.Column('tech_stack', sa.JSON(), nullable=True),
        sa.Column('full_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_id', name='unique_job_metadata')
    )
    op.create_index(op.f('ix_job_metadata_id'), 'job_metadata', ['id'], unique=False)
    op.create_index(op.f('ix_job_metadata_job_id'), 'job_metadata', ['job_id'], unique=False)
    
    # Drop and recreate cv_embeddings with cv_id instead of candidate_id
    op.drop_table('cv_embeddings')
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
    op.create_index(op.f('ix_cv_embeddings_id'), 'cv_embeddings', ['id'], unique=False)
    op.create_index(op.f('ix_cv_embeddings_cv_id'), 'cv_embeddings', ['cv_id'], unique=False)
    
    # Drop and recreate cv_metrics with cv_id instead of candidate_id
    op.drop_table('cv_metrics')
    op.create_table(
        'cv_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cv_id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=True),
        sa.Column('skills_match_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('experience_relevance_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('education_fit_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('achievement_impact_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('keyword_density_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('employment_gap_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('readability_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('ai_confidence_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('composite_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('metric_details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['cv_id'], ['cvs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cv_id', 'job_id', name='unique_cv_job_metrics')
    )
    op.create_index(op.f('ix_cv_metrics_id'), 'cv_metrics', ['id'], unique=False)
    op.create_index(op.f('ix_cv_metrics_cv_id'), 'cv_metrics', ['cv_id'], unique=False)
    op.create_index(op.f('ix_cv_metrics_job_id'), 'cv_metrics', ['job_id'], unique=False)


def downgrade() -> None:
    # Drop new tables
    op.drop_table('cv_metrics')
    op.drop_table('cv_embeddings')
    op.drop_table('job_metadata')
    op.drop_table('job_embeddings')
    op.drop_table('cvs')
    
    # Recreate old cv_embeddings table with candidate_id
    op.create_table(
        'cv_embeddings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('candidate_id', sa.Integer(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('chunk_text', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(1536), nullable=False),
        sa.Column('embedding_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cv_embeddings_candidate_id'), 'cv_embeddings', ['candidate_id'], unique=False)
    op.create_index(op.f('ix_cv_embeddings_id'), 'cv_embeddings', ['id'], unique=False)
    
    # Recreate old cv_metrics table with candidate_id
    op.create_table(
        'cv_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('candidate_id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=True),
        sa.Column('skills_match_score', sa.Float(), nullable=False),
        sa.Column('experience_relevance_score', sa.Float(), nullable=False),
        sa.Column('education_fit_score', sa.Float(), nullable=False),
        sa.Column('achievement_impact_score', sa.Float(), nullable=False),
        sa.Column('keyword_density_score', sa.Float(), nullable=False),
        sa.Column('employment_gap_score', sa.Float(), nullable=False),
        sa.Column('readability_score', sa.Float(), nullable=False),
        sa.Column('ai_confidence_score', sa.Float(), nullable=False),
        sa.Column('composite_score', sa.Float(), nullable=False),
        sa.Column('metric_details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('candidate_id', 'job_id', name='unique_candidate_job_metrics')
    )
    op.create_index(op.f('ix_cv_metrics_candidate_id'), 'cv_metrics', ['candidate_id'], unique=False)
    op.create_index(op.f('ix_cv_metrics_id'), 'cv_metrics', ['id'], unique=False)
    op.create_index(op.f('ix_cv_metrics_job_id'), 'cv_metrics', ['job_id'], unique=False)
