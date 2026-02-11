import { KnowledgeWorkspace } from "@/components/KnowledgeWorkspace";
import { TopNav } from "@/components/TopNav";

export default function KnowledgeBlogPage() {
  return (
    <main className="page-shell">
      <TopNav />
      <KnowledgeWorkspace kind="blog" title="博客" description="面向问题解决过程，支持 Markdown 编辑和渲染预览。" />
    </main>
  );
}
