// The only place components talk to the server. Mutations refresh the affected queries.

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "./client";
import type { FollowUpUpdate, InteractionCreate } from "./types";

export const queryKeys = {
  health: ["health"] as const,
  dashboard: ["dashboard"] as const,
  customer: (id: string) => ["customer", id] as const,
};

export function useHealth() {
  return useQuery({ queryKey: queryKeys.health, queryFn: api.health, staleTime: Infinity });
}

export function useDashboard() {
  return useQuery({ queryKey: queryKeys.dashboard, queryFn: api.dashboard });
}

export function useCustomer(id: string) {
  return useQuery({ queryKey: queryKeys.customer(id), queryFn: () => api.customer(id) });
}

function useCustomerMutation<TVariables>(
  id: string,
  mutationFn: (variables: TVariables) => ReturnType<typeof api.customer>,
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn,
    onSuccess: (detail) => {
      queryClient.setQueryData(queryKeys.customer(id), detail);
      void queryClient.invalidateQueries({ queryKey: queryKeys.dashboard });
    },
  });
}

export function useAddInteraction(id: string) {
  return useCustomerMutation(id, (payload: InteractionCreate) => api.addInteraction(id, payload));
}

export function useReanalyze(id: string) {
  return useCustomerMutation(id, () => api.reanalyze(id));
}

export function useUpdateFollowUp(id: string) {
  return useCustomerMutation(id, (payload: FollowUpUpdate) => api.updateFollowUp(id, payload));
}

export function useDraftMessage(id: string) {
  return useMutation({ mutationFn: () => api.draftMessage(id) });
}
