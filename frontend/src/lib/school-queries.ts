/** Shared query keys and cache refresh for the school screens. */

import { useMutation, useQueryClient } from "@tanstack/react-query";

export const schoolKeys = {
  students: (filters: object) => ["students", filters] as const,
  student: (studentId: string) => ["student", studentId] as const,
  guardians: ["guardians"] as const,
  routes: ["routes"] as const,
  route: (routeId: string) => ["route", routeId] as const,
  vehicles: ["vehicles"] as const,
  crew: ["crew"] as const,
  stopRequests: ["stop-requests"] as const,
};

/**
 * A mutation that refreshes every school list afterwards. School data is small and
 * interlinked (a guardian change shows on the child, the list and the requests), so a
 * broad refresh is simpler and safer than tracking each dependency.
 */
export function useSchoolMutation<TVariables, TResult>(
  mutationFn: (variables: TVariables) => Promise<TResult>,
  onSuccess?: (result: TResult) => void,
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn,
    onSuccess: async (result) => {
      onSuccess?.(result);
      await Promise.all(
        ["students", "student", "guardians", "routes", "route", "vehicles", "crew", "stop-requests"].map(
          (key) => queryClient.invalidateQueries({ queryKey: [key] }),
        ),
      );
    },
  });
}
