"""add keyword fields and google trends cache

Revision ID: 001_add_keyword_fields
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = "001_add_keyword_fields"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add new fields to keywords table (nullable first)
    op.add_column(
        "keywords", sa.Column("keyword_type", sa.String(length=20), nullable=True)
    )
    op.add_column("keywords", sa.Column("first_seen", sa.Date(), nullable=True))
    op.add_column("keywords", sa.Column("last_seen", sa.Date(), nullable=True))

    # Set default keyword_type for existing rows
    op.execute(
        "UPDATE keywords SET keyword_type = 'keyword' WHERE keyword_type IS NULL"
    )

    # Make keyword_type NOT NULL after setting defaults
    # Portable approach: use batch_alter_table for SQLite compatibility
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        # SQLite: Use batch_alter_table which handles table recreation
        with op.batch_alter_table("keywords", schema=None) as batch_op:
            batch_op.alter_column("keyword_type", nullable=False)
    else:
        # PostgreSQL: Direct ALTER
        op.alter_column(
            "keywords", "keyword_type", nullable=False, server_default="keyword"
        )

    # Create indexes
    op.create_index("ix_keywords_keyword_type", "keywords", ["keyword_type"])
    op.create_index("ix_keywords_first_seen", "keywords", ["first_seen"])
    op.create_index("ix_keywords_last_seen", "keywords", ["last_seen"])

    # Create google_trends_cache table
    op.create_table(
        "google_trends_cache",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("keyword_id", sa.Integer(), nullable=False),
        sa.Column("geo", sa.String(length=10), nullable=False),
        sa.Column("timeframe", sa.String(length=50), nullable=False),
        sa.Column("time_series_data", sa.JSON(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["keyword_id"],
            ["keywords.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "keyword_id", "geo", "timeframe", name="uq_keyword_geo_timeframe"
        ),
    )

    # Create indexes for google_trends_cache
    op.create_index(
        "ix_google_trends_cache_keyword_id", "google_trends_cache", ["keyword_id"]
    )
    op.create_index(
        "ix_google_trends_cache_fetched_at", "google_trends_cache", ["fetched_at"]
    )
    op.create_index(
        "idx_keyword_fetched", "google_trends_cache", ["keyword_id", "fetched_at"]
    )


def downgrade():
    # Drop google_trends_cache table
    op.drop_index("idx_keyword_fetched", table_name="google_trends_cache")
    op.drop_index("ix_google_trends_cache_fetched_at", table_name="google_trends_cache")
    op.drop_index("ix_google_trends_cache_keyword_id", table_name="google_trends_cache")
    op.drop_table("google_trends_cache")

    # Drop indexes from keywords
    op.drop_index("ix_keywords_last_seen", table_name="keywords")
    op.drop_index("ix_keywords_first_seen", table_name="keywords")
    op.drop_index("ix_keywords_keyword_type", table_name="keywords")

    # Drop columns from keywords
    op.drop_column("keywords", "last_seen")
    op.drop_column("keywords", "first_seen")
    op.drop_column("keywords", "keyword_type")
