import { useMutation } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError, resetPassword } from "@/lib/api";

const MIN_PASSWORD = 8;

export function ResetPasswordPage() {
  const [params] = useSearchParams();
  const token = params.get("token") ?? "";
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const reset = useMutation({ mutationFn: resetPassword });

  const passwordTooShort = password.length > 0 && password.length < MIN_PASSWORD;
  const mismatch = confirm.length > 0 && password !== confirm;

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (password.length < MIN_PASSWORD || password !== confirm) {
      return;
    }
    reset.mutate({ token, password });
  }

  return (
    <div className="mx-auto w-full max-w-md px-4 py-14">
      <Card>
        <CardHeader>
          <CardTitle>Choose a new password</CardTitle>
          <CardDescription>
            {token.length === 0
              ? "This link is missing its token."
              : "The link works once; signing in with it does not."}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {reset.isSuccess ? (
            <>
              <p role="status" className="text-sm">
                Your password has been changed.
              </p>
              <Link to="/signin" className="text-sm underline">
                Sign in
              </Link>
            </>
          ) : (
            <form onSubmit={onSubmit} className="flex flex-col gap-4">
              <div className="flex flex-col gap-2">
                <Label htmlFor="password">New password</Label>
                <Input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="new-password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                />
                <p className="text-xs text-muted-foreground">At least {MIN_PASSWORD} characters.</p>
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
              {reset.isError ? (
                <p role="alert" className="text-sm text-destructive">
                  {reset.error instanceof ApiError
                    ? reset.error.message
                    : "Could not change the password."}
                </p>
              ) : null}
              <Button
                type="submit"
                disabled={reset.isPending || passwordTooShort || mismatch || token.length === 0}
              >
                {reset.isPending ? "Saving…" : "Save the new password"}
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
