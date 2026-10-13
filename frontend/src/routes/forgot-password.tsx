import { useMutation } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError, forgotPassword } from "@/lib/api";

export function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const request = useMutation({ mutationFn: forgotPassword });

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    request.mutate(email);
  }

  return (
    <div className="mx-auto w-full max-w-md px-4 py-14">
      <Card>
        <CardHeader>
          <CardTitle>Reset your password</CardTitle>
          <CardDescription>
            We will send a link to the address on your account. It works once and expires.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {request.data ? (
            <>
              <p role="status" className="text-sm">
                {request.data.message}
              </p>
              {request.data.reset_url ? (
                <p className="text-sm text-muted-foreground">
                  Nothing sends email yet, so here is the link:{" "}
                  <a href={request.data.reset_url} className="underline">
                    open the reset link
                  </a>
                  .
                </p>
              ) : null}
              <Link to="/signin" className="text-sm underline">
                Back to sign in
              </Link>
            </>
          ) : (
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
              {request.isError ? (
                <p role="alert" className="text-sm text-destructive">
                  {request.error instanceof ApiError
                    ? request.error.message
                    : "Could not send the request."}
                </p>
              ) : null}
              <Button type="submit" disabled={request.isPending}>
                {request.isPending ? "Sending…" : "Send me a link"}
              </Button>
              <Link to="/signin" className="text-sm text-muted-foreground underline">
                Back to sign in
              </Link>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
