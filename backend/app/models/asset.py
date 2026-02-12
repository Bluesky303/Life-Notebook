from sqlalchemy import Boolean, Date, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class AssetAccountRecord(Base):
    __tablename__ = "asset_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    is_cash: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    balance: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0)


class AssetTransactionRecord(Base):
    __tablename__ = "asset_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    happened_on: Mapped[Date] = mapped_column(Date, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class AssetInvestmentLogRecord(Base):
    __tablename__ = "asset_investment_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    happened_on: Mapped[Date] = mapped_column(Date, nullable=False)
    invested: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    daily_profit: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
