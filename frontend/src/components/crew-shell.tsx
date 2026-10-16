import { Outlet, useNavigate } from "react-router-dom";

import { useSession, useSignOut } from "@/lib/session";

/** The crew app's own shell: no school menu, just their trips (wireframe 5). */
export function CrewShell() {
  const navigate = useNavigate();
  const signOut = useSignOut();
  const { user, crew } = useSession();

  return (
    <div className="flex min-h-dvh flex-col bg-background text-foreground">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:top-3 focus:left-3 focus:z-50 focus:rounded-md focus:bg-primary focus:px-4 focus:py-2 focus:text-sm focus:text-primary-foreground"
      >
        Skip to content
      </a>
      <header className="border-b border-border bg-card">
        <div className="mx-auto flex w-full max-w-2xl items-center justify-between gap-3 px-4 py-3">
          <p className="font-display text-lg font-bold tracking-tight">
            Tafi <span className="text-xs font-medium text-muted-foreground">crew</span>
          </p>
          <div className="flex items-center gap-3">
            <span className="hidden text-sm text-muted-foreground sm:inline">
              {user?.name ?? ""}
              {crew ? ` · ${crew.role}` : ""}
            </span>
            <button
              type="button"
              onClick={() =>
                signOut.mutate(undefined, { onSettled: () => navigate("/", { replace: true }) })
              }
              className="text-sm font-medium text-muted-foreground underline"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>
      <p role="status" className="border-b border-border bg-brand-soft px-4 py-2 text-center text-xs">
        Development build — the school is not sent WhatsApp messages yet (Sprint 5).
      </p>
      <main id="main" className="flex-1">
        <Outlet />
      </main>
    </div>
  );
}
