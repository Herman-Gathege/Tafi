import { Navigate, Outlet, useLocation } from "react-router-dom";

import { hasDevSession } from "@/lib/session";

/**
 * Stands in for the real route guard. Sprint 2 replaces the localStorage check
 * with the API session; the shape of the wrapper stays the same.
 */
export function RequireAuth() {
  const location = useLocation();

  if (!hasDevSession()) {
    return <Navigate to="/signin" replace state={{ from: location.pathname }} />;
  }

  return <Outlet />;
}
