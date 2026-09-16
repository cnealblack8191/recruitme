import { useEffect } from "react";
import { Link, useLocation } from "wouter";
import { PageShell } from "@/components/Brand";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { trpc } from "@/lib/trpc";
import { useCandidate } from "@/contexts/CandidateContext";
import { motion } from "framer-motion";
import {
  ClipboardList,
  ShieldCheck,
  CheckCircle2,
  CircleDashed,
  ArrowRight,
  Award,
  Video,
  PartyPopper,
} from "lucide-react";

function StatusBadge({ status }: { status: "completed" | "in-progress" | "pending" }) {
  if (status === "completed")
    return (
      <Badge className="bg-[oklch(0.92_0.05_155)] text-[oklch(0.4_0.09_155)] hover:bg-[oklch(0.92_0.05_155)] border-0 gap-1">
        <CheckCircle2 className="h-3 w-3" /> Completed
      </Badge>
    );
  if (status === "in-progress")
    return (
      <Badge className="bg-[oklch(0.95_0.03_27)] text-[oklch(0.45_0.15_27)] hover:bg-[oklch(0.95_0.03_27)] border-0 gap-1">
        <CircleDashed className="h-3 w-3" /> In progress
      </Badge>
    );
  return (
    <Badge variant="secondary" className="gap-1">
      <CircleDashed className="h-3 w-3" /> Pending
    </Badge>
  );
}

export default function Dashboard() {
  const { candidate, ready } = useCandidate();
  const [, navigate] = useLocation();

  useEffect(() => {
    if (ready && !candidate) navigate("/register");
  }, [ready, candidate, navigate]);

  const { data, isLoading } = trpc.candidate.dashboard.useQuery(
    { candidateId: candidate?.id ?? 0 },
    { enabled: Boolean(candidate?.id), refetchOnWindowFocus: true }
  );

  if (!candidate) return null;

  const aptitudeDone = data?.aptitude.status === "completed";
  const lessonsCompleted = data?.lessonsCompleted ?? 0;
  const lessonsTotal = data?.lessonsTotal ?? 3;
  const overallSteps = 1 + lessonsTotal;
  const doneSteps = (aptitudeDone ? 1 : 0) + lessonsCompleted;
  const overallPercent = Math.round((doneSteps / overallSteps) * 100);
  const allDone = aptitudeDone && data?.safetyComplete;

  return (
    <PageShell>
      <section className="border-b border-border/70 bg-secondary/40">
        <div className="container py-10 sm:py-14">
          <motion.div
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, ease: [0.23, 1, 0.32, 1] }}
          >
            <p className="text-xs uppercase tracking-[0.24em] text-[oklch(0.5_0.17_27)] font-semibold">
              Candidate dashboard
            </p>
            <h1 className="mt-2 font-display text-3xl sm:text-4xl font-semibold">
              Welcome, {candidate.fullName.split(" ")[0]}
            </h1>
            <p className="mt-2 text-muted-foreground">
              Track your aptitude assessment and safety training below. Everything is saved to your
              candidate record automatically.
            </p>
            <div className="mt-6 max-w-xl">
              <div className="flex items-center justify-between text-sm mb-2">
                <span className="font-semibold">Overall completion</span>
                <span className="text-muted-foreground">
                  {doneSteps} of {overallSteps} requirements · {overallPercent}%
                </span>
              </div>
              <Progress value={overallPercent} className="h-2.5" />
            </div>
          </motion.div>
        </div>
      </section>

      <section className="container py-10 sm:py-14">
        {allDone && (
          <motion.div
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
          >
            <Card className="mb-8 border-[oklch(0.62_0.19_27/0.5)] bg-[oklch(0.96_0.02_27)]">
              <CardContent className="p-6 flex items-start gap-4">
                <PartyPopper className="h-6 w-6 shrink-0 text-[oklch(0.5_0.17_27)]" />
                <div>
                  <h2 className="font-display text-xl font-semibold">
                    All requirements complete — well done!
                  </h2>
                  <p className="mt-1 text-sm text-muted-foreground leading-relaxed">
                    You have finished the aptitude assessment and all safety training. The ECI hiring
                    team will review your complete record and be in touch about next steps.
                  </p>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {isLoading ? (
          <div className="grid gap-6 lg:grid-cols-2">
            <Skeleton className="h-64 rounded-xl" />
            <Skeleton className="h-64 rounded-xl" />
          </div>
        ) : (
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Aptitude card */}
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45, delay: 0.05, ease: [0.23, 1, 0.32, 1] }}
            >
              <Card className="card-lift h-full border-border/80">
                <CardContent className="p-6 sm:p-8 flex flex-col h-full">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/8 text-primary">
                      <ClipboardList className="h-6 w-6" />
                    </div>
                    <StatusBadge
                      status={
                        aptitudeDone
                          ? "completed"
                          : data?.aptitude.status === "in-progress"
                            ? "in-progress"
                            : "pending"
                      }
                    />
                  </div>
                  <h2 className="mt-5 font-display text-2xl font-semibold">Aptitude Assessment</h2>
                  <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                    Taken on ECI's secure assessment form (opens in a new tab). Confirm completion
                    here and the hiring team verifies your score from the form.
                  </p>
                  {aptitudeDone && data?.aptitude.status === "completed" ? (
                    <div className="mt-5 rounded-lg border border-border/80 bg-secondary/50 p-4 flex items-center gap-4">
                      <Award className="h-8 w-8 text-[oklch(0.5_0.17_27)]" />
                      <div>
                        {data.aptitude.scoreTotal > 0 && data.aptitude.scorePercent > 0 ? (
                          <>
                            <div className="font-display text-2xl font-semibold">
                              {data.aptitude.scorePercent}%
                            </div>
                            <div className="text-sm text-muted-foreground">
                              {data.aptitude.passed
                                ? "Meets the ECI benchmark (70%)"
                                : "Below the ECI benchmark (70%)"}
                              {" · "}
                              {new Date(data.aptitude.completedAt).toLocaleDateString()}
                            </div>
                          </>
                        ) : (
                          <>
                            <div className="font-display text-2xl font-semibold">Submitted</div>
                            <div className="text-sm text-muted-foreground">
                              Completed on the assessment form · score verified by the ECI team ·{" "}
                              {new Date(data.aptitude.completedAt).toLocaleDateString()}
                            </div>
                          </>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="mt-auto pt-6">
                      <Link href="/aptitude">
                        <Button className="btn-press gap-2 font-semibold">
                          {data?.aptitude.status === "in-progress"
                            ? "Continue the assessment"
                            : "Take the assessment"}{" "}
                          <ArrowRight className="h-4 w-4" />
                        </Button>
                      </Link>
                    </div>
                  )}
                  {aptitudeDone && (
                    <div className="mt-auto pt-6">
                      <Link href="/aptitude">
                        <Button variant="outline" className="btn-press gap-2 bg-card">
                          Retake the assessment <ArrowRight className="h-4 w-4" />
                        </Button>
                      </Link>
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>

            {/* Safety card */}
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45, delay: 0.12, ease: [0.23, 1, 0.32, 1] }}
            >
              <Card className="card-lift h-full border-border/80">
                <CardContent className="p-6 sm:p-8 flex flex-col h-full">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/8 text-primary">
                      <ShieldCheck className="h-6 w-6" />
                    </div>
                    <StatusBadge
                      status={
                        data?.safetyComplete
                          ? "completed"
                          : lessonsCompleted > 0 || data?.lessons.some((l) => l.videoWatched)
                            ? "in-progress"
                            : "pending"
                      }
                    />
                  </div>
                  <h2 className="mt-5 font-display text-2xl font-semibold">Safety Training</h2>
                  <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                    Watch each lesson video, then pass its knowledge check. More ECI safety topics
                    are added over time.
                  </p>
                  <div className="mt-5 space-y-3">
                    {data?.lessons.filter((l) => l.available).map((lesson) => (
                      <div
                        key={lesson.id}
                        className="flex items-center gap-3 rounded-lg border border-border/70 bg-secondary/40 px-4 py-3"
                      >
                        {lesson.completed ? (
                          <CheckCircle2 className="h-5 w-5 shrink-0 text-[oklch(0.5_0.1_155)]" />
                        ) : lesson.videoWatched ? (
                          <CircleDashed className="h-5 w-5 shrink-0 text-[oklch(0.5_0.17_27)]" />
                        ) : (
                          <Video className="h-5 w-5 shrink-0 text-muted-foreground" />
                        )}
                        <div className="min-w-0 flex-1">
                          <div className="truncate text-sm font-semibold">{lesson.title}</div>
                          <div className="text-xs text-muted-foreground">
                            {lesson.completed
                              ? `Completed · best score ${lesson.bestQuizPercent ?? 0}%`
                              : lesson.videoWatched
                                ? "Video watched · quiz pending"
                                : "Video pending"}
                          </div>
                        </div>
                      </div>
                    ))}
                    {(data?.lessons.filter((l) => !l.available).length ?? 0) > 0 && (
                      <div className="rounded-lg border border-dashed border-border px-4 py-3 text-xs text-muted-foreground">
                        + {data?.lessons.filter((l) => !l.available).length} more topic
                        {data?.lessons.filter((l) => !l.available).length === 1 ? "" : "s"} coming
                        soon — no action needed yet.
                      </div>
                    )}
                  </div>
                  <div className="mt-auto pt-6">
                    <Link href="/safety">
                      <Button
                        variant={lessonsCompleted > 0 ? "outline" : "default"}
                        className={`btn-press gap-2 font-semibold ${lessonsCompleted > 0 ? "bg-card" : ""}`}
                      >
                        {lessonsCompleted > 0 ? "Continue training" : "Start safety training"}
                        <ArrowRight className="h-4 w-4" />
                      </Button>
                    </Link>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </div>
        )}
      </section>
    </PageShell>
  );
}
