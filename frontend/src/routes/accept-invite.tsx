import { useQuery } from "@tanstack/react-query";
import { useState, type FormEvent, type ReactNode } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError, fetchInvitation } from "@/lib/api";
import { useAcceptInvite } from "@/lib/session";

const MIN_PASSWORD = 8;

export function AcceptInvitePage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const token = params.get("token") ?? "";
  const accept = useAcceptInvite();
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");

  const invitation = useQuery({
    queryKey: ["invitation", token],
    queryFn: () => fetchInvitation(token),
    enabled: token.length > 0,
    retry: false,
  });

  const passwordTooShort = password.length > 0 && password.length < MIN_PASSWORD;
  const mismatch = confirm.length > 0 && password !== confirm;

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (password.length < MIN_PASSWORD || password !== confirm) {
      return;
    }
    accept.mutate(
      { token, name, password },
      { onSuccess: () => navigate("/app", { replace: true }) },
    );
  }

  if (token.length === 0) {
    return (
      <Shell title="Invitation link" description="This link is missing its token.">
        <p className="text-sm text-muted-foreground">
          Ask whoever invited you to send it again, or{" "}
          <Link to="/signin" className="underline">
            sign in
          </Link>
          .
        </p>
      </Shell>
    );
  }

  if (invitation.isPending) {
    return <Shell title="Invitation" description="Checking the link…" />;
  }

  if (invitation.isError || !invitation.data) {
    return (
      <Shell title="Invitation link" description="This link is not usable.">
        <p role="alert" className="text-sm text-destructive">
          {invitation.error instanceof ApiError
            ? invitation.error.message
            : "We could not check that invitation."}
        </p>
        <p className="text-sm text-muted-foreground">
          Invitations expire, and each works once. Ask for a new one, or{" "}
          <Link to="/signin" className="underline">
            sign in
          </Link>
          .
        </p>
      </Shell>
    );
  }

  return (
    <Shell
      title={`Join ${invitation.data.organization_name}`}
      description={`You were invited as a ${invitation.data.role.replace("_", " ")} and will sign in with ${invitation.data.email}.`}
    >
      <form onSubmit={onSubmit} className="flex flex-col gap-4">
        <div className="flex flex-col gap-2">
          <Label htmlFor="name">Your name</Label>
          <Input
            id="name"
            name="name"
            autoComplete="name"
            value={name}
            onChange={(event) => setName(event.target.value)}
            required
          />
        </div>
        <div className="flex flex-col gap-2">
          <Label htmlFor="password">Choose a password</Label>
          <Input
            id="password"
            name="password"
            type="password"
            autoComplete="new-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            aria-describedby="password-hint"
            required
          />
          <p id="password-hint" className="text-xs text-muted-foreground">
            At least {MIN_PASSWORD} characters.
          </p>
        </div>
        <div className="flex flex-col gap-2">
          <Label htmlFor="confirm">Repeat the password</Label>
          <Input
            id="confirm"
            name="confirm"
            type="password"
            autoComplete="new-password"
            value={confirm}
            onChange={(event) => setConfirm(event.target.value)}
            required
          />
        </div>
        {passwordTooShort ? (
          <p role="alert" className="text-sm text-destructive">
            That password is too short.
          </p>
        ) : null}
        {mismatch ? (
          <p role="alert" className="text-sm text-destructive">
            The two passwords do not match.
          </p>
        ) : null}
        {accept.isError ? (
          <p role="alert" className="text-sm text-destructive">
            {accept.error instanceof ApiError
              ? accept.error.message
              : "Could not accept the invitation."}
          </p>
        ) : null}
        <Button type="submit" disabled={accept.isPending || passwordTooShort || mismatch}>
          {accept.isPending ? "Setting up…" : "Create my account"}
        </Button>
      </form>
    </Shell>
  );
}

function Shell({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children?: ReactNode;
}) {
  return (
    <div className="mx-auto w-full max-w-md px-4 py-14">
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">{children}</CardContent>
      </Card>
    </div>
  );
}
