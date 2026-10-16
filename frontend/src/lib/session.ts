/**
 * The signed-in session, as the API sees it.
 *
 * The cookie is httpOnly, so the browser cannot read it; this asks the API who
 * we are and caches the answer.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  acceptInvite,
  fetchSession,
  signIn,
  signOut,
  type Session,
  type User,
} from "@/lib/api";

export const sessionKey = ["session"] as const;

export interface SessionState {
  session: Session | null;
  user: User | null;
  isSignedIn: boolean;
  isPlatformAdmin: boolean;
  isLoading: boolean;
  school: Session["memberships"][number] | null;
  /** The crew membership (driver or conductor) if this person is crew anywhere. */
  crew: Session["memberships"][number] | null;
}

export function useSession(): SessionState {
  const query = useQuery({
    queryKey: sessionKey,
    queryFn: fetchSession,
    retry: false,
    staleTime: 30_000,
  });

  const session = query.data ?? null;
  return {
    session,
    user: session?.user ?? null,
    isSignedIn: session !== null,
    isPlatformAdmin: session?.user.is_platform_admin ?? false,
    isLoading: query.isPending,
    school: session?.memberships[0] ?? null,
    crew:
      session?.memberships.find(
        (membership) => membership.role === "driver" || membership.role === "conductor",
      ) ?? null,
  };
}

export function useSignIn() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      signIn(email, password),
    onSuccess: (session) => {
      queryClient.setQueryData(sessionKey, session);
    },
  });
}

export function useAcceptInvite() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { token: string; name: string; password: string }) =>
      acceptInvite(payload),
    onSuccess: (session) => {
      queryClient.setQueryData(sessionKey, session);
    },
  });
}

export function useSignOut() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: signOut,
    onSettled: () => {
      queryClient.setQueryData(sessionKey, null);
      queryClient.clear();
    },
  });
}
