from datetime import UTC, datetime
from enum import Enum as PyEnum

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ActionStatus(str, PyEnum):
    active = "active"
    ended = "ended"


class FleetAction(Base):
    __tablename__ = "fleet_action_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    fleet_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    fc_character_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    fc_character_name: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[str] = mapped_column(
        PgEnum(ActionStatus, name="fleet_action_status", create_type=False),
        default=ActionStatus.active,
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    pap_records: Mapped[list["PapRecord"]] = relationship(
        "PapRecord", back_populates="action", cascade="all, delete-orphan"
    )


class PapRecord(Base):
    __tablename__ = "fleet_action_pap_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("fleet_action_actions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    character_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    character_name: Mapped[str] = mapped_column(String(256), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    issued_by_character_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    action: Mapped["FleetAction"] = relationship("FleetAction", back_populates="pap_records")
