"use client";

import { useEffect, useState } from "react";

import { TopNav } from "@/components/TopNav";
import { getAppSettings, updateAppSettings } from "@/lib/api";

export default function SettingsPage() {
  const [defaultProvider, setDefaultProvider] = useState("codex");
  const [modelName, setModelName] = useState("gpt-5-codex");
  const [theme, setTheme] = useState("sci-fi");
  const [localOnly, setLocalOnly] = useState(true);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const data = await getAppSettings();
        setDefaultProvider(data.default_provider);
        setModelName(data.model_name);
        setTheme(data.theme);
        setLocalOnly(data.local_only);
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setMessage("");
    try {
      await updateAppSettings({
        default_provider: defaultProvider,
        model_name: modelName,
        theme,
        local_only: localOnly
      });
      setMessage("设置已保存");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "保存失败");
    } finally {
      setSaving(false);
    }
  };

  return (
    <main className="page-shell">
      <TopNav />
      <section className="panel placeholder-page">
        <h1>选项</h1>
        <p>模型与隐私策略设置。</p>

        {loading ? <article className="feed-item">读取设置中...</article> : null}

        <div className="task-form-row">
          <label>
            默认 Provider
            <select className="quick-input" value={defaultProvider} onChange={(e) => setDefaultProvider(e.target.value)}>
              <option value="codex">codex</option>
              <option value="openai-compatible">openai-compatible</option>
              <option value="ollama">ollama</option>
            </select>
          </label>

          <label>
            模型名
            <input className="quick-input" value={modelName} onChange={(e) => setModelName(e.target.value)} />
          </label>

          <label>
            主题
            <select className="quick-input" value={theme} onChange={(e) => setTheme(e.target.value)}>
              <option value="sci-fi">科幻简洁</option>
              <option value="minimal-light">浅色简洁</option>
              <option value="deep-space">深空</option>
            </select>
          </label>
        </div>

        <div className="task-form-row">
          <label>
            隐私模式
            <select className="quick-input" value={localOnly ? "true" : "false"} onChange={(e) => setLocalOnly(e.target.value === "true")}>
              <option value="true">仅本地模型</option>
              <option value="false">允许外部模型</option>
            </select>
          </label>
          <label>
            保存
            <button className="pill" type="button" onClick={() => void handleSave()} disabled={saving}>
              {saving ? "保存中..." : "保存设置"}
            </button>
          </label>
          <label>
            状态
            <div className="quick-input">{message || "未修改"}</div>
          </label>
        </div>
      </section>
    </main>
  );
}
