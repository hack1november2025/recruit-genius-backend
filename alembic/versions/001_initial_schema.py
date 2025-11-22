"""Initial database schema

Revision ID: 001_initial
Revises: 
Create Date: 2025-11-22 00:00:00.000000

This is a baseline migration for existing databases.
All core tables are already created.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Initial schema - this is a baseline migration.
    
    If running on a fresh database, this will create all tables.
    If running on an existing database, this will be stamped as completed.
    """
    # Check if tables already exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    # Only create tables if they don't exist
    if 'candidates' not in existing_tables:
        # Create candidates table
        op.create_table(
            'candidates',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('phone', sa.String(length=50), nullable=True),
            sa.Column('resume_text', sa.Text(), nullable=True),
            sa.Column('resume_url', sa.String(length=500), nullable=True),
            sa.Column('skills', postgresql.JSON(astext_type=sa.Text()), nullable=False),
            sa.Column('experience_years', sa.String(length=50), nullable=True),
            sa.Column('education', sa.Text(), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=False),
            sa.Column('analysis', postgresql.JSON(astext_type=sa.Text()), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_candidates_email'), 'candidates', ['email'], unique=True)
        op.create_index(op.f('ix_candidates_id'), 'candidates', ['id'], unique=False)
        op.create_index(op.f('ix_candidates_name'), 'candidates', ['name'], unique=False)
        op.create_index(op.f('ix_candidates_status'), 'candidates', ['status'], unique=False)

    if 'jobs' not in existing_tables:
        # Create jobs table
        op.create_table(
            'jobs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('department', sa.String(length=100), nullable=True),
            sa.Column('location', sa.String(length=255), nullable=True),
            sa.Column('salary_range', sa.String(length=100), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=False),
            sa.Column('additional_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_jobs_department'), 'jobs', ['department'], unique=False)
        op.create_index(op.f('ix_jobs_id'), 'jobs', ['id'], unique=False)
        op.create_index(op.f('ix_jobs_status'), 'jobs', ['status'], unique=False)
        op.create_index(op.f('ix_jobs_title'), 'jobs', ['title'], unique=False)

    if 'matches' not in existing_tables:
        # Create matches table
        op.create_table(
            'matches',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('candidate_id', sa.Integer(), nullable=False),
            sa.Column('job_id', sa.Integer(), nullable=False),
            sa.Column('match_score', sa.Float(), nullable=False),
            sa.Column('reasoning', sa.Text(), nullable=True),
            sa.Column('matching_skills', postgresql.JSON(astext_type=sa.Text()), nullable=False),
            sa.Column('missing_skills', postgresql.JSON(astext_type=sa.Text()), nullable=False),
            sa.Column('ai_insights', postgresql.JSON(astext_type=sa.Text()), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ),
            sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_matches_candidate_id'), 'matches', ['candidate_id'], unique=False)
        op.create_index(op.f('ix_matches_id'), 'matches', ['id'], unique=False)
        op.create_index(op.f('ix_matches_job_id'), 'matches', ['job_id'], unique=False)

    if 'cvs' not in existing_tables:
        # Create CVs table
        op.create_table(
            'cvs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('candidate_id', sa.Integer(), nullable=False),
            sa.Column('original_text', sa.Text(), nullable=False),
            sa.Column('translated_text', sa.Text(), nullable=True),
            sa.Column('original_language', sa.String(length=10), nullable=True),
            sa.Column('file_name', sa.String(length=255), nullable=True),
            sa.Column('file_path', sa.String(length=500), nullable=True),
            sa.Column('file_size_bytes', sa.Integer(), nullable=True),
            sa.Column('extracted_name', sa.String(length=255), nullable=True),
            sa.Column('extracted_email', sa.String(length=255), nullable=True),
            sa.Column('extracted_phone', sa.String(length=50), nullable=True),
            sa.Column('structured_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
            sa.Column('is_processed', sa.Boolean(), default=False, nullable=False),
            sa.Column('is_translated', sa.Boolean(), default=False, nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_cvs_candidate_id'), 'cvs', ['candidate_id'], unique=False)
        op.create_index(op.f('ix_cvs_id'), 'cvs', ['id'], unique=False)

    if 'cv_metrics' not in existing_tables:
        # Create CV metrics table
        op.create_table(
            'cv_metrics',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('cv_id', sa.Integer(), nullable=False),
            sa.Column('job_id', sa.Integer(), nullable=True),
            sa.Column('skills_match_score', sa.Float(), nullable=False, default=0.0),
            sa.Column('experience_relevance_score', sa.Float(), nullable=False, default=0.0),
            sa.Column('education_fit_score', sa.Float(), nullable=False, default=0.0),
            sa.Column('achievement_impact_score', sa.Float(), nullable=False, default=0.0),
            sa.Column('keyword_density_score', sa.Float(), nullable=False, default=0.0),
            sa.Column('employment_gap_score', sa.Float(), nullable=False, default=0.0),
            sa.Column('readability_score', sa.Float(), nullable=False, default=0.0),
            sa.Column('ai_confidence_score', sa.Float(), nullable=False, default=0.0),
            sa.Column('composite_score', sa.Float(), nullable=False, default=0.0),
            sa.Column('metric_details', postgresql.JSON(astext_type=sa.Text()), default=dict),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['cv_id'], ['cvs.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('cv_id', 'job_id', name='unique_cv_job_metrics')
        )
        op.create_index(op.f('ix_cv_metrics_cv_id'), 'cv_metrics', ['cv_id'], unique=False)
        op.create_index(op.f('ix_cv_metrics_job_id'), 'cv_metrics', ['job_id'], unique=False)

    if 'job_metadata' not in existing_tables:
        # Create job metadata table
        op.create_table(
            'job_metadata',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('job_id', sa.Integer(), nullable=False),
            sa.Column('required_skills', postgresql.JSON(astext_type=sa.Text()), default=list),
            sa.Column('preferred_skills', postgresql.JSON(astext_type=sa.Text()), default=list),
            sa.Column('min_experience_years', sa.Integer(), nullable=True),
            sa.Column('max_experience_years', sa.Integer(), nullable=True),
            sa.Column('required_education', sa.String(length=100), nullable=True),
            sa.Column('preferred_education', sa.String(length=100), nullable=True),
            sa.Column('remote_type', sa.String(length=50), nullable=True),
            sa.Column('locations', postgresql.JSON(astext_type=sa.Text()), default=list),
            sa.Column('seniority_level', sa.String(length=50), nullable=True),
            sa.Column('role_type', sa.String(length=50), nullable=True),
            sa.Column('min_salary', sa.Float(), nullable=True),
            sa.Column('max_salary', sa.Float(), nullable=True),
            sa.Column('currency', sa.String(length=10), default='USD'),
            sa.Column('required_certifications', postgresql.JSON(astext_type=sa.Text()), default=list),
            sa.Column('preferred_certifications', postgresql.JSON(astext_type=sa.Text()), default=list),
            sa.Column('responsibilities', postgresql.JSON(astext_type=sa.Text()), default=list),
            sa.Column('benefits', postgresql.JSON(astext_type=sa.Text()), default=list),
            sa.Column('tech_stack', postgresql.JSON(astext_type=sa.Text()), default=list),
            sa.Column('full_metadata', postgresql.JSON(astext_type=sa.Text()), default=dict),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('job_id', name='unique_job_metadata')
        )
        op.create_index(op.f('ix_job_metadata_job_id'), 'job_metadata', ['job_id'], unique=False)

    if 'langchain_pg_collection' not in existing_tables:
        # Create LangChain collection table
        op.create_table(
            'langchain_pg_collection',
            sa.Column('uuid', sa.UUID(), nullable=False),
            sa.Column('name', sa.String(), nullable=True),
            sa.Column('cmetadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.PrimaryKeyConstraint('uuid')
        )

    if 'langchain_pg_embedding' not in existing_tables:
        # Create LangChain embedding table
        op.create_table(
            'langchain_pg_embedding',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('collection_id', sa.UUID(), nullable=True),
            sa.Column('embedding', Vector(1536), nullable=True),
            sa.Column('document', sa.String(), nullable=True),
            sa.Column('cmetadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('custom_id', sa.String(), nullable=True),
            sa.ForeignKeyConstraint(['collection_id'], ['langchain_pg_collection.uuid'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_langchain_pg_embedding_collection_id'), 'langchain_pg_embedding', ['collection_id'])
        op.create_index(op.f('ix_langchain_pg_embedding_custom_id'), 'langchain_pg_embedding', ['custom_id'])
        
        # Create HNSW vector index
        op.execute(
            """
            CREATE INDEX ix_langchain_pg_embedding_vector 
            ON langchain_pg_embedding 
            USING hnsw (embedding vector_cosine_ops)
            """
        )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('langchain_pg_embedding')
    op.drop_table('langchain_pg_collection')
    op.drop_table('job_metadata')
    op.drop_table('cv_metrics')
    op.drop_table('cvs')
    op.drop_table('matches')
    op.drop_table('jobs')
    op.drop_table('candidates')
