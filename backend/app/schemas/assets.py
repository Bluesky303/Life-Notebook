from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class TransactionCreate(BaseModel):
    account: str
    type: str
    category: str
    amount: Decimal
    happened_on: date
    note: str | None = None


class TransactionOut(TransactionCreate):
    id: int


class InvestmentLogCreate(BaseModel):
    happened_on: date
    invested: Decimal
    daily_profit: Decimal
    note: str | None = None


class InvestmentLogOut(InvestmentLogCreate):
    id: int
