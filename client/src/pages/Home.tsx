import { PageShell, BrandMark } from "@/components/Brand";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { BRAND } from "@shared/assessment";
import { Link } from "wouter";
import { motion } from "framer-motion";
import {
  ClipboardList,
  ShieldCheck,
  HardHat,
  ArrowRight,
  FileCheck2,
  Video,
  UserRoundPlus,
} from "lucide-react";
import { useCandidate } from "@/contexts/CandidateContext";

const steps = [
  {
    icon: UserRoundPlus,
    title: "Register",
    body: "Tell us your full name and birthdate so we can create your candidate record.",
  },
  {
    icon: ClipboardList,
    title: "Aptitude Assessment",
    body: "Complete ECI's aptitude assessment on our secure online form — it opens in a new tab.",
  },
  {
    icon: Video,
    title: "Safety Training",
    body: "Watch three short safety lessons and pass a knowledge check after each one.",
  },
  {
    icon: FileCheck2,
    title: "ECI Review",
    body: "Our hiring team reviews your complete record — registration, scores, and training.",
  },
];

export default function Home() {
  const { candidate } = useCandidate();
  return (
    <PageShell>
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0">
          <img
            src={BRAND.heroUrl}
            alt=""
            className="h-full w-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-[oklch(0.16_0.01_260/0.96)] via-[oklch(0.19_0.012_260/0.88)] to-[oklch(0.22_0.015_260/0.55)]" />
        </div>
        <div className="container relative py-20 sm:py-28 lg:py-32">
          <div className="max-w-2xl">
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, ease: [0.23, 1, 0.32, 1] }}
              className="flex items-center gap-4 mb-8"
            >
              <BrandMark size="lg" />
              <div className="h-12 w-px bg-white/25" />
              <p className="text-sm uppercase tracking-[0.28em] text-[oklch(0.75_0.12_40)] font-semibold">
                Careers at {BRAND.companyName}
              </p>
            </motion.div>
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.55, delay: 0.08, ease: [0.23, 1, 0.32, 1] }}
              className="font-display text-4xl sm:text-5xl lg:text-6xl font-semibold text-white leading-[1.05] text-balance"
            >
              {BRAND.tagline}
            </motion.h1>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.55, delay: 0.16, ease: [0.23, 1, 0.32, 1] }}
              className="mt-6 text-lg text-white/80 leading-relaxed max-w-xl"
            >
              Welcome to the {BRAND.companyName} candidate portal — Electrical Contractor Inc., est.
              1984. Register, complete our aptitude assessment, and finish the required safety
              training — all in one place, at your own pace.
            </motion.p>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.55, delay: 0.24, ease: [0.23, 1, 0.32, 1] }}
              className="mt-10 flex flex-wrap items-center gap-4"
            >
              {candidate ? (
                <Link href="/dashboard">
                  <Button size="lg" className="btn-press gap-2 bg-[oklch(0.62_0.19_27)] text-[oklch(0.16_0.01_260)] hover:bg-[oklch(0.66_0.19_27)] font-semibold">
                    Continue as {candidate.fullName.split(" ")[0]}
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                </Link>
              ) : (
                <Link href="/register">
                  <Button size="lg" className="btn-press gap-2 bg-[oklch(0.62_0.19_27)] text-[oklch(0.16_0.01_260)] hover:bg-[oklch(0.66_0.19_27)] font-semibold">
                    Begin Your Application
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                </Link>
              )}
              <Link href="/register?resume=1">
                <Button
                  size="lg"
                  variant="outline"
                  className="btn-press border-white/35 bg-transparent text-white hover:bg-white/10 hover:text-white"
                >
                  Returning candidate
                </Button>
              </Link>
            </motion.div>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="container py-16 sm:py-24">
        <div className="max-w-2xl">
          <p className="text-xs uppercase tracking-[0.24em] text-[oklch(0.5_0.17_27)] font-semibold">
            The hiring process
          </p>
          <h2 className="mt-3 font-display text-3xl sm:text-4xl font-semibold text-foreground text-balance">
            Four steps between you and the job site
          </h2>
        </div>
        <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {steps.map((step, i) => (
            <motion.div
              key={step.title}
              initial={{ opacity: 0, y: 18 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.45, delay: i * 0.07, ease: [0.23, 1, 0.32, 1] }}
            >
              <Card className="card-lift h-full border-border/80 shadow-sm">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-primary/8 text-primary">
                      <step.icon className="h-5 w-5" />
                    </div>
                    <span className="font-display text-3xl font-semibold text-[oklch(0.62_0.19_27/0.45)]">
                      {String(i + 1).padStart(2, "0")}
                    </span>
                  </div>
                  <h3 className="mt-5 font-display text-xl font-semibold">{step.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{step.body}</p>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Assurance band */}
      <section className="border-t border-border/70 bg-secondary/50">
        <div className="container py-14 grid gap-8 sm:grid-cols-3">
          <div className="flex gap-4">
            <ShieldCheck className="h-6 w-6 shrink-0 text-[oklch(0.5_0.17_27)]" />
            <div>
              <h3 className="font-display font-semibold">Your record, saved</h3>
              <p className="mt-1 text-sm text-muted-foreground leading-relaxed">
                Registration details, assessment scores, and training completion are recorded to your
                candidate file automatically.
              </p>
            </div>
          </div>
          <div className="flex gap-4">
            <HardHat className="h-6 w-6 shrink-0 text-[oklch(0.5_0.17_27)]" />
            <div>
              <h3 className="font-display font-semibold">Safety first, always</h3>
              <p className="mt-1 text-sm text-muted-foreground leading-relaxed">
                Every ECI hire completes the same core safety curriculum before stepping onto a site.
              </p>
            </div>
          </div>
          <div className="flex gap-4">
            <ClipboardList className="h-6 w-6 shrink-0 text-[oklch(0.5_0.17_27)]" />
            <div>
              <h3 className="font-display font-semibold">Fair, scored assessments</h3>
              <p className="mt-1 text-sm text-muted-foreground leading-relaxed">
                The aptitude assessment is scored automatically and reviewed alongside your safety
                training record.
              </p>
            </div>
          </div>
        </div>
      </section>
    </PageShell>
  );
}
