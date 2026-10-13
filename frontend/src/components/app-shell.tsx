import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { endDevSession } from "@/lib/session";
import { cn } from "@/lib/utils";

const navigation = [
  { to: "/app", label: "Dashboard", end: true },
  { to: "/app/organizations", label: "Organizations", end: false },
];

export function AppShell() {
  const navigate = useNavigate();

  function signOut() {
    endDevSession();
    navigate("/", { replace: true });
  }

  return (
    <div className="flex min-h-dvh flex-col bg-background text-foreground">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:top-3 focus:left-3 focus:z-50 focus:rounded-md focus:bg-primary focus:px-4 focus:py-2 focus:text-sm focus:text-primary-foreground"
      >
        Skip to content
      </a>

      <header className="border-b border-border bg-card">
        <div className="mx-auto flex w-full max-w-5xl flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
          <NavLink to="/app" className="font-display text-lg font-bold tracking-tight">
            Tafi
            <span className="ml-2 text-xs font-medium text-muted-foreground">school portal</span>
          </NavLink>
          <div className="flex items-center gap-2">
            <nav aria-label="Main">
              <ul className="flex items-center gap-1 overflow-x-auto">
                {navigation.map((item) => (
                  <li key={item.to}>
                    <NavLink
                      to={item.to}
                      end={item.end}
                      className={({ isActive }) =>
                        cn(
                          "inline-flex h-9 items-center rounded-md px-3 text-sm font-medium transition",
                          isActive
                            ? "bg-primary text-primary-foreground"
                            : "text-muted-foreground hover:bg-muted hover:text-foreground",
                        )
                      }
                    >
                      {item.label}
                    </NavLink>
                  </li>
                ))}
              </ul>
            </nav>
            <button
              type="button"
              onClick={signOut}
              className="inline-flex h-9 items-center rounded-md px-3 text-sm font-medium text-muted-foreground transition hover:bg-muted hover:text-foreground"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      <p
        role="status"
        className="border-b border-border bg-brand-soft px-4 py-2 text-center text-xs text-foreground"
      >
        Development build — you are signed in with a demo session. Real accounts arrive in Sprint 2.
      </p>

      <main id="main" className="mx-auto w-full max-w-5xl flex-1 px-4 py-6">
        <Outlet />
      </main>

      <footer className="border-t border-border px-4 py-4 text-center text-xs text-muted-foreground">
        Tafi — MVP 1 in development. Nairobi, Kenya.
      </footer>
    </div>
  );
}
