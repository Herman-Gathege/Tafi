import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError, signUp } from "@/lib/api";
import { roleHome } from "@/lib/roles";
import { sessionKey } from "@/lib/session";

/** The one new function in this pass: a school creates itself and its first admin. */
export function SignupPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [schoolName, setSchoolName] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const signup = useMutation({
    mutationFn: signUp,
    onSuccess: (session) => {
      queryClient.setQueryData(sessionKey, session);
      navigate(roleHome(session), { replace: true });
    },
  });

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    signup.mutate({ school_name: schoolName, name, email, password });
  }

  return (
    <div className="mx-auto w-full max-w-md px-4 py-14">
      <Card>
        <CardHeader>
          <CardTitle>Create your school's account</CardTitle>
          <CardDescription>
            You become the first school admin. You can add your routes, children and crew next.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <Label htmlFor="school-name">School name</Label>
              <Input
                id="school-name"
                value={schoolName}
                onChange={(event) => setSchoolName(event.target.value)}
                placeholder="Riverside Academy"
                required
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="name">Your name</Label>
              <Input
                id="name"
                autoComplete="name"
                value={name}
                onChange={(event) => setName(event.target.value)}
                required
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
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
                type="password"
                autoComplete="new-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                minLength={8}
                required
              />
              <p className="text-xs text-muted-foreground">At least 8 characters.</p>
            </div>
            {signup.isError ? (
              <p role="alert" className="text-sm text-destructive">
                {signup.error instanceof ApiError
                  ? signup.error.message
                  : "Could not create the account."}
              </p>
            ) : null}
            <Button type="submit" disabled={signup.isPending}>
              {signup.isPending ? "Creating…" : "Create account"}
            </Button>
            <p className="text-sm text-muted-foreground">
              Already have an account?{" "}
              <Link to="/signin" className="underline">
                Sign in
              </Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
