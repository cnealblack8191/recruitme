import { BRAND } from "@shared/assessment";
import { Link } from "wouter";
import { useCandidate } from "@/contexts/CandidateContext";
import { Button } from "@/components/ui/button";
import { LogOut, LayoutDashboard } from "lucide-react";

export function BrandMark({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const dims = size === "lg" ? "h-16 w-16" : size === "sm" ? "h-9 w-9" : "h-11 w-11";
  return (
    <img
      src={BRAND.logoUrl}
      alt="ECI logo"
      className={`${dims} rounded-full object-cover shadow-sm`}
    />
  );
}

export function SiteHeader() {
  const { candidate, clearCandidate } = useCandidate();
  return (
    <header className="sticky top-0 z-40 border-b border-border/70 bg-background/85 backdrop-blur supports-[backdrop-filter]:bg-background/70">
      <div className="container flex h-16 items-center justify-between gap-4">
        <Link href="/" className="flex items-center gap-3 group">
          <BrandMark size="sm" />
          <div className="leading-tight">
            <div className="font-display font-semibold text-lg tracking-tight text-foreground group-hover:text-primary transition-colors">
              {BRAND.companyName}
            </div>
            <div className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
              Candidate Portal
            </div>
          </div>
        </Link>
        <nav className="flex items-center gap-2">
          {candidate ? (
            <>
              <span className="hidden sm:block text-sm text-muted-foreground">
                Signed in as <span className="font-semibold text-foreground">{candidate.fullName}</span>
              </span>
              <Link href="/dashboard">
                <Button variant="ghost" size="sm" className="btn-press gap-1.5">
                  <LayoutDashboard className="h-4 w-4" /> My Progress
                </Button>
              </Link>
              <Button
                variant="outline"
                size="sm"
                className="btn-press gap-1.5 bg-card"
                onClick={clearCandidate}
              >
                <LogOut className="h-4 w-4" /> Switch candidate
              </Button>
            </>
          ) : (
            <Link href="/register">
              <Button size="sm" className="btn-press">Begin Registration</Button>
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
}

export function SiteFooter() {
  return (
    <footer className="mt-auto border-t border-border/70 bg-secondary/40">
      <div className="container py-8 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <BrandMark size="sm" />
          <div className="text-sm text-muted-foreground">
            <span className="font-display font-semibold text-foreground">{BRAND.companyName}</span>
            {" — "}
            {BRAND.tagline}
          </div>
        </div>
        <p className="text-xs text-muted-foreground">
          Candidate assessments and safety training records are stored securely and reviewed by the ECI hiring team.
        </p>
      </div>
    </footer>
  );
}

export function PageShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground">
      <SiteHeader />
      <main className="flex-1">{children}</main>
      <SiteFooter />
    </div>
  );
}
