from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query

from app.schemas.assets import InvestmentLogCreate, InvestmentLogOut, TransactionCreate, TransactionOut
from app.services.assets_storage import cash_total as db_cash_total
from app.services.assets_storage import category_summary as db_category_summary
from app.services.assets_storage import create_investment_log as db_create_investment_log
from app.services.assets_storage import create_transaction as db_create_transaction
from app.services.assets_storage import delete_investment_log as db_delete_investment_log
from app.services.assets_storage import delete_transaction as db_delete_transaction
from app.services.assets_storage import investment_trend as db_investment_trend
from app.services.assets_storage import list_accounts as db_list_accounts
from app.services.assets_storage import list_investment_logs as db_list_investment_logs
from app.services.assets_storage import list_transactions as db_list_transactions
from app.services.assets_storage import monthly_summary as db_monthly_summary

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("/accounts")
def list_accounts() -> list[dict[str, str | bool]]:
    return db_list_accounts()


@router.get("/transactions", response_model=list[TransactionOut])
def list_transactions(
    category: str | None = Query(default=None), month: str | None = Query(default=None)
) -> list[TransactionOut]:
    rows = db_list_transactions(category=category, month=month)
    return [TransactionOut.model_validate(row) for row in rows]


@router.post("/transactions", response_model=TransactionOut)
def create_transaction(payload: TransactionCreate) -> TransactionOut:
    if payload.type not in {"income", "expense"}:
        raise HTTPException(status_code=400, detail="type must be income or expense")

    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="amount must be greater than 0")

    try:
        row = db_create_transaction(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return TransactionOut.model_validate(row)


@router.delete("/transactions/{transaction_id}")
def delete_transaction(transaction_id: int) -> dict[str, int | bool]:
    row = db_delete_transaction(transaction_id)
    if not row:
        raise HTTPException(status_code=404, detail="transaction not found")
    return row


@router.get("/cash-total")
def cash_total() -> dict[str, str]:
    return db_cash_total()


@router.get("/category-summary")
def category_summary(month: str | None = Query(default=None)) -> list[dict[str, str]]:
    return db_category_summary(month=month)


@router.get("/monthly-summary")
def monthly_summary() -> list[dict[str, str]]:
    return db_monthly_summary()


@router.get("/investment/logs", response_model=list[InvestmentLogOut])
def list_investment_logs() -> list[InvestmentLogOut]:
    rows = db_list_investment_logs()
    return [InvestmentLogOut.model_validate(row) for row in rows]


@router.post("/investment/logs", response_model=InvestmentLogOut)
def create_investment_log(payload: InvestmentLogCreate) -> InvestmentLogOut:
    row = db_create_investment_log(payload.model_dump())
    return InvestmentLogOut.model_validate(row)


@router.delete("/investment/logs/{log_id}")
def delete_investment_log(log_id: int) -> dict[str, int | bool]:
    ok = db_delete_investment_log(log_id)
    if not ok:
        raise HTTPException(status_code=404, detail="investment log not found")

    return {"deleted": True, "id": log_id}


@router.get("/investment/trend")
def investment_trend() -> list[dict[str, str]]:
    return db_investment_trend()