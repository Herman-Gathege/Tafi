const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export type OrganizationType = "school" | "operator";
export type MembershipRole = "school_admin" | "driver";

export interface Organization {
  id: string;
  name: string;
  type: OrganizationType;
  created_at: string;
  updated_at: string;
}

export interface OrganizationCreate {
  name: string;
  type: OrganizationType;
}

export interface User {
  id: string;
  email: string;
  name: string;
  is_platform_admin: boolean;
}

export interface Membership {
  organization_id: string;
  organization_name: string;
  role: MembershipRole;
}

export interface Session {
  user: User;
  memberships: Membership[];
}

export interface InvitationPreview {
  email: string;
  organization_name: string;
  role: MembershipRole;
}

export interface InvitationCreated {
  id: string;
  email: string;
  role: MembershipRole;
  expires_at: string;
  invite_url: string | null;
}

export interface MessageResponse {
  message: string;
  reset_url: string | null;
}

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      headers: { "Content-Type": "application/json" },
      // The session lives in an httpOnly cookie, so every call has to carry it.
      credentials: "include",
      ...init,
    });
  } catch {
    throw new ApiError(`Cannot reach the Tafi API at ${API_BASE_URL}.`, 0);
  }

  if (!response.ok) {
    throw new ApiError(await readErrorMessage(response), response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const body: unknown = await response.json();
    if (typeof body === "object" && body !== null && "detail" in body) {
      const detail = (body as { detail: unknown }).detail;
      if (typeof detail === "string") {
        return detail;
      }
      if (Array.isArray(detail) && detail.length > 0) {
        const first = detail[0] as { msg?: unknown };
        if (typeof first.msg === "string") {
          return first.msg;
        }
      }
    }
  } catch {
    // Fall through to the generic message below.
  }
  return `Request failed with status ${response.status}.`;
}

// --- Session -----------------------------------------------------------------

export function fetchSession(): Promise<Session | null> {
  return request<Session>("/api/v1/auth/me").catch((error: unknown) => {
    if (error instanceof ApiError && error.status === 401) {
      return null;
    }
    throw error;
  });
}

export function signIn(email: string, password: string): Promise<Session> {
  return request<Session>("/api/v1/auth/sign-in", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function signOut(): Promise<void> {
  return request<void>("/api/v1/auth/sign-out", { method: "POST" });
}

export function fetchInvitation(token: string): Promise<InvitationPreview> {
  return request<InvitationPreview>(`/api/v1/auth/invitations/${encodeURIComponent(token)}`);
}

export function acceptInvite(payload: {
  token: string;
  name: string;
  password: string;
}): Promise<Session> {
  return request<Session>("/api/v1/auth/accept-invite", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function forgotPassword(email: string): Promise<MessageResponse> {
  return request<MessageResponse>("/api/v1/auth/forgot-password", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export function resetPassword(payload: { token: string; password: string }): Promise<void> {
  return request<void>("/api/v1/auth/reset-password", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// --- Tenants -----------------------------------------------------------------

export function listOrganizations(): Promise<Organization[]> {
  return request<Organization[]>("/api/v1/organizations");
}

export function createOrganization(payload: OrganizationCreate): Promise<Organization> {
  return request<Organization>("/api/v1/organizations", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createInvitation(
  organizationId: string,
  payload: { email: string; role: MembershipRole },
): Promise<InvitationCreated> {
  return request<InvitationCreated>(
    `/api/v1/organizations/${encodeURIComponent(organizationId)}/invitations`,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function fetchOwnOrganization(): Promise<Organization> {
  return request<Organization>("/api/v1/organization");
}
