"""Add user_id to processing_jobs table

Revision ID: e696d1a27c50
Revises: f6631d3cd1e3
Create Date: 2025-08-23 17:30:00.123456
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e696d1a27c50'
down_revision: Union[str, None] = 'f6631d3cd1e3'
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    # Step 1: Add the user_id column as nullable first.
    op.add_column('processing_jobs', sa.Column('user_id', sa.UUID(), nullable=True))

    # --- IMPORTANT ---
    # Replace this UUID with the one you SELECTed from your `users` table.
    default_user_uuid = 'f0fe7c3b-5618-424b-ba75-23f1af5fdee9'

    # Step 2: Backfill user_id for all existing rows.
    op.execute(
        f"UPDATE processing_jobs SET user_id = '{default_user_uuid}' WHERE user_id IS NULL"
    )

    # Step 3: Alter the column to be NOT NULL.
    op.alter_column('processing_jobs', 'user_id', nullable=False)

    # Step 4: Add index + foreign key constraint.
    op.create_index(op.f('ix_processing_jobs_user_id'), 'processing_jobs', ['user_id'], unique=False)
    op.create_foreign_key(
        'fk_processing_jobs_user_id_users',
        'processing_jobs', 'users',
        ['user_id'], ['uuid']
    )


def downgrade() -> None:
    op.drop_constraint('fk_processing_jobs_user_id_users', 'processing_jobs', type_='foreignkey')
    op.drop_index(op.f('ix_processing_jobs_user_id'), table_name='processing_jobs')
    op.drop_column('processing_jobs', 'user_id')
