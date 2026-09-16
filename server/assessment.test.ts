import { describe, expect, it } from "vitest";
import {
  APTITUDE_PASS_PERCENT,
  APTITUDE_QUESTIONS,
  SAFETY_LESSONS,
  publicAptitudeQuestions,
  publicSafetyLessons,
  scoreAptitude,
  scoreSafetyQuiz,
} from "../shared/assessment";
import { appRouter } from "./routers";
import type { TrpcContext } from "./_core/context";

/* ------------------------------------------------------------------ */
/* Scoring helpers                                                     */
/* ------------------------------------------------------------------ */

function allCorrectAnswers(): Record<string, number> {
  const answers: Record<string, number> = {};
  for (const q of APTITUDE_QUESTIONS) answers[q.id] = q.correctIndex;
  return answers;
}

function allWrongAnswers(): Record<string, number> {
  const answers: Record<string, number> = {};
  for (const q of APTITUDE_QUESTIONS) answers[q.id] = (q.correctIndex + 1) % q.options.length;
  return answers;
}

describe("scoreAptitude", () => {
  it("awards 100% and a pass for a perfect paper", () => {
    const result = scoreAptitude(allCorrectAnswers());
    expect(result.percent).toBe(100);
    expect(result.correct).toBe(APTITUDE_QUESTIONS.length);
    expect(result.passed).toBe(true);
  });

  it("awards 0% and a fail for an all-wrong paper", () => {
    const result = scoreAptitude(allWrongAnswers());
    expect(result.percent).toBe(0);
    expect(result.correct).toBe(0);
    expect(result.passed).toBe(false);
  });

  it("breaks scores down by category", () => {
    const answers = allWrongAnswers();
    // Answer the three numerical questions correctly
    for (const q of APTITUDE_QUESTIONS.filter((q) => q.category === "numerical")) {
      answers[q.id] = q.correctIndex;
    }
    const result = scoreAptitude(answers);
    expect(result.byCategory.numerical).toEqual({ correct: 3, total: 3 });
    expect(result.byCategory.verbal).toEqual({ correct: 0, total: 3 });
    expect(result.correct).toBe(3);
    expect(result.percent).toBe(25);
  });

  it("applies the pass threshold exactly", () => {
    // 12 questions: 70% pass mark => 9 correct = 75% (pass), 8 correct = 67% (fail)
    const nineCorrect = allWrongAnswers();
    APTITUDE_QUESTIONS.slice(0, 9).forEach((q) => (nineCorrect[q.id] = q.correctIndex));
    expect(scoreAptitude(nineCorrect).passed).toBe(true);

    const eightCorrect = allWrongAnswers();
    APTITUDE_QUESTIONS.slice(0, 8).forEach((q) => (eightCorrect[q.id] = q.correctIndex));
    const result = scoreAptitude(eightCorrect);
    expect(result.percent).toBe(67);
    expect(result.passed).toBe(false);
    expect(APTITUDE_PASS_PERCENT).toBe(70);
  });
});

describe("scoreSafetyQuiz", () => {
  it("passes at or above the lesson pass mark", () => {
    const lesson = SAFETY_LESSONS[0];
    const answers: Record<string, number> = {};
    lesson.quiz.forEach((q) => (answers[q.id] = q.correctIndex));
    const result = scoreSafetyQuiz(lesson.id, answers);
    expect(result.percent).toBe(100);
    expect(result.passed).toBe(true);
  });

  it("fails below the lesson pass mark", () => {
    const lesson = SAFETY_LESSONS[0];
    const answers: Record<string, number> = {};
    lesson.quiz.forEach((q) => (answers[q.id] = (q.correctIndex + 1) % q.options.length));
    const result = scoreSafetyQuiz(lesson.id, answers);
    expect(result.percent).toBe(0);
    expect(result.passed).toBe(false);
  });

  it("throws for an unknown lesson", () => {
    expect(() => scoreSafetyQuiz("no-such-lesson", {})).toThrow();
  });
});

describe("public projections", () => {
  it("never leak correct answers to the client", () => {
    for (const q of publicAptitudeQuestions()) {
      expect(q).not.toHaveProperty("correctIndex");
    }
    for (const lesson of publicSafetyLessons()) {
      for (const q of lesson.quiz) {
        expect(q).not.toHaveProperty("correctIndex");
      }
    }
  });
});

/* ------------------------------------------------------------------ */
/* Router-level validation (no database required)                      */
/* ------------------------------------------------------------------ */

function publicCtx(): TrpcContext {
  return {
    user: null,
    req: { protocol: "https", headers: {} } as TrpcContext["req"],
    res: { clearCookie: () => {} } as TrpcContext["res"],
  };
}

function staffCtx(role: "admin" | "user"): TrpcContext {
  return {
    user: {
      id: 1,
      openId: "staff-user",
      email: "staff@eci.example",
      name: "Staff User",
      loginMethod: "manus",
      role,
      createdAt: new Date(),
      updatedAt: new Date(),
      lastSignedIn: new Date(),
    },
    req: { protocol: "https", headers: {} } as TrpcContext["req"],
    res: { clearCookie: () => {} } as TrpcContext["res"],
  };
}

describe("candidate.register validation", () => {
  it("rejects an invalid birthdate format", async () => {
    const caller = appRouter.createCaller(publicCtx());
    await expect(
      caller.candidate.register({ fullName: "Jordan Martinez", birthdate: "12/05/1990" })
    ).rejects.toThrow();
  });

  it("rejects a name that is too short", async () => {
    const caller = appRouter.createCaller(publicCtx());
    await expect(
      caller.candidate.register({ fullName: "J", birthdate: "1990-12-05" })
    ).rejects.toThrow();
  });

  it("rejects candidates younger than 16", async () => {
    const caller = appRouter.createCaller(publicCtx());
    const recent = new Date();
    recent.setFullYear(recent.getFullYear() - 10);
    const dob = recent.toISOString().slice(0, 10);
    await expect(
      caller.candidate.register({ fullName: "Young Person", birthdate: dob })
    ).rejects.toThrow();
  });
});

describe("aptitude.submit validation", () => {
  it("rejects submissions for unknown candidates", async () => {
    const caller = appRouter.createCaller(publicCtx());
    const complete = allCorrectAnswers();
    await expect(
      caller.aptitude.submit({ candidateId: 999999, answers: complete })
    ).rejects.toThrow(/candidate record not found/i);
  });

  it("rejects submissions with missing answers", async () => {
    const caller = appRouter.createCaller(publicCtx());
    await expect(
      caller.aptitude.submit({ candidateId: 1, answers: { "num-1": 0 } })
    ).rejects.toThrow(/answer all questions/i);
  });
});

describe("safety.submitQuiz validation", () => {
  it("rejects unknown lessons", async () => {
    const caller = appRouter.createCaller(publicCtx());
    await expect(
      caller.safety.submitQuiz({ candidateId: 1, lessonId: "nope", answers: {} })
    ).rejects.toThrow();
  });
});

describe("admin access control", () => {
  it("rejects unauthenticated callers", async () => {
    const caller = appRouter.createCaller(publicCtx());
    await expect(caller.admin.candidates()).rejects.toThrow();
  });

  it("rejects non-admin staff", async () => {
    const caller = appRouter.createCaller(staffCtx("user"));
    await expect(caller.admin.candidates()).rejects.toThrow();
  });
});

/* ------------------------------------------------------------------ */
/* DB-backed flows (skipped when no test database is configured)       */
/* ------------------------------------------------------------------ */

const dbIt = process.env.DATABASE_URL ? it : it.skip;
const RUN_TAG = `Run${Date.now().toString(36).replace(/[0-9]/g, (d) => "ABCDEFGHIJ"[Number(d)]).slice(-8)}`;

describe("candidate registration persistence (DB)", () => {
  dbIt("saves name + birthdate and resumes the same record on re-register", async () => {
    const caller = appRouter.createCaller(publicCtx());
    const fullName = `Test Candidate ${RUN_TAG}`;
    const first = await caller.candidate.register({ fullName, birthdate: "1995-06-15" });
    expect(first.isReturning).toBe(false);
    expect(first.candidate.fullName).toBe(fullName);
    expect(first.candidate.birthdate).toBe("1995-06-15");

    const again = await caller.candidate.register({ fullName, birthdate: "1995-06-15" });
    expect(again.isReturning).toBe(true);
    expect(again.candidate.id).toBe(first.candidate.id);
  });
});

describe("safety completion flow (DB)", () => {
  dbIt("records watch + quiz pass and marks the lesson complete", async () => {
    const caller = appRouter.createCaller(publicCtx());
    const reg = await caller.candidate.register({
      fullName: `Safety Flow ${RUN_TAG}`,
      birthdate: "1992-03-20",
    });
    const cid = reg.candidate.id;
    const lesson = SAFETY_LESSONS[0];

    // Initially: nothing watched, nothing complete
    const before = await caller.safety.lessons({ candidateId: cid });
    const beforeLesson = before.find((l) => l.id === lesson.id)!;
    expect(beforeLesson.videoWatched).toBe(false);
    expect(beforeLesson.completed).toBe(false);

    // Watch the video
    await caller.safety.markWatched({ candidateId: cid, lessonId: lesson.id });
    const afterWatch = await caller.safety.lessons({ candidateId: cid });
    expect(afterWatch.find((l) => l.id === lesson.id)!.videoWatched).toBe(true);

    // Fail the quiz first — lesson must NOT be complete
    const wrong: Record<string, number> = {};
    lesson.quiz.forEach((q) => (wrong[q.id] = (q.correctIndex + 1) % q.options.length));
    const failed = await caller.safety.submitQuiz({ candidateId: cid, lessonId: lesson.id, answers: wrong });
    expect(failed.passed).toBe(false);
    const afterFail = await caller.safety.lessons({ candidateId: cid });
    expect(afterFail.find((l) => l.id === lesson.id)!.completed).toBe(false);

    // Pass the quiz — lesson becomes complete with a completion record
    const right: Record<string, number> = {};
    lesson.quiz.forEach((q) => (right[q.id] = q.correctIndex));
    const passed = await caller.safety.submitQuiz({ candidateId: cid, lessonId: lesson.id, answers: right });
    expect(passed.passed).toBe(true);
    const afterPass = await caller.safety.lessons({ candidateId: cid });
    const done = afterPass.find((l) => l.id === lesson.id)!;
    expect(done.quizPassed).toBe(true);
    expect(done.completed).toBe(true);
    expect(done.bestQuizPercent).toBe(100);

    // Dashboard reflects the completion
    const dash = await caller.candidate.dashboard({ candidateId: cid });
    expect(dash.lessonsCompleted).toBe(1);
    // The orientation is currently the only available lesson, so safety is complete
    expect(dash.safetyComplete).toBe(true);
  });
});

describe("coming-soon lessons", () => {
  it("placeholder topics are not available and cannot be watched or quizzed", async () => {
    const caller = appRouter.createCaller(publicCtx());
    const placeholder = SAFETY_LESSONS.find((l) => !l.videoUrl)!;
    expect(placeholder).toBeDefined();
    expect(placeholder.quiz.length).toBe(0);

    await expect(
      caller.safety.markWatched({ candidateId: 1, lessonId: placeholder.id })
    ).rejects.toThrow(/not available/i);
    await expect(
      caller.safety.submitQuiz({ candidateId: 1, lessonId: placeholder.id, answers: {} })
    ).rejects.toThrow(/not available/i);
  });

  it("dashboard only counts available lessons toward completion", async () => {
    const caller = appRouter.createCaller(publicCtx());
    const reg = await caller.candidate.register({
      fullName: `Placeholder Check ${RUN_TAG}`,
      birthdate: "1990-01-15",
    });
    const dash = await caller.candidate.dashboard({ candidateId: reg.candidate.id });
    const availableCount = SAFETY_LESSONS.filter((l) => l.videoUrl).length;
    expect(dash.lessonsTotal).toBe(availableCount);
    expect(dash.lessons.length).toBe(SAFETY_LESSONS.length);
    expect(dash.lessons.filter((l) => !l.available).length).toBeGreaterThan(0);
  });
});

describe("aptitude external form flow (DB)", () => {
  dbIt("confirmCompleted marks the assessment done without a score", async () => {
    const caller = appRouter.createCaller(publicCtx());
    const reg = await caller.candidate.register({
      fullName: `External Aptitude ${RUN_TAG}`,
      birthdate: "1993-07-08",
    });
    const cid = reg.candidate.id;

    const before = await caller.candidate.dashboard({ candidateId: cid });
    expect(before.aptitude.status).toBe("pending");

    await caller.aptitude.confirmCompleted({ candidateId: cid });
    const after = await caller.candidate.dashboard({ candidateId: cid });
    expect(after.aptitude.status).toBe("completed");

    // Idempotent: confirming twice does not create a second record
    const second = await caller.aptitude.confirmCompleted({ candidateId: cid });
    expect(second.alreadyRecorded).toBe(true);
  });
});

describe("registration email & resume", () => {
  dbIt("stores an optional email and backfills it for returning candidates", async () => {
    const caller = appRouter.createCaller(publicCtx());
    const name = `Email Test ${RUN_TAG}`;

    // Register without email
    const first = await caller.candidate.register({ fullName: name, birthdate: "1992-03-14" });
    expect(first.candidate.email).toBeNull();

    // Returning with an email backfills it
    const second = await caller.candidate.register({
      fullName: name,
      birthdate: "1992-03-14",
      email: "Candidate@Example.com",
    });
    expect(second.isReturning).toBe(true);
    expect(second.candidate.email).toBe("candidate@example.com");
  });

  it("rejects malformed email addresses", async () => {
    const caller = appRouter.createCaller(publicCtx());
    await expect(
      caller.candidate.register({
        fullName: "Bad Email Person",
        birthdate: "1990-01-01",
        email: "not-an-email",
      })
    ).rejects.toThrow(/valid email/i);
  });

  it("rejects disallowed resume file types", async () => {
    const caller = appRouter.createCaller(publicCtx());
    await expect(
      caller.candidate.uploadResume({
        candidateId: 1,
        filename: "evil.exe",
        contentType: "application/x-msdownload",
        dataBase64: Buffer.from("x").toString("base64"),
      })
    ).rejects.toThrow(/PDF, Word/i);
  });
});

describe("aptitude start → in-progress → completed (DB)", () => {
  dbIt("tracks assessment status transitions on the dashboard", async () => {
    const caller = appRouter.createCaller(publicCtx());
    const reg = await caller.candidate.register({
      fullName: `Aptitude Flow ${RUN_TAG}`,
      birthdate: "1988-11-02",
    });
    const cid = reg.candidate.id;

    const pending = await caller.candidate.dashboard({ candidateId: cid });
    expect(pending.aptitude.status).toBe("pending");

    await caller.aptitude.start({ candidateId: cid });
    const started = await caller.candidate.dashboard({ candidateId: cid });
    expect(started.aptitude.status).toBe("in-progress");

    const answers: Record<string, number> = {};
    APTITUDE_QUESTIONS.forEach((q) => (answers[q.id] = q.correctIndex));
    const result = await caller.aptitude.submit({ candidateId: cid, answers });
    expect(result.percent).toBe(100);
    const done = await caller.candidate.dashboard({ candidateId: cid });
    expect(done.aptitude.status).toBe("completed");
  });
});
