import { Outlet, useNavigate } from "react-router-dom";

import { useSession, useSignOut } from "@/lib/session";

/** The parent's own shell: their family, not the school's operations. */
export function ParentShell() {
  const navigate = useNavigate();
  const signOut = useSignOut();
  const { user } = useSession();

  return (
    <div className="flex min-h-dvh flex-col bg-background text-foreground">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:top-3 focus:left-3 focus:z-50 focus:rounded-md focus:bg-primary focus:px-4 focus:py-2 focus:text-sm focus:text-primary-foreground"
      >
        Skip to content
      </a>
      <header className="border-b border-border bg-card">
        <div className="mx-auto flex w-full max-w-3xl items-center justify-between gap-3 px-4 py-3">
          <p className="font-display text-lg font-bold tracking-tight">
            Tafi <span className="text-xs font-medium text-muted-foreground">family</span>
          </p>
          <div className="flex items-center gap-3">
            <span className="hidden text-sm text-muted-foreground sm:inline">{user?.name ?? ""}</span>
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
      <main id="main" className="mx-auto w-full max-w-3xl flex-1 px-4 py-6">
        <Outlet />
      </main>
      <footer className="border-t border-border px-4 py-4 text-center text-xs text-muted-foreground">
        Tafi — parent safety for school transport. Nairobi, Kenya.
      </footer>
    </div>
  );
}
