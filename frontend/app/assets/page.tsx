"use client";

import { useEffect, useMemo, useState } from "react";

import { TopNav } from "@/components/TopNav";
import {
  createAssetTransaction,
  createInvestmentLog,
  deleteAssetTransaction,
  deleteInvestmentLog,
  getAssetAccounts,
  getAssetTransactions,
  getCategorySummary,
  getInvestmentLogs,
  getInvestmentTrend,
  getMonthlySummary,
  type AssetAccount,
  type AssetTransaction,
  type CategorySummary,
  type InvestmentLog,
  type InvestmentTrendPoint,
  type MonthlySummary
} from "@/lib/api";

function parseNumber(value: string): number {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

export default function AssetsPage() {
  const [accounts, setAccounts] = useState<AssetAccount[]>([]);
  const [transactions, setTransactions] = useState<AssetTransaction[]>([]);
  const [categorySummary, setCategorySummary] = useState<CategorySummary[]>([]);
  const [monthlySummary, setMonthlySummary] = useState<MonthlySummary[]>([]);
  const [investmentLogs, setInvestmentLogs] = useState<InvestmentLog[]>([]);
  const [investmentTrend, setInvestmentTrend] = useState<InvestmentTrendPoint[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [formAccount, setFormAccount] = useState("微信钱包");
  const [formType, setFormType] = useState<"income" | "expense">("expense");
  const [formCategory, setFormCategory] = useState("吃饭");
  const [formAmount, setFormAmount] = useState("0");
  const [formDate, setFormDate] = useState("");
  const [formNote, setFormNote] = useState("");

  const [filterMonth, setFilterMonth] = useState("");
  const [filterCategory, setFilterCategory] = useState("");

  const [investDate, setInvestDate] = useState("");
  const [invested, setInvested] = useState("0");
  const [dailyProfit, setDailyProfit] = useState("0");
  const [investNote, setInvestNote] = useState("");

  const loadAll = async () => {
    setLoading(true);
    setError("");
    try {
      const [acc, tx, cat, month, iLogs, iTrend] = await Promise.all([
        getAssetAccounts(),
        getAssetTransactions({ month: filterMonth || undefined, category: filterCategory || undefined }),
        getCategorySummary(filterMonth || undefined),
        getMonthlySummary(),
        getInvestmentLogs(),
        getInvestmentTrend()
      ]);
      setAccounts(acc);
      setTransactions(tx);
      setCategorySummary(cat);
      setMonthlySummary(month);
      setInvestmentLogs(iLogs);
      setInvestmentTrend(iTrend);
      if (!formDate) {
        setFormDate(new Date().toISOString().slice(0, 10));
      }
      if (!investDate) {
        setInvestDate(new Date().toISOString().slice(0, 10));
      }
      if (!formAccount && acc.length > 0) {
        setFormAccount(acc[0].name);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "读取资产数据失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadAll();
  }, [filterMonth, filterCategory]);

  const cashTotal = useMemo(() => {
    return accounts.filter((item) => item.is_cash).reduce((sum, item) => sum + parseNumber(item.balance), 0);
  }, [accounts]);

  const monthIncome = useMemo(() => {
    return categorySummary.reduce((sum, row) => sum + parseNumber(row.income), 0);
  }, [categorySummary]);

  const monthExpense = useMemo(() => {
    return categorySummary.reduce((sum, row) => sum + parseNumber(row.expense), 0);
  }, [categorySummary]);

  const handleCreateTransaction = async () => {
    try {
      await createAssetTransaction({
        account: formAccount,
        type: formType,
        category: formCategory,
        amount: formAmount,
        happened_on: formDate,
        note: formNote
      });
      setFormNote("");
      await loadAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "新增流水失败");
    }
  };

  const handleCreateInvestment = async () => {
    try {
      await createInvestmentLog({
        happened_on: investDate,
        invested,
        daily_profit: dailyProfit,
        note: investNote
      });
      setInvestNote("");
      await loadAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "新增理财记录失败");
    }
  };

  const handleDeleteTransaction = async (transactionId: number) => {
    if (!window.confirm("确认删除这条流水吗？删除后会回滚账户余额。")) {
      return;
    }

    try {
      await deleteAssetTransaction(transactionId);
      await loadAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "删除流水失败");
    }
  };

  const handleDeleteInvestment = async (logId: number) => {
    if (!window.confirm("确认删除这条理财记录吗？此操作不可撤销。")) {
      return;
    }

    try {
      await deleteInvestmentLog(logId);
      await loadAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "删除理财记录失败");
    }
  };

  return (
    <main className="page-shell">
      <TopNav />
      <section className="panel placeholder-page">
        <h1>财产记录</h1>
        <p>流水录入、分类统计、月度收支、理财收益趋势。</p>

        <div className="asset-overview">
          <article className="feed-item">
            <div className="feed-meta">现金总资产</div>
            <div className="wealth-value">¥ {cashTotal.toFixed(2)}</div>
          </article>
          <article className="feed-item">
            <div className="feed-meta">本月收入</div>
            <div className="wealth-value">¥ {monthIncome.toFixed(2)}</div>
          </article>
          <article className="feed-item">
            <div className="feed-meta">本月支出</div>
            <div className="wealth-value">¥ {monthExpense.toFixed(2)}</div>
          </article>
        </div>

        <div className="task-form">
          <h3>新增流水</h3>
          <div className="task-form-row">
            <label>
              账户
              <select className="quick-input" value={formAccount} onChange={(e) => setFormAccount(e.target.value)}>
                {accounts.map((account) => (
                  <option key={account.name} value={account.name}>
                    {account.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              类型
              <select className="quick-input" value={formType} onChange={(e) => setFormType(e.target.value as "income" | "expense")}>
                <option value="expense">支出</option>
                <option value="income">收入</option>
              </select>
            </label>
            <label>
              分类
              <input className="quick-input" value={formCategory} onChange={(e) => setFormCategory(e.target.value)} />
            </label>
          </div>

          <div className="task-form-row">
            <label>
              金额
              <input className="quick-input" value={formAmount} onChange={(e) => setFormAmount(e.target.value)} />
            </label>
            <label>
              日期
              <input className="quick-input" type="date" value={formDate} onChange={(e) => setFormDate(e.target.value)} />
            </label>
            <label>
              备注
              <input className="quick-input" value={formNote} onChange={(e) => setFormNote(e.target.value)} />
            </label>
          </div>
          <button className="pill" type="button" onClick={() => void handleCreateTransaction()}>
            新增流水
          </button>
        </div>

        <div className="task-form">
          <h3>筛选</h3>
          <div className="task-form-row">
            <label>
              月份
              <input className="quick-input" value={filterMonth} onChange={(e) => setFilterMonth(e.target.value)} placeholder="2026-02" />
            </label>
            <label>
              分类
              <input className="quick-input" value={filterCategory} onChange={(e) => setFilterCategory(e.target.value)} placeholder="吃饭" />
            </label>
            <label>
              操作
              <button className="pill" type="button" onClick={() => { setFilterMonth(""); setFilterCategory(""); }}>
                清空筛选
              </button>
            </label>
          </div>
        </div>

        <div className="feed-list">
          <h3>账户余额</h3>
          <div className="asset-accounts">
            {accounts.map((item) => (
              <article className="feed-item" key={item.name}>
                <div className="feed-meta">{item.is_cash ? "现金账户" : "投资账户"}</div>
                <div>{item.name}</div>
                <div>¥ {item.balance}</div>
              </article>
            ))}
          </div>

          <h3>分类收支</h3>
          <div className="asset-bars">
            {categorySummary.map((row) => {
              const total = parseNumber(row.income) + parseNumber(row.expense);
              const expenseRatio = total > 0 ? (parseNumber(row.expense) / total) * 100 : 0;
              return (
                <article className="feed-item" key={row.category}>
                  <div className="feed-meta">{row.category}</div>
                  <div>收入 ¥{row.income} / 支出 ¥{row.expense}</div>
                  <div className="bar-track">
                    <div className="bar-expense" style={{ width: `${expenseRatio}%` }} />
                  </div>
                </article>
              );
            })}
          </div>

          <h3>月度收支趋势</h3>
          <div className="asset-bars">
            {monthlySummary.map((row) => {
              const income = parseNumber(row.income);
              const expense = parseNumber(row.expense);
              const max = Math.max(income, expense, 1);
              return (
                <article className="feed-item" key={row.month}>
                  <div className="feed-meta">{row.month}</div>
                  <div className="bar-track">
                    <div className="bar-income" style={{ width: `${(income / max) * 100}%` }} />
                  </div>
                  <div className="bar-track">
                    <div className="bar-expense" style={{ width: `${(expense / max) * 100}%` }} />
                  </div>
                  <div className="feed-meta">收入 ¥{row.income} / 支出 ¥{row.expense}</div>
                </article>
              );
            })}
          </div>

          <h3>理财收益记录</h3>
          <div className="task-form-row">
            <label>
              日期
              <input className="quick-input" type="date" value={investDate} onChange={(e) => setInvestDate(e.target.value)} />
            </label>
            <label>
              投入资产
              <input className="quick-input" value={invested} onChange={(e) => setInvested(e.target.value)} />
            </label>
            <label>
              当日收益
              <input className="quick-input" value={dailyProfit} onChange={(e) => setDailyProfit(e.target.value)} />
            </label>
          </div>
          <input className="quick-input" placeholder="备注" value={investNote} onChange={(e) => setInvestNote(e.target.value)} />
          <button className="pill" type="button" onClick={() => void handleCreateInvestment()}>
            新增理财收益
          </button>

          <div className="asset-bars">
            {investmentTrend.map((row) => (
              <article className="feed-item" key={row.date}>
                <div className="feed-meta">{row.date}</div>
                <div>投入 ¥{row.invested} / 当日收益 ¥{row.daily_profit}</div>
                <div>累计收益 ¥{row.acc_profit}</div>
              </article>
            ))}
          </div>

          <h3>理财记录明细</h3>
          <div className="asset-bars">
            {investmentLogs.map((row) => (
              <article className="feed-item" key={row.id}>
                <div className="feed-meta">{row.happened_on}</div>
                <div>投入 ¥{row.invested} / 当日收益 ¥{row.daily_profit}</div>
                <div className="feed-meta">{row.note ?? "-"}</div>
                <button className="pill danger" type="button" onClick={() => void handleDeleteInvestment(row.id)}>
                  删除
                </button>
              </article>
            ))}
          </div>

          <h3>最近流水</h3>
          {loading ? <article className="feed-item">加载中...</article> : null}
          {error ? <article className="feed-item">{error}</article> : null}
          {!loading && transactions.length === 0 ? <article className="feed-item">暂无流水</article> : null}
          {transactions.map((item) => (
            <article className="feed-item" key={item.id}>
              <div className="feed-meta">
                {item.happened_on} · {item.account} · {item.type === "income" ? "收入" : "支出"}
              </div>
              <div>
                {item.category} · ¥{item.amount}
              </div>
              <div className="feed-meta">{item.note ?? "-"}</div>
              <button className="pill danger" type="button" onClick={() => void handleDeleteTransaction(item.id)}>
                删除
              </button>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
