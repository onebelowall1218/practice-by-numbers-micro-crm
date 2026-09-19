import { Sparkles } from "lucide-react";

import { useHealth } from "@/api/hooks";
import { Badge } from "@/components/ui/badge";

export function ProviderBadge() {
  const { data } = useHealth();
  if (!data) return null;
  const label =
    data.generation_provider === "rules"
      ? "Rule-based mode (no API key)"
      : `${data.generation_provider} · ${data.model}`;
  return (
    <Badge variant="outline" className="gap-1 text-muted-foreground">
      <Sparkles className="size-3" /> {label}
    </Badge>
  );
}
