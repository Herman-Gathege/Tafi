const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export type OrganizationType = "school" | "operator";
export type MembershipRole = "school_admin" | "driver" | "conductor";

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
          // Pydantic prefixes custom messages with "Value error, ".
          return first.msg.replace(/^Value error, /, "");
        }
      }
    }
  } catch {
    // Fall through to the generic message below.
  }
  return `Request failed with status ${response.status}.`;
}

function post<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: "POST",
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

function put<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, { method: "PUT", body: JSON.stringify(body) });
}

function patch<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, { method: "PATCH", body: JSON.stringify(body) });
}

function del<T>(path: string): Promise<T> {
  return request<T>(path, { method: "DELETE" });
}

const id = encodeURIComponent;

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

// --- School data (Sprint 3) --------------------------------------------------

const SCHOOL = "/api/v1/school";

export type StudentStatus = "active" | "inactive";
export type GuardianStatus = "invited" | "confirmed";
export type GuardianRelationship = "mother" | "father" | "guardian" | "other";
export type RunDirection = "morning" | "afternoon";
export type RequestStatus = "pending" | "approved" | "declined";

export interface StopBrief {
  id: string;
  name: string;
  sequence: number;
}

export interface CurrentRoute {
  route_id: string;
  route_code: string;
  route_name: string;
  pickup_stop: StopBrief | null;
  dropoff_stop: StopBrief | null;
  active_from: string;
}

export interface LinkedGuardian {
  guardian_id: string;
  full_name: string;
  whatsapp_number: string;
  email: string | null;
  status: GuardianStatus;
  has_consent: boolean;
  relationship: GuardianRelationship;
  is_primary: boolean;
  receives_messages: boolean;
}

export interface EmergencyContact {
  id: string;
  name: string;
  phone: string;
  relationship: string | null;
}

export interface StudentSummary {
  id: string;
  first_name: string;
  last_name: string;
  grade: string | null;
  status: StudentStatus;
  guardians: LinkedGuardian[];
  route: CurrentRoute | null;
}

export interface StudentDetail extends StudentSummary {
  emergency_contacts: EmergencyContact[];
}

export interface GuardianInput {
  full_name: string;
  whatsapp_number: string;
  email?: string | null;
  relationship: GuardianRelationship;
  is_primary?: boolean;
  receives_messages?: boolean;
}

export interface ChildBrief {
  id: string;
  first_name: string;
  last_name: string;
}

export interface GuardianSummary {
  id: string;
  full_name: string;
  whatsapp_number: string;
  email: string | null;
  status: GuardianStatus;
  has_consent: boolean;
  children: ChildBrief[];
}

export interface GuardianInviteCreated {
  guardian_id: string;
  full_name: string;
  whatsapp_number: string;
  expires_at: string;
  invite_url: string | null;
}

export interface RouteSummary {
  id: string;
  code: string;
  name: string;
  is_active: boolean;
  stop_count: number;
}

export interface Stop {
  id: string;
  name: string;
  landmark: string | null;
  sequence: number;
  latitude: number | null;
  longitude: number | null;
}

export interface Run {
  id: string;
  direction: RunDirection;
  departure_time: string;
  vehicle_id: string | null;
  driver_membership_id: string;
  conductor_membership_id: string | null;
}

export interface RouteDetail {
  id: string;
  code: string;
  name: string;
  is_active: boolean;
  stops: Stop[];
  runs: Run[];
}

export interface RunInput {
  departure_time: string;
  vehicle_id: string | null;
  driver_membership_id: string;
  conductor_membership_id: string | null;
}

export interface Vehicle {
  id: string;
  plate: string;
  seats: number;
  is_active: boolean;
}

export interface CrewMember {
  membership_id: string;
  name: string;
  email: string;
  role: MembershipRole;
  joined_at: string;
}

export interface CrewInvitation {
  id: string;
  email: string;
  role: MembershipRole;
  expires_at: string;
  invite_url: string | null;
}

export interface Crew {
  members: CrewMember[];
  pending_invitations: CrewInvitation[];
}

export interface RouteAssignmentInput {
  route_id: string;
  pickup_stop_id: string | null;
  dropoff_stop_id: string | null;
}

export interface StopChangeRequest {
  id: string;
  student: ChildBrief;
  guardian_id: string;
  guardian_name: string;
  current_route: CurrentRoute | null;
  requested_stop: StopBrief | null;
  requested_location: string | null;
  status: RequestStatus;
  created_at: string;
  decided_at: string | null;
}

// Students

export function listStudents(params: {
  q?: string;
  status?: StudentStatus;
  route_id?: string;
}): Promise<StudentSummary[]> {
  const query = new URLSearchParams();
  if (params.q) query.set("q", params.q);
  if (params.status) query.set("status", params.status);
  if (params.route_id) query.set("route_id", params.route_id);
  const suffix = query.size > 0 ? `?${query.toString()}` : "";
  return request<StudentSummary[]>(`${SCHOOL}/students${suffix}`);
}

export function getStudent(studentId: string): Promise<StudentDetail> {
  return request<StudentDetail>(`${SCHOOL}/students/${id(studentId)}`);
}

export function createStudent(payload: {
  first_name: string;
  last_name: string;
  grade: string | null;
  guardians: GuardianInput[];
}): Promise<StudentDetail> {
  return post<StudentDetail>(`${SCHOOL}/students`, payload);
}

export function updateStudent(
  studentId: string,
  payload: Partial<{ first_name: string; last_name: string; grade: string | null; status: StudentStatus }>,
): Promise<StudentDetail> {
  return patch<StudentDetail>(`${SCHOOL}/students/${id(studentId)}`, payload);
}

export function addGuardianToStudent(studentId: string, payload: GuardianInput): Promise<StudentDetail> {
  return post<StudentDetail>(`${SCHOOL}/students/${id(studentId)}/guardians`, payload);
}

export function updateGuardianLink(
  studentId: string,
  guardianId: string,
  payload: Partial<{ relationship: GuardianRelationship; is_primary: boolean; receives_messages: boolean }>,
): Promise<StudentDetail> {
  return patch<StudentDetail>(`${SCHOOL}/students/${id(studentId)}/guardians/${id(guardianId)}`, payload);
}

export function removeGuardianLink(studentId: string, guardianId: string): Promise<StudentDetail> {
  return del<StudentDetail>(`${SCHOOL}/students/${id(studentId)}/guardians/${id(guardianId)}`);
}

export function addEmergencyContact(
  studentId: string,
  payload: { name: string; phone: string; relationship: string | null },
): Promise<StudentDetail> {
  return post<StudentDetail>(`${SCHOOL}/students/${id(studentId)}/emergency-contacts`, payload);
}

export function removeEmergencyContact(contactId: string): Promise<StudentDetail> {
  return del<StudentDetail>(`${SCHOOL}/emergency-contacts/${id(contactId)}`);
}

export function setStudentRoute(studentId: string, payload: RouteAssignmentInput): Promise<StudentDetail> {
  return put<StudentDetail>(`${SCHOOL}/students/${id(studentId)}/route`, payload);
}

export function removeStudentRoute(studentId: string): Promise<StudentDetail> {
  return del<StudentDetail>(`${SCHOOL}/students/${id(studentId)}/route`);
}

// Guardians, invites and consent

export function listGuardians(params: { status?: GuardianStatus } = {}): Promise<GuardianSummary[]> {
  const suffix = params.status ? `?status=${params.status}` : "";
  return request<GuardianSummary[]>(`${SCHOOL}/guardians${suffix}`);
}

export function inviteGuardian(guardianId: string): Promise<GuardianInviteCreated> {
  return post<GuardianInviteCreated>(`${SCHOOL}/guardians/${id(guardianId)}/invite`);
}

export function invitePendingGuardians(): Promise<GuardianInviteCreated[]> {
  return post<GuardianInviteCreated[]>(`${SCHOOL}/guardians/invite-pending`);
}

export function recordConsent(guardianId: string): Promise<GuardianSummary> {
  return post<GuardianSummary>(`${SCHOOL}/guardians/${id(guardianId)}/consent`);
}

export function withdrawConsent(guardianId: string): Promise<GuardianSummary> {
  return del<GuardianSummary>(`${SCHOOL}/guardians/${id(guardianId)}/consent`);
}

// Routes, stops and runs

export function listRoutes(): Promise<RouteSummary[]> {
  return request<RouteSummary[]>(`${SCHOOL}/routes`);
}

export function getRoute(routeId: string): Promise<RouteDetail> {
  return request<RouteDetail>(`${SCHOOL}/routes/${id(routeId)}`);
}

export function createRoute(payload: { code: string; name: string }): Promise<RouteDetail> {
  return post<RouteDetail>(`${SCHOOL}/routes`, payload);
}

export function updateRoute(
  routeId: string,
  payload: Partial<{ code: string; name: string; is_active: boolean }>,
): Promise<RouteDetail> {
  return patch<RouteDetail>(`${SCHOOL}/routes/${id(routeId)}`, payload);
}

export function addStop(
  routeId: string,
  payload: { name: string; landmark: string | null },
): Promise<RouteDetail> {
  return post<RouteDetail>(`${SCHOOL}/routes/${id(routeId)}/stops`, payload);
}

export function reorderStops(routeId: string, stopIds: string[]): Promise<RouteDetail> {
  return put<RouteDetail>(`${SCHOOL}/routes/${id(routeId)}/stops/order`, { stop_ids: stopIds });
}

export function removeStop(stopId: string): Promise<RouteDetail> {
  return del<RouteDetail>(`${SCHOOL}/stops/${id(stopId)}`);
}

export function setRun(routeId: string, direction: RunDirection, payload: RunInput): Promise<Run> {
  return put<Run>(`${SCHOOL}/routes/${id(routeId)}/runs/${direction}`, payload);
}

export function removeRun(routeId: string, direction: RunDirection): Promise<void> {
  return del<void>(`${SCHOOL}/routes/${id(routeId)}/runs/${direction}`);
}

// Vehicles and crew

export function listVehicles(): Promise<Vehicle[]> {
  return request<Vehicle[]>(`${SCHOOL}/vehicles`);
}

export function addVehicle(payload: { plate: string; seats: number }): Promise<Vehicle> {
  return post<Vehicle>(`${SCHOOL}/vehicles`, payload);
}

export function updateVehicle(
  vehicleId: string,
  payload: Partial<{ plate: string; seats: number; is_active: boolean }>,
): Promise<Vehicle> {
  return patch<Vehicle>(`${SCHOOL}/vehicles/${id(vehicleId)}`, payload);
}

export function getCrew(): Promise<Crew> {
  return request<Crew>(`${SCHOOL}/crew`);
}

export function inviteCrew(payload: { email: string; role: MembershipRole }): Promise<CrewInvitation> {
  return post<CrewInvitation>(`${SCHOOL}/crew/invitations`, payload);
}

export function removeCrewMember(membershipId: string): Promise<void> {
  return del<void>(`${SCHOOL}/crew/members/${id(membershipId)}`);
}

// Stop-change requests

export function listStopChangeRequests(status: RequestStatus = "pending"): Promise<StopChangeRequest[]> {
  return request<StopChangeRequest[]>(`${SCHOOL}/stop-change-requests?status=${status}`);
}

export function approveStopChange(requestId: string, payload: RouteAssignmentInput): Promise<StudentDetail> {
  return post<StudentDetail>(`${SCHOOL}/stop-change-requests/${id(requestId)}/approve`, payload);
}

export function declineStopChange(requestId: string): Promise<StopChangeRequest> {
  return post<StopChangeRequest>(`${SCHOOL}/stop-change-requests/${id(requestId)}/decline`);
}

// --- Guardian registration (public, from the invite link) --------------------

export interface InvitedChild {
  id: string;
  first_name: string;
  last_name: string;
  grade: string | null;
  route: CurrentRoute | null;
  stops_on_route: StopBrief[];
}

export interface GuardianInvitePreview {
  school_name: string;
  full_name: string;
  whatsapp_number: string;
  email: string | null;
  children: InvitedChild[];
  consent_version: string;
  consent_text: string;
}

export interface GuardianConfirmPayload {
  full_name: string;
  email: string | null;
  consent: boolean;
  consent_version: string;
  second_guardian: { full_name: string; whatsapp_number: string; relationship: GuardianRelationship } | null;
  emergency_contacts: { student_id: string; name: string; phone: string; relationship: string | null }[];
  stop_changes: { student_id: string; requested_stop_id: string | null; requested_location: string | null }[];
}

export function fetchGuardianInvite(token: string): Promise<GuardianInvitePreview> {
  return request<GuardianInvitePreview>(`/api/v1/guardian-invites/${id(token)}`);
}

export function confirmGuardianInvite(
  token: string,
  payload: GuardianConfirmPayload,
): Promise<{ message: string; school_name: string }> {
  return post(`/api/v1/guardian-invites/${id(token)}/confirm`, payload);
}
