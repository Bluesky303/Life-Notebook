import { KnowledgeWorkspace } from "@/components/KnowledgeWorkspace";
import { TopNav } from "@/components/TopNav";

export default function KnowledgeEntryPage() {
  return (
    <main className="page-shell">
      <TopNav />
      <KnowledgeWorkspace kind="entry" title="词条" description="面向新事物记录，支持 Markdown 编辑和渲染预览。" />
    </main>
  );
}
