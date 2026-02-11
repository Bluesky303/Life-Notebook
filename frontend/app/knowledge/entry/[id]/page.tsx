import { KnowledgeDetail } from "@/components/KnowledgeDetail";
import { TopNav } from "@/components/TopNav";

export default function KnowledgeEntryDetailPage({ params }: { params: { id: string } }) {
  const entryId = Number(params.id);

  return (
    <main className="page-shell">
      <TopNav />
      <KnowledgeDetail entryId={entryId} expectedKind="entry" />
    </main>
  );
}
