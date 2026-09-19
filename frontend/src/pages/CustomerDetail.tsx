import { ArrowLeft, Mail, RefreshCw } from "lucide-react";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { toast } from "sonner";

import { useCustomer, useHealth, useReanalyze, useUpdateFollowUp } from "@/api/hooks";
import { AddInteractionDialog } from "@/components/AddInteractionDialog";
import { AnalysisPanel } from "@/components/AnalysisPanel";
import { DraftMessageDialog } from "@/components/DraftMessageDialog";
import { FollowUpControl } from "@/components/FollowUpControl";
import { StatusChip } from "@/components/StatusChip";
import { Timeline } from "@/components/Timeline";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { describeDaysAgo, formatDate } from "@/lib/format";

/** Everything about one account: AI read, follow-up, contacts, and the raw timeline. */
export function CustomerDetail() {
  const { id = "" } = useParams();
  const { data: customer, isLoading, error } = useCustomer(id);
  const { data: health } = useHealth();
  const reanalyze = useReanalyze(id);
  const updateFollowUp = useUpdateFollowUp(id);
  const [analyzing, setAnalyzing] = useState(false);
  const [highlightedId, setHighlightedId] = useState<string | null>(null);

  if (isLoading || !health) return <DetailSkeleton />;
  if (error || !customer) return <p className="text-sm text-destructive">Customer not found.</p>;

  const today = health.as_of;
  const narrative = customer.analysis?.narrative ?? null;

  function runReanalysis() {
    setAnalyzing(true);
    reanalyze.mutate(undefined, {
      onSuccess: () => toast.success("Analysis refreshed"),
      onError: (err) => toast.error(err.message),
      onSettled: () => setAnalyzing(false),
    });
  }

  return (
    <div className="space-y-6">
      <Link to="/" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="size-4" /> Back to today
      </Link>

      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-semibold tracking-tight">{customer.name}</h1>
            <StatusChip status={customer.status} />
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            {customer.status === "customer" ? "Customer since" : "Prospect since"}{" "}
            {formatDate(customer.created_at, "MMM d, yyyy")} · {customer.signals.interaction_count}{" "}
            interactions · {describeDaysAgo(customer.signals.days_since_last_interaction)}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <AddInteractionDialog
            customerId={customer.id}
            contacts={customer.contacts}
            today={today}
            onAnalyzing={setAnalyzing}
          />
          <DraftMessageDialog customerId={customer.id} />
          <Button variant="ghost" onClick={runReanalysis} disabled={analyzing}>
            <RefreshCw className="size-4" /> Re-analyze
          </Button>
        </div>
      </header>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <AnalysisPanel
            analysis={customer.analysis}
            interactions={customer.interactions}
            isRefreshing={analyzing}
            onHoverEvidence={setHighlightedId}
          />
          <section className="space-y-3">
            <h2 className="text-lg font-semibold">Interaction history</h2>
            <Timeline
              interactions={customer.interactions}
              highlightedId={highlightedId}
              evidenceIds={narrative?.evidence_ids ?? []}
            />
          </section>
        </div>

        <aside className="space-y-6">
          <FollowUpControl
            followUp={customer.follow_up}
            narrative={narrative}
            today={today}
            isSaving={updateFollowUp.isPending}
            onChangeDate={(date) => updateFollowUp.mutate({ follow_up_date: date })}
            onToggleDone={(done) => updateFollowUp.mutate({ completed: done })}
          />
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Contacts</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {customer.contacts.map((contact) => (
                <div key={contact.id} className="text-sm">
                  <p className="font-medium">{contact.name}</p>
                  <p className="text-muted-foreground">{contact.role}</p>
                  <a
                    href={`mailto:${contact.email}`}
                    className="inline-flex items-center gap-1 text-muted-foreground hover:text-foreground"
                  >
                    <Mail className="size-3" /> {contact.email}
                  </a>
                </div>
              ))}
            </CardContent>
          </Card>
        </aside>
      </div>
    </div>
  );
}

function DetailSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-8 w-72" />
      <div className="grid gap-6 lg:grid-cols-3">
        <Skeleton className="h-72 lg:col-span-2" />
        <Skeleton className="h-48" />
      </div>
    </div>
  );
}
