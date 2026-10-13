import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  ApiError,
  createOrganization,
  listOrganizations,
  type OrganizationType,
} from "@/lib/api";

export function OrganizationsPage() {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [type, setType] = useState<OrganizationType>("school");

  const organizations = useQuery({
    queryKey: ["organizations"],
    queryFn: listOrganizations,
  });

  const create = useMutation({
    mutationFn: createOrganization,
    onSuccess: async () => {
      setName("");
      await queryClient.invalidateQueries({ queryKey: ["organizations"] });
    },
  });

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (name.trim().length > 0) {
      create.mutate({ name: name.trim(), type });
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-display text-2xl font-bold tracking-tight">Organizations</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          The tenant root. Schools in MVP 1; transport operators come later.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Add an organization</CardTitle>
          <CardDescription>Proves the API, database and web app are wired together.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="flex flex-col gap-4 sm:flex-row sm:items-end">
            <div className="flex flex-1 flex-col gap-2">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                name="name"
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="Riverside Academy"
                required
              />
            </div>
            <div className="flex flex-col gap-2 sm:w-48">
              <Label htmlFor="type">Type</Label>
              <select
                id="type"
                name="type"
                value={type}
                onChange={(event) => setType(event.target.value as OrganizationType)}
                className="h-10 w-full rounded-md border border-input bg-card px-3 text-sm text-foreground"
              >
                <option value="school">School</option>
                <option value="operator">Operator</option>
              </select>
            </div>
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? "Saving…" : "Add"}
            </Button>
          </form>
          {create.isError ? (
            <p role="alert" className="mt-3 text-sm text-destructive">
              {create.error instanceof ApiError ? create.error.message : "Could not save."}
            </p>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>All organizations</CardTitle>
          <CardDescription>
            {organizations.data
              ? `${organizations.data.length} on record`
              : "Loading from the API…"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {organizations.isPending ? <p className="text-sm">Loading…</p> : null}
          {organizations.isError ? (
            <p role="alert" className="text-sm text-destructive">
              {organizations.error instanceof ApiError
                ? organizations.error.message
                : "Could not load organizations."}
            </p>
          ) : null}
          {organizations.data && organizations.data.length === 0 ? (
            <p className="text-sm text-muted-foreground">Nothing yet. Add the first one above.</p>
          ) : null}
          {organizations.data && organizations.data.length > 0 ? (
            <ul className="flex flex-col divide-y divide-border">
              {organizations.data.map((organization) => (
                <li key={organization.id} className="flex items-center justify-between gap-4 py-3">
                  <span className="text-sm font-medium">{organization.name}</span>
                  <span className="rounded-full bg-secondary px-3 py-1 text-xs text-secondary-foreground">
                    {organization.type}
                  </span>
                </li>
              ))}
            </ul>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
