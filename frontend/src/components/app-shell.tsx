import { useQuery } from "@tanstack/react-query";
import { Bus, Inbox, LayoutDashboard, LogOut, Route as RouteIcon, Shield, Users } from "lucide-react";
import { Navigate, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuBadge,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarTrigger,
  useSidebar,
} from "@/components/ui/sidebar";
import { listStopChangeRequests } from "@/lib/api";
import { roleHome } from "@/lib/roles";
import { schoolKeys } from "@/lib/school-queries";
import { useSession, useSignOut } from "@/lib/session";

interface NavItem {
  to: string;
  label: string;
  icon: typeof LayoutDashboard;
  end?: boolean;
  count?: number;
}

export function AppShell() {
  const navigate = useNavigate();
  const location = useLocation();
  const signOut = useSignOut();
  const { session, user, school, isPlatformAdmin, crew } = useSession();
  const isSchoolAdmin = !isPlatformAdmin && school?.role === "school_admin";

  const pendingRequests = useQuery({
    queryKey: schoolKeys.stopRequests,
    queryFn: () => listStopChangeRequests("pending"),
    enabled: isSchoolAdmin,
  });
  const pendingCount = pendingRequests.data?.length ?? 0;

  // Keep non-school users out of the school-only Today screen.
  if (session && location.pathname === "/app" && !isSchoolAdmin) {
    const home = roleHome(session);
    if (home !== "/app") {
      return <Navigate to={home} replace />;
    }
  }

  const items: NavItem[] = [
    ...(isSchoolAdmin ? [{ to: "/app", label: "Today", icon: LayoutDashboard, end: true }] : []),
    ...(crew && !isPlatformAdmin ? [{ to: "/crew", label: "My trips", icon: Bus }] : []),
    ...(isSchoolAdmin
      ? [
          { to: "/app/children", label: "Children & guardians", icon: Users },
          { to: "/app/routes", label: "Routes & crew", icon: RouteIcon },
          { to: "/app/requests", label: "Stop requests", icon: Inbox, count: pendingCount },
        ]
      : []),
    ...(isPlatformAdmin ? [{ to: "/app/admin", label: "Platform admin", icon: Shield }] : []),
  ];

  const isActive = (item: NavItem) =>
    item.end ? location.pathname === item.to : location.pathname.startsWith(item.to);

  return (
    <SidebarProvider>
      <Sidebar>
        <SidebarHeader>
          <div className="flex items-center gap-2 px-2 py-1">
            <span className="font-display text-lg font-bold tracking-tight">Tafi</span>
            <span className="truncate text-xs text-muted-foreground">
              {isPlatformAdmin ? "Tafi platform" : (school?.organization_name ?? "School portal")}
            </span>
          </div>
        </SidebarHeader>
        <SidebarContent>
          <SidebarGroup>
            <SidebarGroupLabel>{isSchoolAdmin ? "School" : "Platform"}</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarNav items={items} isActive={isActive} />
            </SidebarGroupContent>
          </SidebarGroup>
        </SidebarContent>
        <SidebarFooter>
          <div className="flex flex-col gap-2 px-2 py-1">
            <p className="truncate text-sm font-medium">{user?.name ?? ""}</p>
            <button
              type="button"
              onClick={() =>
                signOut.mutate(undefined, { onSettled: () => navigate("/", { replace: true }) })
              }
              className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
            >
              <LogOut className="size-4" />
              Sign out
            </button>
          </div>
        </SidebarFooter>
      </Sidebar>

      <SidebarInset>
        <header className="flex h-14 items-center gap-3 border-b border-border px-3">
          <SidebarTrigger />
          <span className="font-medium">
            {isPlatformAdmin ? "Tafi platform" : (school?.organization_name ?? "Tafi")}
          </span>
        </header>
        <p
          role="status"
          className="border-b border-border bg-brand-soft px-4 py-2 text-center text-xs"
        >
          Development build — WhatsApp delivery arrives in Sprint 5.
        </p>
        <main id="main" className="flex-1 p-4 sm:p-6">
          <Outlet />
        </main>
      </SidebarInset>
    </SidebarProvider>
  );
}

function SidebarNav({
  items,
  isActive,
}: {
  items: NavItem[];
  isActive: (item: NavItem) => boolean;
}) {
  const { isMobile, setOpenMobile } = useSidebar();

  return (
    <SidebarMenu>
      {items.map((item) => (
        <SidebarMenuItem key={item.to}>
          <SidebarMenuButton asChild isActive={isActive(item)}>
            <NavLink
              to={item.to}
              end={item.end}
              onClick={() => {
                if (isMobile) {
                  setOpenMobile(false);
                }
              }}
            >
              <item.icon />
              <span>{item.label}</span>
            </NavLink>
          </SidebarMenuButton>
          {item.count ? <SidebarMenuBadge>{item.count}</SidebarMenuBadge> : null}
        </SidebarMenuItem>
      ))}
    </SidebarMenu>
  );
}
