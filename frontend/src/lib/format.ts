// Small date and text helpers shared by components.

import { differenceInCalendarDays, format, parseISO } from "date-fns";

export function formatDate(iso: string | null | undefined, pattern = "MMM d"): string {
  return iso ? format(parseISO(iso), pattern) : "—";
}

export function formatLongDate(iso: string): string {
  return format(parseISO(iso), "EEEE, MMMM d, yyyy");
}

/** Human phrase for a follow-up date relative to the app's "today". */
export function describeDueDate(iso: string | null, today: string): string {
  if (!iso) return "No date";
  const days = differenceInCalendarDays(parseISO(iso), parseISO(today));
  if (days < -1) return `${-days} days overdue`;
  if (days === -1) return "1 day overdue";
  if (days === 0) return "Due today";
  if (days === 1) return "Due tomorrow";
  return `Due in ${days} days`;
}

export function describeDaysAgo(days: number | null): string {
  if (days === null) return "No interactions yet";
  if (days === 0) return "Last touch today";
  if (days === 1) return "Last touch yesterday";
  return `Last touch ${days} days ago`;
}

export function firstName(fullName: string): string {
  return fullName.split(" ")[0];
}
