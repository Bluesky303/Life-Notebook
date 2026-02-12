"use client";

import { useEffect, useMemo, useState } from "react";

import { TopNav } from "@/components/TopNav";
import { createTask, deleteTask, getTasks, updateTask, type TaskItem } from "@/lib/api";

type Importance = "high" | "medium" | "low";
type TaskType = "task" | "sleep";
type TaskStatus = "todo" | "in_progress" | "done" | "skipped";
type RecurrenceFreq = "daily" | "weekly" | "monthly" | "yearly";

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
  if (value === "high") return "high";
  if (value === "medium") return "medium";
  return "low";
}

function statusLabel(value: string): string {
  if (value === "in_progress") return "in progress";
  if (value === "done") return "done";
  if (value === "skipped") return "skipped";
  return "todo";
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
  const [category, setCategory] = useState("general");
  const [taskType, setTaskType] = useState<TaskType>("task");
  const [importance, setImportance] = useState<Importance>("medium");
  const [plannedStartAt, setPlannedStartAt] = useState("");
  const [plannedEndAt, setPlannedEndAt] = useState("");
  const [note, setNote] = useState("");

  const [isRecurring, setIsRecurring] = useState(false);
  const [recurrenceFreq, setRecurrenceFreq] = useState<RecurrenceFreq>("weekly");
  const [recurrenceInterval, setRecurrenceInterval] = useState("1");
  const [recurrenceWeekdays, setRecurrenceWeekdays] = useState<number[]>([1, 2, 3, 4, 5]);
  const [recurrenceUntil, setRecurrenceUntil] = useState("");

  const [editDraft, setEditDraft] = useState<TaskDraft | null>(null);

  const canSubmit = useMemo(() => {
    if (submitting) return false;
    if (title.trim().length === 0 || category.trim().length === 0) return false;
    if (isRecurring && (!plannedStartAt || !plannedEndAt)) return false;
    return true;
  }, [title, category, submitting, isRecurring, plannedStartAt, plannedEndAt]);

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
    if (!canSubmit) return;

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
        note: note.trim() || null,
        is_recurring_template: isRecurring,
        recurrence: isRecurring
          ? {
              freq: recurrenceFreq,
              interval: Math.max(1, Number.parseInt(recurrenceInterval || "1", 10)),
              weekdays: recurrenceFreq === "weekly" ? recurrenceWeekdays : null,
              until: recurrenceUntil ? toApiDateTime(recurrenceUntil) : null
            }
          : null
      });
      setTitle("");
      setCategory(taskType === "sleep" ? "sleep" : "general");
      setImportance("medium");
      setPlannedStartAt("");
      setPlannedEndAt("");
      setNote("");
      setIsRecurring(false);
      setRecurrenceFreq("weekly");
      setRecurrenceInterval("1");
      setRecurrenceWeekdays([1, 2, 3, 4, 5]);
      setRecurrenceUntil("");
      await loadTasks();
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed to create task");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (taskId: number) => {
    if (!window.confirm("Confirm delete this task?")) return;

    try {
      await deleteTask(taskId);
      await loadTasks();
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed to delete task");
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
      setError(err instanceof Error ? err.message : "failed to update status");
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
    if (!editDraft) return;

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
      setError(err instanceof Error ? err.message : "failed to save task");
    } finally {
      setSavingId(null);
    }
  };

  return (
    <main className="page-shell">
      <TopNav />
      <section className="panel placeholder-page">
        <h1>Tasks</h1>
        <p>Support planned/actual time, completion mark, editing, and recurring templates.</p>

        <div className="task-form">
          <input className="quick-input" placeholder="Task title" value={title} onChange={(e) => setTitle(e.target.value)} />
          <div className="task-form-row">
            <label>
              Type
              <select
                className="quick-input"
                value={taskType}
                onChange={(e) => {
                  const value = e.target.value as TaskType;
                  setTaskType(value);
                  if (value === "sleep") {
                    setCategory("sleep");
                    if (!title.trim()) setTitle("sleep");
                  }
                }}
              >
                <option value="task">Task</option>
                <option value="sleep">Sleep</option>
              </select>
            </label>
            <label>
              Category
              <input className="quick-input" value={category} onChange={(e) => setCategory(e.target.value)} />
            </label>
            <label>
              Importance
              <select className="quick-input" value={importance} onChange={(e) => setImportance(e.target.value as Importance)}>
                <option value="high">high</option>
                <option value="medium">medium</option>
                <option value="low">low</option>
              </select>
            </label>
          </div>
          <div className="task-form-row">
            <label>
              Planned start
              <input className="quick-input" type="datetime-local" value={plannedStartAt} onChange={(e) => setPlannedStartAt(e.target.value)} />
            </label>
            <label>
              Planned end
              <input className="quick-input" type="datetime-local" value={plannedEndAt} onChange={(e) => setPlannedEndAt(e.target.value)} />
            </label>
            <label>
              Note
              <input className="quick-input" value={note} onChange={(e) => setNote(e.target.value)} />
            </label>
          </div>

          <div className="task-form-row">
            <label>
              <input type="checkbox" checked={isRecurring} onChange={(e) => setIsRecurring(e.target.checked)} />
              &nbsp;Recurring task
            </label>
            {isRecurring ? (
              <>
                <label>
                  Frequency
                  <select className="quick-input" value={recurrenceFreq} onChange={(e) => setRecurrenceFreq(e.target.value as RecurrenceFreq)}>
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                    <option value="monthly">Monthly</option>
                    <option value="yearly">Yearly</option>
                  </select>
                </label>
                <label>
                  Interval
                  <input
                    className="quick-input"
                    type="number"
                    min={1}
                    value={recurrenceInterval}
                    onChange={(e) => setRecurrenceInterval(e.target.value)}
                  />
                </label>
                <label>
                  Until
                  <input
                    className="quick-input"
                    type="datetime-local"
                    value={recurrenceUntil}
                    onChange={(e) => setRecurrenceUntil(e.target.value)}
                  />
                </label>
              </>
            ) : null}
          </div>

          {isRecurring && recurrenceFreq === "weekly" ? (
            <div className="task-form-row">
              <label>Weekdays</label>
              {[1, 2, 3, 4, 5, 6, 0].map((day) => (
                <label key={day}>
                  <input
                    type="checkbox"
                    checked={recurrenceWeekdays.includes(day)}
                    onChange={(e) => {
                      setRecurrenceWeekdays((prev) => {
                        if (e.target.checked) return [...prev, day].sort();
                        return prev.filter((v) => v !== day);
                      });
                    }}
                  />
                  &nbsp;{["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][day === 0 ? 6 : day - 1]}
                </label>
              ))}
            </div>
          ) : null}

          <button className="pill" type="button" disabled={!canSubmit} onClick={() => void handleCreate()}>
            {submitting ? "Creating..." : "Create task"}
          </button>
          {error ? <p className="wealth-note">{error}</p> : null}
        </div>

        <div className="feed-list">
          {loading ? <article className="feed-item">Loading tasks...</article> : null}
          {!loading && tasks.length === 0 ? <article className="feed-item">No tasks</article> : null}
          {tasks.map((task) => {
            const isEditing = editingId === task.id && !!editDraft;
            return (
              <article className="feed-item" key={task.id}>
                {!isEditing ? (
                  <>
                    <div className="feed-meta">
                      {task.type === "sleep" ? "sleep" : task.category} · importance {importanceLabel(task.importance)} · status {statusLabel(task.status)}
                    </div>
                    {task.template_id ? <div className="feed-meta">recurring instance</div> : null}
                    <div>{task.title}</div>
                    <div className="feed-meta">
                      Planned: {toInputDateTime(task.planned_start_at) || "--"} - {toInputDateTime(task.planned_end_at) || "--"}
                    </div>
                    <div className="feed-meta">
                      Actual: {toInputDateTime(task.actual_start_at) || "--"} - {toInputDateTime(task.actual_end_at) || "--"}
                    </div>
                    <div className="feed-meta">Completed: {toInputDateTime(task.completed_at) || "--"}</div>
                    {task.note ? <div>{task.note}</div> : null}
                    <div className="task-actions">
                      <button className="pill" type="button" disabled={savingId === task.id} onClick={() => void handleToggleDone(task)}>
                        {task.status === "done" ? "Undo done" : "Mark done"}
                      </button>
                      <button className="pill" type="button" disabled={savingId === task.id} onClick={() => startEdit(task)}>
                        Edit
                      </button>
                      <button className="pill danger" type="button" disabled={savingId === task.id} onClick={() => void handleDelete(task.id)}>
                        Delete
                      </button>
                    </div>
                  </>
                ) : (
                  <div className="task-edit">
                    <div className="task-form-row">
                      <label>
                        Title
                        <input className="quick-input" value={editDraft.title} onChange={(e) => setEditDraft({ ...editDraft, title: e.target.value })} />
                      </label>
                      <label>
                        Category
                        <input className="quick-input" value={editDraft.category} onChange={(e) => setEditDraft({ ...editDraft, category: e.target.value })} />
                      </label>
                      <label>
                        Type
                        <select className="quick-input" value={editDraft.type} onChange={(e) => setEditDraft({ ...editDraft, type: e.target.value as TaskType })}>
                          <option value="task">Task</option>
                          <option value="sleep">Sleep</option>
                        </select>
                      </label>
                    </div>
                    <div className="task-form-row">
                      <label>
                        Status
                        <select className="quick-input" value={editDraft.status} onChange={(e) => setEditDraft({ ...editDraft, status: e.target.value as TaskStatus })}>
                          <option value="todo">todo</option>
                          <option value="in_progress">in progress</option>
                          <option value="done">done</option>
                          <option value="skipped">skipped</option>
                        </select>
                      </label>
                      <label>
                        Importance
                        <select className="quick-input" value={editDraft.importance} onChange={(e) => setEditDraft({ ...editDraft, importance: e.target.value as Importance })}>
                          <option value="high">high</option>
                          <option value="medium">medium</option>
                          <option value="low">low</option>
                        </select>
                      </label>
                      <label>
                        Note
                        <input className="quick-input" value={editDraft.note} onChange={(e) => setEditDraft({ ...editDraft, note: e.target.value })} />
                      </label>
                    </div>
                    <div className="task-form-row">
                      <label>
                        Planned start
                        <input
                          className="quick-input"
                          type="datetime-local"
                          value={editDraft.plannedStartAt}
                          onChange={(e) => setEditDraft({ ...editDraft, plannedStartAt: e.target.value })}
                        />
                      </label>
                      <label>
                        Planned end
                        <input
                          className="quick-input"
                          type="datetime-local"
                          value={editDraft.plannedEndAt}
                          onChange={(e) => setEditDraft({ ...editDraft, plannedEndAt: e.target.value })}
                        />
                      </label>
                      <label>
                        Actual start
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
                        Actual end
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
                        Save
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
                        Cancel
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