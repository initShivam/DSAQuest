import {
  createContext,
  useContext,
  useCallback,
  useEffect,
  useMemo,
  useState,
  type FormEvent,
  type ReactNode,
} from "react";
import { useAuth } from "./auth";
import { ApiError, api } from "./api";
import type {
  Achievement,
  DailyActivity,
  DailyChallenge,
  Difficulty,
  HistoryData,
  Level,
  Pattern,
  ProgressData,
  Question,
  QuestionProgress,
} from "./types";

type IconName =
  | "grid"
  | "target"
  | "layers"
  | "chart"
  | "trophy"
  | "clock"
  | "user"
  | "arrow"
  | "menu"
  | "close"
  | "sun"
  | "moon"
  | "flame"
  | "check"
  | "external"
  | "chevron"
  | "refresh"
  | "lock"
  | "calendar"
  | "zap"
  | "logout"
  | "settings"
  | "search"
  | "spark"
  | "book"
  | "sliders"
  | "info"
  | "eye"
  | "eyeOff";

function Icon({ name, size = 18 }: { name: IconName; size?: number }) {
  const common = { width: size, height: size, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round" as const, strokeLinejoin: "round" as const, "aria-hidden": true };
  const paths: Record<IconName, ReactNode> = {
    grid: <><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></>,
    target: <><circle cx="12" cy="12" r="8.5" /><circle cx="12" cy="12" r="4.5" /><path d="m12 12 5.2-5.2" /><path d="M17.2 6.8h-3.5" /><path d="M17.2 6.8v3.5" /></>,
    layers: <><path d="m12 3 9 5-9 5-9-5 9-5Z" /><path d="m3 12 9 5 9-5" /><path d="m3 16 9 5 9-5" /></>,
    chart: <><path d="M4 19V5" /><path d="M4 19h17" /><path d="m7 15 3-4 3 2 5-7" /><path d="M15 6h3v3" /></>,
    trophy: <><path d="M8 21h8" /><path d="M12 17v4" /><path d="M7 4h10v6a5 5 0 0 1-10 0V4Z" /><path d="M7 7H4v1a4 4 0 0 0 4 4" /><path d="M17 7h3v1a4 4 0 0 1-4 4" /></>,
    clock: <><circle cx="12" cy="12" r="8.5" /><path d="M12 7v5l3 2" /></>,
    user: <><circle cx="12" cy="8" r="3.5" /><path d="M4.5 20c.9-3.2 3.3-5 7.5-5s6.6 1.8 7.5 5" /></>,
    arrow: <><path d="M5 12h14" /><path d="m13 6 6 6-6 6" /></>,
    menu: <><path d="M4 6h16" /><path d="M4 12h16" /><path d="M4 18h16" /></>,
    close: <><path d="m6 6 12 12" /><path d="m18 6-12 12" /></>,
    sun: <><circle cx="12" cy="12" r="3.5" /><path d="M12 2v2" /><path d="M12 20v2" /><path d="m4.9 4.9 1.4 1.4" /><path d="m17.7 17.7 1.4 1.4" /><path d="M2 12h2" /><path d="M20 12h2" /><path d="m4.9 19.1 1.4-1.4" /><path d="m17.7 6.3 1.4-1.4" /></>,
    moon: <><path d="M20.5 15.5A8.5 8.5 0 0 1 8.5 3.5 8.6 8.6 0 1 0 20.5 15.5Z" /><path d="M17 4v3M15.5 5.5h3" /></>,
    flame: <path d="M12.3 21c4.1 0 6.7-2.5 6.7-6.2 0-3-1.7-5.5-4.6-7.8.1 2.2-.8 3.6-2.1 4.4.2-3.4-1.2-5.8-3.8-7.4.2 2.8-3.5 5.1-3.5 9 0 4.5 3.1 8 7.3 8Z" />,
    check: <><path d="m5 12 4.2 4.2L19 6.5" /></>,
    external: <><path d="M14 4h6v6" /><path d="m20 4-9 9" /><path d="M18 13v5a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h5" /></>,
    chevron: <path d="m9 18 6-6-6-6" />,
    refresh: <><path d="M20 11a8.1 8.1 0 0 0-14.8-3L3 11" /><path d="M3 5v6h6" /><path d="M4 13a8.1 8.1 0 0 0 14.8 3L21 13" /><path d="M21 19v-6h-6" /></>,
    lock: <><rect x="5" y="10" width="14" height="10" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></>,
    calendar: <><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M16 3v4M8 3v4M3 10h18" /></>,
    zap: <path d="m13 2-9 12h7l-1 8 9-12h-7l1-8Z" />,
    logout: <><path d="M10 17l5-5-5-5" /><path d="M15 12H3" /><path d="M21 19V5a2 2 0 0 0-2-2h-6" /></>,
    settings: <><path d="M12 15.2a3.2 3.2 0 1 0 0-6.4 3.2 3.2 0 0 0 0 6.4Z" /><path d="m19.4 15 .1.1a2 2 0 0 1-2.8 2.8l-.1-.1a2 2 0 0 0-3.4 1.4v.2a2 2 0 0 1-4 0v-.2a2 2 0 0 0-3.4-1.4l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1A2 2 0 0 0 1.7 12a2 2 0 0 1 2-2h.2a2 2 0 0 0 1.4-3.4l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1A2 2 0 0 0 11.5 2h.2a2 2 0 0 1 2 2v.2a2 2 0 0 0 3.4 1.4l.1-.1A2 2 0 1 1 20 8.3l-.1.1A2 2 0 0 0 21.3 12a2 2 0 0 1-2 2h-.2a2 2 0 0 0 .3 1Z" /></>,
    search: <><circle cx="10.8" cy="10.8" r="6.8" /><path d="m16 16 5 5" /></>,
    spark: <><path d="m12 3-1.2 5.8L5 10l5.8 1.2L12 17l1.2-5.8L19 10l-5.8-1.2L12 3Z" /><path d="m19 16-.5 2.5L16 19l2.5.5L19 22l.5-2.5L22 19l-2.5-.5L19 16Z" /></>,
    book: <><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v16H6.5A2.5 2.5 0 0 0 4 21V5.5Z" /><path d="M4 5.5v15" /><path d="M8 7h8M8 11h8" /></>,
    sliders: <><path d="M4 6h16M4 12h16M4 18h16" /><circle cx="9" cy="6" r="2" /><circle cx="15" cy="12" r="2" /><circle cx="11" cy="18" r="2" /></>,
    info: <><circle cx="12" cy="12" r="9" /><path d="M12 11v5" /><path d="M12 8h.01" /></>,
    eye: <><path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z" /><circle cx="12" cy="12" r="2.5" /></>,
    eyeOff: <><path d="m3 3 18 18" /><path d="M10.6 6.2A10.8 10.8 0 0 1 12 6c6 0 9.5 6 9.5 6a16.8 16.8 0 0 1-3 3.6" /><path d="M6.2 6.8C3.8 8.5 2.5 12 2.5 12s3.5 6 9.5 6c1.2 0 2.3-.2 3.3-.6" /><path d="M9.9 9.9a3 3 0 0 0 4.2 4.2" /></>,
  };
  return <svg {...common}>{paths[name]}</svg>;
}

type Theme = "dark" | "light";
const THEME_KEY = "dsa-quest-theme";
const ThemeContext = createContext<{ theme: Theme; toggleTheme: () => void }>({ theme: "dark", toggleTheme: () => undefined });

function getInitialTheme(): Theme {
  if (typeof window === "undefined") return "dark";
  const saved = window.localStorage.getItem(THEME_KEY);
  return saved === "light" || saved === "dark" ? saved : "dark";
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(getInitialTheme);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;
    document.querySelector('meta[name="theme-color"]')?.setAttribute("content", theme === "light" ? "#f6f2ec" : "#0b1017");
    window.localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  const value = useMemo(() => ({ theme, toggleTheme: () => setTheme((current) => current === "dark" ? "light" : "dark") }), [theme]);
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

function useTheme() {
  return useContext(ThemeContext);
}

function ThemeToggle({ compact = false }: { compact?: boolean }) {
  const { theme, toggleTheme } = useTheme();
  const nextTheme = theme === "dark" ? "light" : "dark";
  return <button className={compact ? "icon-button theme-toggle" : "theme-toggle theme-toggle-wide"} onClick={toggleTheme} aria-label={`Switch to ${nextTheme} mode`} aria-pressed={theme === "light"} title={`Switch to ${nextTheme} mode`}><Icon name={theme === "dark" ? "sun" : "moon"} size={compact ? 18 : 16} />{!compact && <span>{theme === "dark" ? "Light mode" : "Dark mode"}</span>}</button>;
}

const navItems: { label: string; path: string; icon: IconName }[] = [
  { label: "Dashboard", path: "/", icon: "grid" },
  { label: "Daily Quest", path: "/quest", icon: "target" },
  { label: "Patterns", path: "/patterns", icon: "layers" },
  { label: "Progress", path: "/progress", icon: "chart" },
  { label: "Achievements", path: "/achievements", icon: "trophy" },
  { label: "History", path: "/history", icon: "clock" },
  { label: "Profile", path: "/profile", icon: "user" },
];

function navigateTo(path: string) {
  if (window.location.pathname === path) return;
  window.history.pushState({}, "", path);
  window.dispatchEvent(new PopStateEvent("popstate"));
  window.scrollTo({ top: 0, behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
}

let displayTimeZone = Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";

function useRoute() {
  const [path, setPath] = useState(window.location.pathname || "/");
  useEffect(() => {
    const update = () => setPath(window.location.pathname || "/");
    window.addEventListener("popstate", update);
    return () => window.removeEventListener("popstate", update);
  }, []);
  return path;
}

function formatDate(date: string | Date, options: Intl.DateTimeFormatOptions = { month: "short", day: "numeric" }, timeZone?: string) {
  const dateOnly = typeof date === "string" && date.length === 10;
  const value = typeof date === "string" ? new Date(dateOnly ? `${date}T12:00:00Z` : date) : date;
  return new Intl.DateTimeFormat(undefined, { ...options, timeZone: dateOnly ? "UTC" : timeZone || displayTimeZone }).format(value);
}

function formatLongDate(date: string) {
  return formatDate(date, { weekday: "long", month: "long", day: "numeric" });
}

function titleCase(value: string) {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function dateKeyInTimeZone(date: Date, timeZone: string) {
  const parts = new Intl.DateTimeFormat("en-US", { timeZone, year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(date);
  const values = Object.fromEntries(parts.filter((part) => part.type !== "literal").map((part) => [part.type, part.value]));
  return `${values.year}-${values.month}-${values.day}`;
}

function shiftDateKey(dateKey: string, offset: number) {
  const date = new Date(`${dateKey}T12:00:00Z`);
  date.setUTCDate(date.getUTCDate() + offset);
  return date.toISOString().slice(0, 10);
}

function recentDateKeys(count: number, timeZone: string) {
  const today = dateKeyInTimeZone(new Date(), timeZone);
  return Array.from({ length: count }, (_, index) => shiftDateKey(today, index - count + 1));
}

function initials(name: string) {
  return name.split(" ").filter(Boolean).slice(0, 2).map((part) => part[0]).join("").toUpperCase() || "DQ";
}

function errorMessage(error: unknown) {
  if (error instanceof ApiError) return error.detail;
  return "We couldn't load this section. Please try again.";
}

function useLoad<T>(loader: () => Promise<T>, dependencies: unknown[] = []) {
  const [state, setState] = useState<{ data: T | null; loading: boolean; error: unknown }>({ data: null, loading: true, error: null });
  const [reloadKey, setReloadKey] = useState(0);
  useEffect(() => {
    let active = true;
    setState((current) => ({ ...current, loading: true, error: null }));
    loader()
      .then((data) => active && setState({ data, loading: false, error: null }))
      .catch((error) => active && setState({ data: null, loading: false, error }));
    return () => { active = false; };
    // The loader is intentionally supplied by each page and keyed by its request inputs.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...dependencies, reloadKey]);
  return { ...state, reload: () => setReloadKey((key) => key + 1) };
}

function App() {
  const path = useRoute();
  const { user, loading } = useAuth();
  if (isPublicAuthPath(path)) return <AuthFlowScreen path={path} />;
  if (loading) return <FullScreenLoader label="Checking your session" />;
  if (!user) return <AuthScreen />;
  return <AppShell />;
}

function isPublicAuthPath(path: string) {
  return path === "/forgot-password" || path === "/reset-password" || path === "/verify-email";
}

function FullScreenLoader({ label }: { label: string }) {
  return <div className="full-screen-loader"><div className="loader-mark"><span /></div><p>{label}<span className="loading-dots">...</span></p></div>;
}

function AuthPageLayout({ children }: { children: ReactNode }) {
  return <main className="auth-page">
    <section className="auth-story" aria-label="DSA Quest overview">
      <div className="brand brand-large"><span className="brand-glyph"><span /></span><span>DSA<span className="brand-accent">Quest</span></span></div>
      <div className="story-copy">
        <p className="eyebrow">A better daily loop</p>
        <h1>Make progress<br /><em>visible.</em></h1>
        <p className="story-lead">A calm, focused workspace for turning interview prep into a habit that compounds.</p>
      </div>
      <div className="story-list">
        <div><span className="story-icon"><Icon name="target" size={18} /></span><span><strong>One clear quest</strong><small>Two curated problems, every day.</small></span></div>
        <div><span className="story-icon"><Icon name="chart" size={18} /></span><span><strong>See your trajectory</strong><small>Patterns, streaks, and real momentum.</small></span></div>
        <div><span className="story-icon"><Icon name="spark" size={18} /></span><span><strong>Build the signal</strong><small>Small wins that add up to confidence.</small></span></div>
      </div>
      <p className="story-foot">Built for deliberate practice · v1.0</p>
    </section>
    <section className="auth-panel">
      <div className="auth-form-wrap">
        <div className="auth-theme-row"><span>Appearance</span><ThemeToggle compact /></div>
        <div className="mobile-brand brand"><span className="brand-glyph"><span /></span><span>DSA<span className="brand-accent">Quest</span></span></div>
        {children}
      </div>
    </section>
  </main>;
}

function AuthScreen() {
  const { signIn, signUp } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [form, setForm] = useState({ email: "", password: "", confirm_password: "", display_name: "", timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC", challenge_mode: "balanced" });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [pendingEmail, setPendingEmail] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      if (mode === "login") await signIn(form.email, form.password);
      else {
        if (form.password !== form.confirm_password) {
          setError("Passwords do not match.");
          return;
        }
        const result = await signUp(form);
        setPendingEmail(result.email);
      }
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setSubmitting(false);
    }
  };

  if (pendingEmail) return <AuthPageLayout><VerificationPending email={pendingEmail} /></AuthPageLayout>;
  return <AuthPageLayout>
    <div className="auth-heading"><p className="eyebrow">{mode === "login" ? "Welcome back" : "Start your run"}</p><h2>{mode === "login" ? "Continue your quest." : "Create your account."}</h2><p>{mode === "login" ? "Pick up where your practice left off." : "A focused practice system, ready when you are."}</p></div>
    <div className="auth-tabs" role="tablist" aria-label="Authentication mode"><button type="button" className={mode === "login" ? "active" : ""} onClick={() => { setMode("login"); setError(""); }} role="tab" aria-selected={mode === "login"}>Sign in</button><button type="button" className={mode === "register" ? "active" : ""} onClick={() => { setMode("register"); setError(""); }} role="tab" aria-selected={mode === "register"}>Create account</button></div>
    <form onSubmit={submit} className="auth-form">
      {mode === "register" && <Field label="Display name" value={form.display_name} onChange={(value) => setForm({ ...form, display_name: value })} placeholder="How should we call you?" autoComplete="name" required />}
      <Field label="Email address" type="email" value={form.email} onChange={(value) => setForm({ ...form, email: value })} placeholder="you@example.com" autoComplete="email" required />
      <PasswordField label="Password" value={form.password} onChange={(value) => setForm({ ...form, password: value })} placeholder={mode === "register" ? "At least 8 characters" : "Enter your password"} autoComplete={mode === "login" ? "current-password" : "new-password"} required minLength={mode === "register" ? 8 : undefined} visible={showPassword} onToggle={() => setShowPassword((value) => !value)} />
      {mode === "login" && <div className="auth-field-action"><button type="button" className="auth-link" onClick={() => navigateTo("/forgot-password")}>Forgot password?</button></div>}
      {mode === "register" && <>
        <PasswordField label="Confirm password" value={form.confirm_password} onChange={(value) => setForm({ ...form, confirm_password: value })} placeholder="Repeat your password" autoComplete="new-password" required minLength={8} visible={showConfirmation} onToggle={() => setShowConfirmation((value) => !value)} />
        <p className="password-hint">Use at least 8 characters. A verification link will be sent before you can sign in.</p>
        <div className="form-row"><label className="field"><span>Challenge mode</span><select value={form.challenge_mode} onChange={(event) => setForm({ ...form, challenge_mode: event.target.value })}><option value="beginner">Beginner · Easy + Easy</option><option value="balanced">Balanced · Easy + Medium</option><option value="intermediate">Intermediate · Medium + Medium</option><option value="advanced">Advanced · Medium + Hard</option><option value="adaptive">Adaptive · Easy + Medium (MVP)</option></select></label><label className="field"><span>Timezone</span><input value={form.timezone} onChange={(event) => setForm({ ...form, timezone: event.target.value })} required /></label></div>
      </>}
      {error && <div className="form-error" role="alert"><Icon name="info" size={17} /><span>{error}</span></div>}
      {mode === "login" && error.toLowerCase().includes("verify") && <button type="button" className="auth-link auth-link-left" onClick={() => navigateTo("/verify-email")}>Need a new verification link?</button>}
      <button className="button button-primary button-wide" type="submit" disabled={submitting}>{submitting ? <><span className="button-spinner" /> {mode === "login" ? "Signing in" : "Creating account"}</> : <>{mode === "login" ? "Enter DSA Quest" : "Begin my quest"}<Icon name="arrow" size={17} /></>}</button>
    </form>
    <p className="auth-note"><Icon name="lock" size={14} /> Your account is secured by the DSA Quest API.</p>
  </AuthPageLayout>;
}

function Field({ label, value, onChange, placeholder, type = "text", autoComplete, required, minLength }: { label: string; value: string; onChange: (value: string) => void; placeholder?: string; type?: string; autoComplete?: string; required?: boolean; minLength?: number }) {
  return <label className="field"><span>{label}</span><input type={type} value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} autoComplete={autoComplete} required={required} minLength={minLength} /></label>;
}

function PasswordField({ label, value, onChange, placeholder, autoComplete, required, minLength, visible, onToggle }: { label: string; value: string; onChange: (value: string) => void; placeholder?: string; autoComplete?: string; required?: boolean; minLength?: number; visible: boolean; onToggle: () => void }) {
  return <label className="field"><span className="field-label-row"><span>{label}</span><button className="password-toggle" type="button" onClick={onToggle} aria-label={`${visible ? "Hide" : "Show"} ${label.toLowerCase()}`}><Icon name={visible ? "eyeOff" : "eye"} size={14} /> {visible ? "Hide" : "Show"}</button></span><span className="input-with-action"><input type={visible ? "text" : "password"} value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} autoComplete={autoComplete} required={required} minLength={minLength} /><span className="input-lock"><Icon name="lock" size={14} /></span></span></label>;
}

function AuthFlowScreen({ path }: { path: string }) {
  return <AuthPageLayout>{path === "/forgot-password" ? <ForgotPasswordPage /> : path === "/reset-password" ? <ResetPasswordPage /> : <VerifyEmailPage />}</AuthPageLayout>;
}

function AuthBackLink() {
  return <button type="button" className="auth-link auth-link-left" onClick={() => navigateTo("/")}>Back to sign in</button>;
}

function VerificationPending({ email }: { email: string }) {
  const [resending, setResending] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const resend = async () => {
    setResending(true); setMessage(""); setError("");
    try { const response = await api.resendVerification(email); setMessage(response.detail); }
    catch (requestError) { setError(errorMessage(requestError)); }
    finally { setResending(false); }
  };
  return <div className="auth-flow-card"><div className="auth-flow-icon"><Icon name="check" size={22} /></div><div className="auth-heading"><p className="eyebrow">Check your inbox</p><h2>Verify your email.</h2><p>We sent a verification link to <strong>{email}</strong>. Open it to activate your DSA Quest account.</p></div>{message && <div className="form-success" role="status">{message}</div>}{error && <div className="form-error" role="alert"><Icon name="info" size={17} /><span>{error}</span></div>}<button className="button button-secondary button-wide" type="button" onClick={resend} disabled={resending}>{resending ? <><span className="button-spinner" /> Sending</> : <><Icon name="refresh" size={15} /> Resend verification email</>}</button><AuthBackLink /></div>;
}

function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const submit = async (event: FormEvent) => {
    event.preventDefault(); setSubmitting(true); setMessage(""); setError("");
    try { const response = await api.requestPasswordReset(email); setMessage(response.detail); }
    catch (requestError) { setError(errorMessage(requestError)); }
    finally { setSubmitting(false); }
  };
  return <div className="auth-flow-card"><div className="auth-heading"><p className="eyebrow">Account recovery</p><h2>Forgot your password?</h2><p>Enter your email and we’ll send a secure reset link if an account exists.</p></div>{message ? <><div className="form-success" role="status">{message}</div><AuthBackLink /></> : <form onSubmit={submit} className="auth-form"><Field label="Email address" type="email" value={email} onChange={setEmail} placeholder="you@example.com" autoComplete="email" required />{error && <div className="form-error" role="alert"><Icon name="info" size={17} /><span>{error}</span></div>}<button className="button button-primary button-wide" type="submit" disabled={submitting}>{submitting ? <><span className="button-spinner" /> Sending</> : <>Send reset link <Icon name="arrow" size={17} /></>}</button><AuthBackLink /></form>}</div>;
}

function VerifyEmailPage() {
  const params = new URLSearchParams(window.location.search);
  const uid = params.get("uid") || "";
  const token = params.get("token") || "";
  const [state, setState] = useState<"loading" | "success" | "error">("loading");
  const [message, setMessage] = useState("");
  const [email, setEmail] = useState("");
  const [resending, setResending] = useState(false);
  useEffect(() => {
    if (!uid || !token) { setState("error"); setMessage("This verification link is incomplete or invalid."); return; }
    api.verifyEmail(uid, token).then((response) => { setState("success"); setMessage(response.detail); }).catch((error) => { setState("error"); setMessage(errorMessage(error)); });
  }, [uid, token]);
  const resend = async (event: FormEvent) => {
    event.preventDefault(); setResending(true);
    try { const response = await api.resendVerification(email); setMessage(response.detail); }
    catch (error) { setMessage(errorMessage(error)); }
    finally { setResending(false); }
  };
  if (state === "loading") return <div className="auth-flow-card"><div className="auth-flow-icon"><span className="button-spinner" /></div><div className="auth-heading"><p className="eyebrow">Email verification</p><h2>Checking your link.</h2><p>Please wait while we securely verify your email address.</p></div></div>;
  if (state === "success") return <div className="auth-flow-card"><div className="auth-flow-icon success"><Icon name="check" size={22} /></div><div className="auth-heading"><p className="eyebrow">You’re verified</p><h2>Welcome to DSA Quest.</h2><p>{message}</p></div><button className="button button-primary button-wide" type="button" onClick={() => navigateTo("/")}>Sign in <Icon name="arrow" size={17} /></button></div>;
  return <div className="auth-flow-card"><div className="auth-flow-icon error"><Icon name="info" size={22} /></div><div className="auth-heading"><p className="eyebrow">Link unavailable</p><h2>We couldn’t verify that link.</h2><p>{message} Request a new link below if you still need to activate your account.</p></div><form onSubmit={resend} className="auth-form"><Field label="Email address" type="email" value={email} onChange={setEmail} placeholder="you@example.com" autoComplete="email" required /><button className="button button-secondary button-wide" type="submit" disabled={resending}>{resending ? <><span className="button-spinner" /> Sending</> : <>Send a new verification link <Icon name="refresh" size={15} /></>}</button><AuthBackLink /></form></div>;
}

function ResetPasswordPage() {
  const params = new URLSearchParams(window.location.search);
  const uid = params.get("uid") || "";
  const token = params.get("token") || "";
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const submit = async (event: FormEvent) => {
    event.preventDefault(); setError("");
    if (!uid || !token) { setError("This password reset link is incomplete or invalid."); return; }
    if (password.length < 8) { setError("Use at least 8 characters for your new password."); return; }
    if (password !== confirmation) { setError("Passwords do not match."); return; }
    setSubmitting(true);
    try { await api.resetPassword({ uid, token, new_password: password, confirm_password: confirmation }); setSuccess(true); }
    catch (requestError) { setError(errorMessage(requestError)); }
    finally { setSubmitting(false); }
  };
  if (success) return <div className="auth-flow-card"><div className="auth-flow-icon success"><Icon name="check" size={22} /></div><div className="auth-heading"><p className="eyebrow">Password updated</p><h2>You’re ready to sign in.</h2><p>Your password was changed and existing sessions were signed out.</p></div><button className="button button-primary button-wide" type="button" onClick={() => navigateTo("/")}>Back to sign in <Icon name="arrow" size={17} /></button></div>;
  return <div className="auth-flow-card"><div className="auth-heading"><p className="eyebrow">Account recovery</p><h2>Choose a new password.</h2><p>Use a strong password you do not reuse elsewhere.</p></div><form onSubmit={submit} className="auth-form"><PasswordField label="New password" value={password} onChange={setPassword} placeholder="At least 8 characters" autoComplete="new-password" required minLength={8} visible={showPassword} onToggle={() => setShowPassword((value) => !value)} /><PasswordField label="Confirm new password" value={confirmation} onChange={setConfirmation} placeholder="Repeat your new password" autoComplete="new-password" required minLength={8} visible={showConfirmation} onToggle={() => setShowConfirmation((value) => !value)} /><p className="password-hint">Passwords must satisfy the security rules configured by DSA Quest.</p>{error && <div className="form-error" role="alert"><Icon name="info" size={17} /><span>{error}</span></div>}<button className="button button-primary button-wide" type="submit" disabled={submitting}>{submitting ? <><span className="button-spinner" /> Updating</> : <>Reset password <Icon name="arrow" size={17} /></>}</button><AuthBackLink /></form></div>;
}

function AppShell() {
  const { user, signOut } = useAuth();
  const path = useRoute();
  const [mobileNav, setMobileNav] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);
  const activePath = navItems.some((item) => item.path === path) ? path : "/";
  const current = navItems.find((item) => item.path === activePath) || navItems[0];

  useEffect(() => setMobileNav(false), [path]);
  useEffect(() => {
    document.body.classList.toggle("drawer-open", mobileNav);
    return () => document.body.classList.remove("drawer-open");
  }, [mobileNav]);
  useEffect(() => {
    if (user?.timezone) displayTimeZone = user.timezone;
  }, [user?.timezone]);
  useEffect(() => {
    if (!mobileNav) return;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setMobileNav(false);
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [mobileNav]);
  useEffect(() => {
    const media = window.matchMedia("(max-width: 800px)");
    const closeOnDesktop = (event: MediaQueryListEvent) => {
      if (!event.matches) setMobileNav(false);
    };
    media.addEventListener?.("change", closeOnDesktop);
    return () => media.removeEventListener?.("change", closeOnDesktop);
  }, []);

  const logout = async () => {
    setLoggingOut(true);
    try {
      await signOut();
    } catch {
      // Local credentials are cleared by AuthProvider even if the API is unavailable.
    } finally {
      setLoggingOut(false);
    }
  };

  return <ToastProvider><div className="app-shell">
    <button className={`mobile-overlay ${mobileNav ? "visible" : ""}`} onClick={() => setMobileNav(false)} aria-label="Close navigation" tabIndex={mobileNav ? 0 : -1} />
    <aside id="main-navigation" className={`sidebar ${mobileNav ? "open" : ""}`} aria-label="Main navigation">
      <div className="sidebar-top"><div className="brand"><span className="brand-glyph"><span /></span><span>DSA<span className="brand-accent">Quest</span></span></div><button className="icon-button mobile-close" onClick={() => setMobileNav(false)} aria-label="Close navigation"><Icon name="close" /></button></div>
      <div className="workspace-label"><span className="workspace-dot" /> Practice workspace</div>
      <nav className="main-nav" aria-label="Main navigation"><p className="nav-label">Workspace</p>{navItems.slice(0, 5).map((item) => <NavItem key={item.path} {...item} active={activePath === item.path} />)}<p className="nav-label nav-label-spaced">Review</p>{navItems.slice(5).map((item) => <NavItem key={item.path} {...item} active={activePath === item.path} />)}</nav>
      <div className="sidebar-bottom"><div className="sidebar-tip"><div className="tip-icon"><Icon name="spark" size={16} /></div><strong>Consistency beats intensity.</strong><span>Show up today. Future you will thank you.</span></div><button className="sidebar-account" onClick={() => navigateTo("/profile")}><span className="avatar avatar-small">{initials(user?.display_name || "")}</span><span className="account-text"><strong>{user?.display_name || "Developer"}</strong><small>{user?.email}</small></span><Icon name="chevron" size={15} /></button><button className="sidebar-logout" onClick={logout} disabled={loggingOut}><Icon name="logout" size={16} /> {loggingOut ? "Signing out..." : "Sign out"}</button></div>
    </aside>
    <div className="main-area">
      <header className="topbar"><div className="topbar-left"><button className="icon-button mobile-menu" onClick={() => setMobileNav(true)} aria-label="Open navigation" aria-expanded={mobileNav} aria-controls="main-navigation"><Icon name="menu" /></button><div><p className="breadcrumb"><span>Workspace</span><Icon name="chevron" size={13} /><strong>{current.label}</strong></p><p className="topbar-context">{activePath === "/" ? "Your daily practice at a glance" : current.label === "Daily Quest" ? "Keep today's momentum moving" : `Build your ${current.label.toLowerCase()} over time`}</p></div></div><div className="topbar-right"><span className="api-status"><span className="status-dot" /> API connected</span><ThemeToggle compact /><button className="icon-button" onClick={() => navigateTo("/profile")} aria-label="Open profile settings"><Icon name="settings" size={18} /></button><button className="avatar" onClick={() => navigateTo("/profile")} aria-label="Open profile">{initials(user?.display_name || "")}</button></div></header>
      <main className="page-content">{activePath === "/" && <DashboardView />} {activePath === "/quest" && <QuestView />} {activePath === "/patterns" && <PatternsView />} {activePath === "/progress" && <ProgressView />} {activePath === "/achievements" && <AchievementsView />} {activePath === "/history" && <HistoryView />} {activePath === "/profile" && <ProfileView />}</main>
    </div>
  </div></ToastProvider>;
}

function NavItem({ label, path, icon, active }: { label: string; path: string; icon: IconName; active: boolean }) {
  return <button className={`nav-item ${active ? "active" : ""}`} onClick={() => navigateTo(path)} aria-current={active ? "page" : undefined}><Icon name={icon} size={18} /><span>{label}</span>{label === "Daily Quest" && <span className="nav-live-dot" />}</button>;
}

function ToastProvider({ children }: { children: ReactNode }) {
  const [toast, setToast] = useState<{ message: string; tone: "success" | "info" | "error" } | null>(null);
  const showToast = useCallback((message: string, tone: "success" | "info" | "error" = "success") => setToast({ message, tone }), []);
  useEffect(() => { if (!toast) return; const timer = window.setTimeout(() => setToast(null), 4200); return () => window.clearTimeout(timer); }, [toast]);
  return <ToastContext.Provider value={showToast}>{children}{toast && <div className={`toast toast-${toast.tone}`} role="status"><span className="toast-symbol"><Icon name={toast.tone === "success" ? "check" : "info"} size={15} /></span>{toast.message}<button onClick={() => setToast(null)} aria-label="Dismiss notification"><Icon name="close" size={14} /></button></div>}</ToastContext.Provider>;
}

const ToastContext = createContext<(message: string, tone?: "success" | "info" | "error") => void>(() => undefined);
const useToast = () => useContext(ToastContext);

function PageHeader({ eyebrow, title, description, action }: { eyebrow: string; title: string; description: string; action?: ReactNode }) {
  return <div className="page-header"><div><p className="eyebrow">{eyebrow}</p><h1>{title}</h1><p className="page-description">{description}</p></div>{action && <div className="page-header-action">{action}</div>}</div>;
}

function SectionHeading({ title, detail, action }: { title: string; detail?: string; action?: ReactNode }) {
  return <div className="section-heading"><div><h2>{title}</h2>{detail && <p>{detail}</p>}</div>{action}</div>;
}

function ErrorNotice({ error, retry }: { error: unknown; retry: () => void }) {
  return <div className="state-card error-state"><div className="state-icon"><Icon name="info" size={20} /></div><div><strong>Couldn’t load this view</strong><p>{errorMessage(error)}</p><button className="button button-secondary button-small" onClick={retry}><Icon name="refresh" size={14} /> Try again</button></div></div>;
}

function EmptyState({ icon = "book", title, description }: { icon?: IconName; title: string; description: string }) {
  return <div className="state-card empty-state"><div className="state-icon"><Icon name={icon} size={20} /></div><div><strong>{title}</strong><p>{description}</p></div></div>;
}

function Skeleton({ className = "" }: { className?: string }) { return <div className={`skeleton ${className}`} />; }

function LoadingGrid({ count = 3 }: { count?: number }) { return <div className="loading-grid">{Array.from({ length: count }).map((_, index) => <div className="skeleton-card" key={index}><Skeleton className="skeleton-line short" /><Skeleton className="skeleton-line" /><Skeleton className="skeleton-line medium" /></div>)}</div>; }

function StatCard({ icon, label, value, detail, tone }: { icon: IconName; label: string; value: string | number; detail: string; tone: "orange" | "blue" | "green" | "purple" }) {
  return <div className="stat-card"><div className={`stat-icon stat-${tone}`}><Icon name={icon} size={18} /></div><div className="stat-copy"><span>{label}</span><strong>{value}</strong><small>{detail}</small></div></div>;
}

function DifficultyBadge({ difficulty }: { difficulty: Difficulty }) { return <span className={`difficulty difficulty-${difficulty}`}>{titleCase(difficulty)}</span>; }

function ProgressBar({ value, max, tone = "orange" }: { value: number; max: number; tone?: string }) { const percentage = max ? Math.min(100, (value / max) * 100) : 0; return <div className="progress-track" role="progressbar" aria-valuemin={0} aria-valuemax={max} aria-valuenow={Math.min(value, max)} aria-label={`${value} of ${max} complete`}><span className={`progress-fill fill-${tone}`} style={{ width: `${percentage}%` }} /></div>; }

function QuestProgress({ completed, total }: { completed: number; total: number }) {
  return <div className="quest-progress"><div className="quest-progress-label"><span>Daily goal</span><strong>{completed} <small>/ {total}</small></strong></div><ProgressBar value={completed} max={total} /><span className="quest-progress-note">{completed >= total ? "Goal complete — nice work." : `${total - completed} ${total - completed === 1 ? "problem" : "problems"} left to qualify`}</span></div>;
}

function QuestCard({ challenge, compact = false, onOpen }: { challenge: DailyChallenge; compact?: boolean; onOpen?: () => void }) {
  const mandatory = challenge.assignments.filter((assignment) => !assignment.is_bonus);
  const bonus = challenge.assignments.filter((assignment) => assignment.is_bonus);
  return <div className={`quest-card ${compact ? "quest-card-compact" : ""}`}>
    <div className="quest-card-head"><div><div className="quest-kicker"><span className="quest-kicker-mark"><Icon name="target" size={13} /></span> Today’s quest <span className="self-report-label">Self-reported</span></div><h3>{challenge.goal_completed ? "Daily goal complete" : "Two problems. One focused hour."}</h3><p>{formatLongDate(challenge.challenge_date)} <span className="dot-separator" /> {challenge.goal_completed ? "You showed up today." : "Your next step is ready."}</p></div><div className={`quest-status ${challenge.goal_completed ? "complete" : ""}`}><span>{challenge.goal_completed ? "Complete" : "In progress"}</span><span className="status-ring"><Icon name={challenge.goal_completed ? "check" : "target"} size={14} /></span></div></div>
    <QuestProgress completed={challenge.mandatory_completed} total={challenge.mandatory_total} />
    <div className="quest-items">{mandatory.map((assignment, index) => <AssignmentRow key={assignment.id} assignment={assignment} index={index} />)}</div>
    {bonus.map((assignment) => <AssignmentRow key={assignment.id} assignment={assignment} index={2} bonus />)}
    {!compact && onOpen && <button className="button button-primary quest-open-button" onClick={onOpen}>{challenge.goal_completed ? "Review today's quest" : "Open daily quest"}<Icon name="arrow" size={16} /></button>}
  </div>;
}

function AssignmentRow({ assignment, index, bonus = false }: { assignment: { id: number; question: Question; status: string; is_revision: boolean }; index: number; bonus?: boolean }) {
  const question = assignment.question;
  const done = assignment.status === "completed";
  return <div className={`assignment-row ${done ? "done" : ""} ${bonus ? "bonus-row" : ""}`}><span className={`assignment-number ${done ? "done-number" : ""}`}>{done ? <Icon name="check" size={15} /> : bonus ? "＋" : String(index + 1).padStart(2, "0")}</span><div className="assignment-main"><div className="assignment-title"><strong>{question.title}</strong>{assignment.is_revision && <span className="revision-pill">Revision</span>}</div><div className="assignment-meta"><DifficultyBadge difficulty={question.difficulty} />{question.patterns.slice(0, 2).map((pattern) => <span className="pattern-tag" key={pattern.id}>{pattern.name}</span>)}{question.estimated_minutes && <span className="time-meta"><Icon name="clock" size={13} /> {question.estimated_minutes} min</span>}</div></div><a className="external-link" href={question.leetcode_url} target="_blank" rel="noreferrer" aria-label={`Open ${question.title} on LeetCode`}>Solve <Icon name="external" size={14} /></a></div>;
}

function DashboardView() {
  const dashboard = useLoad(() => api.dashboard());
  const patterns = useLoad(() => api.patterns());
  const achievements = useLoad(() => api.achievements());
  const history = useLoad(() => api.history(7));
  const { user } = useAuth();
  const firstName = (user?.display_name || dashboard.data?.user.display_name || "there").split(" ")[0];
  const goQuest = () => navigateTo("/quest");

  if (dashboard.loading) return <><PageHeader eyebrow="Dashboard" title="Good to see you." description="Loading your practice snapshot..." /><div className="hero-skeleton"><Skeleton className="skeleton-line short" /><Skeleton className="skeleton-line large" /><Skeleton className="skeleton-line medium" /></div><LoadingGrid count={4} /></>;
  if (dashboard.error || !dashboard.data) return <><PageHeader eyebrow="Dashboard" title="Your practice snapshot" description="We need a live API connection to load your progress." /><ErrorNotice error={dashboard.error} retry={dashboard.reload} /></>;
  const data = dashboard.data;
  const level = data.level;
  const levelBase = level.next_level_xp === null ? level.current_xp : level.current_xp - (level.next_level_xp > 1000 ? 1000 : level.next_level_xp > 500 ? 500 : level.next_level_xp > 250 ? 250 : level.next_level_xp > 100 ? 100 : 0);
  const levelStart = level.next_level_xp === null ? 2000 : level.next_level_xp === 100 ? 0 : level.next_level_xp === 250 ? 100 : level.next_level_xp === 500 ? 250 : level.next_level_xp === 1000 ? 500 : 2000;
  const levelProgress = level.next_level_xp === null ? 100 : Math.max(0, level.current_xp - levelStart);
  const levelRange = level.next_level_xp === null ? 2000 : level.next_level_xp - levelStart;
  return <>
    <PageHeader eyebrow="Dashboard" title={`Good to see you, ${firstName}.`} description={`${formatLongDate(data.today.challenge_date)} · Keep your streak alive with one focused session.`} action={<button className="button button-secondary button-small" onClick={() => navigateTo("/profile")}><Icon name="settings" size={15} /> Preferences</button>} />
    <section className="welcome-hero"><div className="hero-orb orb-one" /><div className="hero-orb orb-two" /><div className="hero-content"><div className="level-overline"><span className="level-badge">LVL {level.level}</span><span>{level.title}</span></div><h2>Your next solved problem<br /><em>starts here.</em></h2><p>Small, deliberate practice is how strong problem solvers are built.</p><div className="hero-progress"><div className="hero-progress-top"><span>Level {level.level} progress</span><strong>{level.current_xp.toLocaleString()} XP <small>{level.next_level_xp ? `/ ${level.next_level_xp.toLocaleString()} XP` : "· Max level"}</small></strong></div><div className="hero-track"><span style={{ width: `${level.next_level_xp ? Math.min(100, (levelProgress / levelRange) * 100) : 100}%` }} /></div></div></div><div className="hero-action"><div className="hero-action-label"><span className="live-pulse" /> Your quest is ready</div><button className="button button-light" onClick={goQuest}>Continue quest <Icon name="arrow" size={16} /></button><span className="hero-action-meta"><Icon name="clock" size={13} /> ~30–45 min today</span></div></section>
    <div className="stats-grid"><StatCard icon="flame" label="Current streak" value={data.current_streak} detail={data.current_streak === 1 ? "day in the making" : "days in the making"} tone="orange" /><StatCard icon="check" label="Questions solved" value={data.completed_questions} detail="self-reported completions" tone="green" /><StatCard icon="zap" label="Total XP" value={level.current_xp.toLocaleString()} detail={`Level ${level.level} · ${level.title}`} tone="blue" /><StatCard icon="layers" label="Patterns practiced" value={data.patterns_practiced} detail="distinct patterns explored" tone="purple" /></div>
    <div className="dashboard-main-grid"><section><SectionHeading title="Today’s quest" detail="Your focused practice plan" action={<button className="text-button" onClick={goQuest}>View full quest <Icon name="arrow" size={14} /></button>} /><QuestCard challenge={data.today} compact onOpen={goQuest} /></section><section><SectionHeading title="This week" detail="Goal-qualified activity" action={<button className="text-button" onClick={() => navigateTo("/progress")}>See progress <Icon name="arrow" size={14} /></button>} /><WeeklyActivity activity={history.data?.activity || []} loading={history.loading} timeZone={user?.timezone} /></section></div>
    <div className="dashboard-lower-grid"><section><SectionHeading title="Pattern progress" detail="Keep widening your toolkit" action={<button className="text-button" onClick={() => navigateTo("/patterns")}>Explore patterns <Icon name="arrow" size={14} /></button>} />{patterns.loading ? <LoadingGrid count={2} /> : patterns.error ? <ErrorNotice error={patterns.error} retry={patterns.reload} /> : patterns.data?.length ? <div className="pattern-mini-grid">{patterns.data.slice(0, 4).map((pattern) => <PatternMiniCard key={pattern.id} pattern={pattern} />)}</div> : <EmptyState title="Your pattern map is waiting" description="Complete a quest to start seeing your practice coverage." />}</section><section><SectionHeading title="Achievements" detail="Milestones worth noticing" action={<button className="text-button" onClick={() => navigateTo("/achievements")}>View all <Icon name="arrow" size={14} /></button>} />{achievements.loading ? <LoadingGrid count={2} /> : achievements.error ? <ErrorNotice error={achievements.error} retry={achievements.reload} /> : achievements.data?.length ? <div className="achievement-mini-list">{achievements.data.filter((item) => item.unlocked).slice(0, 3).map((achievement) => <AchievementMini key={achievement.id} achievement={achievement} />)}{!achievements.data.some((item) => item.unlocked) && <EmptyState icon="trophy" title="Your first milestone is close" description="Complete your first problem to unlock an achievement." />}</div> : <EmptyState icon="trophy" title="No milestones yet" description="Your first milestone is close." />}</section></div>
    <section className="recent-section"><SectionHeading title="Recent activity" detail="Your latest completed problems" action={<button className="text-button" onClick={() => navigateTo("/history")}>Open history <Icon name="arrow" size={14} /></button>} />{history.loading ? <LoadingGrid count={2} /> : history.error ? <ErrorNotice error={history.error} retry={history.reload} /> : history.data?.questions.length ? <div className="activity-table">{history.data.questions.slice(0, 4).map((item) => <QuestionHistoryRow key={item.id} item={item} />)}</div> : <EmptyState icon="clock" title="No completed problems yet" description="Your activity will appear here after your first self-reported completion." />}</section>
  </>;
}

function WeeklyActivity({ activity, loading, timeZone = "UTC" }: { activity: DailyActivity[]; loading: boolean; timeZone?: string }) {
  if (loading) return <div className="weekly-card"><div className="skeleton-week"><Skeleton /><Skeleton /><Skeleton /><Skeleton /><Skeleton /><Skeleton /><Skeleton /></div></div>;
  const activityMap = new Map(activity.map((item) => [item.activity_date, item]));
  const days = recentDateKeys(7, timeZone).map((key) => new Date(`${key}T12:00:00Z`));
  return <div className="weekly-card"><div className="week-summary"><div><strong>{activity.filter((item) => item.goal_completed).length}</strong><span>goal days logged</span></div><span className="week-trend"><Icon name="flame" size={14} /> Keep showing up</span></div><div className="week-days">{days.map((date) => { const key = date.toISOString().slice(0, 10); const item = activityMap.get(key); return <div className="week-day" key={key}><span>{date.toLocaleDateString(undefined, { weekday: "short" }).slice(0, 2)}</span><div className={`day-dot ${item?.goal_completed ? "complete" : item?.questions_completed ? "partial" : ""}`} aria-label={`${formatDate(date)}: ${item?.questions_completed || 0} questions`} /> <small>{date.getDate()}</small></div>; })}</div><div className="week-legend"><span><i className="legend-dot complete" /> Goal complete</span><span><i className="legend-dot partial" /> In progress</span></div></div>;
}

function PatternMiniCard({ pattern }: { pattern: Pattern }) {
  return <button className="pattern-mini-card" onClick={() => navigateTo("/patterns")}><span className="pattern-card-icon"><Icon name="layers" size={17} /></span><span className="pattern-card-copy"><strong>{pattern.name}</strong><small>{pattern.completed_count} / {pattern.available_count} complete</small><ProgressBar value={pattern.completed_count} max={pattern.available_count} tone="purple" /></span><Icon name="chevron" size={16} /></button>;
}

function AchievementMini({ achievement }: { achievement: Achievement }) { return <div className="achievement-mini"><span className="achievement-icon"><Icon name="trophy" size={16} /></span><span><strong>{achievement.name}</strong><small>{achievement.description}</small></span><Icon name="check" size={15} /></div>; }

function QuestionHistoryRow({ item }: { item: QuestionProgress }) { return <div className="activity-row"><span className="activity-check"><Icon name="check" size={15} /></span><div><strong>{item.question.title}</strong><span>{item.question.patterns[0]?.name || "DSA practice"} <span className="dot-separator" /> {item.solved_at ? formatDate(item.solved_at, { month: "short", day: "numeric", year: "numeric" }) : "Completed"}</span></div><div className="activity-xp">+{item.xp_earned} XP</div><DifficultyBadge difficulty={item.question.difficulty} /></div>; }

function QuestView() {
  const loaded = useLoad(() => api.today());
  const [challenge, setChallenge] = useState<DailyChallenge | null>(null);
  const [submitting, setSubmitting] = useState<number | null>(null);
  const [notesOpen, setNotesOpen] = useState<number | null>(null);
  const [notes, setNotes] = useState<Record<number, string>>({});
  const toast = useToast();
  useEffect(() => { if (loaded.data) setChallenge(loaded.data); }, [loaded.data]);
  const submitCompletion = async (assignment: DailyChallenge["assignments"][number]) => {
    setSubmitting(assignment.question.id);
    try {
      const result = await api.complete(assignment.question.id, notes[assignment.question.id] || "");
      setChallenge(result.challenge);
      toast(result.duplicate ? "This completion was already recorded." : `+${result.xp_awarded + result.bonus_xp} XP added to your run.`);
      if (result.new_achievements.length) toast(`Achievement unlocked: ${result.new_achievements[0].name}`, "info");
    } catch (error) { toast(errorMessage(error), "error"); }
    finally { setSubmitting(null); }
  };
  if (loaded.loading && !challenge) return <><PageHeader eyebrow="Daily quest" title="Your focused practice plan" description="Generating today’s assignments..." /><div className="hero-skeleton"><Skeleton className="skeleton-line short" /><Skeleton className="skeleton-line large" /><Skeleton className="skeleton-line medium" /></div><LoadingGrid count={2} /></>;
  if (loaded.error && !challenge) return <><PageHeader eyebrow="Daily quest" title="Your focused practice plan" description="Your next two problems are generated from your practice history." /><ErrorNotice error={loaded.error} retry={loaded.reload} /></>;
  if (!challenge) return null;
  const mandatory = challenge.assignments.filter((assignment) => !assignment.is_bonus);
  const bonus = challenge.assignments.filter((assignment) => assignment.is_bonus);

  if (mandatory.length === 0 && bonus.length === 0) {
    return (
      <>
        <PageHeader eyebrow="Daily quest" title="Your focused practice plan" description={`${formatLongDate(challenge.challenge_date)} · Two qualifying problems earn your daily goal.`} action={<button className="button button-secondary button-small" onClick={loaded.reload}><Icon name="refresh" size={15} /> Refresh quest</button>} />
        <section className="quest-intro">
          <div className="quest-intro-copy">
            <span className="quest-intro-mark"><Icon name="target" size={20} /></span>
            <div>
              <p className="eyebrow">Questions unavailable</p>
              <h2>No problems assigned for today.</h2>
              <p>We couldn't find suitable problems for your current challenge mode. This usually happens if the question catalog is empty or too sparse for your selected difficulty. Try adjusting your preferences in the profile settings.</p>
            </div>
          </div>
          <QuestProgress completed={challenge.mandatory_completed} total={challenge.mandatory_total} />
        </section>
        <div className="quest-layout">
          <section>
            <div className="quest-section-label"><span>Mandatory problems</span><small>0/0 complete</small></div>
            <EmptyState icon="book" title="No assignments found" description="Your daily quest is currently empty. Please ensure the question catalog is populated." />
          </section>
          <aside className="quest-aside">
            <div className="aside-card">
              <span className="aside-icon"><Icon name="flame" size={18} /></span>
              <p className="eyebrow">Reward loop</p>
              <h3>Make today count.</h3>
              <div className="reward-row"><span>Easy completion</span><strong>+10 XP</strong></div>
              <div className="reward-row"><span>Medium completion</span><strong>+25 XP</strong></div>
              <div className="reward-row"><span>Hard completion</span><strong>+50 XP</strong></div>
              <div className="reward-row reward-bonus"><span>Daily goal bonus</span><strong>+20 XP</strong></div>
            </div>
            <div className="aside-note">
              <Icon name="info" size={16} />
              <p><strong>Be honest with your log.</strong> Completions are self-reported so your progress stays meaningful.</p>
            </div>
          </aside>
        </div>
      </>
    );
  }

  return <><PageHeader eyebrow="Daily quest" title="Your focused practice plan" description={`${formatLongDate(challenge.challenge_date)} · Two qualifying problems earn your daily goal.`} action={<button className="button button-secondary button-small" onClick={loaded.reload}><Icon name="refresh" size={15} /> Refresh quest</button>} /><section className="quest-intro"><div className="quest-intro-copy"><span className="quest-intro-mark"><Icon name="target" size={20} /></span><div><p className="eyebrow">{challenge.goal_completed ? "Quest complete" : "The daily loop"}</p><h2>{challenge.goal_completed ? "You made the time." : "Solve, report, repeat."}</h2><p>Open the official problem, work it through on LeetCode, then record your completion here. DSA Quest tracks your practice—it does not verify LeetCode submissions.</p></div></div><QuestProgress completed={challenge.mandatory_completed} total={challenge.mandatory_total} /></section><div className="quest-layout"><section><div className="quest-section-label"><span>Mandatory problems</span><small>{challenge.mandatory_completed}/{challenge.mandatory_total} complete</small></div><div className="quest-detail-list">{mandatory.map((assignment, index) => <QuestAssignmentCard key={assignment.id} assignment={assignment} index={index} submitting={submitting === assignment.question.id} notesOpen={notesOpen === assignment.question.id} notes={notes[assignment.question.id] || ""} setNotes={(value) => setNotes({ ...notes, [assignment.question.id]: value })} toggleNotes={() => setNotesOpen(notesOpen === assignment.question.id ? null : assignment.question.id)} onComplete={() => submitCompletion(assignment)} />)}</div>{bonus.length > 0 && <><div className="quest-section-label bonus-label"><span>Bonus practice</span><small>Optional · does not affect your daily goal</small></div>{bonus.map((assignment) => <QuestAssignmentCard key={assignment.id} assignment={assignment} index={2} bonus submitting={submitting === assignment.question.id} notesOpen={notesOpen === assignment.question.id} notes={notes[assignment.question.id] || ""} setNotes={(value) => setNotes({ ...notes, [assignment.question.id]: value })} toggleNotes={() => setNotesOpen(notesOpen === assignment.question.id ? null : assignment.question.id)} onComplete={() => submitCompletion(assignment)} />)}</>}</section><aside className="quest-aside"><div className="aside-card"><span className="aside-icon"><Icon name="flame" size={18} /></span><p className="eyebrow">Reward loop</p><h3>Make today count.</h3><div className="reward-row"><span>Easy completion</span><strong>+10 XP</strong></div><div className="reward-row"><span>Medium completion</span><strong>+25 XP</strong></div><div className="reward-row"><span>Hard completion</span><strong>+50 XP</strong></div><div className="reward-row reward-bonus"><span>Daily goal bonus</span><strong>+20 XP</strong></div></div><div className="aside-note"><Icon name="info" size={16} /><p><strong>Be honest with your log.</strong> Completions are self-reported so your progress stays meaningful.</p></div></aside></div></>;
}

function QuestAssignmentCard({ assignment, index, bonus = false, submitting, notesOpen, notes, setNotes, toggleNotes, onComplete }: { assignment: DailyChallenge["assignments"][number]; index: number; bonus?: boolean; submitting: boolean; notesOpen: boolean; notes: string; setNotes: (value: string) => void; toggleNotes: () => void; onComplete: () => void }) {
  const { question } = assignment;
  const complete = assignment.status === "completed";
  return <article className={`quest-assignment-card ${complete ? "completed-card" : ""}`}><div className="assignment-card-top"><span className={`large-assignment-number ${complete ? "complete-number" : ""}`}>{complete ? <Icon name="check" size={19} /> : bonus ? "＋" : String(index + 1).padStart(2, "0")}</span><div className="assignment-card-copy"><div className="assignment-card-label"><span>{bonus ? "Bonus problem" : `Problem ${index + 1}`}</span>{assignment.is_revision && <span className="revision-pill">Revision task</span>}<span className="self-report-label">Self-reported</span></div><h3>{question.title}</h3><div className="assignment-meta"><DifficultyBadge difficulty={question.difficulty} />{question.patterns.map((pattern) => <span className="pattern-tag" key={pattern.id}>{pattern.name}</span>)}{question.estimated_minutes && <span className="time-meta"><Icon name="clock" size={13} /> {question.estimated_minutes} min</span>}</div></div><span className={`assignment-state ${complete ? "state-complete" : ""}`}>{complete ? "Completed" : "Up next"}</span></div><div className="assignment-card-footer"><a className="button button-secondary" href={question.leetcode_url} target="_blank" rel="noreferrer"><Icon name="external" size={15} /> Open on LeetCode</a>{!complete && <><button className="notes-button" onClick={toggleNotes}><Icon name="book" size={15} /> {notesOpen ? "Hide notes" : "Add notes"}</button><button className="button button-primary" onClick={onComplete} disabled={submitting}>{submitting ? <><span className="button-spinner" /> Saving</> : <><Icon name="check" size={15} /> Mark complete</>}</button></>}</div>{notesOpen && !complete && <div className="notes-editor"><label htmlFor={`notes-${question.id}`}>Personal notes <span>optional</span></label><textarea id={`notes-${question.id}`} value={notes} onChange={(event) => setNotes(event.target.value)} maxLength={5000} placeholder="What clicked? What would you revisit?" /><small>{notes.length}/5000</small></div>}{complete && <div className="completed-message"><Icon name="check" size={14} /> Logged to your practice history{assignment.completed_at ? ` · ${formatDate(assignment.completed_at, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })}` : ""}</div>}</article>;
}

function PatternsView() {
  const [difficulty, setDifficulty] = useState("");
  const [pattern, setPattern] = useState("");
  const patternLoad = useLoad(() => api.patterns());
  const activePattern = patternLoad.data?.find((item) => item.slug === pattern);
  // Send the numeric id because the Django filter combines slug and pk lookups.
  const questionLoad = useLoad(() => api.questions({ difficulty, pattern: activePattern ? String(activePattern.id) : "", ordering: "title" }), [difficulty, activePattern?.id]);
  return <><PageHeader eyebrow="Practice library" title="Patterns & problems" description="Build pattern fluency with a curated set of official LeetCode problems." action={<button className="button button-primary button-small" onClick={() => navigateTo("/quest")}><Icon name="target" size={15} /> Open daily quest</button>} /><section className="pattern-overview"><div><p className="eyebrow">Your pattern map</p><h2>Practice with a point of view.</h2><p>Patterns are the reusable ideas behind strong solutions. Explore what you have touched, then choose the next problem deliberately.</p></div><div className="pattern-overview-stat"><span>{patternLoad.data?.reduce((sum, item) => sum + item.completed_count, 0) || 0}</span><small>pattern-linked<br />completions</small></div><div className="pattern-overview-stat"><span>{patternLoad.data?.length || 0}</span><small>active<br />patterns</small></div></section><section className="patterns-section"><SectionHeading title="Pattern progress" detail="A map of the ideas you are practicing" />{patternLoad.loading ? <LoadingGrid count={4} /> : patternLoad.error ? <ErrorNotice error={patternLoad.error} retry={patternLoad.reload} /> : patternLoad.data?.length ? <div className="pattern-grid">{patternLoad.data.map((item) => <PatternCard key={item.id} pattern={item} active={item.slug === pattern} onClick={() => setPattern(item.slug === pattern ? "" : item.slug)} />)}</div> : <EmptyState icon="layers" title="No patterns available" description="The catalog will appear here once the backend has been seeded." />}</section><section className="catalog-section"><div className="catalog-heading"><div><p className="eyebrow">Curated catalog</p><h2>{activePattern ? activePattern.name : "All problems"}</h2><p>{activePattern ? activePattern.description : "Official LeetCode links, with difficulty and pattern context."}</p></div><div className="catalog-filters"><label className="select-wrap"><Icon name="sliders" size={15} /><select value={difficulty} onChange={(event) => setDifficulty(event.target.value)} aria-label="Filter by difficulty"><option value="">All difficulty</option><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option></select></label><label className="select-wrap"><Icon name="layers" size={15} /><select value={pattern} onChange={(event) => setPattern(event.target.value)} aria-label="Filter by pattern"><option value="">All patterns</option>{patternLoad.data?.map((item) => <option value={item.slug} key={item.id}>{item.name}</option>)}</select></label></div></div>{questionLoad.loading ? <LoadingGrid count={4} /> : questionLoad.error ? <ErrorNotice error={questionLoad.error} retry={questionLoad.reload} /> : questionLoad.data?.length ? <div className="catalog-list">{questionLoad.data.map((question) => <CatalogRow key={question.id} question={question} />)}</div> : <EmptyState icon="search" title="No problems match those filters" description="Try widening your difficulty or pattern selection." />}</section></>;
}

function PatternCard({ pattern, active, onClick }: { pattern: Pattern; active: boolean; onClick: () => void }) { return <button className={`pattern-card ${active ? "selected" : ""}`} onClick={onClick}><div className="pattern-card-top"><span className="pattern-card-icon"><Icon name="layers" size={17} /></span><span className="pattern-card-arrow"><Icon name={active ? "check" : "arrow"} size={15} /></span></div><h3>{pattern.name}</h3><p>{pattern.description || "Build confidence with this reusable problem-solving pattern."}</p><div className="pattern-card-bottom"><span>{pattern.completed_count}/{pattern.available_count} solved</span><strong>{pattern.available_count ? Math.round((pattern.completed_count / pattern.available_count) * 100) : 0}%</strong></div><ProgressBar value={pattern.completed_count} max={pattern.available_count} tone="purple" /></button>; }

function CatalogRow({ question }: { question: Question }) { return <div className="catalog-row"><div className={`catalog-status ${question.completed ? "completed" : ""}`}>{question.completed ? <Icon name="check" size={14} /> : <Icon name="book" size={14} />}</div><div className="catalog-copy"><strong>{question.title}</strong><div>{question.patterns.slice(0, 3).map((item) => <span key={item.id}>{item.name}</span>)}</div></div><DifficultyBadge difficulty={question.difficulty} /><span className="time-meta catalog-time"><Icon name="clock" size={13} /> {question.estimated_minutes || "—"} min</span><a className="catalog-link" href={question.leetcode_url} target="_blank" rel="noreferrer" aria-label={`Open ${question.title}`}><Icon name="external" size={15} /></a></div>; }

function ProgressView() {
  const progress = useLoad(() => api.progress());
  const history = useLoad(() => api.history(90));
  if (progress.loading) return <><PageHeader eyebrow="Your trajectory" title="Progress" description="Loading your practice metrics..." /><LoadingGrid count={4} /></>;
  if (progress.error || !progress.data) return <><PageHeader eyebrow="Your trajectory" title="Progress" description="A clearer view of your practice over time." /><ErrorNotice error={progress.error} retry={progress.reload} /></>;
  const data = progress.data;
  const activity = history.data?.activity || [];
  const completedByDay = new Map(activity.map((item) => [item.activity_date, item]));
  const maxQuestions = Math.max(1, ...activity.slice(0, 14).map((item) => item.questions_completed));
  return <><PageHeader eyebrow="Your trajectory" title="Progress" description="Measure consistency, not perfection. Your self-reported practice is the signal." action={<button className="button button-secondary button-small" onClick={history.reload}><Icon name="refresh" size={15} /> Refresh data</button>} /><div className="stats-grid progress-stats"><StatCard icon="zap" label="Total XP" value={data.total_xp.toLocaleString()} detail={`Level ${data.level.level} · ${data.level.title}`} tone="blue" /><StatCard icon="check" label="Questions solved" value={data.questions_completed} detail="across your catalog" tone="green" /><StatCard icon="flame" label="Current streak" value={`${data.current_streak}d`} detail={`longest: ${data.longest_streak} days`} tone="orange" /><StatCard icon="layers" label="Patterns practiced" value={data.patterns_practiced} detail="with at least one solve" tone="purple" /></div><div className="progress-grid"><section className="panel"><SectionHeading title="Daily activity" detail="Last 14 days of logged practice" /><div className="bar-chart">{Array.from({ length: 14 }, (_, index) => { const date = new Date(); date.setHours(12, 0, 0, 0); date.setDate(date.getDate() - (13 - index)); const key = date.toISOString().slice(0, 10); const item = completedByDay.get(key); return <div className="bar-column" key={key}><div className="bar-value">{item?.questions_completed || ""}</div><div className="bar-track"><span className={item?.goal_completed ? "bar-complete" : "bar-partial"} style={{ height: `${item ? Math.max(8, (item.questions_completed / maxQuestions) * 100) : 3}%` }} /></div><span>{date.toLocaleDateString(undefined, { weekday: "short" }).slice(0, 2)}</span><small>{date.getDate()}</small></div>; })}</div><div className="chart-legend"><span><i className="legend-bar complete" /> Goal complete</span><span><i className="legend-bar partial" /> Activity logged</span></div></section><section className="panel"><SectionHeading title="Difficulty mix" detail="Where your solved problems land" /><div className="difficulty-breakdown">{(["easy", "medium", "hard"] as Difficulty[]).map((item) => <div className="difficulty-line" key={item}><div><DifficultyBadge difficulty={item} /><strong>{data.difficulty[item]}</strong></div><ProgressBar value={data.difficulty[item]} max={Math.max(1, data.questions_completed)} tone={item} /></div>)}</div><div className="progress-callout"><Icon name="info" size={16} /><span>Self-reported completion tracks practice volume. It does not claim accepted-submission accuracy.</span></div></section></div><section className="panel heatmap-panel"><SectionHeading title="Consistency map" detail="The last 30 days, by local activity date" /><ActivityHeatmap activity={activity} /></section></>;
}

function ActivityHeatmap({ activity }: { activity: DailyActivity[] }) { const map = new Map(activity.map((item) => [item.activity_date, item])); const days = Array.from({ length: 30 }, (_, index) => { const date = new Date(); date.setHours(12, 0, 0, 0); date.setDate(date.getDate() - (29 - index)); return date; }); return <div className="heatmap-wrap"><div className="heatmap-months"><span>Past 30 days</span><span>{formatDate(new Date(), { month: "short", year: "numeric" })}</span></div><div className="heatmap">{days.map((date) => { const key = date.toISOString().slice(0, 10); const item = map.get(key); const level = item?.goal_completed ? "heat-high" : item?.questions_completed ? "heat-mid" : "heat-none"; return <div key={key} className={`heat-cell ${level}`} title={`${formatDate(date)} · ${item?.questions_completed || 0} questions`} />; })}</div><div className="heatmap-legend"><span>Less</span><i className="heat-cell heat-none" /><i className="heat-cell heat-mid" /><i className="heat-cell heat-high" /><span>More</span></div></div>; }

function AchievementsView() { const loaded = useLoad(() => api.achievements()); const achievements = loaded.data || []; const unlocked = achievements.filter((item) => item.unlocked); return <><PageHeader eyebrow="Milestones" title="Achievements" description="Notice the moments that prove your consistency is becoming a skill." action={<div className="achievement-summary"><strong>{unlocked.length}</strong><span>of {achievements.length} unlocked</span></div>} />{loaded.loading ? <LoadingGrid count={6} /> : loaded.error ? <ErrorNotice error={loaded.error} retry={loaded.reload} /> : achievements.length ? <><section className="achievement-banner"><div className="achievement-banner-icon"><Icon name="trophy" size={24} /></div><div><p className="eyebrow">Keep the chain going</p><h2>{unlocked.length ? `${unlocked.length} milestone${unlocked.length === 1 ? "" : "s"} in the book.` : "Your first milestone is within reach."}</h2><p>{unlocked.length ? "Every unlocked achievement is a trace of the work you put in." : "Complete a question to unlock First Blood and start your collection."}</p></div><div className="achievement-banner-progress"><strong>{achievements.length ? Math.round((unlocked.length / achievements.length) * 100) : 0}%</strong><span>collection complete</span></div></section><div className="achievement-grid">{achievements.map((item) => <AchievementCard key={item.id} achievement={item} />)}</div></> : <EmptyState icon="trophy" title="No achievements configured" description="Achievements will appear once the backend catalog is seeded." />}</>; }

function AchievementCard({ achievement }: { achievement: Achievement }) { const progress = Math.min(achievement.criteria_value, achievement.current_progress); return <article className={`achievement-card ${achievement.unlocked ? "unlocked" : "locked"}`}><div className="achievement-card-top"><span className="achievement-large-icon"><Icon name={achievement.unlocked ? "trophy" : "lock"} size={21} /></span>{achievement.unlocked ? <span className="unlocked-label"><Icon name="check" size={13} /> Unlocked</span> : <span className="locked-label">In progress</span>}</div><h3>{achievement.name}</h3><p>{achievement.description}</p><div className="achievement-progress"><div><span>{achievement.unlocked ? "Completed" : "Progress"}</span><strong>{progress} / {achievement.criteria_value}</strong></div><ProgressBar value={progress} max={achievement.criteria_value} tone={achievement.unlocked ? "green" : "orange"} /></div>{achievement.unlocked_at && <small className="unlocked-date">Unlocked {formatDate(achievement.unlocked_at, { month: "short", day: "numeric", year: "numeric" })}</small>}</article>; }

function HistoryView() { const history = useLoad(() => api.history(366)); const xpHistory = useLoad(() => api.xpHistory()); const questions = history.data?.questions || []; return <><PageHeader eyebrow="Practice log" title="History" description="A durable record of the problems you chose to show up for." action={<button className="button button-secondary button-small" onClick={() => { history.reload(); xpHistory.reload(); }}><Icon name="refresh" size={15} /> Refresh log</button>} /><div className="history-summary"><div><span className="summary-icon"><Icon name="check" size={17} /></span><span><strong>{questions.length}</strong><small>questions logged</small></span></div><div><span className="summary-icon xp-summary"><Icon name="zap" size={17} /></span><span><strong>{xpHistory.data?.total_xp.toLocaleString() || "—"}</strong><small>total XP earned</small></span></div><div><span className="summary-icon"><Icon name="calendar" size={17} /></span><span><strong>{history.data?.activity.filter((item) => item.goal_completed).length || 0}</strong><small>goal days completed</small></span></div></div><section className="panel history-panel"><SectionHeading title="Completed questions" detail="Most recent first" />{history.loading ? <LoadingGrid count={4} /> : history.error ? <ErrorNotice error={history.error} retry={history.reload} /> : questions.length ? <div className="history-list">{questions.map((item) => <HistoryDetailRow key={item.id} item={item} />)}</div> : <EmptyState icon="clock" title="Your history is empty" description="Complete your first daily assignment and it will be recorded here." />}</section><section className="panel xp-history-panel"><SectionHeading title="XP ledger" detail="Reward events from your practice" />{xpHistory.loading ? <LoadingGrid count={3} /> : xpHistory.error ? <ErrorNotice error={xpHistory.error} retry={xpHistory.reload} /> : xpHistory.data?.transactions.length ? <div className="xp-list">{xpHistory.data.transactions.slice(0, 10).map((item) => <div className="xp-row" key={item.id}><span className="xp-row-icon"><Icon name="zap" size={14} /></span><div><strong>{item.event_type === "daily_goal_completed" ? "Daily goal completed" : "Question completed"}</strong><small>{formatDate(item.created_at, { month: "short", day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit" })}</small></div><strong className="xp-amount">+{item.xp_amount} XP</strong></div>)}</div> : <EmptyState icon="zap" title="No XP events yet" description="Your reward ledger will populate as you complete problems." />}</section></>; }

function HistoryDetailRow({ item }: { item: QuestionProgress }) { return <div className="history-detail-row"><div className="history-date"><strong>{item.solved_at ? new Date(item.solved_at).getDate() : "—"}</strong><span>{item.solved_at ? formatDate(item.solved_at, { month: "short" }) : ""}</span></div><div className="history-question"><strong>{item.question.title}</strong><div><DifficultyBadge difficulty={item.question.difficulty} />{item.question.patterns.map((pattern) => <span className="pattern-tag" key={pattern.id}>{pattern.name}</span>)}</div></div><div className="history-notes">{item.personal_notes ? <><Icon name="book" size={13} /> Note added</> : <span>No notes</span>}</div><span className="history-xp">+{item.xp_earned} XP</span></div>; }

function ProfileView() { const { user, updateUser } = useAuth(); const [form, setForm] = useState({ display_name: user?.display_name || "", timezone: user?.timezone || "UTC", challenge_mode: user?.challenge_mode || "balanced" }); const [saving, setSaving] = useState(false); const toast = useToast(); const save = async (event: FormEvent) => { event.preventDefault(); setSaving(true); try { const updated = await api.updateMe(form); updateUser(updated); toast("Preferences saved."); } catch (error) { toast(errorMessage(error), "error"); } finally { setSaving(false); } }; return <><PageHeader eyebrow="Your workspace" title="Profile & preferences" description="Tune the practice loop around how you actually work." /><div className="profile-layout"><section className="profile-card"><div className="profile-card-top"><div className="profile-avatar">{initials(user?.display_name || "")}</div><div><h2>{user?.display_name}</h2><p>{user?.email}</p><span className="member-since">Member since {user?.date_joined ? formatDate(user.date_joined, { month: "long", year: "numeric" }) : "today"}</span></div></div><div className="profile-divider" /><form onSubmit={save} className="profile-form"><div className="profile-form-section"><p className="eyebrow">Identity</p><Field label="Display name" value={form.display_name} onChange={(value) => setForm({ ...form, display_name: value })} required /><Field label="Email address" value={user?.email || ""} onChange={() => undefined} type="email" /><small className="field-help">Email is managed as your sign-in identity.</small></div><div className="profile-form-section"><p className="eyebrow">Practice defaults</p><label className="field"><span>Challenge mode</span><select value={form.challenge_mode} onChange={(event) => setForm({ ...form, challenge_mode: event.target.value })}><option value="beginner">Beginner · Easy + Easy</option><option value="balanced">Balanced · Easy + Medium</option><option value="intermediate">Intermediate · Medium + Medium</option><option value="advanced">Advanced · Medium + Hard</option><option value="adaptive">Adaptive · Based on progress</option></select></label><label className="field"><span>Timezone</span><input value={form.timezone} onChange={(event) => setForm({ ...form, timezone: event.target.value })} /></label><small className="field-help"><Icon name="info" size={13} /> Historical activity stays anchored to its original local date.</small></div><button className="button button-primary" type="submit" disabled={saving}>{saving ? <><span className="button-spinner" /> Saving changes</> : <><Icon name="check" size={15} /> Save preferences</>}</button></form></section><aside className="profile-aside"><div className="profile-aside-card"><span className="aside-icon"><Icon name="settings" size={18} /></span><p className="eyebrow">Your setup</p><h3>One honest log at a time.</h3><p>DSA Quest is designed to keep your practice visible and your goals grounded. The app records what you tell it; it never pretends to verify a LeetCode submission.</p></div><div className="profile-api-note"><span className="status-dot" /><div><strong>API connection</strong><small>Token-authenticated session</small></div></div></aside></div></>; }

export default App;
