"""initial migration with pgvector

Revision ID: 001
Revises:
Create Date: 2025-01-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Create wardrobe table
    op.create_table(
        'wardrobe',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('image_path', sa.Text(), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('color_primary', sa.String(30)),
        sa.Column('color_secondary', sa.String(30)),
        sa.Column('pattern', sa.String(50)),
        sa.Column('material', sa.String(100)),
        sa.Column('brand', sa.String(100)),
        sa.Column('purchase_date', sa.Date()),
        sa.Column('last_worn', sa.Date()),
        sa.Column('wear_count', sa.Integer(), server_default='0'),
        sa.Column('season_tags', postgresql.ARRAY(sa.Text())),
        sa.Column('style_tags', postgresql.ARRAY(sa.Text())),
        sa.Column('care_instructions', sa.Text()),
    )

    # Add vector column separately
    op.execute('ALTER TABLE wardrobe ADD COLUMN vector_embedding vector(768)')

    # Create indexes
    op.create_index('idx_wardrobe_category', 'wardrobe', ['category'])
    op.create_index('idx_wardrobe_color_primary', 'wardrobe', ['color_primary'])

    # Create outfits table
    op.create_table(
        'outfits',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.Date(), nullable=False),
        sa.Column('worn_date', sa.Date()),
        sa.Column('item_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True))),
        sa.Column('weather_temp', sa.Float()),
        sa.Column('weather_condition', sa.String(50)),
        sa.Column('occasion', sa.String(100)),
        sa.Column('user_rating', sa.Integer()),
        sa.Column('notes', sa.Text()),
    )

    # Create weather_cache table
    op.create_table(
        'weather_cache',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('date', sa.Date(), nullable=False, unique=True),
        sa.Column('temperature', sa.Float()),
        sa.Column('condition', sa.String(50)),
        sa.Column('humidity', sa.Integer()),
        sa.Column('wind_speed', sa.Float()),
        sa.Column('raw_data', sa.Text()),
    )

    op.create_index('idx_weather_cache_date', 'weather_cache', ['date'])


def downgrade() -> None:
    op.drop_index('idx_weather_cache_date')
    op.drop_table('weather_cache')
    op.drop_table('outfits')
    op.drop_index('idx_wardrobe_color_primary')
    op.drop_index('idx_wardrobe_category')
    op.drop_table('wardrobe')
    op.execute('DROP EXTENSION IF EXISTS vector')
