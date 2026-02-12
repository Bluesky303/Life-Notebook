"use client";

import { useEffect, useMemo, useState } from "react";

import { TopNav } from "@/components/TopNav";
import { createTask, deleteTask, getTasks, updateTask, type TaskItem } from "@/lib/api";

type Importance = "high" | "medium" | "low";
type TaskType = "task" | "sleep";
type TaskStatus = "todo" | "in_progress" | "done" | "skipped";

type TaskDraft = {
  title: string;
  category: string;
  type: TaskType;
  status: TaskStatus;
  importance: Importance;
  plannedStartAt: string;
  plannedEndAt: string;
  actualStartAt: string;
  actualEndAt: string;
  note: string;
};

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

function statusLabel(value: string): string {
  if (value === "in_progress") return "进行中";
  if (value === "done") return "已完成";
  if (value === "skipped") return "已跳过";
  return "待处理";
}

function toDraft(task: TaskItem): TaskDraft {
  return {
    title: task.title,
    category: task.category,
    type: task.type === "sleep" ? "sleep" : "task",
    status:
      task.status === "in_progress" || task.status === "done" || task.status === "skipped"
        ? task.status
        : "todo",
    importance: task.importance === "high" || task.importance === "medium" ? task.importance : "low",
    plannedStartAt: toInputDateTime(task.planned_start_at),
    plannedEndAt: toInputDateTime(task.planned_end_at),
    actualStartAt: toInputDateTime(task.actual_start_at),
    actualEndAt: toInputDateTime(task.actual_end_at),
    note: task.note ?? ""
  };
}

export default function TasksPage() {
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [savingId, setSavingId] = useState<number | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [error, setError] = useState("");

  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("日常");
  const [taskType, setTaskType] = useState<TaskType>("task");
  const [importance, setImportance] = useState<Importance>("medium");
  const [plannedStartAt, setPlannedStartAt] = useState("");
  const [plannedEndAt, setPlannedEndAt] = useState("");
  const [note, setNote] = useState("");
  const [editDraft, setEditDraft] = useState<TaskDraft | null>(null);

  const canSubmit = useMemo(() => {
    return title.trim().length > 0 && category.trim().length > 0 && !submitting;
  }, [title, category, submitting]);

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
        type: taskType,
        importance,
        status: "todo",
        planned_start_at: plannedStartAt ? toApiDateTime(plannedStartAt) : null,
        planned_end_at: plannedEndAt ? toApiDateTime(plannedEndAt) : null,
        note: note.trim() || null
      });
      setTitle("");
      setCategory(taskType === "sleep" ? "睡眠" : "日常");
      setImportance("medium");
      setPlannedStartAt("");
      setPlannedEndAt("");
      setNote("");
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

  const handleToggleDone = async (task: TaskItem) => {
    const nextDone = task.status !== "done";
    const now = new Date().toISOString();

    try {
      setSavingId(task.id);
      await updateTask(task.id, {
        status: nextDone ? "done" : "todo",
        completed_at: nextDone ? now : null,
        actual_end_at: nextDone ? task.actual_end_at ?? now : task.actual_end_at
      });
      await loadTasks();
    } catch (err) {
      setError(err instanceof Error ? err.message : "更新任务状态失败");
    } finally {
      setSavingId(null);
    }
  };

  const startEdit = (task: TaskItem) => {
    setEditingId(task.id);
    setEditDraft(toDraft(task));
    setError("");
  };

  const handleSaveEdit = async (taskId: number) => {
    if (!editDraft) {
      return;
    }

    try {
      setSavingId(taskId);
      await updateTask(taskId, {
        title: editDraft.title.trim(),
        category: editDraft.category.trim(),
        type: editDraft.type,
        status: editDraft.status,
        importance: editDraft.importance,
        planned_start_at: editDraft.plannedStartAt ? toApiDateTime(editDraft.plannedStartAt) : null,
        planned_end_at: editDraft.plannedEndAt ? toApiDateTime(editDraft.plannedEndAt) : null,
        actual_start_at: editDraft.actualStartAt ? toApiDateTime(editDraft.actualStartAt) : null,
        actual_end_at: editDraft.actualEndAt ? toApiDateTime(editDraft.actualEndAt) : null,
        note: editDraft.note.trim() || null,
        completed_at: editDraft.status === "done" ? new Date().toISOString() : null
      });
      setEditingId(null);
      setEditDraft(null);
      await loadTasks();
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存任务失败");
    } finally {
      setSavingId(null);
    }
  };

  return (
    <main className="page-shell">
      <TopNav />
      <section className="panel placeholder-page">
        <h1>任务栏</h1>
        <p>任务统一支持计划时间、实际时间、完成标记和随时编辑。睡眠也作为任务管理。</p>

        <div className="task-form">
          <input className="quick-input" placeholder="任务标题" value={title} onChange={(e) => setTitle(e.target.value)} />
          <div className="task-form-row">
            <label>
              类型
              <select
                className="quick-input"
                value={taskType}
                onChange={(e) => {
                  const value = e.target.value as TaskType;
                  setTaskType(value);
                  if (value === "sleep") {
                    setCategory("睡眠");
                    if (!title.trim()) {
                      setTitle("睡眠");
                    }
                  }
                }}
              >
                <option value="task">普通任务</option>
                <option value="sleep">睡眠</option>
              </select>
            </label>
            <label>
              分类
              <input className="quick-input" value={category} onChange={(e) => setCategory(e.target.value)} />
            </label>
            <label>
              重要性
              <select className="quick-input" value={importance} onChange={(e) => setImportance(e.target.value as Importance)}>
                <option value="high">高</option>
                <option value="medium">中</option>
                <option value="low">低</option>
              </select>
            </label>
          </div>
          <div className="task-form-row">
            <label>
              计划开始
              <input className="quick-input" type="datetime-local" value={plannedStartAt} onChange={(e) => setPlannedStartAt(e.target.value)} />
            </label>
            <label>
              计划结束
              <input className="quick-input" type="datetime-local" value={plannedEndAt} onChange={(e) => setPlannedEndAt(e.target.value)} />
            </label>
            <label>
              备注
              <input className="quick-input" value={note} onChange={(e) => setNote(e.target.value)} />
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
          {tasks.map((task) => {
            const isEditing = editingId === task.id && !!editDraft;
            return (
              <article className="feed-item" key={task.id}>
                {!isEditing ? (
                  <>
                    <div className="feed-meta">
                      {task.type === "sleep" ? "睡眠" : task.category} · 重要性 {importanceLabel(task.importance)} · 状态 {statusLabel(task.status)}
                    </div>
                    <div>{task.title}</div>
                    <div className="feed-meta">
                      计划: {toInputDateTime(task.planned_start_at) || "--"} - {toInputDateTime(task.planned_end_at) || "--"}
                    </div>
                    <div className="feed-meta">
                      实际: {toInputDateTime(task.actual_start_at) || "--"} - {toInputDateTime(task.actual_end_at) || "--"}
                    </div>
                    <div className="feed-meta">完成时间: {toInputDateTime(task.completed_at) || "--"}</div>
                    {task.note ? <div>{task.note}</div> : null}
                    <div className="task-actions">
                      <button className="pill" type="button" disabled={savingId === task.id} onClick={() => void handleToggleDone(task)}>
                        {task.status === "done" ? "撤销完成" : "标记完成"}
                      </button>
                      <button className="pill" type="button" disabled={savingId === task.id} onClick={() => startEdit(task)}>
                        编辑
                      </button>
                      <button className="pill danger" type="button" disabled={savingId === task.id} onClick={() => void handleDelete(task.id)}>
                        删除
                      </button>
                    </div>
                  </>
                ) : (
                  <div className="task-edit">
                    <div className="task-form-row">
                      <label>
                        标题
                        <input
                          className="quick-input"
                          value={editDraft.title}
                          onChange={(e) => setEditDraft({ ...editDraft, title: e.target.value })}
                        />
                      </label>
                      <label>
                        分类
                        <input
                          className="quick-input"
                          value={editDraft.category}
                          onChange={(e) => setEditDraft({ ...editDraft, category: e.target.value })}
                        />
                      </label>
                      <label>
                        类型
                        <select
                          className="quick-input"
                          value={editDraft.type}
                          onChange={(e) => setEditDraft({ ...editDraft, type: e.target.value as TaskType })}
                        >
                          <option value="task">普通任务</option>
                          <option value="sleep">睡眠</option>
                        </select>
                      </label>
                    </div>
                    <div className="task-form-row">
                      <label>
                        状态
                        <select
                          className="quick-input"
                          value={editDraft.status}
                          onChange={(e) => setEditDraft({ ...editDraft, status: e.target.value as TaskStatus })}
                        >
                          <option value="todo">待处理</option>
                          <option value="in_progress">进行中</option>
                          <option value="done">已完成</option>
                          <option value="skipped">已跳过</option>
                        </select>
                      </label>
                      <label>
                        重要性
                        <select
                          className="quick-input"
                          value={editDraft.importance}
                          onChange={(e) => setEditDraft({ ...editDraft, importance: e.target.value as Importance })}
                        >
                          <option value="high">高</option>
                          <option value="medium">中</option>
                          <option value="low">低</option>
                        </select>
                      </label>
                      <label>
                        备注
                        <input
                          className="quick-input"
                          value={editDraft.note}
                          onChange={(e) => setEditDraft({ ...editDraft, note: e.target.value })}
                        />
                      </label>
                    </div>
                    <div className="task-form-row">
                      <label>
                        计划开始
                        <input
                          className="quick-input"
                          type="datetime-local"
                          value={editDraft.plannedStartAt}
                          onChange={(e) => setEditDraft({ ...editDraft, plannedStartAt: e.target.value })}
                        />
                      </label>
                      <label>
                        计划结束
                        <input
                          className="quick-input"
                          type="datetime-local"
                          value={editDraft.plannedEndAt}
                          onChange={(e) => setEditDraft({ ...editDraft, plannedEndAt: e.target.value })}
                        />
                      </label>
                      <label>
                        实际开始
                        <input
                          className="quick-input"
                          type="datetime-local"
                          value={editDraft.actualStartAt}
                          onChange={(e) => setEditDraft({ ...editDraft, actualStartAt: e.target.value })}
                        />
                      </label>
                    </div>
                    <div className="task-form-row">
                      <label>
                        实际结束
                        <input
                          className="quick-input"
                          type="datetime-local"
                          value={editDraft.actualEndAt}
                          onChange={(e) => setEditDraft({ ...editDraft, actualEndAt: e.target.value })}
                        />
                      </label>
                    </div>
                    <div className="task-actions">
                      <button className="pill" type="button" disabled={savingId === task.id} onClick={() => void handleSaveEdit(task.id)}>
                        保存
                      </button>
                      <button
                        className="pill"
                        type="button"
                        disabled={savingId === task.id}
                        onClick={() => {
                          setEditingId(null);
                          setEditDraft(null);
                        }}
                      >
                        取消
                      </button>
                    </div>
                  </div>
                )}
              </article>
            );
          })}
        </div>
      </section>
    </main>
  );
}
