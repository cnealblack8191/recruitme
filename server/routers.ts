import { COOKIE_NAME } from "@shared/const";
import { getSessionCookieOptions } from "./_core/cookies";
import { systemRouter } from "./_core/systemRouter";
import { protectedProcedure, publicProcedure, router } from "./_core/trpc";
import { TRPCError } from "@trpc/server";
import { z } from "zod";
import {
  APTITUDE_PASS_PERCENT,
  APTITUDE_QUESTIONS,
  activeSafetyLessons,
  publicAptitudeQuestions,
  publicSafetyLessons,
  SAFETY_LESSONS,
  scoreAptitude,
  scoreSafetyQuiz,
} from "../shared/assessment";
import * as db from "./db";
import { notifyOwner } from "./_core/notification";
import { storagePut } from "./storage";
import { recruitmeRouter } from "./recruitme";

/** Fire-and-forget owner alert — never blocks or fails the candidate's action. */
function alertOwner(title: string, content: string) {
  notifyOwner({ title, content }).then((ok) => {
    if (!ok) console.warn("[Notification] Owner alert not delivered:", title);
  });
}

const fullNameSchema = z
  .string()
  .min(2, "Please enter your full name")
  .max(200)
  .regex(/^[a-zA-ZÀ-ÿ'’.\- ]+$/, "Name may only contain letters, spaces, hyphens and apostrophes");

const birthdateSchema = z
  .string()
  .regex(/^\d{4}-\d{2}-\d{2}$/, "Birthdate must be YYYY-MM-DD")
  .refine((v) => {
    const d = new Date(v + "T00:00:00Z");
    if (Number.isNaN(d.getTime())) return false;
    const now = new Date();
    const age = (now.getTime() - d.getTime()) / (365.25 * 24 * 3600 * 1000);
    return age >= 16 && age <= 100;
  }, "Please enter a valid birthdate (candidates must be at least 16)");

const answersSchema = z.record(z.string(), z.number().int().min(0).max(3));

const emailSchema = z
  .string()
  .trim()
  .max(320)
  .refine((v) => v === "" || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v), "Please enter a valid email address")
  .optional();

const RESUME_MAX_BYTES = 10 * 1024 * 1024; // 10 MB
const RESUME_MIME_ALLOWLIST: Record<string, string> = {
  "application/pdf": ".pdf",
  "application/msword": ".doc",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
  "image/jpeg": ".jpg",
  "image/png": ".png",
};

/** Send the candidate a registration receipt when they gave us an email. */
function sendCandidateReceipt(candidate: { fullName: string; email?: string | null }) {
  if (!candidate.email) return;
  notifyOwner({
    title: `ECI Candidate Portal registration receipt for ${candidate.fullName}`,
    content: [
      `To: ${candidate.email}`,
      ``,
      `Hi ${candidate.fullName.split(" ")[0]},`,
      ``,
      `Thank you for registering with the ECI Candidate Portal. Your candidate record has been created.`,
      ``,
      `Next steps:`,
      `1. Complete the ECI aptitude assessment (opens in a new tab from your dashboard).`,
      `2. Watch the safety training video and pass its knowledge check.`,
      ``,
      `You can return at any time using your full name and birthdate.`,
      ``,
      `— Electrical Contractor Inc. (ECI), est. 1984`,
    ].join("\n"),
  }).then((ok) => {
    if (!ok) console.warn("[Notification] Candidate receipt not delivered for", candidate.email);
  });
}

const adminProcedure = protectedProcedure.use(({ ctx, next }) => {
  if (ctx.user.role !== "admin") throw new TRPCError({ code: "FORBIDDEN" });
  return next({ ctx });
});

async function requireCandidate(candidateId: number) {
  const candidate = await db.getCandidateById(candidateId);
  if (!candidate) {
    throw new TRPCError({ code: "NOT_FOUND", message: "Candidate record not found. Please register again." });
  }
  return candidate;
}

export const appRouter = router({
  recruitme: recruitmeRouter,
    // if you need to use socket.io, read and register route in server/_core/index.ts, all api should start with '/api/' so that the gateway can route correctly
  system: systemRouter,
  auth: router({
    me: publicProcedure.query(opts => opts.ctx.user),
    logout: publicProcedure.mutation(({ ctx }) => {
      const cookieOptions = getSessionCookieOptions(ctx.req);
      ctx.res.clearCookie(COOKIE_NAME, { ...cookieOptions, maxAge: -1 });
      return {
        success: true,
      } as const;
    }),
  }),

  /* ---------------------------------------------------------------- */
  /* Candidate registration & progress                                 */
  /* ---------------------------------------------------------------- */
  candidate: router({
    /** Register (or resume) a candidate by full name + birthdate. */
    register: publicProcedure
      .input(
        z.object({
          fullName: fullNameSchema,
          birthdate: birthdateSchema,
          email: emailSchema,
        })
      )
      .mutation(async ({ input }) => {
        const { candidate, isReturning } = await db.upsertCandidate({
          fullName: input.fullName,
          birthdate: input.birthdate,
          email: input.email || null,
        });
        if (!isReturning) sendCandidateReceipt(candidate);
        return { candidate, isReturning };
      }),

    /** Upload (or replace) the candidate's resume. base64 data URL payload. */
    uploadResume: publicProcedure
      .input(
        z.object({
          candidateId: z.number().int().positive(),
          filename: z.string().min(1).max(255),
          contentType: z.string(),
          dataBase64: z.string().min(1),
        })
      )
      .mutation(async ({ input }) => {
        const candidate = await requireCandidate(input.candidateId);
        const ext = RESUME_MIME_ALLOWLIST[input.contentType];
        if (!ext) {
          throw new TRPCError({
            code: "BAD_REQUEST",
            message: "Resume must be a PDF, Word document, JPG, or PNG.",
          });
        }
        const bytes = Buffer.from(input.dataBase64, "base64");
        if (bytes.length === 0 || bytes.length > RESUME_MAX_BYTES) {
          throw new TRPCError({
            code: "BAD_REQUEST",
            message: "Resume must be smaller than 10 MB.",
          });
        }
        const safeName = candidate.fullName.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
        const { key, url } = await storagePut(
          `resumes/${candidate.id}-${safeName}${ext}`,
          bytes,
          input.contentType
        );
        await db.setCandidateResume(candidate.id, { url, key, filename: input.filename });
        return { url, filename: input.filename };
      }),

    /** Full progress snapshot for the candidate dashboard. */
    dashboard: publicProcedure
      .input(z.object({ candidateId: z.number().int().positive() }))
      .query(async ({ input }) => {
        const candidate = await requireCandidate(input.candidateId);
        const [latestAptitude, progressRows] = await Promise.all([
          db.getLatestAptitudeAttempt(candidate.id),
          db.getSafetyProgress(candidate.id),
        ]);

        const lessons = publicSafetyLessons().map((lesson) => {
          const row = progressRows.find((r) => r.lessonId === lesson.id);
          const videoWatched = row?.videoWatched ?? false;
          const quizPassed = row?.quizPassed ?? false;
          const completed = Boolean(row?.completedAt) || (videoWatched && quizPassed);
          return {
            id: lesson.id,
            order: lesson.order,
            title: lesson.title,
            summary: lesson.summary,
            durationLabel: lesson.durationLabel,
            passPercent: lesson.passPercent,
            available: Boolean(lesson.videoUrl),
            videoWatched,
            quizPassed,
            bestQuizPercent: row?.bestQuizPercent ?? null,
            completed,
            completedAt: row?.completedAt ?? null,
          };
        });

        const availableLessons = lessons.filter((l) => l.available);
        const lessonsCompleted = availableLessons.filter((l) => l.completed).length;
        return {
          candidate,
          aptitude: latestAptitude
            ? {
                status: "completed" as const,
                scorePercent: latestAptitude.scorePercent,
                scoreCorrect: latestAptitude.scoreCorrect,
                scoreTotal: latestAptitude.scoreTotal,
                passed: latestAptitude.passed,
                completedAt: latestAptitude.createdAt,
              }
            : candidate.aptitudeStartedAt
              ? { status: "in-progress" as const, startedAt: candidate.aptitudeStartedAt }
              : { status: "pending" as const },
          lessons,
          lessonsCompleted,
          lessonsTotal: availableLessons.length,
          safetyComplete: availableLessons.length > 0 && lessonsCompleted === availableLessons.length,
        };
      }),
  }),

  /* ---------------------------------------------------------------- */
  /* Aptitude assessment                                               */
  /* ---------------------------------------------------------------- */
  aptitude: router({
    /** Question bank without correct answers. */
    questions: publicProcedure.query(() => ({
      questions: publicAptitudeQuestions(),
      passPercent: APTITUDE_PASS_PERCENT,
      total: APTITUDE_QUESTIONS.length,
    })),

    /** Mark that a candidate has started the assessment (for dashboard status). */
    start: publicProcedure
      .input(z.object({ candidateId: z.number().int().positive() }))
      .mutation(async ({ input }) => {
        await requireCandidate(input.candidateId);
        await db.markAptitudeStarted(input.candidateId);
        return { success: true as const };
      }),

    /** Score and persist a completed assessment. */
    submit: publicProcedure
      .input(z.object({ candidateId: z.number().int().positive(), answers: answersSchema }))
      .mutation(async ({ input }) => {
        const candidate = await requireCandidate(input.candidateId);
        const answeredIds = Object.keys(input.answers);
        const missing = APTITUDE_QUESTIONS.filter((q) => !answeredIds.includes(q.id));
        if (missing.length > 0) {
          throw new TRPCError({
            code: "BAD_REQUEST",
            message: `Please answer all questions before submitting (${missing.length} unanswered).`,
          });
        }
        const result = scoreAptitude(input.answers);
        const attempt = await db.insertAptitudeAttempt({
          candidateId: input.candidateId,
          answers: input.answers,
          scoreCorrect: result.correct,
          scoreTotal: result.total,
          scorePercent: result.percent,
          passed: result.passed,
          categoryBreakdown: result.byCategory,
        });
        alertOwner(
          `ECI Candidate Portal: ${candidate.fullName} submitted the aptitude assessment — ${result.percent}%`,
          [
            `Candidate: ${candidate.fullName}`,
            `Birthdate: ${candidate.birthdate}`,
            `Score: ${result.percent}% (${result.correct}/${result.total}) — ${result.passed ? "meets" : "below"} the ${APTITUDE_PASS_PERCENT}% benchmark`,
          ].join("\n")
        );
        return { attemptId: attempt.id, ...result };
      }),

    /** Latest result for a candidate (for the results screen). */
    latest: publicProcedure
      .input(z.object({ candidateId: z.number().int().positive() }))
      .query(async ({ input }) => {
        await requireCandidate(input.candidateId);
        const attempt = await db.getLatestAptitudeAttempt(input.candidateId);
        return attempt ?? null;
      }),

    /**
     * The assessment is hosted externally (Microsoft Forms). Candidates confirm
     * completion here so their record reflects it; ECI staff verify the actual
     * score in Forms and can record it via recordResult.
     */
    confirmCompleted: publicProcedure
      .input(z.object({ candidateId: z.number().int().positive() }))
      .mutation(async ({ input }) => {
        const candidate = await requireCandidate(input.candidateId);
        const existing = await db.getLatestAptitudeAttempt(input.candidateId);
        if (existing) return { attemptId: existing.id, alreadyRecorded: true as const };
        const attempt = await db.insertAptitudeAttempt({
          candidateId: input.candidateId,
          answers: { external: -1 },
          scoreCorrect: 0,
          scoreTotal: 0,
          scorePercent: 0,
          passed: false,
          categoryBreakdown: null,
        });
        alertOwner(
          `ECI Candidate Portal: ${candidate.fullName} completed the aptitude assessment`,
          [
            `Candidate: ${candidate.fullName}`,
            `Birthdate: ${candidate.birthdate}`,
            candidate.email ? `Email: ${candidate.email}` : null,
            candidate.resumeUrl
              ? `Resume: ${candidate.resumeUrl} (${candidate.resumeFilename ?? "download"})`
              : `Resume: not uploaded`,
            ``,
            `The candidate confirmed completion of the aptitude assessment (Microsoft Forms).`,
            `Verify their score in the form responses, then record it from the ECI results view.`,
          ].filter((l): l is string => l !== null).join("\n")
        );
        return { attemptId: attempt.id, alreadyRecorded: false as const };
      }),

    /** Staff-side: record the verified external score onto the candidate record. */
    recordResult: adminProcedure
      .input(
        z.object({
          candidateId: z.number().int().positive(),
          scorePercent: z.number().int().min(0).max(100),
        })
      )
      .mutation(async ({ input }) => {
        await requireCandidate(input.candidateId);
        const attempt = await db.insertAptitudeAttempt({
          candidateId: input.candidateId,
          answers: { external: -1 },
          scoreCorrect: 0,
          scoreTotal: 0,
          scorePercent: input.scorePercent,
          passed: input.scorePercent >= APTITUDE_PASS_PERCENT,
          categoryBreakdown: null,
        });
        return { attemptId: attempt.id, scorePercent: input.scorePercent };
      }),
  }),

  /* ---------------------------------------------------------------- */
  /* Safety training                                                   */
  /* ---------------------------------------------------------------- */
  safety: router({
    /** Lessons (without answers) merged with this candidate's progress. */
    lessons: publicProcedure
      .input(z.object({ candidateId: z.number().int().positive() }))
      .query(async ({ input }) => {
        await requireCandidate(input.candidateId);
        const progressRows = await db.getSafetyProgress(input.candidateId);
        return publicSafetyLessons().map((lesson) => {
          const row = progressRows.find((r) => r.lessonId === lesson.id);
          const videoWatched = row?.videoWatched ?? false;
          const quizPassed = row?.quizPassed ?? false;
          return {
            ...lesson,
            available: Boolean(lesson.videoUrl),
            videoWatched,
            quizPassed,
            bestQuizPercent: row?.bestQuizPercent ?? null,
            completed: Boolean(row?.completedAt) || (videoWatched && quizPassed),
            completedAt: row?.completedAt ?? null,
          };
        });
      }),

    /** Record that the candidate watched a lesson video. */
    markWatched: publicProcedure
      .input(z.object({
        candidateId: z.number().int().positive(),
        lessonId: z
          .string()
          .refine((v) => activeSafetyLessons().some((l) => l.id === v), "Lesson not available"),
      }))
      .mutation(async ({ input }) => {
        await requireCandidate(input.candidateId);
        await db.markLessonWatched(input.candidateId, input.lessonId);
        await db.completeLessonIfReady(input.candidateId, input.lessonId);
        return { success: true as const };
      }),

    /** Score and persist a knowledge-check attempt. */
    submitQuiz: publicProcedure
      .input(z.object({
        candidateId: z.number().int().positive(),
        lessonId: z
          .string()
          .refine((v) => activeSafetyLessons().some((l) => l.id === v), "Lesson not available"),
        answers: answersSchema,
      }))
      .mutation(async ({ input }) => {
        const candidate = await requireCandidate(input.candidateId);
        const lesson = SAFETY_LESSONS.find((l) => l.id === input.lessonId)!;
        const missing = lesson.quiz.filter((q) => !(q.id in input.answers));
        if (missing.length > 0) {
          throw new TRPCError({ code: "BAD_REQUEST", message: "Please answer every question before submitting." });
        }
        const result = scoreSafetyQuiz(input.lessonId, input.answers);
        await db.insertSafetyQuizAttempt({
          candidateId: input.candidateId,
          lessonId: input.lessonId,
          answers: input.answers,
          scoreCorrect: result.correct,
          scoreTotal: result.total,
          scorePercent: result.percent,
          passed: result.passed,
        });
        await db.recordSafetyQuizResult({
          candidateId: input.candidateId,
          lessonId: input.lessonId,
          percent: result.percent,
          passed: result.passed,
        });
        if (result.passed) {
          const progress = await db.getSafetyProgress(input.candidateId);
          const available = activeSafetyLessons();
          const completedCount = available.filter((l) => {
            const row = progress.find((p) => p.lessonId === l.id);
            return Boolean(row?.completedAt) || Boolean(row?.videoWatched && row?.quizPassed);
          }).length;
          const allDone = completedCount === available.length;
          alertOwner(
            `ECI Candidate Portal: ${candidate.fullName} passed "${lesson.title}" — ${result.percent}%`,
            [
              `Candidate: ${candidate.fullName}`,
              `Birthdate: ${candidate.birthdate}`,
              candidate.email ? `Email: ${candidate.email}` : null,
              candidate.resumeUrl
                ? `Resume: ${candidate.resumeUrl} (${candidate.resumeFilename ?? "download"})`
                : null,
              `Lesson: ${lesson.title}`,
              `Score: ${result.percent}% (${result.correct}/${result.total})`,
              ``,
              allDone
                ? `This candidate has now completed ALL required safety training (${completedCount}/${available.length} lessons).`
                : `Safety training progress: ${completedCount}/${available.length} lessons complete.`,
            ].filter((l): l is string => l !== null).join("\n")
          );
        }
        return result;
      }),
  }),

  /* ---------------------------------------------------------------- */
  /* Internal ECI results view (admin only)                            */
  /* ---------------------------------------------------------------- */
  admin: router({
    /** All candidates with their latest aptitude score and safety completion. */
    candidates: adminProcedure.query(async () => {
      const [allCandidates, allAptitude, allProgress] = await Promise.all([
        db.listCandidates(),
        db.listAllAptitudeAttempts(),
        db.listAllSafetyProgress(),
      ]);
      const availableLessons = activeSafetyLessons();
      const totalLessons = availableLessons.length;
      return allCandidates.map((c) => {
        const latest = allAptitude.find((a) => a.candidateId === c.id);
        const progress = allProgress.filter((p) => p.candidateId === c.id);
        const lessonsCompleted = availableLessons.filter((lesson) => {
          const row = progress.find((p) => p.lessonId === lesson.id);
          return Boolean(row?.completedAt) || Boolean(row?.videoWatched && row?.quizPassed);
        }).length;
        return {
          ...c,
          aptitude: latest
            ? {
                scorePercent: latest.scorePercent,
                scoreCorrect: latest.scoreCorrect,
                scoreTotal: latest.scoreTotal,
                passed: latest.passed,
                completedAt: latest.createdAt,
              }
            : null,
          lessonsCompleted,
          lessonsTotal: totalLessons,
          safetyComplete: totalLessons > 0 && lessonsCompleted === totalLessons,
        };
      });
    }),

    /** Full detail for one candidate: aptitude history + every quiz attempt. */
    candidateDetail: adminProcedure
      .input(z.object({ candidateId: z.number().int().positive() }))
      .query(async ({ input }) => {
        const candidate = await requireCandidate(input.candidateId);
        const [aptitudeHistory, progressRows, quizAttempts] = await Promise.all([
          db.listAptitudeAttempts(candidate.id),
          db.getSafetyProgress(candidate.id),
          db.listSafetyQuizAttempts(candidate.id),
        ]);
        const lessons = SAFETY_LESSONS.map((lesson) => {
          const row = progressRows.find((r) => r.lessonId === lesson.id);
          const attempts = quizAttempts.filter((a) => a.lessonId === lesson.id);
          const videoWatched = row?.videoWatched ?? false;
          const quizPassed = row?.quizPassed ?? false;
          return {
            lessonId: lesson.id,
            title: lesson.title,
            available: Boolean(lesson.videoUrl),
            videoWatched,
            watchedAt: row?.watchedAt ?? null,
            quizPassed,
            bestQuizPercent: row?.bestQuizPercent ?? null,
            completed: Boolean(row?.completedAt) || (videoWatched && quizPassed),
            completedAt: row?.completedAt ?? null,
            attempts: attempts.map((a) => ({
              id: a.id,
              scorePercent: a.scorePercent,
              scoreCorrect: a.scoreCorrect,
              scoreTotal: a.scoreTotal,
              passed: a.passed,
              createdAt: a.createdAt,
            })),
          };
        });
        return { candidate, aptitudeHistory, lessons };
      }),
  }),
});

export type AppRouter = typeof appRouter;
