import { describe, expect, it } from "vitest";

import { roleHome } from "@/lib/roles";
import type { Session } from "@/lib/api";

function session(
  role: "school_admin" | "driver" | "conductor" | "parent",
  platformAdmin = false,
): Session {
  return {
    user: {
      id: "user-1",
      email: "person@example.test",
      name: "Test Person",
      is_platform_admin: platformAdmin,
    },
    memberships: [
      {
        organization_id: "org-1",
        organization_name: "Test School",
        role,
      },
    ],
  };
}

describe("roleHome", () => {
  it("sends platform admins to the platform console", () => {
    expect(roleHome(session("parent", true))).toBe("/app/admin");
  });

  it("sends school admins to the school dashboard", () => {
    expect(roleHome(session("school_admin"))).toBe("/app");
  });

  it("sends drivers and conductors to today's trips", () => {
    expect(roleHome(session("driver"))).toBe("/crew");
    expect(roleHome(session("conductor"))).toBe("/crew");
  });

  it("sends parents to the family dashboard", () => {
    expect(roleHome(session("parent"))).toBe("/parent");
  });

  it("prefers the school role over crew and parent roles", () => {
    const mixed = session("parent");
    mixed.memberships.push({
      organization_id: "org-2",
      organization_name: "Second School",
      role: "driver",
    });
    mixed.memberships.push({
      organization_id: "org-3",
      organization_name: "Third School",
      role: "school_admin",
    });

    expect(roleHome(mixed)).toBe("/app");
  });

  it("sends signed-in accounts without a role back to sign in", () => {
    expect(
      roleHome({
        user: {
          id: "user-1",
          email: "person@example.test",
          name: "Test Person",
          is_platform_admin: false,
        },
        memberships: [],
      }),
    ).toBe("/signin");
  });
});
