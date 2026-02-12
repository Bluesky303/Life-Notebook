from collections import defaultdict
from datetime import date
from decimal import Decimal

from sqlalchemy import select

from app.core.db import SessionLocal, init_db
from app.core.json_store import read_json
from app.models.asset import AssetAccountRecord, AssetInvestmentLogRecord, AssetTransactionRecord

_ASSETS_FILE = "assets.json"
_DEFAULT_STATE = {
    "accounts": [
        {"name": "微信钱包", "is_cash": True, "balance": "0.00"},
        {"name": "支付宝钱包", "is_cash": True, "balance": "0.00"},
        {"name": "支付宝理财", "is_cash": False, "balance": "0.00"},
    ],
    "transactions": [],
    "investment_logs": [],
}


def _bootstrap_if_empty() -> None:
    with SessionLocal() as db:
        has_accounts = db.execute(select(AssetAccountRecord.id).limit(1)).first() is not None
        has_tx = db.execute(select(AssetTransactionRecord.id).limit(1)).first() is not None
        has_logs = db.execute(select(AssetInvestmentLogRecord.id).limit(1)).first() is not None
        if has_accounts or has_tx or has_logs:
            return

        state = read_json(_ASSETS_FILE, _DEFAULT_STATE)
        for row in state.get("accounts", []):
            db.add(
                AssetAccountRecord(
                    name=str(row.get("name")),
                    is_cash=bool(row.get("is_cash", False)),
                    balance=Decimal(str(row.get("balance", "0"))),
                )
            )
        for row in state.get("transactions", []):
            db.add(
                AssetTransactionRecord(
                    id=int(row.get("id", 0)) or None,
                    account=str(row.get("account")),
                    type=str(row.get("type")),
                    category=str(row.get("category")),
                    amount=Decimal(str(row.get("amount", "0"))),
                    happened_on=date.fromisoformat(str(row.get("happened_on"))),
                    note=row.get("note"),
                )
            )
        for row in state.get("investment_logs", []):
            db.add(
                AssetInvestmentLogRecord(
                    id=int(row.get("id", 0)) or None,
                    happened_on=date.fromisoformat(str(row.get("happened_on"))),
                    invested=Decimal(str(row.get("invested", "0"))),
                    daily_profit=Decimal(str(row.get("daily_profit", "0"))),
                    note=row.get("note"),
                )
            )
        db.commit()


def list_accounts() -> list[dict]:
    init_db()
    _bootstrap_if_empty()
    with SessionLocal() as db:
        rows = db.execute(select(AssetAccountRecord).order_by(AssetAccountRecord.id)).scalars().all()
        return [{"name": row.name, "is_cash": row.is_cash, "balance": f"{Decimal(str(row.balance)):.2f}"} for row in rows]


def find_account(name: str) -> AssetAccountRecord | None:
    with SessionLocal() as db:
        return db.execute(select(AssetAccountRecord).where(AssetAccountRecord.name == name)).scalar_one_or_none()


def list_transactions(category: str | None = None, month: str | None = None) -> list[dict]:
    init_db()
    _bootstrap_if_empty()
    with SessionLocal() as db:
        rows = db.execute(select(AssetTransactionRecord)).scalars().all()
        result: list[dict] = []
        for row in rows:
            if category and row.category != category:
                continue
            if month and row.happened_on.strftime("%Y-%m") != month:
                continue
            result.append(
                {
                    "id": row.id,
                    "account": row.account,
                    "type": row.type,
                    "category": row.category,
                    "amount": Decimal(str(row.amount)),
                    "happened_on": row.happened_on,
                    "note": row.note,
                }
            )
        return sorted(result, key=lambda item: item["happened_on"], reverse=True)


def create_transaction(payload: dict) -> dict:
    init_db()
    _bootstrap_if_empty()
    with SessionLocal() as db:
        account = db.execute(select(AssetAccountRecord).where(AssetAccountRecord.name == payload["account"])).scalar_one_or_none()
        if not account:
            raise ValueError("account not found")

        row = AssetTransactionRecord(
            account=payload["account"],
            type=payload["type"],
            category=payload["category"],
            amount=payload["amount"],
            happened_on=payload["happened_on"],
            note=payload.get("note"),
        )
        db.add(row)
        if payload["type"] == "income":
            account.balance = Decimal(str(account.balance)) + payload["amount"]
        else:
            account.balance = Decimal(str(account.balance)) - payload["amount"]
        db.commit()
        db.refresh(row)
        return {
            "id": row.id,
            "account": row.account,
            "type": row.type,
            "category": row.category,
            "amount": Decimal(str(row.amount)),
            "happened_on": row.happened_on,
            "note": row.note,
        }


def delete_transaction(transaction_id: int) -> dict | None:
    init_db()
    with SessionLocal() as db:
        row = db.get(AssetTransactionRecord, transaction_id)
        if not row:
            return None
        account = db.execute(select(AssetAccountRecord).where(AssetAccountRecord.name == row.account)).scalar_one_or_none()
        if account:
            amount = Decimal(str(row.amount))
            if row.type == "income":
                account.balance = Decimal(str(account.balance)) - amount
            else:
                account.balance = Decimal(str(account.balance)) + amount
        db.delete(row)
        db.commit()
        return {"deleted": True, "id": transaction_id}


def cash_total() -> dict:
    init_db()
    _bootstrap_if_empty()
    with SessionLocal() as db:
        rows = db.execute(select(AssetAccountRecord).where(AssetAccountRecord.is_cash.is_(True))).scalars().all()
        total = sum([Decimal(str(row.balance)) for row in rows], Decimal("0"))
        return {"currency": "CNY", "cash_total": f"{total:.2f}"}


def category_summary(month: str | None = None) -> list[dict]:
    rows = list_transactions(month=month)
    summary: dict[str, dict[str, Decimal]] = defaultdict(lambda: {"income": Decimal("0"), "expense": Decimal("0")})
    for item in rows:
        summary[item["category"]][item["type"]] += item["amount"]
    result = []
    for category, values in summary.items():
        result.append({"category": category, "income": f"{values['income']:.2f}", "expense": f"{values['expense']:.2f}"})
    return sorted(result, key=lambda row: Decimal(row["income"]) + Decimal(row["expense"]), reverse=True)


def monthly_summary() -> list[dict]:
    rows = list_transactions()
    monthly: dict[str, dict[str, Decimal]] = defaultdict(lambda: {"income": Decimal("0"), "expense": Decimal("0")})
    for item in rows:
        key = item["happened_on"].strftime("%Y-%m")
        monthly[key][item["type"]] += item["amount"]
    result = []
    for month_key, values in monthly.items():
        result.append({"month": month_key, "income": f"{values['income']:.2f}", "expense": f"{values['expense']:.2f}"})
    return sorted(result, key=lambda row: row["month"])


def list_investment_logs() -> list[dict]:
    init_db()
    _bootstrap_if_empty()
    with SessionLocal() as db:
        rows = db.execute(select(AssetInvestmentLogRecord).order_by(AssetInvestmentLogRecord.happened_on)).scalars().all()
        return [
            {
                "id": row.id,
                "happened_on": row.happened_on,
                "invested": Decimal(str(row.invested)),
                "daily_profit": Decimal(str(row.daily_profit)),
                "note": row.note,
            }
            for row in rows
        ]


def create_investment_log(payload: dict) -> dict:
    init_db()
    with SessionLocal() as db:
        row = AssetInvestmentLogRecord(
            happened_on=payload["happened_on"],
            invested=payload["invested"],
            daily_profit=payload["daily_profit"],
            note=payload.get("note"),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return {
            "id": row.id,
            "happened_on": row.happened_on,
            "invested": Decimal(str(row.invested)),
            "daily_profit": Decimal(str(row.daily_profit)),
            "note": row.note,
        }


def delete_investment_log(log_id: int) -> bool:
    init_db()
    with SessionLocal() as db:
        row = db.get(AssetInvestmentLogRecord, log_id)
        if not row:
            return False
        db.delete(row)
        db.commit()
        return True


def investment_trend() -> list[dict]:
    logs = list_investment_logs()
    total_profit = Decimal("0")
    result = []
    for row in logs:
        total_profit += row["daily_profit"]
        result.append(
            {
                "date": row["happened_on"].isoformat(),
                "invested": f"{row['invested']:.2f}",
                "daily_profit": f"{row['daily_profit']:.2f}",
                "acc_profit": f"{total_profit:.2f}",
            }
        )
    return result
