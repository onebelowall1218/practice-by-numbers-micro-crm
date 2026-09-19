// Thin fetch wrapper. All endpoints are relative (/api/...) so the same build works behind the
// Vite dev proxy and when FastAPI serves the built app.

import type {
  CustomerDetail,
  CustomerSummary,
  Dashboard,
  Draft,
  FollowUpUpdate,
  Health,
  InteractionCreate,
} from "./types";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(response.status, body.detail ?? response.statusText);
  }
  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<Health>("/api/health"),
  dashboard: () => request<Dashboard>("/api/dashboard"),
  customers: () => request<CustomerSummary[]>("/api/customers"),
  customer: (id: string) => request<CustomerDetail>(`/api/customers/${id}`),
  addInteraction: (id: string, payload: InteractionCreate) =>
    request<CustomerDetail>(`/api/customers/${id}/interactions`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  reanalyze: (id: string) =>
    request<CustomerDetail>(`/api/customers/${id}/analyze`, { method: "POST" }),
  updateFollowUp: (id: string, payload: FollowUpUpdate) =>
    request<CustomerDetail>(`/api/customers/${id}/follow-up`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  draftMessage: (id: string) =>
    request<Draft>(`/api/customers/${id}/draft-message`, { method: "POST" }),
};
