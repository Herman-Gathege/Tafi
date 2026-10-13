import { useMutation, useQuery } from "@tanstack/react-query";
import { useState, type FormEvent, type ReactNode } from "react";
import { useSearchParams } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorText, Eyebrow, Loading } from "@/components/ui/feedback";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import {
  confirmGuardianInvite,
  fetchGuardianInvite,
  type GuardianInvitePreview,
  type GuardianRelationship,
} from "@/lib/api";
import { formatPhone, fullName, relationships } from "@/lib/labels";

/** The page a guardian reaches from their WhatsApp link (S3-05, D-22). No account needed. */
export function GuardianInvitePage() {
  const [params] = useSearchParams();
  const token = params.get("token") ?? "";
  const invite = useQuery({
    queryKey: ["guardian-invite", token],
    queryFn: () => fetchGuardianInvite(token),
    enabled: token.length > 0,
    retry: false,
    staleTime: Infinity,
  });

  if (token.length === 0) {
    return (
      <Shell title="Bus updates" description="This link is missing a part. Open it again from your WhatsApp message." />
    );
  }
  if (invite.isPending) {
    return (
      <Shell title="Bus updates" description="Opening your link…">
        <Loading />
      </Shell>
    );
  }
  if (!invite.data) {
    return (
      <Shell title="Bus updates" description="This link cannot be used.">
        <ErrorText error={invite.error} fallback="We could not open this link." />
        <p className="text-sm text-muted-foreground">Each link works once and expires after 7 days.</p>
      </Shell>
    );
  }
  return <Registration token={token} invite={invite.data} />;
}

function Registration({ token, invite }: { token: string; invite: GuardianInvitePreview }) {
  const [name, setName] = useState(invite.full_name);
  const [email, setEmail] = useState(invite.email ?? "");
  const [consent, setConsent] = useState(false);
  const [second, setSecond] = useState<{ open: boolean; full_name: string; whatsapp_number: string; relationship: GuardianRelationship }>(
    { open: false, full_name: "", whatsapp_number: "", relationship: "father" },
  );
  const [emergency, setEmergency] = useState({ open: false, name: "", phone: "", relationship: "" });
  const [stopChange, setStopChange] = useState({
    open: false,
    student_id: invite.children[0]?.id ?? "",
    stop_id: "",
    location: "",
  });

  const confirm = useMutation({
    mutationFn: () =>
      confirmGuardianInvite(token, {
        full_name: name,
        email: email.trim() || null,
        consent,
        consent_version: invite.consent_version,
        second_guardian: second.open
          ? { full_name: second.full_name, whatsapp_number: second.whatsapp_number, relationship: second.relationship }
          : null,
        emergency_contacts: emergency.open
          ? invite.children.map((child) => ({
              student_id: child.id,
              name: emergency.name,
              phone: emergency.phone,
              relationship: emergency.relationship.trim() || null,
            }))
          : [],
        stop_changes: stopChange.open
          ? [
              {
                student_id: stopChange.student_id,
                requested_stop_id: stopChange.stop_id || null,
                requested_location: stopChange.stop_id ? null : stopChange.location.trim() || null,
              },
            ]
          : [],
      }),
  });

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    confirm.mutate();
  }

  if (confirm.data) {
    return (
      <Shell title="You're all set" description={confirm.data.message}>
        <p className="text-sm text-muted-foreground">
          You can close this page. If anything changes, ask {confirm.data.school_name} to send you a new link.
        </p>
      </Shell>
    );
  }

  const changeChild = invite.children.find((child) => child.id === stopChange.student_id);

  return (
    <div className="mx-auto w-full max-w-md px-4 py-10">
      <Eyebrow>For {invite.school_name}</Eyebrow>
      <h1 className="mt-2 font-display text-2xl font-extrabold tracking-tight">
        Get bus updates for {invite.children.map((child) => child.first_name).join(" and ") || "your child"}
      </h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Confirm your details and we'll send you a WhatsApp message each time your child gets on or off the
        school bus.
      </p>

      <form onSubmit={onSubmit} className="mt-6 flex flex-col gap-5">
        <ul className="flex flex-col gap-2">
          {invite.children.map((child) => (
            <li key={child.id} className="rounded-2xl bg-muted p-4 text-sm">
              <Eyebrow>From the school</Eyebrow>
              <p className="mt-1 font-bold">
                {fullName(child)}
                {child.grade ? ` · ${child.grade}` : ""}
              </p>
              <p className="text-muted-foreground">
                {child.route
                  ? `${child.route.route_code} · pickup ${child.route.pickup_stop?.name ?? "—"}, drop-off ${child.route.dropoff_stop?.name ?? "—"}`
                  : "The school has not set a route yet."}
              </p>
            </li>
          ))}
        </ul>

        <Field id="name" label="Your name">
          <Input id="name" autoComplete="name" value={name} onChange={(e) => setName(e.target.value)} required />
        </Field>
        <div className="flex flex-col gap-1.5">
          <span className="text-sm font-medium">WhatsApp number</span>
          <p className="rounded-md border border-input bg-muted px-3 py-2 font-mono text-sm">
            {formatPhone(invite.whatsapp_number)}
          </p>
          <p className="text-xs text-muted-foreground">Wrong number? Ask the school to change it and send a new link.</p>
        </div>
        <Field id="email" label="Email (optional)">
          <Input id="email" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        </Field>

        <Optional
          open={second.open}
          onToggle={() => setSecond({ ...second, open: !second.open })}
          label="Add another guardian"
          hint="They will get their own link to agree to updates."
        >
          <Field id="second-name" label="Their name">
            <Input id="second-name" value={second.full_name} onChange={(e) => setSecond({ ...second, full_name: e.target.value })} required />
          </Field>
          <Field id="second-number" label="Their WhatsApp number">
            <Input
              id="second-number"
              type="tel"
              inputMode="tel"
              value={second.whatsapp_number}
              onChange={(e) => setSecond({ ...second, whatsapp_number: e.target.value })}
              placeholder="0712 345 678"
              required
            />
          </Field>
          <Field id="second-relationship" label="Relationship to the child">
            <Select
              id="second-relationship"
              value={second.relationship}
              onChange={(e) => setSecond({ ...second, relationship: e.target.value as GuardianRelationship })}
            >
              {relationships.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </Select>
          </Field>
        </Optional>

        <Optional
          open={emergency.open}
          onToggle={() => setEmergency({ ...emergency, open: !emergency.open })}
          label="Add an emergency contact"
          hint="Someone the school can call if you cannot be reached."
        >
          <Field id="emergency-name" label="Name">
            <Input id="emergency-name" value={emergency.name} onChange={(e) => setEmergency({ ...emergency, name: e.target.value })} required />
          </Field>
          <Field id="emergency-phone" label="Phone">
            <Input
              id="emergency-phone"
              type="tel"
              inputMode="tel"
              value={emergency.phone}
              onChange={(e) => setEmergency({ ...emergency, phone: e.target.value })}
              required
            />
          </Field>
          <Field id="emergency-relationship" label="Relationship (optional)">
            <Input
              id="emergency-relationship"
              value={emergency.relationship}
              onChange={(e) => setEmergency({ ...emergency, relationship: e.target.value })}
              placeholder="Aunt"
            />
          </Field>
        </Optional>

        <Optional
          open={stopChange.open}
          onToggle={() => setStopChange({ ...stopChange, open: !stopChange.open })}
          label="Ask for a different stop"
          hint="The school will review the request."
        >
          {invite.children.length > 1 ? (
            <Field id="change-child" label="For">
              <Select
                id="change-child"
                value={stopChange.student_id}
                onChange={(e) => setStopChange({ ...stopChange, student_id: e.target.value, stop_id: "" })}
              >
                {invite.children.map((child) => (
                  <option key={child.id} value={child.id}>
                    {child.first_name}
                  </option>
                ))}
              </Select>
            </Field>
          ) : null}
          {changeChild && changeChild.stops_on_route.length > 0 ? (
            <Field id="change-stop" label="A stop on the route">
              <Select id="change-stop" value={stopChange.stop_id} onChange={(e) => setStopChange({ ...stopChange, stop_id: e.target.value })}>
                <option value="">Somewhere else (describe it below)</option>
                {changeChild.stops_on_route.map((stop) => (
                  <option key={stop.id} value={stop.id}>
                    {stop.name}
                  </option>
                ))}
              </Select>
            </Field>
          ) : null}
          {!stopChange.stop_id ? (
            <Field id="change-location" label="Where?">
              <Input
                id="change-location"
                value={stopChange.location}
                onChange={(e) => setStopChange({ ...stopChange, location: e.target.value })}
                placeholder="e.g. Naivas, Kilimani"
                required
                minLength={3}
              />
            </Field>
          ) : null}
        </Optional>

        <section aria-labelledby="consent-heading" className="rounded-2xl border border-border bg-card p-4">
          <h2 id="consent-heading" className="text-sm font-bold">
            What you are agreeing to
          </h2>
          <p className="mt-2 text-sm whitespace-pre-line text-muted-foreground">{invite.consent_text}</p>
          <label className="mt-4 flex items-start gap-3 text-sm">
            <input
              type="checkbox"
              checked={consent}
              onChange={(e) => setConsent(e.target.checked)}
              className="mt-0.5 size-5 shrink-0 accent-[var(--color-safe)]"
              required
            />
            <span>I agree to receive bus updates on WhatsApp as described above.</span>
          </label>
        </section>

        <ErrorText error={confirm.error} fallback="We could not save your details. Please try again." />
        <Button
          type="submit"
          disabled={!consent || confirm.isPending}
          className="h-14 rounded-2xl bg-safe text-base font-bold text-white"
        >
          {confirm.isPending ? "Saving…" : "Confirm and start updates"}
        </Button>
        <p className="text-center">
          <Badge tone="muted">Wording version {invite.consent_version}</Badge>
        </p>
      </form>
    </div>
  );
}

function Optional({
  open,
  onToggle,
  label,
  hint,
  children,
}: {
  open: boolean;
  onToggle: () => void;
  label: string;
  hint: string;
  children: ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-dashed border-border p-4">
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={open}
        className="flex w-full items-center justify-between gap-2 text-left text-sm font-semibold"
      >
        {open ? `Remove: ${label.toLowerCase()}` : `+ ${label}`}
      </button>
      {open ? (
        <div className="mt-3 flex flex-col gap-3">
          <p className="text-xs text-muted-foreground">{hint}</p>
          {children}
        </div>
      ) : null}
    </div>
  );
}

function Field({ id, label, children }: { id: string; label: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor={id}>{label}</Label>
      {children}
    </div>
  );
}

function Shell({ title, description, children }: { title: string; description: string; children?: ReactNode }) {
  return (
    <div className="mx-auto w-full max-w-md px-4 py-14">
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
        {children ? <CardContent className="flex flex-col gap-3">{children}</CardContent> : null}
      </Card>
    </div>
  );
}
