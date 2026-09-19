import { Badge } from "@/components/ui/badge";
import type { CustomerStatus } from "@/api/types";

export function StatusChip({ status }: { status: CustomerStatus }) {
  return (
    <Badge variant="secondary" className="capitalize">
      {status}
    </Badge>
  );
}
