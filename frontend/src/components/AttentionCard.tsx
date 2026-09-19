import { ArrowRight, Clock } from "lucide-react";
import { Link } from "react-router-dom";

import type { CustomerSummary } from "@/api/types";
import { PriorityBadge } from "@/components/PriorityBadge";
import { StatusChip } from "@/components/StatusChip";
import { Card } from "@/components/ui/card";
import { describeDaysAgo, describeDueDate } from "@/lib/format";
import { cn } from "@/lib/utils";

const BAR: Record<string, string> = { high: "bg-high", medium: "bg-medium", low: "bg-low" };

/** One row on the dashboard: who, why, what to do, and when. */
export function AttentionCard({ customer, today }: { customer: CustomerSummary; today: string }) {
  const analysis = customer.analysis;
  const priority = analysis?.judgment.priority ?? "low";
  const isDone = customer.follow_up.completed_at !== null;
  return (
    <Link to={`/customers/${customer.id}`} className="block focus:outline-none">
      <Card className="group relative flex flex-row gap-4 overflow-hidden p-4 transition hover:shadow-md focus-visible:ring-2">
        <div className={cn("w-1 shrink-0 self-stretch rounded-full", BAR[priority])} />
        <div className="min-w-0 flex-1 space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-semibold leading-tight">{customer.name}</h3>
            <StatusChip status={customer.status} />
            <PriorityBadge priority={priority} className="ml-auto" />
          </div>
          {analysis && (
            <>
              <p className="text-sm text-muted-foreground">{analysis.narrative.priority_reason}</p>
              <p className="flex items-start gap-1.5 text-sm">
                <ArrowRight className="mt-0.5 size-4 shrink-0 text-primary" />
                <span>{analysis.narrative.next_action}</span>
              </p>
            </>
          )}
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
            <span className="inline-flex items-center gap-1">
              <Clock className="size-3" />
              {isDone ? "Follow-up done" : describeDueDate(customer.follow_up.date, today)}
            </span>
            <span>{describeDaysAgo(customer.signals.days_since_last_interaction)}</span>
            {analysis?.fallback_used && <span>Rule-based analysis</span>}
          </div>
        </div>
      </Card>
    </Link>
  );
}
