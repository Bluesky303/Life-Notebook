from collections import defaultdict
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query

from app.core.json_store import read_json, write_json
from app.schemas.assets import InvestmentLogCreate, InvestmentLogOut, TransactionCreate, TransactionOut

router = APIRouter(prefix="/assets", tags=["assets"])

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


def _load_state() -> dict:
    return read_json(_ASSETS_FILE, _DEFAULT_STATE)


def _save_state(state: dict) -> None:
    write_json(_ASSETS_FILE, state)


def _account_map(accounts: list[dict]) -> dict[str, dict]:
    return {account["name"]: account for account in accounts}


def _load_transactions(state: dict) -> list[TransactionOut]:
    return [TransactionOut.model_validate(item) for item in state["transactions"]]


def _load_investment_logs(state: dict) -> list[InvestmentLogOut]:
    return [InvestmentLogOut.model_validate(item) for item in state["investment_logs"]]


@router.get("/accounts")
def list_accounts() -> list[dict[str, str | bool]]:
    state = _load_state()
    return state["accounts"]


@router.get("/transactions", response_model=list[TransactionOut])
def list_transactions(
    category: str | None = Query(default=None), month: str | None = Query(default=None)
) -> list[TransactionOut]:
    state = _load_state()
    data = _load_transactions(state)

    if category:
        data = [item for item in data if item.category == category]

    if month:
        data = [item for item in data if item.happened_on.strftime("%Y-%m") == month]

    return list(sorted(data, key=lambda item: item.happened_on, reverse=True))


@router.post("/transactions", response_model=TransactionOut)
def create_transaction(payload: TransactionCreate) -> TransactionOut:
    if payload.type not in {"income", "expense"}:
        raise HTTPException(status_code=400, detail="type must be income or expense")

    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="amount must be greater than 0")

    state = _load_state()
    accounts = state["accounts"]
    account = _account_map(accounts).get(payload.account)
    if not account:
        raise HTTPException(status_code=404, detail="account not found")

    transactions = _load_transactions(state)
    next_id = max([item.id for item in transactions], default=0) + 1

    transaction = TransactionOut(id=next_id, **payload.model_dump())
    transactions.append(transaction)

    balance = Decimal(account["balance"])
    balance = balance + payload.amount if payload.type == "income" else balance - payload.amount
    account["balance"] = f"{balance:.2f}"

    state["transactions"] = [item.model_dump(mode="json") for item in transactions]
    _save_state(state)
    return transaction


@router.delete("/transactions/{transaction_id}")
def delete_transaction(transaction_id: int) -> dict[str, int | bool]:
    state = _load_state()
    transactions = _load_transactions(state)

    target = next((item for item in transactions if item.id == transaction_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="transaction not found")

    account = _account_map(state["accounts"]).get(target.account)
    if account:
        balance = Decimal(account["balance"])
        amount = Decimal(target.amount)
        balance = balance - amount if target.type == "income" else balance + amount
        account["balance"] = f"{balance:.2f}"

    new_transactions = [item for item in transactions if item.id != transaction_id]
    state["transactions"] = [item.model_dump(mode="json") for item in new_transactions]
    _save_state(state)
    return {"deleted": True, "id": transaction_id}


@router.get("/cash-total")
def cash_total() -> dict[str, str]:
    state = _load_state()
    total = sum([Decimal(account["balance"]) for account in state["accounts"] if account["is_cash"]], Decimal("0"))
    return {"currency": "CNY", "cash_total": f"{total:.2f}"}


@router.get("/category-summary")
def category_summary(month: str | None = Query(default=None)) -> list[dict[str, str]]:
    state = _load_state()
    transactions = _load_transactions(state)
    summary: dict[str, dict[str, Decimal]] = defaultdict(lambda: {"income": Decimal("0"), "expense": Decimal("0")})

    for item in transactions:
        if month and item.happened_on.strftime("%Y-%m") != month:
            continue
        summary[item.category][item.type] += item.amount

    result: list[dict[str, str]] = []
    for category, values in summary.items():
        result.append(
            {
                "category": category,
                "income": f"{values['income']:.2f}",
                "expense": f"{values['expense']:.2f}",
            }
        )

    return sorted(result, key=lambda row: Decimal(row["income"]) + Decimal(row["expense"]), reverse=True)


@router.get("/monthly-summary")
def monthly_summary() -> list[dict[str, str]]:
    state = _load_state()
    transactions = _load_transactions(state)
    monthly: dict[str, dict[str, Decimal]] = defaultdict(lambda: {"income": Decimal("0"), "expense": Decimal("0")})

    for item in transactions:
        key = item.happened_on.strftime("%Y-%m")
        monthly[key][item.type] += item.amount

    result: list[dict[str, str]] = []
    for month_key, values in monthly.items():
        result.append(
            {
                "month": month_key,
                "income": f"{values['income']:.2f}",
                "expense": f"{values['expense']:.2f}",
            }
        )

    return sorted(result, key=lambda row: row["month"])


@router.get("/investment/logs", response_model=list[InvestmentLogOut])
def list_investment_logs() -> list[InvestmentLogOut]:
    state = _load_state()
    logs = _load_investment_logs(state)
    return list(sorted(logs, key=lambda row: row.happened_on))


@router.post("/investment/logs", response_model=InvestmentLogOut)
def create_investment_log(payload: InvestmentLogCreate) -> InvestmentLogOut:
    state = _load_state()
    logs = _load_investment_logs(state)
    next_id = max([item.id for item in logs], default=0) + 1

    log = InvestmentLogOut(id=next_id, **payload.model_dump())
    logs.append(log)

    state["investment_logs"] = [item.model_dump(mode="json") for item in logs]
    _save_state(state)
    return log


@router.delete("/investment/logs/{log_id}")
def delete_investment_log(log_id: int) -> dict[str, int | bool]:
    state = _load_state()
    logs = _load_investment_logs(state)

    new_logs = [item for item in logs if item.id != log_id]
    if len(new_logs) == len(logs):
        raise HTTPException(status_code=404, detail="investment log not found")

    state["investment_logs"] = [item.model_dump(mode="json") for item in new_logs]
    _save_state(state)
    return {"deleted": True, "id": log_id}


@router.get("/investment/trend")
def investment_trend() -> list[dict[str, str]]:
    state = _load_state()
    logs = _load_investment_logs(state)

    total_profit = Decimal("0")
    rows = []

    for log in sorted(logs, key=lambda row: row.happened_on):
        total_profit += log.daily_profit
        rows.append(
            {
                "date": log.happened_on.isoformat(),
                "invested": f"{log.invested:.2f}",
                "daily_profit": f"{log.daily_profit:.2f}",
                "acc_profit": f"{total_profit:.2f}",
            }
        )

    return rows
