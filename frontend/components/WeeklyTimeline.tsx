"use client";

import { useEffect, useMemo, useState } from "react";

import { getTasks, type TaskItem } from "@/lib/api";

type Importance = "high" | "medium" | "low";

type TimelineBlock = {
  startMinute: number;
  endMinute: number;
  title: string;
  kind: "task" | "free" | "sleep";
  importance?: Importance;
};

const dayOrder = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"];
const weekDayMap = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"];
const SLOT_MINUTES = 5;
const TOTAL_SLOTS = (24 * 60) / SLOT_MINUTES;

function formatMinute(minute: number): string {
  const h = Math.floor(minute / 60)
    .toString()
    .padStart(2, "0");
  const m = (minute % 60).toString().padStart(2, "0");
  return `${h}:${m}`;
}

function toGridRow(minute: number): number {
  return Math.floor(minute / SLOT_MINUTES) + 1;
}

function clampMinute(minute: number): number {
  if (minute < 0) return 0;
  if (minute > 24 * 60) return 24 * 60;
  return minute;
}

function normalizeImportance(value: string): Importance {
  if (value === "high" || value === "medium" || value === "low") {
    return value;
  }
  return "low";
}

function mapTasksToDayEvents(tasks: TaskItem[]): Record<string, TimelineBlock[]> {
  const dayEvents: Record<string, TimelineBlock[]> = Object.fromEntries(dayOrder.map((day) => [day, []]));

  for (const task of tasks) {
    if (!task.start_at || !task.end_at) {
      continue;
    }

    const startDate = new Date(task.start_at);
    const endDate = new Date(task.end_at);

    if (Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime())) {
      continue;
    }

    const day = weekDayMap[startDate.getDay()];
    if (!dayEvents[day]) {
      continue;
    }

    const startMinute = clampMinute(startDate.getHours() * 60 + startDate.getMinutes());
    const endMinute = clampMinute(endDate.getHours() * 60 + endDate.getMinutes());

    if (endMinute <= startMinute) {
      continue;
    }

    dayEvents[day].push({
      startMinute,
      endMinute,
      title: task.title,
      kind: "task",
      importance: normalizeImportance(task.importance)
    });
  }

  for (const day of dayOrder) {
    dayEvents[day] = dayEvents[day].sort((a, b) => a.startMinute - b.startMinute);
  }

  return dayEvents;
}

function createDayBlocks(dayTaskBlocks: TimelineBlock[]): TimelineBlock[] {
  const sleepBlocks: TimelineBlock[] = [
    { startMinute: 0, endMinute: 7 * 60, title: "睡眠", kind: "sleep" },
    { startMinute: 23 * 60, endMinute: 24 * 60, title: "睡眠", kind: "sleep" }
  ];

  const fixedBlocks = [...sleepBlocks, ...dayTaskBlocks].sort((a, b) => a.startMinute - b.startMinute);

  const blocks: TimelineBlock[] = [];
  let cursor = 0;

  for (const block of fixedBlocks) {
    if (block.startMinute > cursor) {
      blocks.push({
        startMinute: cursor,
        endMinute: block.startMinute,
        title: "空闲时间",
        kind: "free"
      });
    }

    if (block.endMinute > cursor) {
      blocks.push(block);
      cursor = block.endMinute;
    }
  }

  if (cursor < 24 * 60) {
    blocks.push({
      startMinute: cursor,
      endMinute: 24 * 60,
      title: "空闲时间",
      kind: "free"
    });
  }

  return blocks;
}

function blockClassName(block: TimelineBlock): string {
  if (block.kind === "free") {
    return "time-block aligned-block free";
  }

  if (block.kind === "sleep") {
    return "time-block aligned-block sleep";
  }

  return `time-block aligned-block ${block.importance ?? "low"}`;
}

export function WeeklyTimeline() {
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await getTasks();
        setTasks(data);
      } catch {
        setTasks([]);
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, []);

  const dayTaskMap = useMemo(() => mapTasksToDayEvents(tasks), [tasks]);
  const hourLabels = useMemo(() => Array.from({ length: 24 }, (_, i) => i), []);

  return (
    <section className="panel timeline-panel">
      <p className="panel-title">一周时间表</p>
      {loading ? <p className="wealth-note">正在读取任务...</p> : null}
      <div className="timeline-board">
        <div className="time-axis">
          <div className="day-name axis-title">时间</div>
          <div className="axis-track" style={{ gridTemplateRows: `repeat(${TOTAL_SLOTS}, minmax(0, 1fr))` }}>
            {hourLabels.map((hour) => {
              const minute = hour * 60;
              return (
                <div className="axis-label" key={hour} style={{ gridRow: `${toGridRow(minute)} / span 1` }}>
                  {formatMinute(minute)}
                </div>
              );
            })}
          </div>
        </div>

        <div className="timeline-grid">
          {dayOrder.map((day) => {
            const blocks = createDayBlocks(dayTaskMap[day] ?? []);

            return (
              <article className="day-col" key={day}>
                <h3 className="day-name">{day}</h3>
                <div className="day-track" style={{ gridTemplateRows: `repeat(${TOTAL_SLOTS}, minmax(0, 1fr))` }}>
                  {blocks.map((block, idx) => {
                    const rowStart = toGridRow(block.startMinute);
                    const rowEnd = toGridRow(block.endMinute);

                    return (
                      <div
                        className={blockClassName(block)}
                        key={`${day}-${block.startMinute}-${idx}`}
                        style={{ gridRow: `${rowStart} / ${rowEnd}` }}
                      >
                        <div>
                          {formatMinute(block.startMinute)}-{formatMinute(block.endMinute)}
                        </div>
                        <div>{block.title}</div>
                      </div>
                    );
                  })}
                </div>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}
