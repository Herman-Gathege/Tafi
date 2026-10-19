import { useQuery } from "@tanstack/react-query";
import { ArrowRight, Inbox, Route as RouteIcon, Users, UserRound } from "lucide-react";
import { Link } from "react-router-dom";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorText } from "@/components/ui/feedback";
import { Skeleton } from "@/components/ui/skeleton";
import { getCrew, listRoutes, listStopChangeRequests, listStudents } from "@/lib/api";
import { schoolKeys } from "@/lib/school-queries";
import { useSession } from "@/lib/session";

/** The school admin's home: what is true about the school today, from the real APIs. */
export function DashboardPage() {
  const { school, user } = useSession();
  const children = useQuery({
    queryKey: schoolKeys.students({ status: "active" }),
    queryFn: () => listStudents({ status: "active" }),
  });
  const routes = useQuery({ queryKey: schoolKeys.routes, queryFn: listRoutes });
  const crew = useQuery({ queryKey: schoolKeys.crew, queryFn: getCrew });
  const requests = useQuery({
    queryKey: schoolKeys.stopRequests,
    queryFn: () => listStopChangeRequests("pending"),
  });

  const loading = children.isPending || routes.isPending || crew.isPending || requests.isPending;
  const counts = [
    {
      label: "Children",
      value: children.data?.length,
      hint: "active on transport",
      to: "/app/children",
      icon: Users,
    },
    {
      label: "Routes",
      value: routes.data?.length,
      hint: "with ordered stops",
      to: "/app/routes",
      icon: RouteIcon,
    },
    {
      label: "Crew",
      value: crew.data ? crew.data.members.length : undefined,
      hint: "drivers and conductors",
      to: "/app/routes",
      icon: UserRound,
    },
    {
      label: "Stop requests",
      value: requests.data?.length,
      hint: "waiting for you",
      to: "/app/requests",
      icon: Inbox,
    },
  ];

  return (
    <div className="flex flex-col gap-6">
      <div>
        <p className="font-mono text-[10px] font-medium tracking-[0.1em] text-muted-foreground uppercase">
          Today
        </p>
        <h1 className="font-display text-2xl font-bold tracking-tight">
          {user?.name ? `Hello, ${user.name.split(" ")[0]}` : "Hello"}
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {school?.organization_name ?? "Your school"} at a glance.
        </p>
      </div>

      <ErrorText
        error={children.error ?? routes.error ?? crew.error ?? requests.error}
        fallback="Could not load the dashboard."
      />

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {counts.map((card) => (
          <Link key={card.label} to={card.to} className="group">
            <Card className="h-full transition group-hover:border-primary">
              <CardHeader className="pb-2">
                <CardDescription className="flex items-center gap-2">
                  <card.icon className="size-4" />
                  {card.label}
                </CardDescription>
                {loading ? (
                  <Skeleton className="h-8 w-14" />
                ) : (
                  <CardTitle className="text-3xl tabular-nums">{card.value ?? 0}</CardTitle>
                )}
              </CardHeader>
              <CardContent>
                <p className="text-xs text-muted-foreground">{card.hint}</p>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Needs attention</CardTitle>
          <CardDescription>Guardians waiting on the school.</CardDescription>
        </CardHeader>
        <CardContent>
          {requests.isPending ? <Skeleton className="h-12 w-full" /> : null}
          {requests.data && requests.data.length === 0 ? (
            <p className="text-sm text-muted-foreground">Nothing is waiting. All caught up.</p>
          ) : null}
          {requests.data && requests.data.length > 0 ? (
            <ul className="flex flex-col divide-y divide-border">
              {requests.data.slice(0, 5).map((request) => (
                <li key={request.id} className="flex items-center justify-between gap-3 py-3">
                  <span className="text-sm">A guardian asked to change a stop</span>
                  <Link
                    to="/app/requests"
                    className="flex items-center gap-1 text-sm font-medium text-primary"
                  >
                    Review <ArrowRight className="size-4" />
                  </Link>
                </li>
              ))}
            </ul>
          ) : null}
        </CardContent>
      </Card>

      <div className="grid gap-3 sm:grid-cols-3">
        {[
          { to: "/app/children", label: "Children & guardians", hint: "Roster, links and consent" },
          { to: "/app/routes", label: "Routes & crew", hint: "Stops, vehicles and runs" },
          { to: "/app/requests", label: "Stop requests", hint: "Approve or decline" },
        ].map((link) => (
          <Link key={link.to} to={link.to}>
            <Card className="h-full transition hover:border-primary">
              <CardHeader>
                <CardTitle className="text-base">{link.label}</CardTitle>
                <CardDescription>{link.hint}</CardDescription>
              </CardHeader>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
