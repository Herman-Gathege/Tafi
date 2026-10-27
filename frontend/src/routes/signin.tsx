import { useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError } from "@/lib/api";
import { useSignIn } from "@/lib/session";

export function SignInPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const signIn = useSignIn();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    signIn.mutate(
      { email, password },
      {
        onSuccess: (session) => {
          const from = (location.state as { from?: string } | null)?.from;
          const roles = session.memberships.map((membership) => membership.role);
          const home = session.user.is_platform_admin
            ? "/app/admin"
            : roles.includes("school_admin")
              ? "/app"
              : roles.includes("driver") || roles.includes("conductor")
                ? "/crew"
                : roles.includes("parent")
                  ? "/parent"
                  : "/app";
          navigate(from ?? home, { replace: true });
        },
      },
    );
  }

  return (
    <div className="mx-auto w-full max-w-md px-4 py-14">
      <Card>
        <CardHeader>
          <CardTitle>Sign in</CardTitle>
          <CardDescription>
            School staff, crew, parents and Tafi staff use the same door.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
              />
            </div>
            {signIn.isError ? (
              <p role="alert" className="text-sm text-destructive">
                {signIn.error instanceof ApiError ? signIn.error.message : "Could not sign in."}
              </p>
            ) : null}
            <Button type="submit" disabled={signIn.isPending}>
              {signIn.isPending ? "Signing in…" : "Sign in"}
            </Button>
            <Link to="/forgot-password" className="text-sm text-muted-foreground underline">
              Forgot your password?
            </Link>
            <p className="text-sm text-muted-foreground">
              New to Tafi?{" "}
              <Link to="/signup" className="underline">
                Create your school's account
              </Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
