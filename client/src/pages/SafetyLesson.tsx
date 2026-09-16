import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useParams } from "wouter";
import { PageShell } from "@/components/Brand";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { trpc } from "@/lib/trpc";
import { useCandidate } from "@/contexts/CandidateContext";
import { toast } from "sonner";
import { AnimatePresence, motion } from "framer-motion";
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  CirclePlay,
  Loader2,
  Lock,
  RotateCcw,
  Send,
  ShieldCheck,
} from "lucide-react";

export default function SafetyLesson() {
  const { candidate, ready } = useCandidate();
  const [, navigate] = useLocation();
  const params = useParams<{ lessonId: string }>();
  const lessonId = params.lessonId;

  const videoRef = useRef<HTMLVideoElement>(null);
  const [watchedLocally, setWatchedLocally] = useState(false);
  const [watchPercent, setWatchPercent] = useState(0);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [quizResult, setQuizResult] = useState<{
    correct: number;
    total: number;
    percent: number;
    passed: boolean;
  } | null>(null);

  useEffect(() => {
    if (ready && !candidate) navigate("/register");
  }, [ready, candidate, navigate]);

  const utils = trpc.useUtils();
  const { data: lessons, isLoading } = trpc.safety.lessons.useQuery(
    { candidateId: candidate?.id ?? 0 },
    { enabled: Boolean(candidate?.id) }
  );
  const lesson = lessons?.find((l) => l.id === lessonId);

  const markWatched = trpc.safety.markWatched.useMutation({
    onSuccess: () => {
      setWatchedLocally(true);
      utils.safety.lessons.invalidate();
      utils.candidate.dashboard.invalidate();
    },
    onError: () => {
      toast.error("We couldn't save your video progress. Please check your connection and keep watching — it will retry automatically.");
    },
  });

  const submitQuiz = trpc.safety.submitQuiz.useMutation({
    onSuccess: (data) => {
      setQuizResult(data);
      utils.safety.lessons.invalidate();
      utils.candidate.dashboard.invalidate();
      if (data.passed) {
        toast.success(`Knowledge check passed — ${data.percent}%.`);
      } else {
        toast.warning(`Score ${data.percent}% — review the video and try again.`);
      }
    },
    onError: (err) => toast.error(err.message || "Could not submit your quiz."),
  });

  const watched = Boolean(lesson?.videoWatched) || watchedLocally;
  const allAnswered = lesson ? lesson.quiz.every((q) => answers[q.id] !== undefined) : false;

  function handleTimeUpdate() {
    const v = videoRef.current;
    if (!v || !v.duration) return;
    const pct = Math.min(100, Math.round((v.currentTime / v.duration) * 100));
    setWatchPercent(pct);
    if (pct >= 90 && !watched) {
      markWatched.mutate({ candidateId: candidate!.id, lessonId });
    }
  }

  function handleEnded() {
    if (!watched) {
      setWatchPercent(100);
      markWatched.mutate({ candidateId: candidate!.id, lessonId });
    }
  }

  function handleSubmitQuiz() {
    if (!allAnswered) {
      toast.warning("Please answer every question before submitting.");
      return;
    }
    submitQuiz.mutate({ candidateId: candidate!.id, lessonId, answers });
  }

  function retakeQuiz() {
    setAnswers({});
    setQuizResult(null);
  }

  if (!candidate) return null;

  if (isLoading) {
    return (
      <PageShell>
        <section className="container py-10">
          <Skeleton className="h-[480px] rounded-xl max-w-4xl mx-auto" />
        </section>
      </PageShell>
    );
  }

  if (!lesson) {
    return (
      <PageShell>
        <section className="container py-20 text-center">
          <h1 className="font-display text-2xl font-semibold">Lesson not found</h1>
          <Link href="/safety">
            <Button className="btn-press mt-6">Back to safety training</Button>
          </Link>
        </section>
      </PageShell>
    );
  }

  if (!lesson.available || !lesson.videoUrl) {
    return (
      <PageShell>
        <section className="container py-20">
          <Card className="mx-auto max-w-md border-border/80">
            <CardContent className="p-10 text-center">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-primary/8 text-primary">
                <ShieldCheck className="h-7 w-7" />
              </div>
              <h1 className="mt-6 font-display text-2xl font-semibold">{lesson.title}</h1>
              <p className="mt-3 text-sm text-muted-foreground leading-relaxed">
                This safety topic is planned but the video lesson isn't available yet. Check back
                soon — no action is needed for your application right now.
              </p>
              <Link href="/safety">
                <Button className="btn-press mt-8 w-full font-semibold">
                  Back to safety training
                </Button>
              </Link>
            </CardContent>
          </Card>
        </section>
      </PageShell>
    );
  }

  return (
    <PageShell>
      <section className="container py-10 sm:py-14">
        <div className="mx-auto max-w-4xl">
          <Link href="/safety">
            <Button variant="ghost" size="sm" className="btn-press gap-1.5 -ml-2 mb-6 text-muted-foreground">
              <ArrowLeft className="h-4 w-4" /> All safety lessons
            </Button>
          </Link>

          <motion.div
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, ease: [0.23, 1, 0.32, 1] }}
          >
            <div className="flex flex-wrap items-center gap-3">
              <span className="font-display text-4xl font-semibold text-[oklch(0.62_0.19_27/0.5)]">
                {String(lesson.order).padStart(2, "0")}
              </span>
              <div>
                <h1 className="font-display text-2xl sm:text-3xl font-semibold text-balance">
                  {lesson.title}
                </h1>
                <p className="mt-1 text-sm text-muted-foreground">{lesson.summary}</p>
              </div>
            </div>

            {/* Video */}
            <Card className="mt-8 border-border/80 overflow-hidden">
              <div className="relative bg-black">
                <video
                  ref={videoRef}
                  src={lesson.videoUrl}
                  controls
                  playsInline
                  className="w-full aspect-video"
                  onTimeUpdate={handleTimeUpdate}
                  onEnded={handleEnded}
                />
              </div>
              <CardContent className="p-4 sm:p-5 flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2 text-sm">
                  {watched ? (
                    <>
                      <CheckCircle2 className="h-4 w-4 text-[oklch(0.5_0.1_155)]" />
                      <span className="font-semibold text-[oklch(0.4_0.09_155)]">Video watched</span>
                      <span className="text-muted-foreground">— the knowledge check is unlocked</span>
                    </>
                  ) : (
                    <>
                      <CirclePlay className="h-4 w-4 text-muted-foreground" />
                      <span className="text-muted-foreground">
                        Watch the video ({watchPercent}%) to unlock the knowledge check
                      </span>
                    </>
                  )}
                </div>
                {!watched && (
                  <div className="h-1.5 w-40 overflow-hidden rounded-full bg-secondary">
                    <div
                      className="h-full bg-[oklch(0.62_0.19_27)] transition-all duration-300"
                      style={{ width: `${watchPercent}%` }}
                    />
                  </div>
                )}
              </CardContent>
            </Card>

            <Separator className="my-10" />

            {/* Knowledge check */}
            <div>
              <div className="flex items-center gap-3">
                <ShieldCheck className="h-6 w-6 text-[oklch(0.5_0.17_27)]" />
                <h2 className="font-display text-2xl font-semibold">Knowledge check</h2>
                {lesson.quizPassed && (
                  <Badge className="bg-[oklch(0.92_0.05_155)] text-[oklch(0.4_0.09_155)] hover:bg-[oklch(0.92_0.05_155)] border-0 gap-1">
                    <CheckCircle2 className="h-3 w-3" /> Passed · best {lesson.bestQuizPercent}%
                  </Badge>
                )}
              </div>
              <p className="mt-2 text-sm text-muted-foreground">
                {lesson.quiz.length} questions · pass mark {lesson.passPercent}%. Every attempt is
                scored and saved to your candidate record.
              </p>

              <div className="relative mt-6">
                {!watched && (
                  <div className="absolute inset-0 z-10 flex flex-col items-center justify-center rounded-xl bg-background/80 backdrop-blur-sm border border-border/70">
                    <Lock className="h-8 w-8 text-muted-foreground" />
                    <p className="mt-3 max-w-xs text-center text-sm text-muted-foreground">
                      Watch the lesson video above to unlock this knowledge check.
                    </p>
                  </div>
                )}
                <div className={`space-y-6 ${!watched ? "pointer-events-none select-none opacity-40" : ""}`}>
                  {lesson.quiz.map((q, qi) => (
                    <Card key={q.id} className="border-border/80">
                      <CardContent className="p-6">
                        <h3 className="font-semibold leading-snug">
                          <span className="text-muted-foreground mr-2">Q{qi + 1}.</span>
                          {q.prompt}
                        </h3>
                        <div className="mt-4 space-y-2.5" role="radiogroup">
                          {q.options.map((option, oi) => {
                            const selected = answers[q.id] === oi;
                            return (
                              <button
                                key={oi}
                                type="button"
                                role="radio"
                                aria-checked={selected}
                                onClick={() => setAnswers((prev) => ({ ...prev, [q.id]: oi }))}
                                className={`btn-press w-full rounded-lg border px-4 py-3 text-left text-sm transition-colors duration-150 flex items-start gap-3 ${
                                  selected
                                    ? "border-primary bg-primary/6 ring-1 ring-primary/40"
                                    : "border-border bg-card hover:border-primary/40 hover:bg-secondary/60"
                                }`}
                              >
                                <span
                                  className={`mt-0.5 flex h-4.5 w-4.5 h-[18px] w-[18px] shrink-0 items-center justify-center rounded-full border-2 transition-colors ${
                                    selected ? "border-primary bg-primary" : "border-muted-foreground/40"
                                  }`}
                                >
                                  {selected && <span className="h-1.5 w-1.5 rounded-full bg-primary-foreground" />}
                                </span>
                                {option}
                              </button>
                            );
                          })}
                        </div>
                      </CardContent>
                    </Card>
                  ))}

                  <AnimatePresence>
                    {quizResult && (
                      <motion.div
                        initial={{ opacity: 0, y: 12 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.3, ease: [0.23, 1, 0.32, 1] }}
                      >
                        <Card
                          className={`border-0 ${
                            quizResult.passed
                              ? "bg-[oklch(0.94_0.04_155)]"
                              : "bg-[oklch(0.95_0.03_85)]"
                          }`}
                        >
                          <CardContent className="p-6 flex flex-wrap items-center justify-between gap-4">
                            <div className="flex items-center gap-4">
                              {quizResult.passed ? (
                                <CheckCircle2 className="h-8 w-8 text-[oklch(0.5_0.1_155)]" />
                              ) : (
                                <RotateCcw className="h-8 w-8 text-[oklch(0.5_0.17_27)]" />
                              )}
                              <div>
                                <div className="font-display text-2xl font-semibold">
                                  {quizResult.percent}%
                                  <span className="text-sm font-normal text-muted-foreground ml-2">
                                    {quizResult.correct} of {quizResult.total} correct
                                  </span>
                                </div>
                                <div className="text-sm text-muted-foreground">
                                  {quizResult.passed
                                    ? "Passed — this lesson is recorded as complete once the video is watched."
                                    : `Below the ${lesson.passPercent}% pass mark — review the video and try again.`}
                                </div>
                              </div>
                            </div>
                            {!quizResult.passed && (
                              <Button variant="outline" onClick={retakeQuiz} className="btn-press gap-2 bg-card">
                                <RotateCcw className="h-4 w-4" /> Try again
                              </Button>
                            )}
                          </CardContent>
                        </Card>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <Button
                      onClick={handleSubmitQuiz}
                      disabled={submitQuiz.isPending || !allAnswered}
                      className="btn-press gap-2 font-semibold"
                    >
                      {submitQuiz.isPending ? (
                        <>
                          <Loader2 className="h-4 w-4 animate-spin" /> Scoring…
                        </>
                      ) : (
                        <>
                          Submit knowledge check <Send className="h-4 w-4" />
                        </>
                      )}
                    </Button>
                    <Link href="/safety">
                      <Button variant="outline" className="btn-press gap-2 bg-card">
                        Back to lessons <ArrowRight className="h-4 w-4" />
                      </Button>
                    </Link>
                  </div>
                  {!allAnswered && watched && (
                    <p className="text-xs text-muted-foreground">
                      Answer all {lesson.quiz.length} questions to submit.
                    </p>
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>
    </PageShell>
  );
}
