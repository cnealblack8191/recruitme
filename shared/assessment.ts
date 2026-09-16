/**
 * ECI Candidate Portal — shared assessment content.
 * This module is imported by BOTH server (scoring) and client (rendering),
 * so it must stay free of server-only or client-only dependencies.
 */

export const BRAND = {
  companyName: "ECI",
  tagline: "Building Careers on Solid Ground",
  logoUrl: "/manus-storage/eci-logo-official_564e18df.svg",
  heroUrl: "/manus-storage/eci-hero-red_3dc638b2.jpg",
} as const;

/** The aptitude assessment is currently hosted externally (Microsoft Forms). */
export const APTITUDE_FORM_URL =
  "https://forms.cloud.microsoft/Pages/ResponsePage.aspx?id=5oRocoX5FUGcPfArPhkUfptjl8VgD0ZPkzZT_IBh62pUOVdKWUhaSVkwWlpBMzdQUVNUNkUxODFXRS4u";

/* ------------------------------------------------------------------ */
/* Aptitude assessment                                                 */
/* ------------------------------------------------------------------ */

export type AptitudeCategory =
  | "numerical"
  | "verbal"
  | "spatial"
  | "safetyJudgment";

export interface AptitudeQuestion {
  id: string;
  category: AptitudeCategory;
  prompt: string;
  options: string[];
  /** Index into options. NEVER sent to the client. */
  correctIndex: number;
}

export const APTITUDE_PASS_PERCENT = 70;

export const APTITUDE_QUESTIONS: AptitudeQuestion[] = [
  {
    id: "num-1",
    category: "numerical",
    prompt:
      "A crew installs 48 feet of railing per hour. At that rate, how many feet will the crew install in 6.5 hours?",
    options: ["288 feet", "312 feet", "324 feet", "336 feet"],
    correctIndex: 1,
  },
  {
    id: "num-2",
    category: "numerical",
    prompt:
      "A pallet holds 1,250 fasteners. A job requires 4,375 fasteners. How many full pallets must be delivered?",
    options: ["3", "3.5", "4", "5"],
    correctIndex: 2,
  },
  {
    id: "num-3",
    category: "numerical",
    prompt:
      "Concrete is ordered by the cubic yard. A slab needs 9.75 cubic yards, and the supplier only sells in whole cubic yards. How many cubic yards should be ordered?",
    options: ["9", "9.75", "10", "11"],
    correctIndex: 2,
  },
  {
    id: "ver-1",
    category: "verbal",
    prompt:
      "Choose the word that is closest in meaning to \"MANDATORY\":",
    options: ["Optional", "Required", "Suggested", "Temporary"],
    correctIndex: 1,
  },
  {
    id: "ver-2",
    category: "verbal",
    prompt:
      "\"All operators who use the lift must wear a harness. Dana is using the lift.\" Which conclusion follows with certainty?",
    options: [
      "Dana is an operator",
      "Dana must wear a harness",
      "Dana does not need a harness",
      "Dana trained the other operators",
    ],
    correctIndex: 1,
  },
  {
    id: "ver-3",
    category: "verbal",
    prompt:
      "A sign reads: \"AUTHORIZED PERSONNEL ONLY BEYOND THIS POINT.\" Who may pass the sign?",
    options: [
      "Anyone wearing a hard hat",
      "Only people with authorization",
      "Any employee of the company",
      "Visitors accompanied by a friend",
    ],
    correctIndex: 1,
  },
  {
    id: "spa-1",
    category: "spatial",
    prompt:
      "A bolt is tightened clockwise when viewed from the head. Viewed from the opposite (threaded) end, the same tightening motion appears to turn:",
    options: [
      "Clockwise",
      "Counterclockwise",
      "It does not appear to turn",
      "It depends on the bolt size",
    ],
    correctIndex: 1,
  },
  {
    id: "spa-2",
    category: "spatial",
    prompt:
      "On a floor plan, 1 inch represents 8 feet. A room measures 3.5 inches by 2 inches on the plan. What is the room's actual area?",
    options: ["56 square feet", "448 square feet", "28 square feet", "224 square feet"],
    correctIndex: 1,
  },
  {
    id: "spa-3",
    category: "spatial",
    prompt:
      "A pipe runs north, turns 90° east, then turns 90° south. In which direction is the pipe now running?",
    options: ["North", "East", "South", "West"],
    correctIndex: 2,
  },
  {
    id: "saf-1",
    category: "safetyJudgment",
    prompt:
      "You notice a coworker about to lift a heavy load alone, bent at the waist with a rounded back. What is the BEST action?",
    options: [
      "Say nothing — it is their choice",
      "Offer to help and suggest lifting with the legs, keeping the back straight",
      "Lift it yourself instead",
      "Report them to a supervisor immediately",
    ],
    correctIndex: 1,
  },
  {
    id: "saf-2",
    category: "safetyJudgment",
    prompt:
      "A ladder you are about to use has a cracked rung. What should you do FIRST?",
    options: [
      "Use it carefully, avoiding the cracked rung",
      "Tape the rung and continue working",
      "Tag the ladder as defective and take it out of service",
      "Lean it at a steeper angle to reduce weight on the rung",
    ],
    correctIndex: 2,
  },
  {
    id: "saf-3",
    category: "safetyJudgment",
    prompt:
      "You are unsure how to operate a piece of equipment you have been assigned. What should you do?",
    options: [
      "Figure it out by trying the controls",
      "Ask a trained coworker to do it for you",
      "Tell your supervisor you need training before operating it",
      "Watch an online video during your break, then operate it",
    ],
    correctIndex: 2,
  },
];

export const APTITUDE_CATEGORY_LABELS: Record<AptitudeCategory, string> = {
  numerical: "Numerical Reasoning",
  verbal: "Verbal Comprehension",
  spatial: "Spatial & Plan Reading",
  safetyJudgment: "Safety Judgment",
};

/* ------------------------------------------------------------------ */
/* Safety training lessons                                             */
/* ------------------------------------------------------------------ */

export interface SafetyQuizQuestion {
  id: string;
  prompt: string;
  options: string[];
  /** Index into options. NEVER sent to the client. */
  correctIndex: number;
}

export interface SafetyLesson {
  id: string;
  order: number;
  title: string;
  summary: string;
  durationLabel: string;
  /** Present when the lesson video is available; absent for coming-soon topics. */
  videoUrl?: string;
  posterNote?: string;
  passPercent: number;
  quiz: SafetyQuizQuestion[];
}

export const SAFETY_LESSONS: SafetyLesson[] = [
  {
    id: "lesson-eci-orientation",
    order: 1,
    title: "ECI Safety Orientation",
    summary:
      "ECI's core safety training video — the expectations, protective equipment, and safe work practices every candidate must know before stepping onto a job site.",
    durationLabel: "About 9.5 minutes",
    videoUrl: "/manus-storage/eci-safety-main_05287cfd.mp4",
    posterNote: "ECI's official safety training video.",
    passPercent: 67,
    quiz: [
      {
        id: "ori-q1",
        prompt: "When should required personal protective equipment (PPE) be put on?",
        options: [
          "Only when hazards are visible",
          "Before starting any task that requires it, and kept on for the whole task",
          "Only when a supervisor is watching",
          "At the end of the shift",
        ],
        correctIndex: 1,
      },
      {
        id: "ori-q2",
        prompt: "What should you do if your PPE or safety equipment is damaged or defective?",
        options: [
          "Keep using it until the end of the week",
          "Repair it yourself with tape",
          "Take it out of service and get a replacement before continuing work",
          "Share a coworker's equipment instead",
        ],
        correctIndex: 2,
      },
      {
        id: "ori-q3",
        prompt: "If you see an unsafe condition on the job site that you cannot fix yourself, you should:",
        options: [
          "Ignore it if it is not your job",
          "Warn others, stop the affected work, and report it to a supervisor",
          "Wait to see if someone else reports it",
          "Mention it at the end of the week",
        ],
        correctIndex: 1,
      },
    ],
  },
  {
    id: "lesson-electrical-safety",
    order: 2,
    title: "Electrical Safety & Lockout/Tagout",
    summary:
      "Working around energized equipment, safe clearances, and the lockout/tagout steps that keep everyone protected.",
    durationLabel: "Video coming soon",
    passPercent: 67,
    quiz: [],
  },
  {
    id: "lesson-fall-protection",
    order: 3,
    title: "Fall Protection & Ladder Safety",
    summary:
      "Harness use and inspection, anchor points, ladder setup, and the rules for working at height.",
    durationLabel: "Video coming soon",
    passPercent: 67,
    quiz: [],
  },
  {
    id: "lesson-ppe-essentials",
    order: 4,
    title: "PPE Essentials: Head, Eye & Hearing",
    summary:
      "Hard hats, eye and face protection, and hearing protection — what to wear, when, and how to inspect it.",
    durationLabel: "Video coming soon",
    passPercent: 67,
    quiz: [],
  },
  {
    id: "lesson-hazard-communication",
    order: 5,
    title: "Hazard Communication & SDS",
    summary:
      "Reading labels and Safety Data Sheets, handling chemicals safely, and knowing your right to understand site hazards.",
    durationLabel: "Video coming soon",
    passPercent: 67,
    quiz: [],
  },
  {
    id: "lesson-tool-equipment-safety",
    order: 6,
    title: "Hand & Power Tool Safety",
    summary:
      "Pre-use inspections, guards, cords, and safe operation of the tools used every day on ECI job sites.",
    durationLabel: "Video coming soon",
    passPercent: 67,
    quiz: [],
  },
];

/** Lessons that currently have a video and can be taken. */
export function activeSafetyLessons() {
  return SAFETY_LESSONS.filter((l) => Boolean(l.videoUrl));
}

/* ------------------------------------------------------------------ */
/* Client-safe projections (strip correct answers)                     */
/* ------------------------------------------------------------------ */

export function publicAptitudeQuestions() {
  return APTITUDE_QUESTIONS.map(({ id, category, prompt, options }) => ({
    id,
    category,
    prompt,
    options,
  }));
}

export function publicSafetyLessons() {
  return SAFETY_LESSONS.map(({ quiz, ...lesson }) => ({
    ...lesson,
    quiz: quiz.map(({ id, prompt, options }) => ({ id, prompt, options })),
  }));
}

/* ------------------------------------------------------------------ */
/* Scoring helpers (shared so tests and server use the same logic)     */
/* ------------------------------------------------------------------ */

export function scoreAptitude(answers: Record<string, number>) {
  let correct = 0;
  const byCategory: Record<AptitudeCategory, { correct: number; total: number }> = {
    numerical: { correct: 0, total: 0 },
    verbal: { correct: 0, total: 0 },
    spatial: { correct: 0, total: 0 },
    safetyJudgment: { correct: 0, total: 0 },
  };

  for (const q of APTITUDE_QUESTIONS) {
    byCategory[q.category].total += 1;
    if (answers[q.id] === q.correctIndex) {
      correct += 1;
      byCategory[q.category].correct += 1;
    }
  }

  const total = APTITUDE_QUESTIONS.length;
  const percent = Math.round((correct / total) * 100);
  return {
    correct,
    total,
    percent,
    passed: percent >= APTITUDE_PASS_PERCENT,
    byCategory,
  };
}

export function scoreSafetyQuiz(
  lessonId: string,
  answers: Record<string, number>
) {
  const lesson = SAFETY_LESSONS.find((l) => l.id === lessonId);
  if (!lesson) throw new Error(`Unknown lesson: ${lessonId}`);
  if (!lesson.videoUrl || lesson.quiz.length === 0)
    throw new Error(`Lesson not yet available: ${lessonId}`);
  let correct = 0;
  for (const q of lesson.quiz) {
    if (answers[q.id] === q.correctIndex) correct += 1;
  }
  const total = lesson.quiz.length;
  const percent = Math.round((correct / total) * 100);
  return { correct, total, percent, passed: percent >= lesson.passPercent };
}
