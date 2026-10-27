import { useQuery } from "@tanstack/react-query";
import { Bus, ShieldCheck, ShieldAlert } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorText } from "@/components/ui/feedback";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchParentMe } from "@/lib/api";
import { useSession } from "@/lib/session";

/** What a parent sees about their own children. Read-only for now (D-20). */
export function ParentHomePage() {
  const { user } = useSession();
  const me = useQuery({ queryKey: ["parent", "me"], queryFn: fetchParentMe });

  return (
    <div className="flex flex-col gap-5">
      <div>
        <p className="font-mono text-[10px] font-medium tracking-[0.1em] text-muted-foreground uppercase">
          {me.data?.school_name ?? "Your school"}
        </p>
        <h1 className="font-display text-2xl font-bold tracking-tight">
          {user?.name ? `Hello, ${user.name.split(" ")[0]}` : "Hello"}
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Your children's transport, in one place. WhatsApp messages carry the live updates.
        </p>
      </div>

      <ErrorText error={me.error} fallback="Could not load your family." />
      {me.isPending ? <Skeleton className="h-40 w-full" /> : null}

      {me.data ? (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {me.data.has_consent ? (
                  <ShieldCheck className="size-5 text-safe" />
                ) : (
                  <ShieldAlert className="size-5 text-destructive" />
                )}
                WhatsApp updates
              </CardTitle>
              <CardDescription>
                {me.data.has_consent
                  ? "You have agreed to receive updates on WhatsApp."
                  : "You have not confirmed your details yet, so no messages can be sent."}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm">
                Number: <span className="font-medium">{me.data.whatsapp_number}</span>
              </p>
            </CardContent>
          </Card>

          <div className="flex flex-col gap-3">
            {me.data.children.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No children are linked to this account yet. Ask the school to link them.
              </p>
            ) : null}
            {me.data.children.map((child) => (
              <Card key={child.student_id}>
                <CardHeader>
                  <CardTitle>
                    {child.first_name} {child.last_name}
                  </CardTitle>
                  <CardDescription>{child.grade ?? "Grade not set"}</CardDescription>
                </CardHeader>
                <CardContent className="flex flex-col gap-2 text-sm">
                  {child.route_code ? (
                    <p className="flex items-center gap-2">
                      <Bus className="size-4 text-muted-foreground" />
                      {child.route_code} · {child.route_name}
                    </p>
                  ) : (
                    <p className="text-muted-foreground">Not on a route yet.</p>
                  )}
                  {child.pickup_stop ? (
                    <p className="text-muted-foreground">
                      Picks up at {child.pickup_stop}
                      {child.dropoff_stop ? `, drops off at ${child.dropoff_stop}` : ""}
                    </p>
                  ) : null}
                </CardContent>
              </Card>
            ))}
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Stop requests</CardTitle>
              <CardDescription>Changes you have asked the school for.</CardDescription>
            </CardHeader>
            <CardContent>
              {me.data.stop_requests.length === 0 ? (
                <p className="text-sm text-muted-foreground">Nothing requested.</p>
              ) : (
                <ul className="flex flex-col divide-y divide-border">
                  {me.data.stop_requests.map((request) => (
                    <li key={request.id} className="flex items-center justify-between py-3">
                      <span className="text-sm">A stop change</span>
                      <Badge tone={request.status === "approved" ? "safe" : "muted"}>
                        {request.status}
                      </Badge>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
        </>
      ) : null}
    </div>
  );
}
