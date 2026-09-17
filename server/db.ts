import { and, desc, eq } from "drizzle-orm";
import { drizzle } from "drizzle-orm/mysql2";
import {
  aptitudeAttempts,
  candidates,
  InsertAptitudeAttempt,
  InsertCandidate,
  InsertSafetyQuizAttempt,
  InsertUser,
  safetyProgress,
  safetyQuizAttempts,
  users,
} from "../drizzle/schema";
import { ENV } from './_core/env';

let _db: ReturnType<typeof drizzle> | null = null;

// Lazily create the drizzle instance so local tooling can run without a DB.
export async function getDb() {
  if (!_db && process.env.DATABASE_URL) {
    try {
      _db = drizzle(process.env.DATABASE_URL);
    } catch (error) {
      console.warn("[Database] Failed to connect:", error);
      _db = null;
    }
  }
  return _db;
}

export async function upsertUser(user: InsertUser): Promise<void> {
  if (!user.openId) {
    throw new Error("User openId is required for upsert");
  }

  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot upsert user: database not available");
    return;
  }

  try {
    const values: InsertUser = {
      openId: user.openId,
    };
    const updateSet: Record<string, unknown> = {};

    const textFields = ["name", "email", "loginMethod"] as const;
    type TextField = (typeof textFields)[number];

    const assignNullable = (field: TextField) => {
      const value = user[field];
      if (value === undefined) return;
      const normalized = value ?? null;
      values[field] = normalized;
      updateSet[field] = normalized;
    };

    textFields.forEach(assignNullable);

    if (user.lastSignedIn !== undefined) {
      values.lastSignedIn = user.lastSignedIn;
      updateSet.lastSignedIn = user.lastSignedIn;
    }
    if (user.role !== undefined) {
      values.role = user.role;
      updateSet.role = user.role;
    } else if (user.openId === ENV.ownerOpenId) {
      values.role = 'admin';
      updateSet.role = 'admin';
    }

    if (!values.lastSignedIn) {
      values.lastSignedIn = new Date();
    }

    if (Object.keys(updateSet).length === 0) {
      updateSet.lastSignedIn = new Date();
    }

    await db.insert(users).values(values).onDuplicateKeyUpdate({
      set: updateSet,
    });
  } catch (error) {
    console.error("[Database] Failed to upsert user:", error);
    throw error;
  }
}

export async function getUserByOpenId(openId: string) {
  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot get user: database not available");
    return undefined;
  }

  const result = await db.select().from(users).where(eq(users.openId, openId)).limit(1);

  return result.length > 0 ? result[0] : undefined;
}

/* ------------------------------------------------------------------ */
/* ECI Candidate Portal queries                                        */
/* ------------------------------------------------------------------ */

/** Register a candidate, or return the existing record for the same
 *  normalized full name + birthdate (returning-candidate resume). */
export async function upsertCandidate(input: {
  fullName: string;
  birthdate: string;
  email?: string | null;
}) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  const fullName = input.fullName.trim().replace(/\s+/g, " ");
  const email = input.email?.trim().toLowerCase() || null;
  const existing = await db
    .select()
    .from(candidates)
    .where(and(eq(candidates.fullName, fullName), eq(candidates.birthdate, input.birthdate)))
    .limit(1);
  if (existing.length > 0) {
    // Returning candidate: backfill a newly provided email if they didn't have one.
    if (email && !existing[0].email) {
      await db.update(candidates).set({ email }).where(eq(candidates.id, existing[0].id));
      existing[0].email = email;
    }
    return { candidate: existing[0], isReturning: true as const };
  }

  const values: InsertCandidate = { fullName, birthdate: input.birthdate, email };
  await db.insert(candidates).values(values);
  const created = await db
    .select()
    .from(candidates)
    .where(and(eq(candidates.fullName, fullName), eq(candidates.birthdate, input.birthdate)))
    .limit(1);
  return { candidate: created[0], isReturning: false as const };
}

/** Attach an uploaded resume to a candidate record. */
export async function setCandidateResume(
  candidateId: number,
  resume: { url: string; key: string; filename: string }
) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  await db
    .update(candidates)
    .set({
      resumeUrl: resume.url,
      resumeKey: resume.key,
      resumeFilename: resume.filename,
    })
    .where(eq(candidates.id, candidateId));
}

/** Portal registrations after a watermark id, oldest first; null when no database is configured. */
export async function listCandidatesAfter(afterId: number, limit: number) {
  const db = await getDb();
  if (!db) return null;
  const { gt, asc } = await import("drizzle-orm");
  return db
    .select({
      id: candidates.id,
      fullName: candidates.fullName,
      email: candidates.email,
      resumeUrl: candidates.resumeUrl,
      createdAt: candidates.createdAt,
    })
    .from(candidates)
    .where(gt(candidates.id, afterId))
    .orderBy(asc(candidates.id))
    .limit(limit);
}

export async function getCandidateById(id: number) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  const rows = await db.select().from(candidates).where(eq(candidates.id, id)).limit(1);
  return rows[0];
}

/** Stamp that a candidate has begun the aptitude assessment (idempotent). */
export async function markAptitudeStarted(candidateId: number) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  await db
    .update(candidates)
    .set({ aptitudeStartedAt: new Date() })
    .where(eq(candidates.id, candidateId));
}

export async function listCandidates() {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  return db.select().from(candidates).orderBy(desc(candidates.createdAt));
}

export async function insertAptitudeAttempt(values: InsertAptitudeAttempt) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  await db.insert(aptitudeAttempts).values(values);
  const rows = await db
    .select()
    .from(aptitudeAttempts)
    .where(eq(aptitudeAttempts.candidateId, values.candidateId))
    .orderBy(desc(aptitudeAttempts.id))
    .limit(1);
  return rows[0];
}

export async function getLatestAptitudeAttempt(candidateId: number) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  const rows = await db
    .select()
    .from(aptitudeAttempts)
    .where(eq(aptitudeAttempts.candidateId, candidateId))
    .orderBy(desc(aptitudeAttempts.createdAt), desc(aptitudeAttempts.id))
    .limit(1);
  return rows[0];
}

export async function listAptitudeAttempts(candidateId: number) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  return db
    .select()
    .from(aptitudeAttempts)
    .where(eq(aptitudeAttempts.candidateId, candidateId))
    .orderBy(desc(aptitudeAttempts.createdAt), desc(aptitudeAttempts.id));
}

export async function getSafetyProgress(candidateId: number) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  return db
    .select()
    .from(safetyProgress)
    .where(eq(safetyProgress.candidateId, candidateId));
}

export async function markLessonWatched(candidateId: number, lessonId: string) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  await db
    .insert(safetyProgress)
    .values({ candidateId, lessonId, videoWatched: true, watchedAt: new Date() })
    .onDuplicateKeyUpdate({
      set: { videoWatched: true, watchedAt: new Date() },
    });
}

export async function recordSafetyQuizResult(input: {
  candidateId: number;
  lessonId: string;
  percent: number;
  passed: boolean;
}) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  const existing = await db
    .select()
    .from(safetyProgress)
    .where(
      and(
        eq(safetyProgress.candidateId, input.candidateId),
        eq(safetyProgress.lessonId, input.lessonId)
      )
    )
    .limit(1);

  const prev = existing[0];
  const best = Math.max(prev?.bestQuizPercent ?? -1, input.percent);
  const quizPassed = (prev?.quizPassed ?? false) || input.passed;
  const completedAt =
    quizPassed && (prev?.videoWatched ?? false)
      ? prev?.completedAt ?? new Date()
      : prev?.completedAt ?? null;

  await db
    .insert(safetyProgress)
    .values({
      candidateId: input.candidateId,
      lessonId: input.lessonId,
      bestQuizPercent: best,
      quizPassed,
      completedAt,
    })
    .onDuplicateKeyUpdate({
      set: { bestQuizPercent: best, quizPassed, completedAt },
    });

  // If the video was already watched and the quiz is now passed, ensure completion is stamped.
  if (quizPassed && (prev?.videoWatched ?? false) && !completedAt) {
    await db
      .update(safetyProgress)
      .set({ completedAt: new Date() })
      .where(
        and(
          eq(safetyProgress.candidateId, input.candidateId),
          eq(safetyProgress.lessonId, input.lessonId)
        )
      );
  }
}

/** When a video is marked watched after the quiz was already passed, stamp completion. */
export async function completeLessonIfReady(candidateId: number, lessonId: string) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  const rows = await db
    .select()
    .from(safetyProgress)
    .where(and(eq(safetyProgress.candidateId, candidateId), eq(safetyProgress.lessonId, lessonId)))
    .limit(1);
  const row = rows[0];
  if (row && row.videoWatched && row.quizPassed && !row.completedAt) {
    await db
      .update(safetyProgress)
      .set({ completedAt: new Date() })
      .where(eq(safetyProgress.id, row.id));
  }
}

export async function insertSafetyQuizAttempt(values: InsertSafetyQuizAttempt) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  await db.insert(safetyQuizAttempts).values(values);
}

export async function listSafetyQuizAttempts(candidateId: number) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  return db
    .select()
    .from(safetyQuizAttempts)
    .where(eq(safetyQuizAttempts.candidateId, candidateId))
    .orderBy(desc(safetyQuizAttempts.createdAt), desc(safetyQuizAttempts.id));
}

export async function listAllAptitudeAttempts() {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  return db
    .select()
    .from(aptitudeAttempts)
    .orderBy(desc(aptitudeAttempts.createdAt), desc(aptitudeAttempts.id));
}

export async function listAllSafetyProgress() {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  return db.select().from(safetyProgress);
}

export async function listAllSafetyQuizAttempts() {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  return db
    .select()
    .from(safetyQuizAttempts)
    .orderBy(desc(safetyQuizAttempts.createdAt), desc(safetyQuizAttempts.id));
}
