import { useQuery } from "@tanstack/react-query";
import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { listStopChangeRequests } from "@/lib/api";
import { schoolKeys } from "@/lib/school-queries";
import { useSession, useSignOut } from "@/lib/session";
import { cn } from "@/lib/utils";

export function AppShell() {
  const navigate = useNavigate();
  const signOut = useSignOut();
  const { user, school, isPlatformAdmin, crew } = useSession();
  const isSchoolAdmin = school?.role === "school_admin";

  // Shown as a count on the nav item, so requests are not missed.
  const pendingRequests = useQuery({
    queryKey: schoolKeys.stopRequests,
    queryFn: () => listStopChangeRequests("pending"),
    enabled: isSchoolAdmin,
  });
  const pendingCount = pendingRequests.data?.length ?? 0;

  const navigation = [
    { to: "/app", label: "Today", end: true, count: 0 },
    ...(crew ? [{ to: "/crew", label: "My trips", end: false, count: 0 }] : []),
    ...(isSchoolAdmin
      ? [
          { to: "/app/children", label: "Children & guardians", end: false, count: 0 },
          { to: "/app/routes", label: "Routes & crew", end: false, count: 0 },
          { to: "/app/requests", label: "Stop requests", end: false, count: pendingCount },
        ]
      : []),
    ...(isPlatformAdmin ? [{ to: "/app/admin", label: "Platform admin", end: false, count: 0 }] : []),
  ];

  function onSignOut() {
    signOut.mutate(undefined, { onSettled: () => navigate("/", { replace: true }) });
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
        <div className="mx-auto flex w-full max-w-6xl flex-col gap-3 px-4 py-3 lg:flex-row lg:items-center lg:justify-between">
          <NavLink to="/app" className="font-display text-lg font-bold tracking-tight">
            Tafi
            <span className="ml-2 text-xs font-medium text-muted-foreground">
              {school ? school.organization_name : "school portal"}
            </span>
          </NavLink>
          <div className="flex flex-wrap items-center gap-2">
            <nav aria-label="Main" className="max-w-full overflow-x-auto">
              <ul className="flex items-center gap-1">
                {navigation.map((item) => (
                  <li key={item.to}>
                    <NavLink
                      to={item.to}
                      end={item.end}
                      className={({ isActive }) =>
                        cn(
                          "inline-flex h-9 items-center gap-2 rounded-md px-3 text-sm font-medium whitespace-nowrap transition",
                          isActive
                            ? "bg-primary text-primary-foreground"
                            : "text-muted-foreground hover:bg-muted hover:text-foreground",
                        )
                      }
                    >
                      {item.label}
                      {item.count > 0 ? (
                        <span className="rounded-full bg-foreground px-1.5 text-xs text-background">
                          {item.count}
                          <span className="sr-only"> waiting</span>
                        </span>
                      ) : null}
                    </NavLink>
                  </li>
                ))}
              </ul>
            </nav>
            <span className="hidden text-sm text-muted-foreground sm:inline">{user?.name ?? ""}</span>
            <button
              type="button"
              onClick={onSignOut}
              disabled={signOut.isPending}
              className="inline-flex h-9 items-center rounded-md px-3 text-sm font-medium text-muted-foreground transition hover:bg-muted hover:text-foreground"
            >
              {signOut.isPending ? "Signing out…" : "Sign out"}
            </button>
          </div>
        </div>
      </header>

      <p
        role="status"
        className="border-b border-border bg-brand-soft px-4 py-2 text-center text-xs text-foreground"
      >
        Development build — WhatsApp delivery arrives in Sprint 5, so invite links are shown on screen.
      </p>

      <main id="main" className="mx-auto w-full max-w-6xl flex-1 px-4 py-6">
        <Outlet />
      </main>

      <footer className="border-t border-border px-4 py-4 text-center text-xs text-muted-foreground">
        Tafi — MVP 1 in development. Nairobi, Kenya.
      </footer>
    </div>
  );
}
