"use client";

import { useEffect, useMemo, useState } from "react";

import { getSleepLogs, getTasks, type SleepLog, type TaskItem } from "@/lib/api";

type Importance = "high" | "medium" | "low";

type TimelineBlock = {
  startMinute: number;
  endMinute: number;
  title: string;
  kind: "task" | "free" | "sleep";
  importance?: Importance;
};

type DayWindowItem = {
  key: string;
  label: string;
};

const weekDayMap = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"];
const WINDOW_DAYS = 7;
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

function dayKey(date: Date): string {
  const y = date.getFullYear();
  const m = (date.getMonth() + 1).toString().padStart(2, "0");
  const d = date.getDate().toString().padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function createDayWindow(): DayWindowItem[] {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  return Array.from({ length: WINDOW_DAYS }, (_, index) => {
    const d = new Date(today);
    d.setDate(today.getDate() + index);
    const mm = (d.getMonth() + 1).toString().padStart(2, "0");
    const dd = d.getDate().toString().padStart(2, "0");
    return {
      key: dayKey(d),
      label: `${weekDayMap[d.getDay()]} ${mm}/${dd}`
    };
  });
}

function createEmptyDayEvents(windowDays: DayWindowItem[]): Record<string, TimelineBlock[]> {
  return Object.fromEntries(windowDays.map((day) => [day.key, []]));
}

function pushRange(
  dayEvents: Record<string, TimelineBlock[]>,
  startDate: Date,
  endDate: Date,
  allowedKeys: Set<string>,
  blockFactory: (startMinute: number, endMinute: number) => TimelineBlock
): void {
  const cursor = new Date(startDate);
  while (cursor < endDate) {
    const key = dayKey(cursor);

    const dayStart = new Date(cursor);
    dayStart.setHours(0, 0, 0, 0);
    const nextDayStart = new Date(dayStart);
    nextDayStart.setDate(nextDayStart.getDate() + 1);

    const segmentEnd = endDate < nextDayStart ? endDate : nextDayStart;
    const startMinute = clampMinute(cursor.getHours() * 60 + cursor.getMinutes());
    const endMinute = clampMinute(
      segmentEnd.getTime() === nextDayStart.getTime() ? 24 * 60 : segmentEnd.getHours() * 60 + segmentEnd.getMinutes()
    );

    if (allowedKeys.has(key) && endMinute > startMinute) {
      dayEvents[key].push(blockFactory(startMinute, endMinute));
    }

    cursor.setTime(segmentEnd.getTime());
  }
}

function mapTasksToDayEvents(tasks: TaskItem[], windowDays: DayWindowItem[]): Record<string, TimelineBlock[]> {
  const dayEvents: Record<string, TimelineBlock[]> = createEmptyDayEvents(windowDays);
  const allowedKeys = new Set(windowDays.map((day) => day.key));

  for (const task of tasks) {
    if (!task.start_at || !task.end_at) {
      continue;
    }

    const startDate = new Date(task.start_at);
    const endDate = new Date(task.end_at);
    if (Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime()) || endDate <= startDate) {
      continue;
    }

    pushRange(dayEvents, startDate, endDate, allowedKeys, (startMinute, endMinute) => ({
      startMinute,
      endMinute,
      title: task.title,
      kind: "task",
      importance: normalizeImportance(task.importance)
    }));
  }

  for (const day of windowDays) {
    dayEvents[day.key] = dayEvents[day.key].sort((a, b) => a.startMinute - b.startMinute);
  }

  return dayEvents;
}

function mapSleepToDayEvents(sleepLogs: SleepLog[], windowDays: DayWindowItem[]): Record<string, TimelineBlock[]> {
  const dayEvents: Record<string, TimelineBlock[]> = createEmptyDayEvents(windowDays);
  const allowedKeys = new Set(windowDays.map((day) => day.key));

  for (const log of sleepLogs) {
    const startDate = new Date(log.start_at);
    const endDate = new Date(log.end_at);
    if (Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime()) || endDate <= startDate) {
      continue;
    }

    pushRange(dayEvents, startDate, endDate, allowedKeys, (startMinute, endMinute) => ({
      startMinute,
      endMinute,
      title: "睡眠",
      kind: "sleep"
    }));
  }

  for (const day of windowDays) {
    dayEvents[day.key] = dayEvents[day.key].sort((a, b) => a.startMinute - b.startMinute);
  }

  return dayEvents;
}

function mergeDayEvents(
  taskMap: Record<string, TimelineBlock[]>,
  sleepMap: Record<string, TimelineBlock[]>,
  windowDays: DayWindowItem[]
): Record<string, TimelineBlock[]> {
  const merged: Record<string, TimelineBlock[]> = createEmptyDayEvents(windowDays);
  for (const day of windowDays) {
    merged[day.key] = [...(sleepMap[day.key] ?? []), ...(taskMap[day.key] ?? [])].sort((a, b) => a.startMinute - b.startMinute);
  }
  return merged;
}

function createDayBlocks(dayBlocks: TimelineBlock[]): TimelineBlock[] {
  const fixedBlocks = [...dayBlocks].sort((a, b) => a.startMinute - b.startMinute);

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
  const [sleepLogs, setSleepLogs] = useState<SleepLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [todayMarker, setTodayMarker] = useState(() => dayKey(new Date()));

  useEffect(() => {
    const load = async () => {
      try {
        const [taskData, sleepData] = await Promise.all([getTasks(), getSleepLogs()]);
        setTasks(taskData);
        setSleepLogs(sleepData);
      } catch {
        setTasks([]);
        setSleepLogs([]);
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, []);

  useEffect(() => {
    const timer = window.setInterval(() => {
      const current = dayKey(new Date());
      setTodayMarker((prev) => (prev === current ? prev : current));
    }, 60 * 1000);

    return () => {
      window.clearInterval(timer);
    };
  }, []);

  const dayWindow = useMemo(() => createDayWindow(), [todayMarker]);
  const dayTaskMap = useMemo(() => mapTasksToDayEvents(tasks, dayWindow), [tasks, dayWindow]);
  const daySleepMap = useMemo(() => mapSleepToDayEvents(sleepLogs, dayWindow), [sleepLogs, dayWindow]);
  const dayMergedMap = useMemo(() => mergeDayEvents(dayTaskMap, daySleepMap, dayWindow), [dayTaskMap, daySleepMap, dayWindow]);
  const hourLabels = useMemo(() => Array.from({ length: 24 }, (_, i) => i), []);

  return (
    <section className="panel timeline-panel">
      <p className="panel-title">时间表（未来7天）</p>
      {loading ? <p className="wealth-note">正在读取任务和睡眠记录...</p> : null}
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

        <div className="timeline-scroll">
          <div className="timeline-grid" style={{ gridTemplateColumns: `repeat(${dayWindow.length}, minmax(120px, 1fr))` }}>
            {dayWindow.map((day) => {
              const blocks = createDayBlocks(dayMergedMap[day.key] ?? []);

              return (
                <article className="day-col" key={day.key}>
                  <h3 className="day-name">{day.label}</h3>
                  <div className="day-track" style={{ gridTemplateRows: `repeat(${TOTAL_SLOTS}, minmax(0, 1fr))` }}>
                    {blocks.map((block, idx) => {
                      const rowStart = toGridRow(block.startMinute);
                      const rowEnd = toGridRow(block.endMinute);

                      return (
                        <div
                          className={blockClassName(block)}
                          key={`${day.key}-${block.startMinute}-${idx}`}
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
      </div>
    </section>
  );
}
