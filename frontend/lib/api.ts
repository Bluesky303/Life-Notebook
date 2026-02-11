export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type CashTotalResponse = {
  currency: string;
  cash_total: string;
};

export type FeedItem = {
  id: number;
  category: string;
  content: string;
  created_at: string;
};

export type TaskItem = {
  id: number;
  title: string;
  category: string;
  importance: "high" | "medium" | "low" | string;
  start_at: string | null;
  end_at: string | null;
};

export type AssetAccount = {
  name: string;
  is_cash: boolean;
  balance: string;
};

export type AssetTransaction = {
  id: number;
  account: string;
  type: "income" | "expense" | string;
  category: string;
  amount: string;
  happened_on: string;
  note: string | null;
};

export type CategorySummary = {
  category: string;
  income: string;
  expense: string;
};

export type MonthlySummary = {
  month: string;
  income: string;
  expense: string;
};

export type InvestmentLog = {
  id: number;
  happened_on: string;
  invested: string;
  daily_profit: string;
  note: string | null;
};

export type InvestmentTrendPoint = {
  date: string;
  invested: string;
  daily_profit: string;
  acc_profit: string;
};

export type KnowledgeEntry = {
  id: number;
  kind: "blog" | "entry" | string;
  title: string;
  markdown: string;
  updated_at: string;
};

export type AppSettings = {
  default_provider: string;
  model_name: string;
  theme: string;
  local_only: boolean;
};

export type AIParseRecordResult = {
  detected_type: string;
  suggested_category: string;
  normalized_text: string;
  extracted_amount: string | null;
  extracted_time: string | null;
};

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    },
    cache: "no-store"
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `API ${path} failed with status ${response.status}`);
  }

  return (await response.json()) as T;
}

export async function getCashTotal(): Promise<CashTotalResponse> {
  return apiRequest<CashTotalResponse>("/assets/cash-total");
}

export async function getFeed(): Promise<FeedItem[]> {
  return apiRequest<FeedItem[]>("/feed/");
}

export async function createFeed(payload: { category: string; content: string }): Promise<FeedItem> {
  return apiRequest<FeedItem>("/feed/", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function deleteFeed(feedId: number): Promise<{ deleted: boolean; id: number }> {
  return apiRequest<{ deleted: boolean; id: number }>(`/feed/${feedId}`, {
    method: "DELETE"
  });
}

export async function getTasks(): Promise<TaskItem[]> {
  return apiRequest<TaskItem[]>("/tasks/");
}

export async function createTask(payload: {
  title: string;
  category: string;
  importance: "high" | "medium" | "low";
  start_at: string;
  end_at: string;
}): Promise<TaskItem> {
  return apiRequest<TaskItem>("/tasks/", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function deleteTask(taskId: number): Promise<{ deleted: boolean; id: number }> {
  return apiRequest<{ deleted: boolean; id: number }>(`/tasks/${taskId}`, {
    method: "DELETE"
  });
}

export async function getAssetAccounts(): Promise<AssetAccount[]> {
  return apiRequest<AssetAccount[]>("/assets/accounts");
}

export async function getAssetTransactions(params?: { category?: string; month?: string }): Promise<AssetTransaction[]> {
  const query = new URLSearchParams();
  if (params?.category) query.set("category", params.category);
  if (params?.month) query.set("month", params.month);
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiRequest<AssetTransaction[]>(`/assets/transactions${suffix}`);
}

export async function createAssetTransaction(payload: {
  account: string;
  type: "income" | "expense";
  category: string;
  amount: string;
  happened_on: string;
  note?: string;
}): Promise<AssetTransaction> {
  return apiRequest<AssetTransaction>("/assets/transactions", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function deleteAssetTransaction(transactionId: number): Promise<{ deleted: boolean; id: number }> {
  return apiRequest<{ deleted: boolean; id: number }>(`/assets/transactions/${transactionId}`, {
    method: "DELETE"
  });
}

export async function getCategorySummary(month?: string): Promise<CategorySummary[]> {
  const suffix = month ? `?month=${encodeURIComponent(month)}` : "";
  return apiRequest<CategorySummary[]>(`/assets/category-summary${suffix}`);
}

export async function getMonthlySummary(): Promise<MonthlySummary[]> {
  return apiRequest<MonthlySummary[]>("/assets/monthly-summary");
}

export async function getInvestmentLogs(): Promise<InvestmentLog[]> {
  return apiRequest<InvestmentLog[]>("/assets/investment/logs");
}

export async function createInvestmentLog(payload: {
  happened_on: string;
  invested: string;
  daily_profit: string;
  note?: string;
}): Promise<InvestmentLog> {
  return apiRequest<InvestmentLog>("/assets/investment/logs", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function deleteInvestmentLog(logId: number): Promise<{ deleted: boolean; id: number }> {
  return apiRequest<{ deleted: boolean; id: number }>(`/assets/investment/logs/${logId}`, {
    method: "DELETE"
  });
}

export async function getInvestmentTrend(): Promise<InvestmentTrendPoint[]> {
  return apiRequest<InvestmentTrendPoint[]>("/assets/investment/trend");
}

export async function getKnowledgeEntries(params?: { kind?: string; q?: string }): Promise<KnowledgeEntry[]> {
  const query = new URLSearchParams();
  if (params?.kind) query.set("kind", params.kind);
  if (params?.q) query.set("q", params.q);
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiRequest<KnowledgeEntry[]>(`/knowledge/${suffix}`);
}

export async function createKnowledgeEntry(payload: {
  kind: "blog" | "entry";
  title: string;
  markdown: string;
}): Promise<KnowledgeEntry> {
  return apiRequest<KnowledgeEntry>("/knowledge/", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function deleteKnowledgeEntry(entryId: number): Promise<{ deleted: boolean; id: number }> {
  return apiRequest<{ deleted: boolean; id: number }>(`/knowledge/${entryId}`, {
    method: "DELETE"
  });
}

export async function getAppSettings(): Promise<AppSettings> {
  return apiRequest<AppSettings>("/settings/");
}

export async function updateAppSettings(payload: AppSettings): Promise<AppSettings> {
  return apiRequest<AppSettings>("/settings/", {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export async function parseRecordWithAI(payload: { text: string }): Promise<AIParseRecordResult> {
  return apiRequest<AIParseRecordResult>("/ai/parse-record", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}
