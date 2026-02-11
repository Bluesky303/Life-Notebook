"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { getCashTotal } from "@/lib/api";

export function WealthCard() {
  const [cashTotal, setCashTotal] = useState("--");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await getCashTotal();
        setCashTotal(`${data.currency === "CNY" ? "¥" : ""} ${data.cash_total}`);
      } catch {
        setCashTotal("读取失败");
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, []);

  return (
    <section className="panel wealth-panel">
      <p className="panel-title">现金总资产</p>
      <p className="wealth-value">{loading ? "加载中..." : cashTotal}</p>
      <p className="wealth-note">仅统计标记为现金的钱包/账户</p>
      <Link className="entry-link" href="/assets">
        进入资产管理
      </Link>
    </section>
  );
}
