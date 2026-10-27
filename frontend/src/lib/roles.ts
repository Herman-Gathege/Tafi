import type { Membership, Session } from "@/lib/api";

export function schoolMembership(session: Session | null): Membership | null {
  return session?.memberships.find((membership) => membership.role === "school_admin") ?? null;
}

export function crewMembership(session: Session | null): Membership | null {
  return (
    session?.memberships.find(
      (membership) => membership.role === "driver" || membership.role === "conductor",
    ) ?? null
  );
}

export function parentMembership(session: Session | null): Membership | null {
  return session?.memberships.find((membership) => membership.role === "parent") ?? null;
}

/** The one route a signed-in person should land on. Platform access wins. */
export function roleHome(session: Session): string {
  if (session.user.is_platform_admin) {
    return "/app/admin";
  }
  if (schoolMembership(session)) {
    return "/app";
  }
  if (crewMembership(session)) {
    return "/crew";
  }
  if (parentMembership(session)) {
    return "/parent";
  }
  return "/signin";
}
