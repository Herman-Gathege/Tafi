import { useQuery } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { buttonStyles } from "@/components/ui/button-styles";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { DevLink, ErrorText, Eyebrow, Loading } from "@/components/ui/feedback";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import {
  addEmergencyContact,
  addGuardianToStudent,
  createStudent,
  getRoute,
  getStudent,
  invitePendingGuardians,
  inviteGuardian,
  listRoutes,
  listStudents,
  recordConsent,
  removeEmergencyContact,
  removeGuardianLink,
  removeStudentRoute,
  setStudentRoute,
  updateGuardianLink,
  updateStudent,
  type GuardianInviteCreated,
  type GuardianRelationship,
  type StudentDetail,
  type StudentStatus,
} from "@/lib/api";
import {
  formatPhone,
  fullName,
  initials,
  relationshipLabel,
  relationships,
  routeLabel,
  whatsappStatus,
} from "@/lib/labels";
import { schoolKeys, useSchoolMutation } from "@/lib/school-queries";
import { cn } from "@/lib/utils";
import { ImportRoster } from "@/routes/school/import-roster";

export function ChildrenPage() {
  const [params, setParams] = useSearchParams();
  const selectedId = params.get("child");
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState<{ q: string; status: StudentStatus | ""; route_id: string }>({
    q: "",
    status: "active",
    route_id: params.get("route") ?? "",
  });
  const [adding, setAdding] = useState(false);
  const [importing, setImporting] = useState(false);

  const students = useQuery({
    queryKey: schoolKeys.students(filters),
    queryFn: () =>
      listStudents({
        q: filters.q || undefined,
        status: filters.status || undefined,
        route_id: filters.route_id || undefined,
      }),
  });
  const routes = useQuery({ queryKey: schoolKeys.routes, queryFn: listRoutes });

  function onSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFilters((current) => ({ ...current, q: search.trim() }));
  }

  function select(studentId: string | null) {
    const next = new URLSearchParams(params);
    if (studentId) {
      next.set("child", studentId);
    } else {
      next.delete("child");
    }
    setParams(next, { replace: true });
  }

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <Eyebrow>Riders</Eyebrow>
          <h1 className="mt-1 font-display text-3xl font-extrabold tracking-tight">Children &amp; guardians</h1>
        </div>
        <div className="flex flex-wrap gap-2">
          <InvitePending />
          <Button variant="secondary" onClick={() => setImporting((open) => !open)} aria-expanded={importing}>
            Import spreadsheet
          </Button>
          <Button onClick={() => setAdding((open) => !open)} aria-expanded={adding}>
            {adding ? "Close" : "Add child"}
          </Button>
        </div>
      </header>

      {importing ? <ImportRoster onDone={() => setImporting(false)} /> : null}

      {adding ? (
        <AddChild
          onAdded={(child) => {
            setAdding(false);
            select(child.id);
          }}
        />
      ) : null}

      <form onSubmit={onSearch} className="flex flex-wrap items-end gap-3">
        <div className="flex min-w-60 flex-1 flex-col gap-1.5">
          <Label htmlFor="search">Search</Label>
          <Input
            id="search"
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Child, guardian or phone number"
          />
        </div>
        <div className="flex w-44 flex-col gap-1.5">
          <Label htmlFor="route-filter">Route</Label>
          <Select
            id="route-filter"
            value={filters.route_id}
            onChange={(event) => setFilters((current) => ({ ...current, route_id: event.target.value }))}
          >
            <option value="">All routes</option>
            {routes.data?.map((route) => (
              <option key={route.id} value={route.id}>
                {route.code} · {route.name}
              </option>
            ))}
          </Select>
        </div>
        <div className="flex w-36 flex-col gap-1.5">
          <Label htmlFor="status-filter">Status</Label>
          <Select
            id="status-filter"
            value={filters.status}
            onChange={(event) =>
              setFilters((current) => ({ ...current, status: event.target.value as StudentStatus | "" }))
            }
          >
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="">Everyone</option>
          </Select>
        </div>
        <Button type="submit" variant="secondary">
          Search
        </Button>
      </form>

      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_380px]">
        <Card className="overflow-hidden">
          {students.isPending ? (
            <div className="p-5">
              <Loading />
            </div>
          ) : null}
          <ErrorText error={students.error} fallback="Could not load the children." className="p-5" />
          {students.data && students.data.length === 0 ? (
            <p className="p-5 text-sm text-muted-foreground">
              {filters.q || filters.route_id ? "No child matches." : "No children yet. Add the first one above."}
            </p>
          ) : null}
          {students.data && students.data.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[640px] text-sm">
                <thead>
                  <tr className="border-b border-border text-left font-mono text-[10px] tracking-[0.1em] text-muted-foreground uppercase">
                    <th className="px-4 py-3 font-medium">Child</th>
                    <th className="px-4 py-3 font-medium">Route · stop</th>
                    <th className="px-4 py-3 font-medium">Guardian</th>
                    <th className="px-4 py-3 font-medium">WhatsApp</th>
                  </tr>
                </thead>
                <tbody>
                  {students.data.map((student) => {
                    const primary = student.guardians.find((guardian) => guardian.is_primary) ?? student.guardians[0];
                    const status = primary ? whatsappStatus(primary) : null;
                    return (
                      <tr
                        key={student.id}
                        className={cn(
                          "border-b border-border/60 last:border-0",
                          student.id === selectedId && "bg-brand-soft/60",
                        )}
                      >
                        <td className="px-4 py-3">
                          <Link
                            to={`?child=${student.id}`}
                            replace
                            className="flex items-center gap-3 rounded-md focus-visible:outline-offset-4"
                          >
                            <span
                              aria-hidden
                              className="flex size-9 shrink-0 items-center justify-center rounded-full bg-muted text-xs font-bold text-muted-foreground"
                            >
                              {initials(student)}
                            </span>
                            <span>
                              <span className="block font-semibold">{fullName(student)}</span>
                              <span className="block text-xs text-muted-foreground">
                                {student.grade ?? "No class set"}
                                {student.status === "inactive" ? " · inactive" : ""}
                              </span>
                            </span>
                          </Link>
                        </td>
                        <td className="px-4 py-3">{routeLabel(student.route)}</td>
                        <td className="px-4 py-3">
                          {primary ? (
                            <>
                              <span className="block">{primary.full_name}</span>
                              <span className="block font-mono text-xs text-muted-foreground">
                                {formatPhone(primary.whatsapp_number)}
                              </span>
                            </>
                          ) : (
                            <span className="text-muted-foreground">No guardian</span>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          {status ? <Badge tone={status.tone}>{status.label}</Badge> : null}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : null}
        </Card>

        {selectedId ? <ChildPanel key={selectedId} studentId={selectedId} onClose={() => select(null)} /> : null}
      </div>
    </div>
  );
}

// --- Invite everyone still to confirm --------------------------------------------------------

function InvitePending() {
  const [sent, setSent] = useState<GuardianInviteCreated[] | null>(null);
  const invite = useSchoolMutation(invitePendingGuardians, setSent);

  return (
    <div className="flex flex-col items-end gap-1">
      <Button variant="secondary" onClick={() => invite.mutate(undefined)} disabled={invite.isPending}>
        {invite.isPending ? "Sending…" : "Send WhatsApp invites"}
      </Button>
      <ErrorText error={invite.error} />
      {sent ? (
        <div role="status" className="max-w-sm text-right text-xs text-muted-foreground">
          {sent.length === 0 ? (
            "Every guardian has confirmed already."
          ) : (
            <>
              {sent.length} link{sent.length === 1 ? "" : "s"} created.
              {sent.some((item) => item.invite_url) ? (
                <ul className="mt-1 flex flex-col gap-0.5">
                  {sent.map((item) =>
                    item.invite_url ? (
                      <li key={item.guardian_id}>
                        <a href={item.invite_url} target="_blank" rel="noreferrer" className="underline">
                          {item.full_name}
                        </a>
                      </li>
                    ) : null,
                  )}
                </ul>
              ) : null}
            </>
          )}
        </div>
      ) : null}
    </div>
  );
}

// --- Add a child ---------------------------------------------------------------------------

function AddChild({ onAdded }: { onAdded: (child: StudentDetail) => void }) {
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    grade: "",
    guardian_name: "",
    whatsapp_number: "",
    relationship: "mother" as GuardianRelationship,
  });
  const create = useSchoolMutation(createStudent, onAdded);

  function update(field: keyof typeof form, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    create.mutate({
      first_name: form.first_name,
      last_name: form.last_name,
      grade: form.grade.trim() || null,
      guardians: [
        {
          full_name: form.guardian_name,
          whatsapp_number: form.whatsapp_number,
          relationship: form.relationship,
          is_primary: true,
        },
      ],
    });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Add a child</CardTitle>
        <CardDescription>
          Every child needs at least one guardian. They get a WhatsApp link to confirm their details and agree
          to updates.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} className="grid gap-4 sm:grid-cols-3">
          <Field id="first_name" label="First name">
            <Input id="first_name" value={form.first_name} onChange={(e) => update("first_name", e.target.value)} required />
          </Field>
          <Field id="last_name" label="Last name">
            <Input id="last_name" value={form.last_name} onChange={(e) => update("last_name", e.target.value)} required />
          </Field>
          <Field id="grade" label="Class (optional)">
            <Input id="grade" value={form.grade} onChange={(e) => update("grade", e.target.value)} placeholder="Grade 4" />
          </Field>
          <Field id="guardian_name" label="Guardian's name">
            <Input
              id="guardian_name"
              value={form.guardian_name}
              onChange={(e) => update("guardian_name", e.target.value)}
              required
            />
          </Field>
          <Field id="whatsapp_number" label="Guardian's WhatsApp number">
            <Input
              id="whatsapp_number"
              type="tel"
              inputMode="tel"
              value={form.whatsapp_number}
              onChange={(e) => update("whatsapp_number", e.target.value)}
              placeholder="0712 345 678"
              required
            />
          </Field>
          <Field id="relationship" label="Relationship">
            <Select
              id="relationship"
              value={form.relationship}
              onChange={(e) => update("relationship", e.target.value)}
            >
              {relationships.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </Select>
          </Field>
          <div className="flex flex-col gap-2 sm:col-span-3">
            <ErrorText error={create.error} fallback="Could not add the child." />
            <div>
              <Button type="submit" disabled={create.isPending}>
                {create.isPending ? "Saving…" : "Add child"}
              </Button>
            </div>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

function Field({ id, label, children }: { id: string; label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor={id}>{label}</Label>
      {children}
    </div>
  );
}

// --- One child -----------------------------------------------------------------------------

function ChildPanel({ studentId, onClose }: { studentId: string; onClose: () => void }) {
  const student = useQuery({ queryKey: schoolKeys.student(studentId), queryFn: () => getStudent(studentId) });
  const setStatus = useSchoolMutation((status: StudentStatus) => updateStudent(studentId, { status }));

  if (student.isPending) {
    return (
      <Card className="p-5">
        <Loading />
      </Card>
    );
  }
  if (!student.data) {
    return (
      <Card className="p-5">
        <ErrorText error={student.error} fallback="Could not load this child." />
      </Card>
    );
  }
  const child = student.data;

  return (
    <Card aria-labelledby="child-heading" className="flex flex-col gap-5 p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <span
            aria-hidden
            className="flex size-14 items-center justify-center rounded-2xl bg-muted font-display text-lg font-bold text-muted-foreground"
          >
            {initials(child)}
          </span>
          <div>
            <h2 id="child-heading" className="font-display text-xl font-bold">
              {fullName(child)}
            </h2>
            <p className="text-sm text-muted-foreground">
              {child.grade ?? "No class set"} · {routeLabel(child.route)}
            </p>
          </div>
        </div>
        <Button variant="ghost" size="sm" onClick={onClose} aria-label="Close">
          ✕
        </Button>
      </div>

      {child.status === "inactive" ? (
        <p className="rounded-lg bg-muted p-3 text-sm">This child is inactive and not on school transport.</p>
      ) : (
        <RouteSection child={child} />
      )}
      <GuardiansSection child={child} />
      <EmergencySection child={child} />

      <div className="border-t border-border pt-4">
        {child.status === "active" ? (
          <Button variant="ghost" size="sm" onClick={() => setStatus.mutate("inactive")} disabled={setStatus.isPending}>
            Mark inactive (left transport)
          </Button>
        ) : (
          <Button variant="secondary" size="sm" onClick={() => setStatus.mutate("active")} disabled={setStatus.isPending}>
            Make active again
          </Button>
        )}
        <ErrorText error={setStatus.error} className="mt-2" />
      </div>
    </Card>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return <h3 className="mb-2 text-sm font-bold">{children}</h3>;
}

function RouteSection({ child }: { child: StudentDetail }) {
  const [editing, setEditing] = useState(false);
  const [routeId, setRouteId] = useState(child.route?.route_id ?? "");
  const [pickup, setPickup] = useState(child.route?.pickup_stop?.id ?? "");
  const [dropoff, setDropoff] = useState(child.route?.dropoff_stop?.id ?? "");
  const routes = useQuery({ queryKey: schoolKeys.routes, queryFn: listRoutes, enabled: editing });
  const route = useQuery({
    queryKey: schoolKeys.route(routeId),
    queryFn: () => getRoute(routeId),
    enabled: editing && routeId !== "",
  });
  const save = useSchoolMutation(
    () => setStudentRoute(child.id, { route_id: routeId, pickup_stop_id: pickup || null, dropoff_stop_id: dropoff || null }),
    () => setEditing(false),
  );
  const remove = useSchoolMutation(() => removeStudentRoute(child.id));

  return (
    <section>
      <SectionTitle>School transport</SectionTitle>
      {child.route && !editing ? (
        <div className="grid grid-cols-2 gap-2">
          <StopTile label="Morning pickup" value={child.route.pickup_stop?.name} />
          <StopTile label="Afternoon drop-off" value={child.route.dropoff_stop?.name} />
        </div>
      ) : null}
      {!child.route && !editing ? <p className="text-sm text-muted-foreground">Not on a route yet.</p> : null}

      {editing ? (
        <form
          onSubmit={(event) => {
            event.preventDefault();
            save.mutate(undefined);
          }}
          className="flex flex-col gap-3 rounded-lg bg-muted/60 p-3"
        >
          <Field id="assign-route" label="Route">
            <Select
              id="assign-route"
              value={routeId}
              onChange={(event) => {
                setRouteId(event.target.value);
                setPickup("");
                setDropoff("");
              }}
              required
            >
              <option value="">Choose a route</option>
              {routes.data
                ?.filter((item) => item.is_active)
                .map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.code} · {item.name}
                  </option>
                ))}
            </Select>
          </Field>
          {routeId && route.data ? (
            route.data.stops.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                This route has no stops yet. <Link to={`/app/routes?route=${routeId}`} className="underline">Add stops</Link>.
              </p>
            ) : (
              <div className="grid grid-cols-2 gap-2">
                <Field id="assign-pickup" label="Pickup">
                  <Select id="assign-pickup" value={pickup} onChange={(event) => setPickup(event.target.value)}>
                    <option value="">None</option>
                    {route.data.stops.map((stop) => (
                      <option key={stop.id} value={stop.id}>
                        {stop.sequence}. {stop.name}
                      </option>
                    ))}
                  </Select>
                </Field>
                <Field id="assign-dropoff" label="Drop-off">
                  <Select id="assign-dropoff" value={dropoff} onChange={(event) => setDropoff(event.target.value)}>
                    <option value="">None</option>
                    {route.data.stops.map((stop) => (
                      <option key={stop.id} value={stop.id}>
                        {stop.sequence}. {stop.name}
                      </option>
                    ))}
                  </Select>
                </Field>
              </div>
            )
          ) : null}
          <ErrorText error={save.error} />
          <div className="flex gap-2">
            <Button type="submit" size="sm" disabled={save.isPending || !routeId || (!pickup && !dropoff)}>
              {save.isPending ? "Saving…" : "Save"}
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setEditing(false)}>
              Cancel
            </Button>
          </div>
        </form>
      ) : (
        <div className="mt-2 flex flex-wrap gap-2">
          <Button size="sm" variant="secondary" onClick={() => setEditing(true)}>
            {child.route ? "Change route or stops" : "Put on a route"}
          </Button>
          {child.route ? (
            <Button size="sm" variant="ghost" onClick={() => remove.mutate(undefined)} disabled={remove.isPending}>
              Take off transport
            </Button>
          ) : null}
        </div>
      )}
      <ErrorText error={remove.error} className="mt-2" />
    </section>
  );
}

function StopTile({ label, value }: { label: string; value: string | undefined }) {
  return (
    <div className="rounded-xl bg-muted p-3">
      <Eyebrow>{label}</Eyebrow>
      <p className="mt-1 text-sm font-semibold">{value ?? "—"}</p>
    </div>
  );
}

function GuardiansSection({ child }: { child: StudentDetail }) {
  const [adding, setAdding] = useState(false);
  const [links, setLinks] = useState<Record<string, string | null>>({});
  const [form, setForm] = useState({
    full_name: "",
    whatsapp_number: "",
    relationship: "father" as GuardianRelationship,
  });
  const add = useSchoolMutation(
    () => addGuardianToStudent(child.id, form),
    () => {
      setAdding(false);
      setForm({ full_name: "", whatsapp_number: "", relationship: "father" });
    },
  );
  const sendLink = useSchoolMutation(inviteGuardian, (invite) =>
    setLinks((current) => ({ ...current, [invite.guardian_id]: invite.invite_url })),
  );
  const makePrimary = useSchoolMutation((guardianId: string) =>
    updateGuardianLink(child.id, guardianId, { is_primary: true }),
  );
  const paperConsent = useSchoolMutation(recordConsent);
  const unlink = useSchoolMutation((guardianId: string) => removeGuardianLink(child.id, guardianId));
  const error = sendLink.error ?? makePrimary.error ?? paperConsent.error ?? unlink.error;

  return (
    <section>
      <SectionTitle>Guardians who get WhatsApp updates</SectionTitle>
      <ul className="flex flex-col gap-2">
        {child.guardians.map((guardian) => {
          const status = whatsappStatus(guardian);
          return (
            <li key={guardian.guardian_id} className="rounded-xl border border-border p-3">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="text-sm font-semibold">
                    {guardian.full_name} · {relationshipLabel(guardian.relationship)}
                  </p>
                  <p className="font-mono text-xs text-muted-foreground">{formatPhone(guardian.whatsapp_number)}</p>
                </div>
                <div className="flex flex-col items-end gap-1">
                  <Badge tone={status.tone}>{status.label}</Badge>
                  {guardian.is_primary ? <Badge>Primary</Badge> : null}
                </div>
              </div>
              <div className="mt-2 flex flex-wrap gap-1">
                <Button size="sm" variant="ghost" onClick={() => sendLink.mutate(guardian.guardian_id)}>
                  {guardian.status === "confirmed" ? "Send update link" : "Send link"}
                </Button>
                {!guardian.is_primary ? (
                  <Button size="sm" variant="ghost" onClick={() => makePrimary.mutate(guardian.guardian_id)}>
                    Make primary
                  </Button>
                ) : null}
                {!guardian.has_consent ? (
                  <Button size="sm" variant="ghost" onClick={() => paperConsent.mutate(guardian.guardian_id)}>
                    Agreed on paper
                  </Button>
                ) : null}
                <Button size="sm" variant="ghost" onClick={() => unlink.mutate(guardian.guardian_id)}>
                  Unlink
                </Button>
              </div>
              {links[guardian.guardian_id] !== undefined ? (
                <p role="status" className="mt-1">
                  {links[guardian.guardian_id] ? (
                    <DevLink url={links[guardian.guardian_id] ?? null} />
                  ) : (
                    <span className="text-xs text-muted-foreground">Link created.</span>
                  )}
                </p>
              ) : null}
            </li>
          );
        })}
      </ul>
      <ErrorText error={error} className="mt-2" />

      {adding ? (
        <form
          onSubmit={(event) => {
            event.preventDefault();
            add.mutate(undefined);
          }}
          className="mt-3 flex flex-col gap-3 rounded-lg bg-muted/60 p-3"
        >
          <Field id="g-name" label="Name">
            <Input
              id="g-name"
              value={form.full_name}
              onChange={(event) => setForm({ ...form, full_name: event.target.value })}
              required
            />
          </Field>
          <Field id="g-number" label="WhatsApp number">
            <Input
              id="g-number"
              type="tel"
              inputMode="tel"
              value={form.whatsapp_number}
              onChange={(event) => setForm({ ...form, whatsapp_number: event.target.value })}
              placeholder="0712 345 678"
              required
            />
          </Field>
          <Field id="g-relationship" label="Relationship">
            <Select
              id="g-relationship"
              value={form.relationship}
              onChange={(event) => setForm({ ...form, relationship: event.target.value as GuardianRelationship })}
            >
              {relationships.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </Select>
          </Field>
          <ErrorText error={add.error} />
          <div className="flex gap-2">
            <Button type="submit" size="sm" disabled={add.isPending}>
              {add.isPending ? "Saving…" : "Add guardian"}
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setAdding(false)}>
              Cancel
            </Button>
          </div>
        </form>
      ) : (
        <Button size="sm" variant="secondary" className="mt-2" onClick={() => setAdding(true)}>
          Add another guardian
        </Button>
      )}
    </section>
  );
}

function EmergencySection({ child }: { child: StudentDetail }) {
  const [adding, setAdding] = useState(false);
  const [form, setForm] = useState({ name: "", phone: "", relationship: "" });
  const add = useSchoolMutation(
    () => addEmergencyContact(child.id, { ...form, relationship: form.relationship.trim() || null }),
    () => {
      setAdding(false);
      setForm({ name: "", phone: "", relationship: "" });
    },
  );
  const remove = useSchoolMutation(removeEmergencyContact);

  return (
    <section>
      <SectionTitle>Emergency contacts</SectionTitle>
      {child.emergency_contacts.length === 0 ? (
        <p className="text-sm text-muted-foreground">None yet.</p>
      ) : (
        <ul className="flex flex-col gap-1">
          {child.emergency_contacts.map((contact) => (
            <li key={contact.id} className="flex items-center justify-between gap-2 text-sm">
              <span>
                {contact.name}
                {contact.relationship ? ` (${contact.relationship})` : ""} ·{" "}
                <span className="font-mono text-xs">{formatPhone(contact.phone)}</span>
              </span>
              <Button size="sm" variant="ghost" onClick={() => remove.mutate(contact.id)} aria-label={`Remove ${contact.name}`}>
                Remove
              </Button>
            </li>
          ))}
        </ul>
      )}
      <ErrorText error={remove.error} />
      {adding ? (
        <form
          onSubmit={(event) => {
            event.preventDefault();
            add.mutate(undefined);
          }}
          className="mt-3 flex flex-col gap-3 rounded-lg bg-muted/60 p-3"
        >
          <Field id="e-name" label="Name">
            <Input id="e-name" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required />
          </Field>
          <Field id="e-phone" label="Phone (a landline is fine)">
            <Input
              id="e-phone"
              type="tel"
              inputMode="tel"
              value={form.phone}
              onChange={(event) => setForm({ ...form, phone: event.target.value })}
              required
            />
          </Field>
          <Field id="e-relationship" label="Relationship (optional)">
            <Input
              id="e-relationship"
              value={form.relationship}
              onChange={(event) => setForm({ ...form, relationship: event.target.value })}
              placeholder="Aunt"
            />
          </Field>
          <ErrorText error={add.error} />
          <div className="flex gap-2">
            <Button type="submit" size="sm" disabled={add.isPending}>
              {add.isPending ? "Saving…" : "Add contact"}
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setAdding(false)}>
              Cancel
            </Button>
          </div>
        </form>
      ) : (
        <button type="button" className={buttonStyles({ variant: "secondary", size: "sm", className: "mt-2" })} onClick={() => setAdding(true)}>
          Add emergency contact
        </button>
      )}
    </section>
  );
}
