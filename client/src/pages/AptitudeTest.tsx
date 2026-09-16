import { useEffect, useState } from "react";
import { useLocation } from "wouter";
import { PageShell } from "@/components/Brand";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { trpc } from "@/lib/trpc";
import { useCandidate } from "@/contexts/CandidateContext";
import { APTITUDE_FORM_URL } from "@shared/assessment";
import { toast } from "sonner";
import { motion } from "framer-motion";
import {
  ArrowRight,
  CheckCircle2,
  ClipboardList,
  ExternalLink,
  Loader2,
} from "lucide-react";

export default function AptitudeTest() {
  const { candidate, ready } = useCandidate();
  const [, navigate] = useLocation();
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [confirmed, setConfirmed] = useState(false);

  useEffect(() => {
    if (ready && !candidate) navigate("/register");
  }, [ready, candidate, navigate]);

  const utils = trpc.useUtils();
  const latestQuery = trpc.aptitude.latest.useQuery(
    { candidateId: candidate?.id ?? 0 },
    { enabled: Boolean(candidate) }
  );
  const startMutation = trpc.aptitude.start.useMutation({
    onSuccess: () => utils.candidate.dashboard.invalidate(),
  });
  const confirmMutation = trpc.aptitude.confirmCompleted.useMutation({
    onSuccess: () => {
      setConfirmed(true);
      utils.candidate.dashboard.invalidate();
      utils.aptitude.latest.invalidate();
      toast.success("Recorded — the ECI team will verify your score from the assessment form.");
    },
    onError: (err) => toast.error(err.message || "Could not record your completion."),
  });

  if (!candidate) return null;

  const alreadyCompleted = Boolean(latestQuery.data) || confirmed;

  function openAssessment() {
    if (candidate) startMutation.mutate({ candidateId: candidate.id });
    window.open(APTITUDE_FORM_URL, "_blank", "noopener,noreferrer");
  }

  return (
    <PageShell>
      <section className="container py-10 sm:py-16">
        <div className="mx-auto max-w-3xl">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, ease: [0.23, 1, 0.32, 1] }}
          >
            <Card className="border-border/80 shadow-lg shadow-primary/5">
              <CardContent className="p-8 sm:p-10">
                <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-primary/8 text-primary">
                  <ClipboardList className="h-7 w-7" />
                </div>
                <h1 className="mt-6 font-display text-3xl sm:text-4xl font-semibold text-balance">
                  ECI Aptitude Assessment
                </h1>
                <p className="mt-4 text-muted-foreground leading-relaxed">
                  The aptitude assessment is hosted on ECI's secure assessment form. It opens in a
                  new tab — complete it there, then come back and confirm so we can mark this step
                  on your candidate record.
                </p>

                <ul className="mt-8 space-y-2.5 text-sm text-muted-foreground">
                  <li className="flex gap-3">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[oklch(0.62_0.19_27)]" />
                    The assessment opens in a new tab — this page will stay open.
                  </li>
                  <li className="flex gap-3">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[oklch(0.62_0.19_27)]" />
                    Answer every question on the form; there is no time limit.
                  </li>
                  <li className="flex gap-3">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[oklch(0.62_0.19_27)]" />
                    When you're done, return here and confirm — the ECI team verifies your score
                    from the form and links it to your record.
                  </li>
                </ul>

                {alreadyCompleted ? (
                  <div className="mt-10 rounded-xl border border-[oklch(0.85_0.06_155)] bg-[oklch(0.95_0.04_155)] p-6">
                    <div className="flex items-start gap-4">
                      <CheckCircle2 className="h-6 w-6 shrink-0 text-[oklch(0.5_0.1_155)]" />
                      <div>
                        <div className="font-semibold">Assessment recorded</div>
                        <p className="mt-1 text-sm text-muted-foreground leading-relaxed">
                          Your aptitude assessment is marked complete on your candidate record. The
                          ECI hiring team reviews your verified score from the assessment form.
                        </p>
                      </div>
                    </div>
                    <div className="mt-6 flex flex-wrap gap-3">
                      <Button
                        onClick={() => navigate("/dashboard")}
                        className="btn-press gap-2 font-semibold"
                      >
                        Back to dashboard <ArrowRight className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="outline"
                        onClick={openAssessment}
                        className="btn-press gap-2 bg-card"
                      >
                        <ExternalLink className="h-4 w-4" /> Open the assessment again
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="mt-10 flex flex-wrap gap-3">
                    <Button
                      size="lg"
                      onClick={openAssessment}
                      className="btn-press gap-2 font-semibold"
                    >
                      <ExternalLink className="h-4 w-4" /> Take the aptitude assessment
                    </Button>
                    <Button
                      size="lg"
                      variant="outline"
                      onClick={() => setConfirmOpen(true)}
                      disabled={confirmMutation.isPending}
                      className="btn-press gap-2 bg-card"
                    >
                      {confirmMutation.isPending ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <CheckCircle2 className="h-4 w-4" />
                      )}
                      I've completed the assessment
                    </Button>
                    <Button
                      size="lg"
                      variant="ghost"
                      onClick={() => navigate("/dashboard")}
                      className="btn-press"
                    >
                      Back to dashboard
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </section>

      <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Confirm assessment completion</AlertDialogTitle>
            <AlertDialogDescription>
              Please only confirm after you have submitted the aptitude assessment form. The ECI
              hiring team verifies every completion against the form responses — unverified
              confirmations are removed from candidate records.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Not yet</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                setConfirmOpen(false);
                confirmMutation.mutate({ candidateId: candidate.id });
              }}
            >
              Yes, I submitted it
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </PageShell>
  );
}
