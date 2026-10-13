import type { SelectHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

/** A native select styled like Input: keyboard and screen-reader friendly for free. */
export function Select({ className, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={cn(
        "h-10 w-full rounded-md border border-input bg-card px-3 text-sm text-foreground",
        "disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    />
  );
}
