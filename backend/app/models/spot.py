"""spots 테이블 SQLAlchemy 모델. DDL(§4)과 1:1 대응."""

from __future__ import annotations

from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import Integer, SmallInteger, String, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TIMESTAMP, Double

from app.db import Base


class Spot(Base):
    __tablename__ = "spots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[str | None] = mapped_column(String, nullable=True)
    geom: Mapped[str] = mapped_column(
        Geography(geometry_type="POINT", srid=4326), nullable=False
    )
    elevation_m: Mapped[int | None] = mapped_column(Integer, nullable=True)
    radiance: Mapped[float | None] = mapped_column(Double, nullable=True)
    darkness_score: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    bortle: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    kma_nx: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    kma_ny: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )
