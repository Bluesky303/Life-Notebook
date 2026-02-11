"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { getKnowledgeEntryById, type KnowledgeEntry } from "@/lib/api";
import { markdownToHtml } from "@/lib/markdown";

function formatTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
}

export function KnowledgeDetail({ entryId, expectedKind }: { entryId: number; expectedKind: "blog" | "entry" }) {
  const [entry, setEntry] = useState<KnowledgeEntry | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError("");
      try {
        const data = await getKnowledgeEntryById(entryId);
        if (data.kind !== expectedKind) {
          setError(`该条目不是${expectedKind === "entry" ? "词条" : "博客"}类型`);
          setEntry(null);
        } else {
          setEntry(data);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "读取详情失败");
        setEntry(null);
      } finally {
        setLoading(false);
      }
    };

    if (!Number.isFinite(entryId) || entryId <= 0) {
      setError("无效的条目 ID");
      setLoading(false);
      return;
    }

    void load();
  }, [entryId, expectedKind]);

  const html = useMemo(() => markdownToHtml(entry?.markdown ?? ""), [entry?.markdown]);

  if (loading) {
    return <section className="panel placeholder-page">加载中...</section>;
  }

  if (error || !entry) {
    return (
      <section className="panel placeholder-page">
        <p>{error || "未找到条目"}</p>
        <Link className="entry-link" href={expectedKind === "entry" ? "/knowledge/entry" : "/knowledge/blog"}>
          返回列表
        </Link>
      </section>
    );
  }

  return (
    <section className="panel placeholder-page">
      <div className="feed-meta">
        {entry.kind === "entry" ? "词条" : "博客"} · {formatTime(entry.updated_at)}
      </div>
      <h1>{entry.title}</h1>
      <div className="markdown-render" dangerouslySetInnerHTML={{ __html: html }} />
      <Link className="entry-link" href={expectedKind === "entry" ? "/knowledge/entry" : "/knowledge/blog"}>
        返回列表
      </Link>
    </section>
  );
}
