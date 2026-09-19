import { Badge } from "@/components/ui/badge";
import type { Interaction } from "@/api/types";
import { formatDate } from "@/lib/format";

interface Props {
  evidenceIds: string[];
  interactions: Interaction[];
  onHover: (id: string | null) => void;
}

/** Links each AI judgment back to the raw interactions it rests on. Hover highlights, click scrolls. */
export function EvidenceChips({ evidenceIds, interactions, onHover }: Props) {
  const byId = new Map(interactions.map((i) => [i.id, i]));
  const items = evidenceIds.map((id) => byId.get(id)).filter((i): i is Interaction => !!i);
  if (items.length === 0) return null;
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <span className="text-xs text-muted-foreground">Based on:</span>
      {items.map((interaction) => (
        <button
          key={interaction.id}
          type="button"
          onMouseEnter={() => onHover(interaction.id)}
          onMouseLeave={() => onHover(null)}
          onFocus={() => onHover(interaction.id)}
          onBlur={() => onHover(null)}
          onClick={() =>
            document
              .getElementById(`interaction-${interaction.id}`)
              ?.scrollIntoView({ behavior: "smooth", block: "center" })
          }
        >
          <Badge variant="outline" className="cursor-pointer capitalize hover:bg-muted">
            {formatDate(interaction.occurred_at)} {interaction.type}
          </Badge>
        </button>
      ))}
    </div>
  );
}
