export type Difficulty = "easy" | "medium" | "hard";

export interface User {
  id: number;
  email: string;
  display_name: string;
  challenge_mode: string;
  timezone: string;
  date_joined: string;
  email_verified: boolean;
}

export interface RegistrationResult {
  verification_required: boolean;
  email: string;
}

export interface Level {
  level: number;
  title: string;
  current_xp: number;
  next_level_xp: number | null;
}

export interface PatternSummary {
  id: number;
  name: string;
  slug: string;
}

export interface Question {
  id: number;
  title: string;
  slug: string;
  leetcode_url: string;
  difficulty: Difficulty;
  estimated_minutes: number | null;
  patterns: PatternSummary[];
  completed: boolean;
}

export interface Pattern {
  id: number;
  name: string;
  slug: string;
  description: string;
  display_order?: number;
  completed_count: number;
  available_count: number;
  last_practiced_at: string | null;
}

export interface Assignment {
  id: number;
  question: Question;
  position: number;
  is_bonus: boolean;
  is_revision: boolean;
  status: "assigned" | "completed";
  completed_at: string | null;
}

export interface DailyChallenge {
  id: number;
  challenge_date: string;
  status: "open" | "completed";
  assignments: Assignment[];
  mandatory_total: number;
  mandatory_completed: number;
  goal_completed: boolean;
  xp_earned: number;
  created_at: string;
}

export interface DashboardData {
  user: Pick<User, "id" | "display_name" | "email">;
  level: Level;
  completed_questions: number;
  patterns_practiced: number;
  current_streak: number;
  today: DailyChallenge;
}

export interface ProgressData {
  questions_completed: number;
  total_xp: number;
  level: Level;
  current_streak: number;
  longest_streak: number;
  difficulty: Record<Difficulty, number>;
  patterns_practiced: number;
}

export interface DailyActivity {
  activity_date: string;
  questions_completed: number;
  goal_completed: boolean;
  xp_earned: number;
  streak_qualified: boolean;
}

export interface QuestionProgress {
  id: number;
  question: Question;
  status: string;
  first_attempt_at: string | null;
  solved_at: string | null;
  solve_count: number;
  personal_notes: string;
  xp_earned: number;
}

export interface HistoryData {
  activity: DailyActivity[];
  questions: QuestionProgress[];
}

export interface Achievement {
  id: number;
  name: string;
  slug: string;
  description: string;
  criteria_type: string;
  criteria_value: number;
  difficulty: Difficulty | "";
  unlocked: boolean;
  unlocked_at: string | null;
  current_progress: number;
}

export interface XPTransaction {
  id: number;
  event_type: string;
  reference_type: string;
  reference_id: number | null;
  xp_amount: number;
  idempotency_key: string;
  created_at: string;
}

export interface XPHistoryData {
  total_xp: number;
  transactions: XPTransaction[];
}

export interface CompletionResult {
  duplicate: boolean;
  xp_awarded: number;
  bonus_xp: number;
  daily_goal_completed: boolean;
  current_streak: number;
  question_progress: QuestionProgress;
  challenge: DailyChallenge;
  new_achievements: Achievement[];
}
