"""Initial database schema with all models

Revision ID: initial_20250703_104151
Revises: 
Create Date: 2025-07-03T10:41:51.992379

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'initial_20250703_104151'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables and indexes."""

    # Create log_entries table
    op.create_table('log_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message', sa.Text(), nullable=False, comment='Raw log message content'),
        sa.Column('level', sa.String(length=20), nullable=False, comment='Log severity level'),
        sa.Column('source', sa.String(length=255), nullable=False, comment='Source system or service name'),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Log entry timestamp'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('extra_data', sa.JSON(), nullable=True, comment='Additional structured log extra_data'),
        sa.Column('processing_time_ms', sa.Float(), nullable=True, comment='Log processing time in milliseconds'),
        sa.Column('classification_confidence', sa.Float(), nullable=True, comment='ML classification confidence score'),
        sa.Column('anomaly_score', sa.Float(), nullable=True, comment='Anomaly detection score'),
        sa.CheckConstraint('anomaly_score >= 0 AND anomaly_score <= 1', name='check_anomaly_score_range'),
        sa.CheckConstraint('classification_confidence >= 0 AND classification_confidence <= 1', name='check_classification_confidence_range'),
        sa.PrimaryKeyConstraint('id'),
        comment='Application log entries with ML analysis results'
    )

    # Create incidents table
    op.create_table('incidents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False, comment='Incident title or summary'),
        sa.Column('description', sa.Text(), nullable=False, comment='Detailed incident description'),
        sa.Column('severity', sa.String(length=20), nullable=False, comment='Incident severity level'),
        sa.Column('status', sa.String(length=20), nullable=False, comment='Current incident status'),
        sa.Column('source', sa.String(length=255), nullable=False, comment='Source system or detector'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Incident creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Last update timestamp'),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True, comment='Incident resolution timestamp'),
        sa.Column('assigned_to', sa.String(length=255), nullable=True, comment='Assigned team or person'),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True, comment='Incident tags for categorization'),
        sa.Column('extra_data', sa.JSON(), nullable=True, comment='Additional incident metadata'),
        sa.Column('resolution_time_minutes', sa.Integer(), nullable=True, comment='Time to resolution in minutes'),
        sa.Column('priority_score', sa.Float(), nullable=True, comment='AI-calculated priority score'),
        sa.CheckConstraint('priority_score >= 0 AND priority_score <= 1', name='check_priority_score_range'),
        sa.PrimaryKeyConstraint('id'),
        comment='System incidents and issues tracking'
    )

    # Create ml_models table
    op.create_table('ml_models',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False, comment='Model name identifier'),
        sa.Column('version', sa.String(length=50), nullable=False, comment='Model version string'),
        sa.Column('model_type', sa.String(length=100), nullable=False, comment='Type of ML model'),
        sa.Column('status', sa.String(length=20), nullable=False, comment='Current model status'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Model creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Last update timestamp'),
        sa.Column('trained_at', sa.DateTime(timezone=True), nullable=True, comment='Training completion timestamp'),
        sa.Column('deployed_at', sa.DateTime(timezone=True), nullable=True, comment='Deployment timestamp'),
        sa.Column('accuracy', sa.Float(), nullable=True, comment='Model accuracy score'),
        sa.Column('precision', sa.Float(), nullable=True, comment='Model precision score'),
        sa.Column('recall', sa.Float(), nullable=True, comment='Model recall score'),
        sa.Column('f1_score', sa.Float(), nullable=True, comment='Model F1 score'),
        sa.Column('training_dataset_size', sa.Integer(), nullable=True, comment='Size of training dataset'),
        sa.Column('training_duration_minutes', sa.Integer(), nullable=True, comment='Training time in minutes'),
        sa.Column('model_path', sa.String(length=500), nullable=True, comment='File system path to model'),
        sa.Column('config', sa.JSON(), nullable=True, comment='Model configuration parameters'),
        sa.Column('extra_data', sa.JSON(), nullable=True, comment='Additional model metadata'),
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Whether model is currently active'),
        sa.Column('deployment_config', sa.JSON(), nullable=True, comment='Deployment configuration'),
        sa.CheckConstraint('accuracy >= 0 AND accuracy <= 1', name='check_accuracy_range'),
        sa.CheckConstraint('f1_score >= 0 AND f1_score <= 1', name='check_f1_score_range'),
        sa.CheckConstraint('precision >= 0 AND precision <= 1', name='check_precision_range'),
        sa.CheckConstraint('recall >= 0 AND recall <= 1', name='check_recall_range'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'version', name='uq_model_name_version'),
        comment='ML model registry with performance tracking'
    )

    # Create incident_logs association table
    op.create_table('incident_logs',
        sa.Column('incident_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('log_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), comment='Association creation timestamp'),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ),
        sa.ForeignKeyConstraint(['log_id'], ['log_entries.id'], ),
        sa.PrimaryKeyConstraint('incident_id', 'log_id'),
        comment='Association between incidents and related log entries'
    )

    # Create indexes for log_entries
    op.create_index('idx_log_created_at', 'log_entries', ['created_at'])
    op.create_index('idx_log_source_timestamp', 'log_entries', ['source', 'timestamp'])
    op.create_index('idx_log_timestamp_level', 'log_entries', ['timestamp', 'level'])
    op.create_index(op.f('ix_log_entries_level'), 'log_entries', ['level'])
    op.create_index(op.f('ix_log_entries_source'), 'log_entries', ['source'])
    op.create_index(op.f('ix_log_entries_timestamp'), 'log_entries', ['timestamp'])

    # Create indexes for incidents
    op.create_index('idx_incident_assigned_to', 'incidents', ['assigned_to'])
    op.create_index('idx_incident_created_at', 'incidents', ['created_at'])
    op.create_index('idx_incident_status_severity', 'incidents', ['status', 'severity'])
    op.create_index(op.f('ix_incidents_assigned_to'), 'incidents', ['assigned_to'])
    op.create_index(op.f('ix_incidents_created_at'), 'incidents', ['created_at'])
    op.create_index(op.f('ix_incidents_severity'), 'incidents', ['severity'])
    op.create_index(op.f('ix_incidents_source'), 'incidents', ['source'])
    op.create_index(op.f('ix_incidents_status'), 'incidents', ['status'])

    # Create indexes for ml_models
    op.create_index('idx_model_created_at', 'ml_models', ['created_at'])
    op.create_index('idx_model_is_active', 'ml_models', ['is_active'])
    op.create_index('idx_model_type_status', 'ml_models', ['model_type', 'status'])
    op.create_index(op.f('ix_ml_models_is_active'), 'ml_models', ['is_active'])
    op.create_index(op.f('ix_ml_models_model_type'), 'ml_models', ['model_type'])
    op.create_index(op.f('ix_ml_models_name'), 'ml_models', ['name'])
    op.create_index(op.f('ix_ml_models_status'), 'ml_models', ['status'])

    # Create indexes for incident_logs
    op.create_index('idx_incident_logs_incident', 'incident_logs', ['incident_id'])
    op.create_index('idx_incident_logs_log', 'incident_logs', ['log_id'])


def downgrade() -> None:
    """Drop all tables and indexes."""

    # Drop indexes
    op.drop_index('idx_incident_logs_log', table_name='incident_logs')
    op.drop_index('idx_incident_logs_incident', table_name='incident_logs')
    op.drop_index(op.f('ix_ml_models_status'), table_name='ml_models')
    op.drop_index(op.f('ix_ml_models_name'), table_name='ml_models')
    op.drop_index(op.f('ix_ml_models_model_type'), table_name='ml_models')
    op.drop_index(op.f('ix_ml_models_is_active'), table_name='ml_models')
    op.drop_index('idx_model_type_status', table_name='ml_models')
    op.drop_index('idx_model_is_active', table_name='ml_models')
    op.drop_index('idx_model_created_at', table_name='ml_models')
    op.drop_index(op.f('ix_incidents_status'), table_name='incidents')
    op.drop_index(op.f('ix_incidents_source'), table_name='incidents')
    op.drop_index(op.f('ix_incidents_severity'), table_name='incidents')
    op.drop_index(op.f('ix_incidents_created_at'), table_name='incidents')
    op.drop_index(op.f('ix_incidents_assigned_to'), table_name='incidents')
    op.drop_index('idx_incident_status_severity', table_name='incidents')
    op.drop_index('idx_incident_created_at', table_name='incidents')
    op.drop_index('idx_incident_assigned_to', table_name='incidents')
    op.drop_index(op.f('ix_log_entries_timestamp'), table_name='log_entries')
    op.drop_index(op.f('ix_log_entries_source'), table_name='log_entries')
    op.drop_index(op.f('ix_log_entries_level'), table_name='log_entries')
    op.drop_index('idx_log_timestamp_level', table_name='log_entries')
    op.drop_index('idx_log_source_timestamp', table_name='log_entries')
    op.drop_index('idx_log_created_at', table_name='log_entries')

    # Drop tables
    op.drop_table('incident_logs')
    op.drop_table('ml_models')
    op.drop_table('incidents')
    op.drop_table('log_entries')
