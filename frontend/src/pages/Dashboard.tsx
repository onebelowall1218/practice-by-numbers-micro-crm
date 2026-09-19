import { useState } from "react";

import { useDashboard } from "@/api/hooks";
import type { BucketKey, CustomerStatus, CustomerSummary } from "@/api/types";
import { AttentionCard } from "@/components/AttentionCard";
import { DemoClockBanner } from "@/components/DemoClockBanner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { formatLongDate } from "@/lib/format";

const BUCKETS: { key: BucketKey; title: string; hint: string }[] = [
  { key: "overdue", title: "Overdue", hint: "Follow-up date has passed" },
  { key: "due_soon", title: "Due this week", hint: "Act in the next 7 days" },
  { key: "later", title: "Later", hint: "Scheduled or deliberately waiting" },
  { key: "done", title: "Done", hint: "Follow-up completed; will reappear on new activity" },
];

type Filter = "all" | CustomerStatus;

/** The daily view: who needs attention, in what order, and why. */
export function Dashboard() {
  const { data, isLoading, error } = useDashboard();
  const [filter, setFilter] = useState<Filter>("all");
  const [search, setSearch] = useState("");

  if (isLoading) return <DashboardSkeleton />;
  if (error || !data) return <p className="text-sm text-destructive">Could not load the dashboard.</p>;

  const matches = (customer: CustomerSummary) =>
    (filter === "all" || customer.status === filter) &&
    customer.name.toLowerCase().includes(search.trim().toLowerCase());
  const total = Object.values(data.buckets).flat().length;
  const attention = data.buckets.overdue.length + data.buckets.due_soon.length;

  return (
    <div className="space-y-6">
      <header className="space-y-3">
        <div>
          <p className="text-sm text-muted-foreground">{formatLongDate(data.as_of)}</p>
          <h1 className="text-2xl font-semibold tracking-tight">
            {attention === 0
              ? "Nothing urgent today."
              : `${attention} of ${total} accounts need attention this week.`}
          </h1>
        </div>
        <DemoClockBanner asOf={data.as_of} demoClock={data.demo_clock} />
        <div className="flex flex-wrap items-center gap-2">
          {(["all", "prospect", "customer"] as Filter[]).map((option) => (
            <Button
              key={option}
              size="sm"
              variant={filter === option ? "default" : "outline"}
              onClick={() => setFilter(option)}
              className="capitalize"
            >
              {option === "all" ? "All accounts" : `${option}s`}
            </Button>
          ))}
          <Input
            placeholder="Search accounts…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="ml-auto max-w-xs"
          />
        </div>
      </header>

      {BUCKETS.map(({ key, title, hint }) => {
        const customers = data.buckets[key].filter(matches);
        if (customers.length === 0) return null;
        return (
          <section key={key} className="space-y-3">
            <div className="flex items-baseline gap-2">
              <h2 className="text-lg font-semibold">{title}</h2>
              <span className="text-sm text-muted-foreground">
                {customers.length} · {hint}
              </span>
            </div>
            <div className="grid gap-3">
              {customers.map((customer) => (
                <AttentionCard key={customer.id} customer={customer} today={data.as_of} />
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-4 w-48" />
      <Skeleton className="h-8 w-96" />
      {[0, 1, 2, 3].map((i) => (
        <Skeleton key={i} className="h-28 w-full" />
      ))}
    </div>
  );
}
