import { Mail, Phone, StickyNote, Users } from "lucide-react";

import type { Interaction, InteractionType } from "@/api/types";
import { formatDate } from "@/lib/format";
import { cn } from "@/lib/utils";

const ICONS: Record<InteractionType, typeof Mail> = {
  email: Mail,
  call: Phone,
  meeting: Users,
  note: StickyNote,
};

interface Props {
  interactions: Interaction[]; // newest first, as the API returns them
  highlightedId: string | null;
  evidenceIds: string[];
}

/** Raw history, always visible, so the user can check the AI's reasoning against the source. */
export function Timeline({ interactions, highlightedId, evidenceIds }: Props) {
  if (interactions.length === 0) {
    return <p className="text-sm text-muted-foreground">No interactions recorded yet.</p>;
  }
  return (
    <ol className="relative space-y-4 border-l pl-6">
      {interactions.map((interaction) => {
        const Icon = ICONS[interaction.type];
        const isEvidence = evidenceIds.includes(interaction.id);
        return (
          <li
            key={interaction.id}
            id={`interaction-${interaction.id}`}
            className={cn(
              "relative rounded-md p-3 transition-colors",
              highlightedId === interaction.id && "bg-primary/10 ring-1 ring-primary/40",
            )}
          >
            <span className="absolute -left-[31px] top-3.5 grid size-6 place-items-center rounded-full border bg-card">
              <Icon className="size-3.5 text-muted-foreground" />
            </span>
            <div className="flex flex-wrap items-baseline gap-x-2 text-sm">
              <span className="font-medium">{formatDate(interaction.occurred_at, "MMM d, yyyy")}</span>
              <span className="capitalize text-muted-foreground">{interaction.type}</span>
              {interaction.contact_name && (
                <span className="text-muted-foreground">· {interaction.contact_name}</span>
              )}
              {isEvidence && (
                <span className="ml-auto text-xs text-primary">Cited by the AI</span>
              )}
            </div>
            <p className="mt-1 text-sm leading-relaxed">{interaction.notes}</p>
            {interaction.ai_summary && (
              <p className="mt-1.5 text-xs text-muted-foreground">
                <span className="font-medium">AI summary:</span> {interaction.ai_summary}
              </p>
            )}
          </li>
        );
      })}
    </ol>
  );
}
