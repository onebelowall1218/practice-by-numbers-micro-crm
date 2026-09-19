import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { Priority } from "@/api/types";

const STYLES: Record<Priority, string> = {
  high: "bg-high-soft text-high border-high/30",
  medium: "bg-medium-soft text-medium border-medium/30",
  low: "bg-low-soft text-low border-low/30",
};

const LABELS: Record<Priority, string> = { high: "High", medium: "Medium", low: "Low" };

export function PriorityBadge({ priority, className }: { priority: Priority; className?: string }) {
  return (
    <Badge variant="outline" className={cn("font-medium", STYLES[priority], className)}>
      {LABELS[priority]} priority
    </Badge>
  );
}
