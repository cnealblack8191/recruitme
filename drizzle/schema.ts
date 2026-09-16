import {
  boolean,
  date,
  int,
  json,
  mysqlEnum,
  mysqlTable,
  text,
  timestamp,
  uniqueIndex,
  varchar,
} from "drizzle-orm/mysql-core";

/**
 * Core user table backing auth flow.
 * Extend this file with additional tables as your product grows.
 * Columns use camelCase to match both database fields and generated types.
 */
export const users = mysqlTable("users", {
  /**
   * Surrogate primary key. Auto-incremented numeric value managed by the database.
   * Use this for relations between tables.
   */
  id: int("id").autoincrement().primaryKey(),
  /** Manus OAuth identifier (openId) returned from the OAuth callback. Unique per user. */
  openId: varchar("openId", { length: 64 }).notNull().unique(),
  name: text("name"),
  email: varchar("email", { length: 320 }),
  loginMethod: varchar("loginMethod", { length: 64 }),
  role: mysqlEnum("role", ["user", "admin"]).default("user").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
  lastSignedIn: timestamp("lastSignedIn").defaultNow().notNull(),
});

export type User = typeof users.$inferSelect;
export type InsertUser = typeof users.$inferInsert;

/* ------------------------------------------------------------------ */
/* ECI Candidate Portal tables                                         */
/* ------------------------------------------------------------------ */

/**
 * A person applying to work at ECI. Registered with full name + birthdate,
 * which together act as the candidate's identity for returning sessions.
 */
export const candidates = mysqlTable(
  "candidates",
  {
    id: int("id").autoincrement().primaryKey(),
    fullName: varchar("fullName", { length: 200 }).notNull(),
    /** Calendar date of birth (no time component), stored as YYYY-MM-DD. */
    birthdate: date("birthdate", { mode: "string" }).notNull(),
    /** Optional contact email — used for the registration confirmation receipt. */
    email: varchar("email", { length: 320 }),
    /** Optional uploaded resume (S3). */
    resumeUrl: text("resumeUrl"),
    resumeKey: varchar("resumeKey", { length: 512 }),
    resumeFilename: varchar("resumeFilename", { length: 255 }),
    /** Set when the candidate begins the aptitude assessment; drives the
     *  dashboard "in progress" state until the first attempt is submitted. */
    aptitudeStartedAt: timestamp("aptitudeStartedAt"),
    createdAt: timestamp("createdAt").defaultNow().notNull(),
    updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
  },
  (table) => [
    uniqueIndex("candidates_name_dob_unique").on(table.fullName, table.birthdate),
  ]
);

export type Candidate = typeof candidates.$inferSelect;
export type InsertCandidate = typeof candidates.$inferInsert;

/**
 * One sitting of the ECI aptitude assessment by a candidate.
 * `answers` maps question id -> chosen option index.
 */
export const aptitudeAttempts = mysqlTable("aptitude_attempts", {
  id: int("id").autoincrement().primaryKey(),
  candidateId: int("candidateId").notNull(),
  answers: json("answers").$type<Record<string, number>>().notNull(),
  scoreCorrect: int("scoreCorrect").notNull(),
  scoreTotal: int("scoreTotal").notNull(),
  scorePercent: int("scorePercent").notNull(),
  passed: boolean("passed").notNull(),
  /** Per-category breakdown, e.g. { numerical: { correct, total }, ... } */
  categoryBreakdown: json("categoryBreakdown").$type<
    Record<string, { correct: number; total: number }>
  >(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
});

export type AptitudeAttempt = typeof aptitudeAttempts.$inferSelect;
export type InsertAptitudeAttempt = typeof aptitudeAttempts.$inferInsert;

/**
 * Per-candidate, per-lesson safety training state.
 * A lesson is complete when the video was watched AND the quiz was passed.
 */
export const safetyProgress = mysqlTable(
  "safety_progress",
  {
    id: int("id").autoincrement().primaryKey(),
    candidateId: int("candidateId").notNull(),
    lessonId: varchar("lessonId", { length: 64 }).notNull(),
    videoWatched: boolean("videoWatched").default(false).notNull(),
    watchedAt: timestamp("watchedAt"),
    bestQuizPercent: int("bestQuizPercent"),
    quizPassed: boolean("quizPassed").default(false).notNull(),
    completedAt: timestamp("completedAt"),
    updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
  },
  (table) => [
    uniqueIndex("safety_progress_candidate_lesson").on(
      table.candidateId,
      table.lessonId
    ),
  ]
);

export type SafetyProgress = typeof safetyProgress.$inferSelect;
export type InsertSafetyProgress = typeof safetyProgress.$inferInsert;

/**
 * Every knowledge-check attempt for a safety lesson (full audit trail).
 */
export const safetyQuizAttempts = mysqlTable("safety_quiz_attempts", {
  id: int("id").autoincrement().primaryKey(),
  candidateId: int("candidateId").notNull(),
  lessonId: varchar("lessonId", { length: 64 }).notNull(),
  answers: json("answers").$type<Record<string, number>>().notNull(),
  scoreCorrect: int("scoreCorrect").notNull(),
  scoreTotal: int("scoreTotal").notNull(),
  scorePercent: int("scorePercent").notNull(),
  passed: boolean("passed").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
});

export type SafetyQuizAttempt = typeof safetyQuizAttempts.$inferSelect;
export type InsertSafetyQuizAttempt = typeof safetyQuizAttempts.$inferInsert;
