# Project TODO — ECI Candidate Portal

## Content & Data
- [x] Source 3 public-domain workplace safety training videos (Pexels, direct mp4) and upload to webdev storage
- [x] Generate ECI logo (attachment never arrived) and upload to webdev storage
- [x] Author aptitude question bank (12 questions, 4 categories) in shared/assessment.ts
- [x] Author 3 safety lessons with knowledge-check quizzes in shared/assessment.ts
- [x] DB schema: candidates, aptitude_attempts, safety_progress, safety_quiz_attempts tables + migration applied

## Backend (tRPC)
- [x] candidate.register (name + birthdate, upsert/returning-candidate resume)
- [x] candidate.dashboard (progress summary for one candidate)
- [x] aptitude.questions (no correct answers leaked) + aptitude.submit (server-side scoring, saved)
- [x] safety.lessons + safety.markWatched + safety.submitQuiz (scored, saved, completion recorded)
- [x] admin.candidates + admin.candidateDetail (role-gated)

## Frontend
- [x] ECI brand theme (fonts, palette, index.css) + branded header/footer layout
- [x] Landing page with ECI logo, welcome, begin/resume entry points
- [x] Registration page (full name + birthdate, saved to DB) + returning-candidate tab
- [x] Candidate dashboard: pending / in-progress / completed status for aptitude + all safety lessons
- [x] Aptitude test: one-question-at-a-time, required-answer validation, progress bar, auto-scored results view
- [x] Safety training: video player per lesson, watch-to-unlock quiz, knowledge check, score + completion record
- [x] Admin results view: all candidates, aptitude scores, safety quiz outcomes, completion status + detail drawer

## Quality & Delivery
- [x] Vitest coverage for scoring, registration, safety completion, admin gating (16 tests passing)
- [x] Screenshot verification of all pages
- [x] End-to-end API smoke test: register → aptitude submit → watch video → pass quiz → dashboard reflects progress
- [x] Persist aptitude in-progress status (aptitudeStartedAt) and show it on the dashboard
- [x] Gate safety quiz unlock on successful markWatched persistence, with error toast + automatic retry on continued watching
- [x] Vitest coverage for registration/resume persistence and safety completion record flow
- [x] Final checkpoint + delivery

## Round 2 — Email & resume
- [x] Add optional email + resume columns to candidates schema, migrate DB
- [x] Resume upload endpoint (S3) + register/resume procedure updates
- [x] Candidate registration receipt routed to owner notification channel with the candidate's email address (true outbound candidate email needs an SMTP provider)
- [x] Include resume link + candidate email in owner completion alert notifications
- [x] Registration form: optional email field + resume file picker
- [x] Admin detail: show candidate email + resume link
- [x] Tests + live verification + checkpoint
