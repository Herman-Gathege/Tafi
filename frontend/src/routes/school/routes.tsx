import { useQuery } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { DevLink, ErrorText, Eyebrow, Loading } from "@/components/ui/feedback";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import {
  addStop,
  addVehicle,
  createRoute,
  getCrew,
  getRoute,
  inviteCrew,
  listRoutes,
  listVehicles,
  removeCrewMember,
  removeRun,
  removeStop,
  reorderStops,
  setRun,
  updateRoute,
  updateVehicle,
  type CrewInvitation,
  type CrewMember,
  type MembershipRole,
  type RouteDetail,
  type Run,
  type RunDirection,
  type Vehicle,
} from "@/lib/api";
import { roleLabel } from "@/lib/labels";
import { schoolKeys, useSchoolMutation } from "@/lib/school-queries";
import { cn } from "@/lib/utils";

export function RoutesPage() {
  const [params, setParams] = useSearchParams();
  const selectedId = params.get("route");
  const routes = useQuery({ queryKey: schoolKeys.routes, queryFn: listRoutes });

  function select(routeId: string) {
    setParams(routeId ? { route: routeId } : {}, { replace: true });
  }

  return (
    <div className="flex flex-col gap-6">
      <header>
        <Eyebrow>Set-up</Eyebrow>
        <h1 className="mt-1 font-display text-3xl font-extrabold tracking-tight">Routes, vehicles &amp; crew</h1>
      </header>

      <section aria-labelledby="routes-heading" className="flex flex-col gap-3">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <h2 id="routes-heading" className="font-display text-xl font-bold">
            Routes
          </h2>
          <NewRoute onCreated={(route) => select(route.id)} />
        </div>
        {routes.isPending ? <Loading /> : null}
        <ErrorText error={routes.error} fallback="Could not load the routes." />
        {routes.data && routes.data.length === 0 ? (
          <p className="text-sm text-muted-foreground">No routes yet. Create the first one.</p>
        ) : null}
        <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {routes.data?.map((route) => (
            <li key={route.id}>
              <Link
                to={`?route=${route.id}`}
                replace
                aria-current={route.id === selectedId ? "true" : undefined}
                className={cn(
                  "block rounded-2xl border bg-card p-4 transition hover:border-brand",
                  route.id === selectedId ? "border-2 border-brand" : "border-border",
                )}
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <Eyebrow>{route.code}</Eyebrow>
                    <p className="mt-1 font-display text-lg font-bold">{route.name}</p>
                  </div>
                  {!route.is_active ? <Badge>Not running</Badge> : null}
                </div>
                <p className="mt-2 text-sm text-muted-foreground">
                  {route.stop_count} stop{route.stop_count === 1 ? "" : "s"}
                </p>
              </Link>
            </li>
          ))}
        </ul>
      </section>

      {selectedId ? <RoutePanel key={selectedId} routeId={selectedId} /> : null}

      <div className="grid items-start gap-6 lg:grid-cols-2">
        <VehiclesCard />
        <CrewCard />
      </div>
    </div>
  );
}

function NewRoute({ onCreated }: { onCreated: (route: RouteDetail) => void }) {
  const [open, setOpen] = useState(false);
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const create = useSchoolMutation(
    () => createRoute({ code, name }),
    (route) => {
      setOpen(false);
      setCode("");
      setName("");
      onCreated(route);
    },
  );

  if (!open) {
    return <Button onClick={() => setOpen(true)}>New route</Button>;
  }
  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        create.mutate(undefined);
      }}
      className="flex flex-wrap items-end gap-2"
    >
      <div className="flex w-24 flex-col gap-1.5">
        <Label htmlFor="route-code">Code</Label>
        <Input id="route-code" value={code} onChange={(e) => setCode(e.target.value)} placeholder="R1" required />
      </div>
      <div className="flex w-56 flex-col gap-1.5">
        <Label htmlFor="route-name">Area</Label>
        <Input id="route-name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Kileleshwa" required />
      </div>
      <Button type="submit" disabled={create.isPending}>
        {create.isPending ? "Saving…" : "Create"}
      </Button>
      <Button variant="ghost" onClick={() => setOpen(false)}>
        Cancel
      </Button>
      <ErrorText error={create.error} className="basis-full" />
    </form>
  );
}

// --- One route: stops and runs -------------------------------------------------------------

function RoutePanel({ routeId }: { routeId: string }) {
  const route = useQuery({ queryKey: schoolKeys.route(routeId), queryFn: () => getRoute(routeId) });
  const toggle = useSchoolMutation((is_active: boolean) => updateRoute(routeId, { is_active }));

  if (route.isPending) {
    return <Loading />;
  }
  if (!route.data) {
    return <ErrorText error={route.error} fallback="Could not load this route." />;
  }
  const detail = route.data;

  return (
    <Card>
      <CardHeader className="flex-row flex-wrap items-start justify-between gap-3">
        <div>
          <Eyebrow>{detail.code}</Eyebrow>
          <CardTitle className="text-xl">{detail.name}</CardTitle>
          <CardDescription>
            <Link to={`/app/children?route=${detail.id}`} className="underline">
              Children on this route
            </Link>
          </CardDescription>
        </div>
        <Button variant="ghost" size="sm" onClick={() => toggle.mutate(!detail.is_active)} disabled={toggle.isPending}>
          {detail.is_active ? "Stop running this route" : "Run this route again"}
        </Button>
      </CardHeader>
      <CardContent className="grid gap-6 lg:grid-cols-2">
        <StopsEditor route={detail} />
        <div className="flex flex-col gap-4">
          {(["morning", "afternoon"] as const).map((direction) => (
            <RunEditor
              key={direction}
              routeId={detail.id}
              direction={direction}
              run={detail.runs.find((run) => run.direction === direction) ?? null}
            />
          ))}
        </div>
        <ErrorText error={toggle.error} />
      </CardContent>
    </Card>
  );
}

function StopsEditor({ route }: { route: RouteDetail }) {
  const [name, setName] = useState("");
  const [landmark, setLandmark] = useState("");
  const add = useSchoolMutation(
    () => addStop(route.id, { name, landmark: landmark.trim() || null }),
    () => {
      setName("");
      setLandmark("");
    },
  );
  const reorder = useSchoolMutation((ids: string[]) => reorderStops(route.id, ids));
  const remove = useSchoolMutation(removeStop);

  function move(index: number, by: -1 | 1) {
    const ids = route.stops.map((stop) => stop.id);
    const target = index + by;
    [ids[index], ids[target]] = [ids[target], ids[index]];
    reorder.mutate(ids);
  }

  function onAdd(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    add.mutate(undefined);
  }

  return (
    <section aria-labelledby="stops-heading">
      <h3 id="stops-heading" className="mb-3 font-bold">
        Stops (morning order)
      </h3>
      {route.stops.length === 0 ? <p className="text-sm text-muted-foreground">No stops yet.</p> : null}
      <ol className="flex flex-col">
        {route.stops.map((stop, index) => (
          <li key={stop.id} className="flex items-center gap-3 border-b border-border/60 py-2 last:border-0">
            <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-muted font-mono text-xs">
              {stop.sequence}
            </span>
            <span className="flex-1">
              <span className="block text-sm font-semibold">{stop.name}</span>
              {stop.landmark ? <span className="block text-xs text-muted-foreground">{stop.landmark}</span> : null}
            </span>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => move(index, -1)}
              disabled={index === 0 || reorder.isPending}
              aria-label={`Move ${stop.name} earlier`}
            >
              ↑
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => move(index, 1)}
              disabled={index === route.stops.length - 1 || reorder.isPending}
              aria-label={`Move ${stop.name} later`}
            >
              ↓
            </Button>
            <Button size="sm" variant="ghost" onClick={() => remove.mutate(stop.id)} aria-label={`Remove ${stop.name}`}>
              Remove
            </Button>
          </li>
        ))}
      </ol>
      <ErrorText error={reorder.error ?? remove.error} className="mt-2" />
      <p className="mt-2 text-xs text-muted-foreground">The afternoon run visits the stops in reverse.</p>

      <form onSubmit={onAdd} className="mt-3 flex flex-col gap-2 rounded-lg bg-muted/60 p-3">
        <div className="grid gap-2 sm:grid-cols-2">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="stop-name">New stop</Label>
            <Input id="stop-name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Shell, Ngong Road" required />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="stop-landmark">Landmark (optional)</Label>
            <Input id="stop-landmark" value={landmark} onChange={(e) => setLandmark(e.target.value)} placeholder="Opposite the church" />
          </div>
        </div>
        <ErrorText error={add.error} />
        <div>
          <Button type="submit" size="sm" disabled={add.isPending}>
            {add.isPending ? "Adding…" : "Add at the end"}
          </Button>
        </div>
      </form>
    </section>
  );
}

function RunEditor({ routeId, direction, run }: { routeId: string; direction: RunDirection; run: Run | null }) {
  const crew = useQuery({ queryKey: schoolKeys.crew, queryFn: getCrew });
  const vehicles = useQuery({ queryKey: schoolKeys.vehicles, queryFn: listVehicles });
  const [time, setTime] = useState(run?.departure_time.slice(0, 5) ?? (direction === "morning" ? "06:30" : "16:10"));
  const [vehicleId, setVehicleId] = useState(run?.vehicle_id ?? "");
  const [driverId, setDriverId] = useState(run?.driver_membership_id ?? "");
  const [conductorId, setConductorId] = useState(run?.conductor_membership_id ?? "");
  const save = useSchoolMutation(() =>
    setRun(routeId, direction, {
      departure_time: time,
      vehicle_id: vehicleId || null,
      driver_membership_id: driverId,
      conductor_membership_id: conductorId || null,
    }),
  );
  const clear = useSchoolMutation(() => removeRun(routeId, direction), () => {
    setVehicleId("");
    setDriverId("");
    setConductorId("");
  });

  const drivers = crew.data?.members.filter((member) => member.role === "driver") ?? [];
  const conductors = crew.data?.members.filter((member) => member.role === "conductor") ?? [];
  const prefix = `${direction}-run`;

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        save.mutate(undefined);
      }}
      className="flex flex-col gap-3 rounded-xl border border-border p-4"
      aria-labelledby={`${prefix}-heading`}
    >
      <div className="flex items-center justify-between">
        <h3 id={`${prefix}-heading`} className="font-bold capitalize">
          {direction} run
        </h3>
        {run ? <Badge tone="safe">Set</Badge> : <Badge tone="brand">Not set</Badge>}
      </div>
      <div className="grid gap-2 sm:grid-cols-2">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor={`${prefix}-time`}>Leaves at</Label>
          <Input id={`${prefix}-time`} type="time" value={time} onChange={(e) => setTime(e.target.value)} required />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor={`${prefix}-vehicle`}>Vehicle</Label>
          <Select id={`${prefix}-vehicle`} value={vehicleId} onChange={(e) => setVehicleId(e.target.value)}>
            <option value="">Not chosen</option>
            {vehicles.data
              ?.filter((vehicle) => vehicle.is_active || vehicle.id === vehicleId)
              .map((vehicle) => (
                <option key={vehicle.id} value={vehicle.id}>
                  {vehicle.plate} ({vehicle.seats} seats)
                </option>
              ))}
          </Select>
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor={`${prefix}-driver`}>Driver (required)</Label>
          <Select id={`${prefix}-driver`} value={driverId} onChange={(e) => setDriverId(e.target.value)} required>
            <option value="">Choose a driver</option>
            {drivers.map((member) => (
              <option key={member.membership_id} value={member.membership_id}>
                {member.name}
              </option>
            ))}
          </Select>
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor={`${prefix}-conductor`}>Conductor (optional)</Label>
          <Select id={`${prefix}-conductor`} value={conductorId} onChange={(e) => setConductorId(e.target.value)}>
            <option value="">No conductor</option>
            {conductors.map((member) => (
              <option key={member.membership_id} value={member.membership_id}>
                {member.name}
              </option>
            ))}
          </Select>
        </div>
      </div>
      {crew.data && drivers.length === 0 ? (
        <p className="text-xs text-muted-foreground">Invite a driver below first.</p>
      ) : null}
      <ErrorText error={save.error ?? clear.error} />
      <div className="flex gap-2">
        <Button type="submit" size="sm" disabled={save.isPending || !driverId}>
          {save.isPending ? "Saving…" : "Save run"}
        </Button>
        {run ? (
          <Button size="sm" variant="ghost" onClick={() => clear.mutate(undefined)} disabled={clear.isPending}>
            Clear
          </Button>
        ) : null}
      </div>
    </form>
  );
}

// --- Vehicles ------------------------------------------------------------------------------

function VehiclesCard() {
  const vehicles = useQuery({ queryKey: schoolKeys.vehicles, queryFn: listVehicles });
  const [plate, setPlate] = useState("");
  const [seats, setSeats] = useState("26");
  const add = useSchoolMutation(
    () => addVehicle({ plate, seats: Number(seats) }),
    () => setPlate(""),
  );
  const toggle = useSchoolMutation((vehicle: Vehicle) => updateVehicle(vehicle.id, { is_active: !vehicle.is_active }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Vehicles</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {vehicles.isPending ? <Loading /> : null}
        <ErrorText error={vehicles.error ?? toggle.error} />
        {vehicles.data && vehicles.data.length === 0 ? <p className="text-sm text-muted-foreground">No vehicles yet.</p> : null}
        <ul className="flex flex-col divide-y divide-border">
          {vehicles.data?.map((vehicle) => (
            <li key={vehicle.id} className="flex items-center justify-between gap-2 py-2">
              <span className="text-sm">
                <span className="rounded-md bg-muted px-2 py-0.5 font-mono">{vehicle.plate}</span>{" "}
                <span className="text-muted-foreground">{vehicle.seats} seats</span>
              </span>
              <span className="flex items-center gap-2">
                {!vehicle.is_active ? <Badge>Out of service</Badge> : null}
                <Button size="sm" variant="ghost" onClick={() => toggle.mutate(vehicle)}>
                  {vehicle.is_active ? "Take out of service" : "Back in service"}
                </Button>
              </span>
            </li>
          ))}
        </ul>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            add.mutate(undefined);
          }}
          className="flex flex-wrap items-end gap-2"
        >
          <div className="flex w-36 flex-col gap-1.5">
            <Label htmlFor="plate">Number plate</Label>
            <Input id="plate" value={plate} onChange={(e) => setPlate(e.target.value)} placeholder="KDA 213A" required />
          </div>
          <div className="flex w-20 flex-col gap-1.5">
            <Label htmlFor="seats">Seats</Label>
            <Input id="seats" type="number" min={1} max={100} value={seats} onChange={(e) => setSeats(e.target.value)} required />
          </div>
          <Button type="submit" disabled={add.isPending}>
            {add.isPending ? "Adding…" : "Add vehicle"}
          </Button>
          <ErrorText error={add.error} className="basis-full" />
        </form>
      </CardContent>
    </Card>
  );
}

// --- Crew ----------------------------------------------------------------------------------

function CrewCard() {
  const crew = useQuery({ queryKey: schoolKeys.crew, queryFn: getCrew });
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<MembershipRole>("driver");
  const [sent, setSent] = useState<CrewInvitation | null>(null);
  const invite = useSchoolMutation(
    () => inviteCrew({ email, role }),
    (invitation) => {
      setSent(invitation);
      setEmail("");
    },
  );
  const remove = useSchoolMutation((member: CrewMember) => removeCrewMember(member.membership_id));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Crew</CardTitle>
        <CardDescription>
          Drivers and conductors sign in to the crew app. A vehicle can run with a driver alone.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {crew.isPending ? <Loading /> : null}
        <ErrorText error={crew.error ?? remove.error} />
        {crew.data && crew.data.members.length === 0 ? <p className="text-sm text-muted-foreground">No crew yet.</p> : null}
        <ul className="flex flex-col divide-y divide-border">
          {crew.data?.members.map((member) => (
            <li key={member.membership_id} className="flex items-center justify-between gap-2 py-2">
              <span>
                <span className="block text-sm font-semibold">{member.name}</span>
                <span className="block text-xs text-muted-foreground">{member.email}</span>
              </span>
              <span className="flex items-center gap-2">
                <Badge tone={member.role === "driver" ? "brand" : "muted"}>{roleLabel(member.role)}</Badge>
                <Button size="sm" variant="ghost" onClick={() => remove.mutate(member)} aria-label={`Remove ${member.name}`}>
                  Remove
                </Button>
              </span>
            </li>
          ))}
        </ul>
        {crew.data && crew.data.pending_invitations.length > 0 ? (
          <div>
            <Eyebrow>Invited, not joined yet</Eyebrow>
            <ul className="mt-1 text-sm text-muted-foreground">
              {crew.data.pending_invitations.map((invitation) => (
                <li key={invitation.id}>
                  {invitation.email} · {roleLabel(invitation.role)}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
        <form
          onSubmit={(event) => {
            event.preventDefault();
            invite.mutate(undefined);
          }}
          className="flex flex-wrap items-end gap-2"
        >
          <div className="flex min-w-48 flex-1 flex-col gap-1.5">
            <Label htmlFor="crew-email">Email</Label>
            <Input id="crew-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div className="flex w-36 flex-col gap-1.5">
            <Label htmlFor="crew-role">Role</Label>
            <Select id="crew-role" value={role} onChange={(e) => setRole(e.target.value as MembershipRole)}>
              <option value="driver">Driver</option>
              <option value="conductor">Conductor</option>
            </Select>
          </div>
          <Button type="submit" disabled={invite.isPending}>
            {invite.isPending ? "Sending…" : "Invite"}
          </Button>
          <ErrorText error={invite.error} className="basis-full" />
        </form>
        {sent ? (
          <p role="status" className="text-sm">
            Invitation for {sent.email} created. <DevLink url={sent.invite_url} label="open the invite link" />
          </p>
        ) : null}
      </CardContent>
    </Card>
  );
}
