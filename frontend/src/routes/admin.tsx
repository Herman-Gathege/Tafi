import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  ApiError,
  createInvitation,
  createOrganization,
  listOrganizations,
  type InvitationCreated,
  type MembershipRole,
  type OrganizationType,
} from "@/lib/api";

export function AdminPage() {
  const queryClient = useQueryClient();
  const organizations = useQuery({ queryKey: ["organizations"], queryFn: listOrganizations });

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-display text-2xl font-bold tracking-tight">Platform admin</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Onboard a school and hand its first admin a way in.
        </p>
      </div>

      <AddSchool onAdded={() => queryClient.invalidateQueries({ queryKey: ["organizations"] })} />

      <Card>
        <CardHeader>
          <CardTitle>Schools</CardTitle>
          <CardDescription>
            {organizations.data
              ? `${organizations.data.length} on the platform`
              : "Loading from the API…"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {organizations.isPending ? <p className="text-sm">Loading…</p> : null}
          {organizations.isError ? (
            <p role="alert" className="text-sm text-destructive">
              {organizations.error instanceof ApiError
                ? organizations.error.message
                : "Could not load the schools."}
            </p>
          ) : null}
          {organizations.data && organizations.data.length === 0 ? (
            <p className="text-sm text-muted-foreground">Nothing yet. Add the first school above.</p>
          ) : null}
          {organizations.data && organizations.data.length > 0 ? (
            <ul className="flex flex-col divide-y divide-border">
              {organizations.data.map((organization) => (
                <li key={organization.id} className="py-3">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <span className="text-sm font-medium">{organization.name}</span>
                    <span className="rounded-full bg-secondary px-3 py-1 text-xs text-secondary-foreground">
                      {organization.type}
                    </span>
                  </div>
                  <InviteAdmin organizationId={organization.id} organizationName={organization.name} />
                </li>
              ))}
            </ul>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}

function AddSchool({ onAdded }: { onAdded: () => void }) {
  const [name, setName] = useState("");
  const [type, setType] = useState<OrganizationType>("school");
  const create = useMutation({
    mutationFn: createOrganization,
    onSuccess: () => {
      setName("");
      onAdded();
    },
  });

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (name.trim().length > 0) {
      create.mutate({ name: name.trim(), type });
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Add a school</CardTitle>
        <CardDescription>
          A school exists before anyone can sign in to it. Invite its first admin next.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} className="flex flex-col gap-4 sm:flex-row sm:items-end">
          <div className="flex flex-1 flex-col gap-2">
            <Label htmlFor="school-name">Name</Label>
            <Input
              id="school-name"
              name="school-name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="Riverside Academy"
              required
            />
          </div>
          <div className="flex flex-col gap-2 sm:w-48">
            <Label htmlFor="school-type">Type</Label>
            <select
              id="school-type"
              name="school-type"
              value={type}
              onChange={(event) => setType(event.target.value as OrganizationType)}
              className="h-10 w-full rounded-md border border-input bg-card px-3 text-sm text-foreground"
            >
              <option value="school">School</option>
              <option value="operator">Operator</option>
            </select>
          </div>
          <Button type="submit" disabled={create.isPending}>
            {create.isPending ? "Saving…" : "Add school"}
          </Button>
        </form>
        {create.isError ? (
          <p role="alert" className="mt-3 text-sm text-destructive">
            {create.error instanceof ApiError ? create.error.message : "Could not add the school."}
          </p>
        ) : null}
      </CardContent>
    </Card>
  );
}

function InviteAdmin({
  organizationId,
  organizationName,
}: {
  organizationId: string;
  organizationName: string;
}) {
  const [open, setOpen] = useState(false);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<MembershipRole>("school_admin");
  const [created, setCreated] = useState<InvitationCreated | null>(null);

  const invite = useMutation({
    mutationFn: () => createInvitation(organizationId, { email, role }),
    onSuccess: (invitation) => {
      setCreated(invitation);
      setEmail("");
    },
  });

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    invite.mutate();
  }

  if (!open) {
    return (
      <div className="mt-2">
        <Button variant="secondary" size="sm" onClick={() => setOpen(true)}>
          Invite an admin
        </Button>
        {created?.invite_url ? (
          <p className="mt-2 text-xs text-muted-foreground">
            Invitation for {created.email}:{" "}
            <a href={created.invite_url} className="underline">
              open the invite link
            </a>
          </p>
        ) : null}
      </div>
    );
  }

  return (
    <form onSubmit={onSubmit} className="mt-3 flex flex-col gap-3 rounded-lg bg-muted/60 p-3">
      <p className="text-xs text-muted-foreground">Invite someone to {organizationName}.</p>
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end">
        <div className="flex flex-1 flex-col gap-1">
          <Label htmlFor={`invite-email-${organizationId}`}>Email</Label>
          <Input
            id={`invite-email-${organizationId}`}
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </div>
        <div className="flex flex-col gap-1 sm:w-40">
          <Label htmlFor={`invite-role-${organizationId}`}>Role</Label>
          <select
            id={`invite-role-${organizationId}`}
            value={role}
            onChange={(event) => setRole(event.target.value as MembershipRole)}
            className="h-10 w-full rounded-md border border-input bg-card px-3 text-sm text-foreground"
          >
            <option value="school_admin">School admin</option>
            <option value="driver">Driver</option>
          </select>
        </div>
        <Button type="submit" disabled={invite.isPending}>
          {invite.isPending ? "Sending…" : "Create invitation"}
        </Button>
        <Button type="button" variant="ghost" onClick={() => setOpen(false)}>
          Cancel
        </Button>
      </div>
      {invite.isError ? (
        <p role="alert" className="text-sm text-destructive">
          {invite.error instanceof ApiError ? invite.error.message : "Could not create the invitation."}
        </p>
      ) : null}
      {created ? (
        <p role="status" className="text-sm">
          Invitation for {created.email} created.
          {created.invite_url ? (
            <>
              {" "}
              Nothing sends email yet, so here is the link:{" "}
              <a href={created.invite_url} className="underline">
                open the invite link
              </a>
              .
            </>
          ) : null}
        </p>
      ) : null}
    </form>
  );
}
