"use client";

import { useEffect, useMemo, useState } from "react";

import { createKnowledgeEntry, deleteKnowledgeEntry, getKnowledgeEntries, type KnowledgeEntry } from "@/lib/api";
import { markdownToHtml } from "@/lib/markdown";

type Kind = "blog" | "entry";

function formatTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
}

export function KnowledgeWorkspace({ kind, title, description }: { kind: Kind; title: string; description: string }) {
  const [entries, setEntries] = useState<KnowledgeEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [query, setQuery] = useState("");
  const [entryTitle, setEntryTitle] = useState("");
  const [markdown, setMarkdown] = useState(
    kind === "entry"
      ? "## 新词条\n- 定义\n- 关键参数\n- 应用场景"
      : "## 问题背景\n描述现象\n\n## 排查过程\n1. 观察日志\n2. 缩小范围\n\n## 结论\n给出解决方案"
  );
  const [submitting, setSubmitting] = useState(false);

  const previewHtml = useMemo(() => markdownToHtml(markdown), [markdown]);

  const loadEntries = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await getKnowledgeEntries({ kind, q: query || undefined });
      setEntries(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "读取失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadEntries();
  }, [kind, query]);

  const handleCreate = async () => {
    if (!entryTitle.trim() || !markdown.trim()) {
      setError("标题和内容不能为空");
      return;
    }

    setSubmitting(true);
    setError("");
    try {
      await createKnowledgeEntry({
        kind,
        title: entryTitle.trim(),
        markdown
      });
      setEntryTitle("");
      await loadEntries();
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建失败");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (entryId: number) => {
    if (!window.confirm("确认删除这个条目吗？此操作不可撤销。")) {
      return;
    }
    try {
      await deleteKnowledgeEntry(entryId);
      await loadEntries();
    } catch (err) {
      setError(err instanceof Error ? err.message : "删除失败");
    }
  };

  return (
    <section className="panel placeholder-page">
      <h1>{title}</h1>
      <p>{description}</p>

      <div className="task-form-row">
        <label>
          搜索
          <input className="quick-input" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="搜索标题或内容" />
        </label>
        <label>
          新条目标题
          <input className="quick-input" value={entryTitle} onChange={(e) => setEntryTitle(e.target.value)} placeholder="输入标题" />
        </label>
        <label>
          操作
          <button className="pill" type="button" onClick={() => void handleCreate()} disabled={submitting}>
            {submitting ? "提交中..." : "新增条目"}
          </button>
        </label>
      </div>

      <div className="task-form">
        <textarea className="knowledge-editor" value={markdown} onChange={(e) => setMarkdown(e.target.value)} />
        <article className="feed-item">
          <div className="feed-meta">Markdown 预览</div>
          <div className="markdown-render" dangerouslySetInnerHTML={{ __html: previewHtml }} />
        </article>
      </div>

      <div className="feed-list">
        <h3>最近条目</h3>
        {loading ? <article className="feed-item">加载中...</article> : null}
        {error ? <article className="feed-item">{error}</article> : null}
        {!loading && entries.length === 0 ? <article className="feed-item">暂无条目</article> : null}
        {entries.map((entry) => (
          <article className="feed-item" key={entry.id}>
            <div className="feed-meta">{formatTime(entry.updated_at)}</div>
            <div>{entry.title}</div>
            <div className="markdown-render" dangerouslySetInnerHTML={{ __html: markdownToHtml(entry.markdown) }} />
            <button className="pill danger" type="button" onClick={() => void handleDelete(entry.id)}>
              删除
            </button>
          </article>
        ))}
      </div>
    </section>
  );
}
