"""initial schema: postgis + spots

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-01

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute(
        """
        CREATE TABLE spots (
          id              SERIAL PRIMARY KEY,
          name            TEXT NOT NULL,
          category        TEXT NOT NULL,
          address         TEXT,
          geom            GEOGRAPHY(POINT, 4326) NOT NULL,
          elevation_m     INTEGER,
          radiance        DOUBLE PRECISION,
          darkness_score  SMALLINT,
          bortle          SMALLINT,
          kma_nx          SMALLINT NOT NULL,
          kma_ny          SMALLINT NOT NULL,
          created_at      TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX idx_spots_geom ON spots USING GIST (geom)")
    op.execute("CREATE INDEX idx_spots_kma ON spots (kma_nx, kma_ny)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS spots")
