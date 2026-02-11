import Link from "next/link";

import { TopNav } from "@/components/TopNav";

export default function KnowledgeHomePage() {
  return (
    <main className="page-shell">
      <TopNav />
      <section className="panel placeholder-page">
        <h1>知识库</h1>
        <p>分成两个独立页面管理，避免词条和博客混在一起。</p>

        <div className="knowledge-hub">
          <article className="feed-item">
            <div className="feed-meta">词条（Wiki 风格）</div>
            <div>记录新概念、新硬件、新术语。</div>
            <Link className="entry-link" href="/knowledge/entry">
              进入词条页
            </Link>
          </article>

          <article className="feed-item">
            <div className="feed-meta">博客（过程记录）</div>
            <div>记录问题排查、方案设计和复盘。</div>
            <Link className="entry-link" href="/knowledge/blog">
              进入博客页
            </Link>
          </article>
        </div>
      </section>
    </main>
  );
}
