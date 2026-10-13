import { NavLink, Outlet } from "react-router-dom";

import { cn } from "@/lib/utils";

const navigation = [
  { to: "/", label: "Home", end: true },
  { to: "/wireframes", label: "Wireframes", end: false },
];

export function PublicShell() {
  return (
    <div className="flex min-h-dvh flex-col bg-background text-foreground">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:top-3 focus:left-3 focus:z-50 focus:rounded-md focus:bg-primary focus:px-4 focus:py-2 focus:text-sm focus:text-primary-foreground"
      >
        Skip to content
      </a>

      <header className="sticky top-0 z-40 border-b border-border bg-card/95 backdrop-blur">
        <div className="mx-auto flex w-full max-w-5xl flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
          <NavLink to="/" className="font-display text-lg font-bold tracking-tight">
            Tafi
            <span className="ml-2 text-xs font-medium text-muted-foreground">school transport</span>
          </NavLink>
          <nav aria-label="Main">
            <ul className="flex items-center gap-1">
              {navigation.map((item) => (
                <li key={item.to}>
                  <NavLink
                    to={item.to}
                    end={item.end}
                    className={({ isActive }) =>
                      cn(
                        "inline-flex h-9 items-center rounded-md px-3 text-sm font-medium transition",
                        isActive
                          ? "bg-secondary text-secondary-foreground"
                          : "text-muted-foreground hover:bg-muted hover:text-foreground",
                      )
                    }
                  >
                    {item.label}
                  </NavLink>
                </li>
              ))}
              <li>
                <NavLink
                  to="/signin"
                  className="inline-flex h-9 items-center rounded-md bg-primary px-3 text-sm font-medium text-primary-foreground transition hover:opacity-90"
                >
                  Sign in
                </NavLink>
              </li>
            </ul>
          </nav>
        </div>
      </header>

      <main id="main" className="flex-1">
        <Outlet />
      </main>

      <footer className="border-t border-border px-4 py-6 text-center text-xs text-muted-foreground">
        <p>Tafi — parent safety for school transport. Nairobi, Kenya.</p>
        <p className="mt-1">In development. The wireframes on this site are a preview, not the finished product.</p>
      </footer>
    </div>
  );
}
