import { ActivityFeed } from "@/components/ActivityFeed";
import { TopNav } from "@/components/TopNav";
import { WealthCard } from "@/components/WealthCard";
import { WeeklyTimeline } from "@/components/WeeklyTimeline";

export default function HomePage() {
  return (
    <main className="page-shell">
      <TopNav />
      <section className="dashboard-grid">
        <WealthCard />
        <WeeklyTimeline />
        <ActivityFeed />
      </section>
    </main>
  );
}
