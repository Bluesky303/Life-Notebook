"use client";

import { useEffect, useMemo, useState } from "react";

import { createFeed, deleteFeed, getFeed, parseRecordWithAI, type AIParseRecordResult, type FeedItem } from "@/lib/api";

const categories = ["消费记录", "任务", "见闻", "知识", "其他"];

function formatTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  });
}

export function ActivityFeed() {
  const [content, setContent] = useState("");
  const [category, setCategory] = useState(categories[0]);
  const [feedItems, setFeedItems] = useState<FeedItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [aiSuggestion, setAiSuggestion] = useState<AIParseRecordResult | null>(null);

  const canSubmit = useMemo(() => content.trim().length > 0 && !submitting, [content, submitting]);

  useEffect(() => {
    const load = async () => {
      try {
        const items = await getFeed();
        setFeedItems(items);
      } catch {
        setFeedItems([]);
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, []);

  const handleParse = async () => {
    if (!content.trim()) return;
    setParsing(true);
    try {
      const result = await parseRecordWithAI({ text: content.trim() });
      setAiSuggestion(result);
      if (categories.includes(result.suggested_category)) {
        setCategory(result.suggested_category);
      }
      setContent(result.normalized_text);
    } finally {
      setParsing(false);
    }
  };

  const handleSubmit = async () => {
    if (!canSubmit) {
      return;
    }

    setSubmitting(true);
    try {
      const created = await createFeed({
        category,
        content: content.trim()
      });
      setFeedItems((prev) => [created, ...prev]);
      setContent("");
      setAiSuggestion(null);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (feedId: number) => {
    if (!window.confirm("确认删除这条动态吗？此操作不可撤销。")) {
      return;
    }

    try {
      await deleteFeed(feedId);
      setFeedItems((prev) => prev.filter((item) => item.id !== feedId));
    } catch {
      // Keep UI simple for now; feed will be refreshed on next load.
    }
  };

  return (
    <section className="panel activity-panel">
      <p className="panel-title">动态</p>
      <input
        className="quick-input"
        placeholder="快速记录：例如“晚餐 35 吃饭”“明晚8点复盘任务”“记录新芯片关键词”"
        value={content}
        onChange={(event) => setContent(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter") {
            event.preventDefault();
            void handleSubmit();
          }
        }}
      />
      <div className="quick-row">
        {categories.map((name) => (
          <button
            className="pill"
            type="button"
            key={name}
            onClick={() => setCategory(name)}
            aria-pressed={category === name}
          >
            {name}
          </button>
        ))}
        <button className="pill" type="button" onClick={() => void handleParse()} disabled={!content.trim() || parsing}>
          {parsing ? "AI 解析中..." : "AI 解析"}
        </button>
        <button className="pill" type="button" onClick={() => void handleSubmit()} disabled={!canSubmit}>
          {submitting ? "提交中..." : "发送到动态"}
        </button>
      </div>

      {aiSuggestion ? (
        <article className="feed-item">
          <div className="feed-meta">AI 建议</div>
          <div>类型：{aiSuggestion.detected_type}</div>
          <div>建议分类：{aiSuggestion.suggested_category}</div>
          <div>识别金额：{aiSuggestion.extracted_amount ?? "-"}</div>
          <div>识别时间：{aiSuggestion.extracted_time ?? "-"}</div>
        </article>
      ) : null}

      <div className="feed-list">
        {loading ? <article className="feed-item">加载中...</article> : null}
        {!loading && feedItems.length === 0 ? <article className="feed-item">暂无动态，先记一条吧。</article> : null}
        {feedItems.map((item) => (
          <article className="feed-item" key={`${item.id}-${item.created_at}`}>
            <div className="feed-meta">
              {formatTime(item.created_at)} · {item.category}
            </div>
            <div>{item.content}</div>
            <button className="pill danger" type="button" onClick={() => void handleDelete(item.id)}>
              删除
            </button>
          </article>
        ))}
      </div>
    </section>
  );
}
