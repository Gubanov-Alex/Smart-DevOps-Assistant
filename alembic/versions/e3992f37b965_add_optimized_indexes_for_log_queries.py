"""Add optimized indexes for log queries.

Revision ID: e3992f37b965
Revises: initial_20250703_104151
Create Date: 2025-07-03
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'e3992f37b965'
down_revision = 'initial_20250703_104151'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add optimized indexes for log repository operations."""
    
    # Only create the essential indexes that work reliably
    
    # 1. Composite index for time + level queries (most important)
    op.create_index(
        'idx_log_timestamp_level_comp',
        'log_entries',
        ['timestamp', 'level']
    )
    
    # 2. Source + timestamp descending for source-based queries  
    op.create_index(
        'idx_log_source_time_desc',
        'log_entries',
        ['source', sa.text('timestamp DESC')]
    )
    
    # 3. Level + timestamp for level-based filtering
    op.create_index(
        'idx_log_level_time_desc', 
        'log_entries',
        ['level', sa.text('timestamp DESC')]
    )


def downgrade() -> None:
    """Remove optimized indexes."""
    
    op.drop_index('idx_log_level_time_desc', 'log_entries')
    op.drop_index('idx_log_source_time_desc', 'log_entries') 
    op.drop_index('idx_log_timestamp_level_comp', 'log_entries')
