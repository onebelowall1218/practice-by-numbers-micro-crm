import { CalendarCheck, Check, Pencil, RotateCcw } from "lucide-react";
import { useState } from "react";

import type { FollowUp, Narrative } from "@/api/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { describeDueDate, formatDate } from "@/lib/format";

interface Props {
  followUp: FollowUp;
  narrative: Narrative | null;
  today: string;
  isSaving: boolean;
  onChangeDate: (date: string) => void;
  onToggleDone: (done: boolean) => void;
}

/** The one thing the user controls: when to follow up. AI proposes, the user accepts or edits. */
export function FollowUpControl({ followUp, narrative, today, isSaving, onChangeDate, onToggleDone }: Props) {
  const [editing, setEditing] = useState(false);
  const [draftDate, setDraftDate] = useState(followUp.date ?? today);
  const isDone = followUp.completed_at !== null;

  function save() {
    onChangeDate(draftDate);
    setEditing(false);
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <CalendarCheck className="size-4 text-primary" /> Follow-up
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div>
          <p className="text-2xl font-semibold">{formatDate(followUp.date, "EEE, MMM d")}</p>
          <p className="text-sm text-muted-foreground">
            {isDone ? "Marked done" : describeDueDate(followUp.date, today)}
            {followUp.source === "ai" && " · suggested by AI"}
            {followUp.source === "user" && " · set by you"}
          </p>
        </div>
        {narrative && followUp.source === "ai" && (
          <p className="text-sm text-muted-foreground">{narrative.follow_up_rationale}</p>
        )}

        {editing ? (
          <div className="flex items-center gap-2">
            <Input
              type="date"
              value={draftDate}
              min={today}
              onChange={(event) => setDraftDate(event.target.value)}
              className="max-w-[180px]"
            />
            <Button size="sm" onClick={save} disabled={isSaving}>
              Save
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setEditing(false)}>
              Cancel
            </Button>
          </div>
        ) : (
          <div className="flex flex-wrap gap-2">
            {followUp.source === "ai" && !isDone && followUp.date && (
              <Button size="sm" variant="outline" onClick={() => onChangeDate(followUp.date!)} disabled={isSaving}>
                <Check className="size-4" /> Accept date
              </Button>
            )}
            <Button size="sm" variant="outline" onClick={() => setEditing(true)} disabled={isSaving}>
              <Pencil className="size-4" /> Change date
            </Button>
            {isDone ? (
              <Button size="sm" variant="ghost" onClick={() => onToggleDone(false)} disabled={isSaving}>
                <RotateCcw className="size-4" /> Reopen
              </Button>
            ) : (
              <Button size="sm" onClick={() => onToggleDone(true)} disabled={isSaving}>
                <Check className="size-4" /> Mark done
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
