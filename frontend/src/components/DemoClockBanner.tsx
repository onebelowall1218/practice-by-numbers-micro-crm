import { CalendarClock } from "lucide-react";

import { formatLongDate } from "@/lib/format";

/** Shown when CRM_TODAY pins "today" so the evaluator knows why dates look the way they do. */
export function DemoClockBanner({ asOf, demoClock }: { asOf: string; demoClock: boolean }) {
  if (!demoClock) return null;
  return (
    <div className="flex items-center gap-2 rounded-md border border-dashed bg-muted/60 px-3 py-2 text-sm text-muted-foreground">
      <CalendarClock className="size-4" />
      <span>
        Demo clock: the app treats <strong className="text-foreground">{formatLongDate(asOf)}</strong>{" "}
        as today so the sample data reads naturally. Unset <code>CRM_TODAY</code> to use the real date.
      </span>
    </div>
  );
}
