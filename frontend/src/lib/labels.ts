/** Plain-language labels for values the API returns. */

import type { BadgeTone } from "@/components/ui/badge";
import type { CurrentRoute, GuardianRelationship, LinkedGuardian, MembershipRole } from "@/lib/api";

export const relationships: { value: GuardianRelationship; label: string }[] = [
  { value: "mother", label: "Mother" },
  { value: "father", label: "Father" },
  { value: "guardian", label: "Guardian" },
  { value: "other", label: "Other" },
];

export function relationshipLabel(value: GuardianRelationship) {
  return relationships.find((item) => item.value === value)?.label ?? value;
}

export function roleLabel(role: MembershipRole) {
  return { school_admin: "School admin", driver: "Driver", conductor: "Conductor" }[role];
}

/** The WhatsApp column of the wireframe. */
export function whatsappStatus(guardian: Pick<LinkedGuardian, "has_consent" | "status">): {
  label: string;
  tone: BadgeTone;
} {
  if (guardian.has_consent) {
    return { label: "Opted in", tone: "safe" };
  }
  if (guardian.status === "confirmed") {
    return { label: "Messages off", tone: "danger" };
  }
  return { label: "Not confirmed", tone: "brand" };
}

export function routeLabel(route: CurrentRoute | null) {
  if (!route) {
    return "Not on a route";
  }
  const stop = route.pickup_stop ?? route.dropoff_stop;
  return stop ? `${route.route_code} · ${stop.name}` : route.route_code;
}

/** "+254712345678" → "+254 712 345 678" for reading; the API stores it without spaces. */
export function formatPhone(number: string) {
  const match = /^\+254(\d{3})(\d{3})(\d{3})$/.exec(number);
  return match ? `+254 ${match[1]} ${match[2]} ${match[3]}` : number;
}

export function fullName(person: { first_name: string; last_name: string }) {
  return `${person.first_name} ${person.last_name}`;
}

export function initials(person: { first_name: string; last_name: string }) {
  return `${person.first_name[0] ?? ""}${person.last_name[0] ?? ""}`.toUpperCase();
}
