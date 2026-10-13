import { useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { startDevSession } from "@/lib/session";

export function SignInPage() {
  const navigate = useNavigate();

  function enterDemo() {
    startDevSession();
    navigate("/app", { replace: true });
  }

  return (
    <div className="mx-auto w-full max-w-md px-4 py-14">
      <Card>
        <CardHeader>
          <CardTitle>School sign in</CardTitle>
          <CardDescription>
            Email and password sign-in, invitations and password reset arrive in Sprint 2 with the accounts work.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <p className="text-sm text-muted-foreground">
            Until then you can walk through the school portal with a demo session. It is a development shortcut,
            not a login.
          </p>
          <Button onClick={enterDemo}>Enter the demo</Button>
          <p className="text-xs text-muted-foreground">
            The demo session is stored in this browser only and clears when you sign out.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
