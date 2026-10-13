import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useSession } from "@/lib/session";

function Checking() {
  return (
    <div className="mx-auto w-full max-w-md px-4 py-20 text-center text-sm text-muted-foreground">
      Checking your session…
    </div>
  );
}

/** Signed-in people only. */
export function RequireAuth() {
  const location = useLocation();
  const { isSignedIn, isLoading } = useSession();

  if (isLoading) {
    return <Checking />;
  }
  if (!isSignedIn) {
    return <Navigate to="/signin" replace state={{ from: location.pathname }} />;
  }
  return <Outlet />;
}

/** Tafi staff only — a signed-in school admin is sent to their own portal. */
export function RequirePlatformAdmin() {
  const { isSignedIn, isPlatformAdmin, isLoading } = useSession();

  if (isLoading) {
    return <Checking />;
  }
  if (!isSignedIn) {
    return <Navigate to="/signin" replace />;
  }
  if (!isPlatformAdmin) {
    return <Navigate to="/app" replace />;
  }
  return <Outlet />;
}
