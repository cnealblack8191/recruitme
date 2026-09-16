import { useState } from "react";
import { PageShell } from "@/components/Brand";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Separator } from "@/components/ui/separator";
import { trpc } from "@/lib/trpc";
import { useAuth } from "@/_core/hooks/useAuth";
import { startLogin } from "@/const";
import { toast } from "sonner";
import { motion } from "framer-motion";
import {
  CheckCircle2,
  ChevronRight,
  ClipboardList,
  Clock,
  Eye,
  Lock,
  Loader2,
  Search,
  ShieldCheck,
  Users,
  XCircle,
} from "lucide-react";

function PassBadge({ passed }: { passed: boolean }) {
  return passed ? (
    <Badge className="bg-[oklch(0.92_0.05_155)] text-[oklch(0.4_0.09_155)] hover:bg-[oklch(0.92_0.05_155)] border-0 gap-1">
      <CheckCircle2 className="h-3 w-3" /> Passed
    </Badge>
  ) : (
    <Badge className="bg-[oklch(0.95_0.05_27)] text-[oklch(0.45_0.15_27)] hover:bg-[oklch(0.95_0.05_27)] border-0 gap-1">
      <XCircle className="h-3 w-3" /> Below mark
    </Badge>
  );
}

export default function AdminResults() {
  const { user, loading, isAuthenticated } = useAuth();
  const [search, setSearch] = useState("");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [scoreInput, setScoreInput] = useState("");

  const isAdmin = isAuthenticated && user?.role === "admin";

  const utils = trpc.useUtils();
  const { data: candidates, isLoading } = trpc.admin.candidates.useQuery(undefined, {
    enabled: isAdmin,
  });
  const { data: detail, isLoading: detailLoading } = trpc.admin.candidateDetail.useQuery(
    { candidateId: selectedId ?? 0 },
    { enabled: isAdmin && selectedId !== null }
  );
  const recordScore = trpc.aptitude.recordResult.useMutation({
    onSuccess: (data) => {
      toast.success(`Recorded verified aptitude score: ${data.scorePercent}%`);
      setScoreInput("");
      utils.admin.candidates.invalidate();
      utils.admin.candidateDetail.invalidate();
    },
    onError: (err) => toast.error(err.message || "Could not record the score."),
  });

  const filtered = (candidates ?? []).filter((c) =>
    c.fullName.toLowerCase().includes(search.trim().toLowerCase())
  );

  if (loading) {
    return (
      <PageShell>
        <section className="container py-20 flex justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </section>
      </PageShell>
    );
  }

  if (!isAdmin) {
    return (
      <PageShell>
        <section className="container py-20">
          <Card className="mx-auto max-w-md border-border/80">
            <CardContent className="p-10 text-center">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-primary/8 text-primary">
                <Lock className="h-7 w-7" />
              </div>
              <h1 className="mt-6 font-display text-2xl font-semibold">ECI staff access only</h1>
              <p className="mt-3 text-sm text-muted-foreground leading-relaxed">
                This results view is reserved for the ECI hiring team. Sign in with an authorized
                staff account to review candidate records.
              </p>
              {!isAuthenticated && (
                <Button onClick={() => startLogin()} className="btn-press mt-8 w-full font-semibold">
                  Sign in as ECI staff
                </Button>
              )}
              {isAuthenticated && (
                <p className="mt-6 text-xs text-muted-foreground">
                  Signed in as {user?.name ?? user?.email ?? "unknown"} — this account does not have
                  staff permissions.
                </p>
              )}
            </CardContent>
          </Card>
        </section>
      </PageShell>
    );
  }

  return (
    <PageShell>
      <section className="border-b border-border/70 bg-secondary/40">
        <div className="container py-10">
          <motion.div
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, ease: [0.23, 1, 0.32, 1] }}
          >
            <div className="flex items-center gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/8 text-primary">
                <Users className="h-6 w-6" />
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.24em] text-[oklch(0.5_0.17_27)] font-semibold">
                  Internal · ECI hiring team
                </p>
                <h1 className="font-display text-3xl font-semibold">Candidate Results</h1>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      <section className="container py-8">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <div className="relative w-full max-w-sm">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search candidates by name…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 bg-card"
            />
          </div>
          <p className="text-sm text-muted-foreground">
            {filtered.length} candidate{filtered.length === 1 ? "" : "s"}
          </p>
        </div>

        {isLoading ? (
          <Skeleton className="h-96 rounded-xl" />
        ) : filtered.length === 0 ? (
          <Card className="border-border/80">
            <CardContent className="p-14 text-center">
              <Users className="mx-auto h-10 w-10 text-muted-foreground/50" />
              <h2 className="mt-4 font-display text-xl font-semibold">
                {search ? "No candidates match your search" : "No candidates yet"}
              </h2>
              <p className="mt-2 text-sm text-muted-foreground">
                {search
                  ? "Try a different name."
                  : "Candidate records will appear here as people register through the portal."}
              </p>
            </CardContent>
          </Card>
        ) : (
          <Card className="border-border/80 overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="bg-secondary/60">
                  <TableHead className="font-semibold">Candidate</TableHead>
                  <TableHead className="font-semibold">Birthdate</TableHead>
                  <TableHead className="font-semibold">Registered</TableHead>
                  <TableHead className="font-semibold">Aptitude</TableHead>
                  <TableHead className="font-semibold">Safety training</TableHead>
                  <TableHead className="w-10" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((c) => (
                  <TableRow
                    key={c.id}
                    className="cursor-pointer hover:bg-secondary/40"
                    onClick={() => setSelectedId(c.id)}
                  >
                    <TableCell className="font-semibold">{c.fullName}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {new Date(c.birthdate + "T00:00:00").toLocaleDateString()}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {new Date(c.createdAt).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      {c.aptitude ? (
                        <div className="flex items-center gap-2">
                          <span className="font-semibold">{c.aptitude.scorePercent}%</span>
                          <PassBadge passed={c.aptitude.passed} />
                        </div>
                      ) : (
                        <span className="text-sm text-muted-foreground">Not taken</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">
                          {c.lessonsCompleted}/{c.lessonsTotal} lessons
                        </span>
                        {c.safetyComplete && (
                          <CheckCircle2 className="h-4 w-4 text-[oklch(0.5_0.1_155)]" />
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <ChevronRight className="h-4 w-4 text-muted-foreground" />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Card>
        )}
      </section>

      {/* Candidate detail drawer */}
      <Sheet open={selectedId !== null} onOpenChange={(open) => !open && setSelectedId(null)}>
        <SheetContent className="w-full sm:max-w-xl overflow-y-auto">
          <SheetHeader>
            <SheetTitle className="font-display text-2xl">
              {detail?.candidate.fullName ?? "Candidate record"}
            </SheetTitle>
            <SheetDescription>
              {detail
                ? `Born ${new Date(detail.candidate.birthdate + "T00:00:00").toLocaleDateString()} · Registered ${new Date(detail.candidate.createdAt).toLocaleDateString()}`
                : "Loading record…"}
            </SheetDescription>
          </SheetHeader>

          {detail && (
            <div className="mt-4 space-y-2 rounded-lg border border-border/70 bg-secondary/40 p-4 text-sm">
              <div className="flex items-center justify-between gap-3">
                <span className="text-muted-foreground">Email</span>
                {detail.candidate.email ? (
                  <a
                    href={`mailto:${detail.candidate.email}`}
                    className="font-semibold text-primary hover:underline truncate"
                  >
                    {detail.candidate.email}
                  </a>
                ) : (
                  <span className="text-muted-foreground">Not provided</span>
                )}
              </div>
              <div className="flex items-center justify-between gap-3">
                <span className="text-muted-foreground">Resume</span>
                {detail.candidate.resumeUrl ? (
                  <a
                    href={detail.candidate.resumeUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="font-semibold text-primary hover:underline truncate"
                  >
                    {detail.candidate.resumeFilename ?? "Download resume"}
                  </a>
                ) : (
                  <span className="text-muted-foreground">Not uploaded</span>
                )}
              </div>
            </div>
          )}

          {detailLoading ? (
            <div className="space-y-4 p-4">
              <Skeleton className="h-32 rounded-lg" />
              <Skeleton className="h-48 rounded-lg" />
            </div>
          ) : detail ? (
            <div className="space-y-8 py-6">
              {/* Aptitude history */}
              <div>
                <div className="flex items-center gap-2 mb-4">
                  <ClipboardList className="h-5 w-5 text-primary" />
                  <h3 className="font-display text-lg font-semibold">Aptitude assessment</h3>
                </div>
                {detail.aptitudeHistory.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No attempts recorded yet.</p>
                ) : (
                  <div className="space-y-3">
                    {detail.aptitudeHistory.map((a) => (
                      <div
                        key={a.id}
                        className="rounded-lg border border-border/70 bg-secondary/40 px-4 py-3 flex flex-wrap items-center justify-between gap-3"
                      >
                        <div>
                          {a.scoreTotal > 0 && a.scorePercent > 0 ? (
                            <div className="font-semibold">
                              {a.scorePercent}%
                              <span className="ml-2 text-xs font-normal text-muted-foreground">
                                verified score
                              </span>
                            </div>
                          ) : (
                            <div className="font-semibold">
                              Completed on external form
                              <span className="ml-2 text-xs font-normal text-muted-foreground">
                                score pending verification
                              </span>
                            </div>
                          )}
                          <div className="text-xs text-muted-foreground">
                            {new Date(a.createdAt).toLocaleString()}
                          </div>
                        </div>
                        {a.scoreTotal > 0 && a.scorePercent > 0 && <PassBadge passed={a.passed} />}
                      </div>
                    ))}
                  </div>
                )}

                {/* Record the verified score from the Microsoft Forms response */}
                <div className="mt-4 rounded-lg border border-dashed border-border p-4">
                  <label className="text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                    Record verified score (from the assessment form)
                  </label>
                  <div className="mt-2 flex gap-2">
                    <Input
                      type="number"
                      min={0}
                      max={100}
                      placeholder="e.g. 85"
                      value={scoreInput}
                      onChange={(e) => setScoreInput(e.target.value)}
                      className="bg-card w-32"
                    />
                    <Button
                      size="sm"
                      disabled={
                        recordScore.isPending ||
                        scoreInput.trim() === "" ||
                        Number(scoreInput) < 0 ||
                        Number(scoreInput) > 100
                      }
                      onClick={() =>
                        selectedId &&
                        recordScore.mutate({
                          candidateId: selectedId,
                          scorePercent: Math.round(Number(scoreInput)),
                        })
                      }
                      className="btn-press font-semibold"
                    >
                      {recordScore.isPending ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        "Save score"
                      )}
                    </Button>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Safety training detail */}
              <div>
                <div className="flex items-center gap-2 mb-4">
                  <ShieldCheck className="h-5 w-5 text-primary" />
                  <h3 className="font-display text-lg font-semibold">Safety training</h3>
                </div>
                <div className="space-y-4">
                  {detail.lessons.map((lesson) => (
                    <div key={lesson.lessonId} className="rounded-lg border border-border/70 p-4">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <h4 className="font-semibold text-sm">{lesson.title}</h4>
                        {!lesson.available ? (
                          <Badge variant="secondary" className="gap-1">
                            <Clock className="h-3 w-3" /> Coming soon
                          </Badge>
                        ) : lesson.completed ? (
                          <Badge className="bg-[oklch(0.92_0.05_155)] text-[oklch(0.4_0.09_155)] hover:bg-[oklch(0.92_0.05_155)] border-0 gap-1">
                            <CheckCircle2 className="h-3 w-3" /> Complete
                          </Badge>
                        ) : (
                          <Badge variant="secondary">Incomplete</Badge>
                        )}
                      </div>
                      {lesson.available && (
                        <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-muted-foreground">
                          <span>
                            Video:{" "}
                            {lesson.videoWatched
                              ? `watched ${lesson.watchedAt ? new Date(lesson.watchedAt).toLocaleDateString() : ""}`
                              : "not watched"}
                          </span>
                          <span>
                            Best quiz:{" "}
                            {lesson.bestQuizPercent !== null ? `${lesson.bestQuizPercent}%` : "—"}
                          </span>
                        </div>
                      )}
                      {lesson.attempts.length > 0 && (
                        <div className="mt-3 space-y-1.5">
                          {lesson.attempts.map((a) => (
                            <div
                              key={a.id}
                              className="flex items-center justify-between rounded bg-secondary/50 px-3 py-1.5 text-xs"
                            >
                              <span>
                                {a.scorePercent}% ({a.scoreCorrect}/{a.scoreTotal})
                              </span>
                              <span className="text-muted-foreground">
                                {new Date(a.createdAt).toLocaleString()}
                              </span>
                              <span
                                className={
                                  a.passed
                                    ? "font-semibold text-[oklch(0.4_0.09_155)]"
                                    : "font-semibold text-[oklch(0.45_0.15_27)]"
                                }
                              >
                                {a.passed ? "Pass" : "Fail"}
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Eye className="h-3.5 w-3.5" />
                All scores and completion records are linked to this candidate's registration.
              </div>
            </div>
          ) : null}
        </SheetContent>
      </Sheet>
    </PageShell>
  );
}
