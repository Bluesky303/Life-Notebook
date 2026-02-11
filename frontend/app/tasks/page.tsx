"use client";

import { useEffect, useMemo, useState } from "react";

import { TopNav } from "@/components/TopNav";
import { createTask, deleteTask, getTasks, type TaskItem } from "@/lib/api";

type Importance = "high" | "medium" | "low";

function toApiDateTime(value: string): string {
  return `${value}:00`;
}

function toInputDateTime(value: string | null): string {
  if (!value) return "";
  const normalized = value.replace("Z", "");
  return normalized.slice(0, 16);
}

function importanceLabel(value: string): string {
  if (value === "high") return "高";
  if (value === "medium") return "中";
  return "低";
}

export default function TasksPage() {
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("日常");
  const [importance, setImportance] = useState<Importance>("medium");
  const [startAt, setStartAt] = useState("");
  const [endAt, setEndAt] = useState("");
  const [error, setError] = useState("");

  const canSubmit = useMemo(() => {
    return title.trim().length > 0 && category.trim().length > 0 && startAt.length > 0 && endAt.length > 0 && !submitting;
  }, [title, category, startAt, endAt, submitting]);

  const loadTasks = async () => {
    setLoading(true);
    try {
      const data = await getTasks();
      setTasks(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadTasks();
  }, []);

  const handleCreate = async () => {
    if (!canSubmit) {
      return;
    }

    setError("");
    setSubmitting(true);
    try {
      await createTask({
        title: title.trim(),
        category: category.trim(),
        importance,
        start_at: toApiDateTime(startAt),
        end_at: toApiDateTime(endAt)
      });
      setTitle("");
      setCategory("日常");
      setImportance("medium");
      setStartAt("");
      setEndAt("");
      await loadTasks();
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建任务失败");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (taskId: number) => {
    if (!window.confirm("确认删除这个任务吗？此操作不可撤销。")) {
      return;
    }

    try {
      await deleteTask(taskId);
      await loadTasks();
    } catch (err) {
      setError(err instanceof Error ? err.message : "删除任务失败");
    }
  };

  return (
    <main className="page-shell">
      <TopNav />
      <section className="panel placeholder-page">
        <h1>任务栏</h1>
        <p>新增任务后会自动进入首页周时间表。</p>

        <div className="task-form">
          <input className="quick-input" placeholder="任务标题" value={title} onChange={(e) => setTitle(e.target.value)} />
          <input className="quick-input" placeholder="分类" value={category} onChange={(e) => setCategory(e.target.value)} />

          <div className="task-form-row">
            <label>
              重要性
              <select className="quick-input" value={importance} onChange={(e) => setImportance(e.target.value as Importance)}>
                <option value="high">高</option>
                <option value="medium">中</option>
                <option value="low">低</option>
              </select>
            </label>
            <label>
              开始时间
              <input className="quick-input" type="datetime-local" value={startAt} onChange={(e) => setStartAt(e.target.value)} />
            </label>
            <label>
              结束时间
              <input className="quick-input" type="datetime-local" value={endAt} onChange={(e) => setEndAt(e.target.value)} />
            </label>
          </div>

          <button className="pill" type="button" disabled={!canSubmit} onClick={() => void handleCreate()}>
            {submitting ? "创建中..." : "创建任务"}
          </button>
          {error ? <p className="wealth-note">{error}</p> : null}
        </div>

        <div className="feed-list">
          {loading ? <article className="feed-item">任务加载中...</article> : null}
          {!loading && tasks.length === 0 ? <article className="feed-item">暂无任务</article> : null}
          {tasks.map((task) => (
            <article className="feed-item" key={task.id}>
              <div className="feed-meta">
                {task.category} · 重要性 {importanceLabel(task.importance)}
              </div>
              <div>{task.title}</div>
              <div className="feed-meta">
                {toInputDateTime(task.start_at)} - {toInputDateTime(task.end_at)}
              </div>
              <button className="pill danger" type="button" onClick={() => void handleDelete(task.id)}>
                删除
              </button>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
