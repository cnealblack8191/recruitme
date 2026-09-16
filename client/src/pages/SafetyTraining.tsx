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
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  CircleDashed,
  Clock,
  PlayCircle,
  ShieldCheck,
} from "lucide-react";

export default function SafetyTraining() {
  const { candidate, ready } = useCandidate();
  const [, navigate] = useLocation();

  useEffect(() => {
    if (ready && !candidate) navigate("/register");
  }, [ready, candidate, navigate]);

  const { data: lessons, isLoading } = trpc.safety.lessons.useQuery(
    { candidateId: candidate?.id ?? 0 },
    { enabled: Boolean(candidate?.id), refetchOnWindowFocus: true }
  );

  if (!candidate) return null;

  const available = lessons?.filter((l) => l.available) ?? [];
  const comingSoon = lessons?.filter((l) => !l.available) ?? [];
  const completed = available.filter((l) => l.completed).length;
  const total = available.length || 1;

  return (
    <PageShell>
      <section className="border-b border-border/70 bg-secondary/40">
        <div className="container py-10 sm:py-14">
          <motion.div
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, ease: [0.23, 1, 0.32, 1] }}
          >
            <Link href="/dashboard">
              <Button variant="ghost" size="sm" className="btn-press gap-1.5 -ml-2 mb-4 text-muted-foreground">
                <ArrowLeft className="h-4 w-4" /> Back to dashboard
              </Button>
            </Link>
            <div className="flex items-center gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/8 text-primary">
                <ShieldCheck className="h-6 w-6" />
              </div>
              <div>
                <h1 className="font-display text-3xl sm:text-4xl font-semibold">Safety Training</h1>
                <p className="mt-1 text-muted-foreground">
                  Watch each lesson video, then pass its knowledge check. {completed} of {total}{" "}
                  available lesson{total === 1 ? "" : "s"} complete.
                </p>
              </div>
            </div>
            <div className="mt-6 max-w-xl">
              <Progress value={(completed / total) * 100} className="h-2.5" />
            </div>
          </motion.div>
        </div>
      </section>

      <section className="container py-10 sm:py-14">
        {isLoading ? (
          <div className="space-y-5">
            <Skeleton className="h-40 rounded-xl" />
            <Skeleton className="h-40 rounded-xl" />
            <Skeleton className="h-40 rounded-xl" />
          </div>
        ) : (
          <div className="space-y-5 max-w-4xl">
            {available.map((lesson, i) => (
              <motion.div
                key={lesson.id}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: i * 0.07, ease: [0.23, 1, 0.32, 1] }}
              >
                <Card className="card-lift border-border/80">
                  <CardContent className="p-6 sm:p-7">
                    <div className="flex flex-col sm:flex-row sm:items-center gap-5">
                      <div className="flex items-center gap-4 sm:w-14 shrink-0">
                        <span className="font-display text-4xl font-semibold text-[oklch(0.62_0.19_27/0.5)]">
                          {String(lesson.order).padStart(2, "0")}
                        </span>
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <h2 className="font-display text-xl font-semibold">{lesson.title}</h2>
                          {lesson.completed ? (
                            <Badge className="bg-[oklch(0.92_0.05_155)] text-[oklch(0.4_0.09_155)] hover:bg-[oklch(0.92_0.05_155)] border-0 gap-1">
                              <CheckCircle2 className="h-3 w-3" /> Completed
                            </Badge>
                          ) : lesson.videoWatched ? (
                            <Badge className="bg-[oklch(0.95_0.03_27)] text-[oklch(0.45_0.15_27)] hover:bg-[oklch(0.95_0.03_27)] border-0 gap-1">
                              <CircleDashed className="h-3 w-3" /> Quiz pending
                            </Badge>
                          ) : (
                            <Badge variant="secondary" className="gap-1">
                              <PlayCircle className="h-3 w-3" /> Not started
                            </Badge>
                          )}
                        </div>
                        <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                          {lesson.summary}
                        </p>
                        <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-xs text-muted-foreground">
                          <span>Video lesson</span>
                          <span>Knowledge check: {lesson.quiz.length} questions</span>
                          <span>Pass mark: {lesson.passPercent}%</span>
                          {lesson.bestQuizPercent !== null && (
                            <span className="font-semibold text-foreground">
                              Your best: {lesson.bestQuizPercent}%
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="shrink-0">
                        <Link href={`/safety/${lesson.id}`}>
                          <Button
                            variant={lesson.completed ? "outline" : "default"}
                            className={`btn-press gap-2 font-semibold ${lesson.completed ? "bg-card" : ""}`}
                          >
                            {lesson.completed
                              ? "Review lesson"
                              : lesson.videoWatched
                                ? "Take the quiz"
                                : "Watch & learn"}
                            <ArrowRight className="h-4 w-4" />
                          </Button>
                        </Link>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}

            {comingSoon.length > 0 && (
              <div className="pt-8">
                <div className="flex items-center gap-3 mb-5">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                    Coming soon — more ECI safety topics
                  </h2>
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  {comingSoon.map((lesson, i) => (
                    <motion.div
                      key={lesson.id}
                      initial={{ opacity: 0, y: 12 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{
                        duration: 0.35,
                        delay: 0.2 + i * 0.05,
                        ease: [0.23, 1, 0.32, 1],
                      }}
                    >
                      <Card className="border-dashed border-border bg-secondary/30">
                        <CardContent className="p-5">
                          <div className="flex items-start justify-between gap-3">
                            <h3 className="font-display text-base font-semibold text-muted-foreground">
                              {lesson.title}
                            </h3>
                            <Badge variant="secondary" className="shrink-0 gap-1">
                              <Clock className="h-3 w-3" /> Coming soon
                            </Badge>
                          </div>
                          <p className="mt-2 text-sm text-muted-foreground/80 leading-relaxed">
                            {lesson.summary}
                          </p>
                        </CardContent>
                      </Card>
                    </motion.div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </section>
    </PageShell>
  );
}
