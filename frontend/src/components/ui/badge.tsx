import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export type BadgeTone = "safe" | "brand" | "muted" | "danger";

const tones: Record<BadgeTone, string> = {
  safe: "bg-safe-soft text-safe",
  brand: "bg-brand-soft text-foreground",
  muted: "bg-muted text-muted-foreground",
  danger: "bg-destructive/10 text-destructive",
};

/** A small status pill, as in the wireframes ("Opted in", "Invite sent"…). */
export function Badge({
  tone = "muted",
  className,
  ...props
}: HTMLAttributes<HTMLSpanElement> & { tone?: BadgeTone }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold whitespace-nowrap",
        tones[tone],
        className,
      )}
      {...props}
    />
  );
}
