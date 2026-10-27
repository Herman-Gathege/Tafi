import { Navigate, Outlet, useLocation } from "react-router-dom";

import { roleHome } from "@/lib/roles";
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
  const { session, isSignedIn, isPlatformAdmin, isLoading } = useSession();

  if (isLoading) {
    return <Checking />;
  }
  if (!isSignedIn) {
    return <Navigate to="/signin" replace />;
  }
  if (!isPlatformAdmin) {
    return <Navigate to={session ? roleHome(session) : "/signin"} replace />;
  }
  return <Outlet />;
}

/**
 * School admins only (Sprint 3 school screens). The API enforces this too; this just keeps
 * crew and Tafi staff away from screens that would only show them errors.
 */
export function RequireSchoolAdmin() {
  const { session, isSignedIn, school, isLoading } = useSession();

  if (isLoading) {
    return <Checking />;
  }
  if (!isSignedIn) {
    return <Navigate to="/signin" replace />;
  }
  if (school?.role !== "school_admin") {
    return <Navigate to={session ? roleHome(session) : "/signin"} replace />;
  }
  return <Outlet />;
}

/** Crew only (a driver or a conductor). The API enforces it too. */
export function RequireCrew() {
  const { session, isSignedIn, crew, isLoading } = useSession();

  if (isLoading) {
    return <Checking />;
  }
  if (!isSignedIn) {
    return <Navigate to="/signin" replace />;
  }
  if (!crew) {
    return <Navigate to={session ? roleHome(session) : "/signin"} replace />;
  }
  return <Outlet />;
}

/** A guardian with a login. The API enforces it too. */
export function RequireParent() {
  const { session, isSignedIn, isParent, isLoading } = useSession();

  if (isLoading) {
    return <Checking />;
  }
  if (!isSignedIn) {
    return <Navigate to="/signin" replace />;
  }
  if (!isParent) {
    return <Navigate to={session ? roleHome(session) : "/signin"} replace />;
  }
  return <Outlet />;
}
