import type {
  Achievement,
  CompletionResult,
  DashboardData,
  DailyChallenge,
  HistoryData,
  Pattern,
  ProgressData,
  Question,
  User,
  XPHistoryData,
  RegistrationResult,
} from "./types";

// Keep local development same-origin so Vite can proxy API calls without a
// separate CORS configuration. Production builds should provide VITE_API_URL
// when the API is hosted on another origin. Accepting the backend origin
// without /api prevents a common deployment misconfiguration from producing
// requests to /auth/*, which is not a Django route in this application.
function normalizeApiUrl(value?: string) {
  const configured = (value || "/api").trim().replace(/\/$/, "");
  if (/^https?:\/\/[^/]+$/i.test(configured)) return `${configured}/api`;
  return configured || "/api";
}

const API_URL = normalizeApiUrl(import.meta.env.VITE_API_URL);
const TOKEN_KEY = "dsa-quest-token";

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(message: string, status = 0, detail = message) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

let unauthorizedHandler: (() => void) | undefined;

export function setUnauthorizedHandler(handler?: () => void) {
  unauthorizedHandler = handler;
}

function getStoredToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function storeToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

export function hasToken() {
  return Boolean(getStoredToken());
}

function detailFromPayload(payload: unknown): string {
  if (!payload) return "Something went wrong. Please try again.";
  if (typeof payload === "string") return payload;
  if (typeof payload === "object") {
    const data = payload as Record<string, unknown>;
    if (typeof data.detail === "string") return data.detail;
    for (const value of Object.values(data)) {
      if (Array.isArray(value) && typeof value[0] === "string") return value[0];
      if (typeof value === "string") return value;
    }
  }
  return "Something went wrong. Please try again.";
}

async function request<T>(path: string, options: RequestInit = {}, includeAuth = true): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Accept", "application/json");
  if (options.body) headers.set("Content-Type", "application/json");
  const token = includeAuth ? getStoredToken() : null;
  if (includeAuth && token) headers.set("Authorization", `Token ${token}`);

  let response: Response;
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 30_000);
  try {
    response = await fetch(path.startsWith("http") ? path : `${API_URL}${path}`, { ...options, headers, signal: controller.signal });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiError("The DSA Quest API took too long to respond. Please try again.");
    }
    throw new ApiError("The DSA Quest API is unavailable. Start the backend and try again.");
  } finally {
    window.clearTimeout(timeout);
  }

  const contentType = response.headers.get("content-type") || "";
  if (response.status === 401 && token === getStoredToken()) {
    clearToken();
    unauthorizedHandler?.();
  }

  let payload: unknown = null;
  if (response.status !== 204) {
    try {
      if (contentType.includes("json")) payload = await response.json();
      else if (contentType.startsWith("text/")) payload = await response.text();
    } catch {
      payload = null;
    }
  }

  if (!response.ok) {
    const genericMessage = response.status >= 500 || contentType.includes("text/html")
      ? "The DSA Quest API is temporarily unavailable. Please try again."
      : detailFromPayload(payload);
    throw new ApiError(genericMessage, response.status, genericMessage);
  }
  return payload as T;
}

function unwrapList<T>(payload: T[] | { results: T[] }): T[] {
  return Array.isArray(payload) ? payload : payload.results;
}

async function requestAll<T>(path: string): Promise<T[]> {
  const values: T[] = [];
  let next: string | null = path;
  while (next) {
    const payload: T[] | { results: T[]; next?: string | null } = await request<T[] | { results: T[]; next?: string | null }>(next);
    values.push(...unwrapList(payload));
    if (Array.isArray(payload) || !payload.next) break;
    try {
      const parsed: URL = new URL(payload.next, window.location.origin);
      const apiPath = API_URL.startsWith("http") ? new URL(API_URL).pathname : API_URL;
      next = `${parsed.pathname.startsWith(apiPath) ? parsed.pathname.slice(apiPath.length) || "/" : parsed.pathname}${parsed.search}`;
    } catch {
      next = payload.next;
    }
  }
  return values;
}

export const api = {
  login: (body: { email: string; password: string }) =>
    request<{ token: string; user: User }>("/auth/login/", { method: "POST", body: JSON.stringify(body) }, false),
  register: (body: { email: string; password: string; confirm_password: string; display_name: string; timezone: string; challenge_mode: string }) =>
    request<RegistrationResult>("/auth/register/", { method: "POST", body: JSON.stringify(body) }, false),
  logout: () => request<null>("/auth/logout/", { method: "POST" }),
  me: () => request<User>("/auth/me/"),
  updateMe: (body: Partial<Pick<User, "display_name" | "timezone" | "challenge_mode">>) =>
    request<User>("/auth/me/", { method: "PATCH", body: JSON.stringify(body) }),
  resendVerification: (email: string) =>
    request<{ detail: string }>("/auth/email/resend/", { method: "POST", body: JSON.stringify({ email }) }, false),
  verifyEmail: (uid: string, token: string) =>
    request<{ detail: string; already_verified?: boolean }>("/auth/email/verify/", { method: "POST", body: JSON.stringify({ uid, token }) }, false),
  requestPasswordReset: (email: string) =>
    request<{ detail: string }>("/auth/password-reset/request/", { method: "POST", body: JSON.stringify({ email }) }, false),
  resetPassword: (body: { uid: string; token: string; new_password: string; confirm_password: string }) =>
    request<{ detail: string }>("/auth/password-reset/confirm/", { method: "POST", body: JSON.stringify(body) }, false),
  dashboard: () => request<DashboardData>("/dashboard/"),
  today: () => request<DailyChallenge>("/challenges/today/"),
  generateChallenge: () => request<DailyChallenge>("/challenges/generate/", { method: "POST" }),
  questions: async (params: { difficulty?: string; pattern?: string; ordering?: string } = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => value && query.set(key, value));
    const suffix = query.toString() ? `?${query.toString()}` : "";
    return requestAll<Question>(`/questions/${suffix}`);
  },
  question: (id: number) => request<Question>(`/questions/${id}/`),
  complete: (id: number, personal_notes = "") =>
    request<CompletionResult>(`/questions/${id}/complete/`, {
      method: "POST",
      body: JSON.stringify({ personal_notes }),
    }),
  progress: () => request<ProgressData>("/progress/"),
  history: async (days = 30) => request<HistoryData>(`/progress/history/?days=${days}`),
  patterns: () => requestAll<Pattern>("/patterns/"),
  pattern: (id: number) => request<Pattern>(`/patterns/${id}/`),
  achievements: () => request<Achievement[]>("/achievements/"),
  streak: () => request<{ today: string; today_goal_completed: boolean; today_questions_completed: number; current_streak: number; longest_streak: number }>("/streak/"),
  xpHistory: () => request<XPHistoryData>("/xp/history/"),
};

export { API_URL, TOKEN_KEY };
