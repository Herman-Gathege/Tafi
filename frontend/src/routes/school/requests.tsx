import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ErrorText, Eyebrow, Loading } from "@/components/ui/feedback";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import {
  approveStopChange,
  declineStopChange,
  getRoute,
  listStopChangeRequests,
  type StopChangeRequest,
} from "@/lib/api";
import { fullName } from "@/lib/labels";
import { schoolKeys, useSchoolMutation } from "@/lib/school-queries";

export function StopRequestsPage() {
  const requests = useQuery({
    queryKey: schoolKeys.stopRequests,
    queryFn: () => listStopChangeRequests("pending"),
  });

  return (
    <div className="flex flex-col gap-6">
      <header>
        <Eyebrow>From guardians</Eyebrow>
        <h1 className="mt-1 font-display text-3xl font-extrabold tracking-tight">Stop change requests</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Guardians can ask for a different stop from their registration link. The school decides.
        </p>
      </header>
      {requests.isPending ? <Loading /> : null}
      <ErrorText error={requests.error} fallback="Could not load the requests." />
      {requests.data && requests.data.length === 0 ? (
        <p className="text-sm text-muted-foreground">No requests waiting.</p>
      ) : null}
      <ul className="flex flex-col gap-4">
        {requests.data?.map((request) => (
          <li key={request.id}>
            <RequestCard request={request} />
          </li>
        ))}
      </ul>
    </div>
  );
}

function RequestCard({ request }: { request: StopChangeRequest }) {
  const current = request.current_route;
  const requestedStopId = request.requested_stop?.id ?? "";
  const [pickup, setPickup] = useState(current?.pickup_stop ? requestedStopId || current.pickup_stop.id : "");
  const [dropoff, setDropoff] = useState(current?.dropoff_stop ? requestedStopId || current.dropoff_stop.id : "");
  const route = useQuery({
    queryKey: schoolKeys.route(current?.route_id ?? ""),
    queryFn: () => getRoute(current?.route_id ?? ""),
    enabled: current !== null,
  });
  const approve = useSchoolMutation(() =>
    approveStopChange(request.id, {
      route_id: current?.route_id ?? "",
      pickup_stop_id: pickup || null,
      dropoff_stop_id: dropoff || null,
    }),
  );
  const decline = useSchoolMutation(() => declineStopChange(request.id));
  const prefix = `request-${request.id}`;

  return (
    <Card className="flex flex-col gap-4 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="font-display text-lg font-bold">
            <Link to={`/app/children?child=${request.student.id}`} className="hover:underline">
              {fullName(request.student)}
            </Link>
          </p>
          <p className="text-sm text-muted-foreground">
            Asked by {request.guardian_name} on {new Date(request.created_at).toLocaleDateString("en-KE")}
          </p>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div className="rounded-xl bg-muted p-3">
          <Eyebrow>Now</Eyebrow>
          <p className="mt-1 text-sm">
            {current
              ? `${current.route_code} · pickup ${current.pickup_stop?.name ?? "none"}, drop-off ${current.dropoff_stop?.name ?? "none"}`
              : "Not on a route"}
          </p>
        </div>
        <div className="rounded-xl bg-brand-soft p-3">
          <Eyebrow>Asking for</Eyebrow>
          <p className="mt-1 text-sm font-semibold">
            {request.requested_stop ? request.requested_stop.name : `“${request.requested_location ?? ""}”`}
          </p>
          {!request.requested_stop ? (
            <p className="mt-1 text-xs text-muted-foreground">
              A place, not a stop on the route. Add it as a stop on the route first if you agree.
            </p>
          ) : null}
        </div>
      </div>

      {current && route.data ? (
        <div className="grid gap-2 sm:grid-cols-2">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor={`${prefix}-pickup`}>New pickup</Label>
            <Select id={`${prefix}-pickup`} value={pickup} onChange={(e) => setPickup(e.target.value)}>
              <option value="">None</option>
              {route.data.stops.map((stop) => (
                <option key={stop.id} value={stop.id}>
                  {stop.sequence}. {stop.name}
                </option>
              ))}
            </Select>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor={`${prefix}-dropoff`}>New drop-off</Label>
            <Select id={`${prefix}-dropoff`} value={dropoff} onChange={(e) => setDropoff(e.target.value)}>
              <option value="">None</option>
              {route.data.stops.map((stop) => (
                <option key={stop.id} value={stop.id}>
                  {stop.sequence}. {stop.name}
                </option>
              ))}
            </Select>
          </div>
        </div>
      ) : null}
      {!current ? (
        <p className="text-sm text-muted-foreground">
          Put the child on a route first, from their{" "}
          <Link to={`/app/children?child=${request.student.id}`} className="underline">
            page
          </Link>
          , then approve here.
        </p>
      ) : null}

      <ErrorText error={approve.error ?? decline.error} />
      <div className="flex gap-2">
        <Button
          onClick={() => approve.mutate(undefined)}
          disabled={!current || (!pickup && !dropoff) || approve.isPending}
        >
          {approve.isPending ? "Saving…" : "Approve"}
        </Button>
        <Button variant="ghost" onClick={() => decline.mutate(undefined)} disabled={decline.isPending}>
          Decline
        </Button>
      </div>
    </Card>
  );
}
