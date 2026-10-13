import { ApiError } from "@/lib/api";
import { cn } from "@/lib/utils";

/** The API's own message when it has one ("Route R1 already exists"), else a fallback. */
function errorMessage(error: unknown, fallback = "Something went wrong.") {
  return error instanceof ApiError ? error.message : fallback;
}

export function ErrorText({
  error,
  fallback,
  className,
}: {
  error: unknown;
  fallback?: string;
  className?: string;
}) {
  if (!error) {
    return null;
  }
  return (
    <p role="alert" className={cn("text-sm text-destructive", className)}>
      {errorMessage(error, fallback)}
    </p>
  );
}

export function Loading({ label = "Loading…" }: { label?: string }) {
  return (
    <p role="status" className="text-sm text-muted-foreground">
      {label}
    </p>
  );
}

/** The mono, upper-case caption the wireframes use above titles and numbers. */
export function Eyebrow({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <p
      className={cn(
        "font-mono text-[10px] font-medium tracking-[0.1em] text-muted-foreground uppercase",
        className,
      )}
    >
      {children}
    </p>
  );
}

/** A local-development invite link (D-18): nothing sends WhatsApp until Sprint 5. */
export function DevLink({ url, label = "open the link" }: { url: string | null; label?: string }) {
  if (!url) {
    return null;
  }
  return (
    <span className="text-xs text-muted-foreground">
      Nothing sends WhatsApp yet, so here is the link:{" "}
      <a href={url} className="underline" target="_blank" rel="noreferrer">
        {label}
      </a>
    </span>
  );
}
