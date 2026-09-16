import { useEffect, useRef, useState } from "react";
import { useLocation, useSearch } from "wouter";
import { PageShell, BrandMark } from "@/components/Brand";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { trpc } from "@/lib/trpc";
import { useCandidate } from "@/contexts/CandidateContext";
import { toast } from "sonner";
import { motion } from "framer-motion";
import { ArrowRight, FileUp, Loader2, UserRoundPlus, RotateCcw, X } from "lucide-react";

function isValidDateString(v: string) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(v)) return false;
  const d = new Date(v + "T00:00:00Z");
  return !Number.isNaN(d.getTime());
}

export default function Register() {
  const [, navigate] = useLocation();
  const search = useSearch();
  const { setCandidate } = useCandidate();
  const [tab, setTab] = useState(search.includes("resume=1") ? "resume" : "new");
  const [fullName, setFullName] = useState("");
  const [birthdate, setBirthdate] = useState("");
  const [email, setEmail] = useState("");
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [errors, setErrors] = useState<{ fullName?: string; birthdate?: string; email?: string; resume?: string }>({});

  const uploadResumeMutation = trpc.candidate.uploadResume.useMutation();

  const registerMutation = trpc.candidate.register.useMutation({
    onSuccess: async (data) => {
      setCandidate({
        id: data.candidate.id,
        fullName: data.candidate.fullName,
        birthdate: data.candidate.birthdate,
      });
      if (resumeFile) {
        try {
          const dataBase64 = await fileToBase64(resumeFile);
          await uploadResumeMutation.mutateAsync({
            candidateId: data.candidate.id,
            filename: resumeFile.name,
            contentType: resumeFile.type,
            dataBase64,
          });
          toast.success("Resume uploaded and attached to your record.");
        } catch {
          toast.error("Your record was created, but the resume upload failed — you can re-upload it later from your dashboard.");
        }
      }
      if (data.isReturning) {
        toast.success(`Welcome back, ${data.candidate.fullName.split(" ")[0]}. Your record has been loaded.`);
      } else {
        toast.success("Your candidate record has been created.");
      }
      navigate("/dashboard");
    },
    onError: (err) => {
      toast.error(err.message || "We could not save your registration. Please try again.");
    },
  });

  useEffect(() => {
    setTab(search.includes("resume=1") ? "resume" : "new");
  }, [search]);

  function validate(): boolean {
    const next: typeof errors = {};
    if (fullName.trim().replace(/\s+/g, " ").length < 2) {
      next.fullName = "Please enter your full legal name.";
    } else if (!/^[a-zA-ZÀ-ÿ'’.\- ]+$/.test(fullName.trim())) {
      next.fullName = "Name may only contain letters, spaces, hyphens and apostrophes.";
    }
    if (!birthdate) {
      next.birthdate = "Please enter your birthdate.";
    } else if (!isValidDateString(birthdate)) {
      next.birthdate = "Please enter a valid date.";
    } else {
      const age =
        (Date.now() - new Date(birthdate + "T00:00:00Z").getTime()) / (365.25 * 24 * 3600 * 1000);
      if (age < 16) next.birthdate = "Candidates must be at least 16 years old.";
      if (age > 100) next.birthdate = "Please check the year entered.";
    }
    const trimmedEmail = email.trim();
    if (trimmedEmail && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmedEmail)) {
      next.email = "Please enter a valid email address, or leave it blank.";
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  function fileToBase64(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const result = reader.result as string;
        resolve(result.split(",")[1] ?? "");
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }

  function handleResumePick(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const allowed = [
      "application/pdf",
      "application/msword",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "image/jpeg",
      "image/png",
    ];
    if (!allowed.includes(file.type)) {
      setErrors((p) => ({ ...p, resume: "Resume must be a PDF, Word document, JPG, or PNG." }));
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setErrors((p) => ({ ...p, resume: "Resume must be smaller than 10 MB." }));
      return;
    }
    setErrors((p) => ({ ...p, resume: undefined }));
    setResumeFile(file);
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validate()) return;
    registerMutation.mutate({
      fullName: fullName.trim().replace(/\s+/g, " "),
      birthdate,
      email: email.trim() || undefined,
    });
  }

  const form = (mode: "new" | "resume") => (
    <form onSubmit={handleSubmit} className="space-y-5" noValidate>
      <div className="space-y-2">
        <Label htmlFor={`fullName-${mode}`} className="text-sm font-semibold">
          Full legal name
        </Label>
        <Input
          id={`fullName-${mode}`}
          placeholder="e.g. Jordan A. Martinez"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          autoComplete="name"
          className="h-11 bg-card"
          aria-invalid={Boolean(errors.fullName)}
        />
        {errors.fullName && <p className="text-sm text-destructive">{errors.fullName}</p>}
      </div>
      <div className="space-y-2">
        <Label htmlFor={`birthdate-${mode}`} className="text-sm font-semibold">
          Date of birth
        </Label>
        <Input
          id={`birthdate-${mode}`}
          type="date"
          value={birthdate}
          onChange={(e) => setBirthdate(e.target.value)}
          max={new Date().toISOString().slice(0, 10)}
          className="h-11 bg-card"
          aria-invalid={Boolean(errors.birthdate)}
        />
        {errors.birthdate && <p className="text-sm text-destructive">{errors.birthdate}</p>}
        <p className="text-xs text-muted-foreground">
          {mode === "new"
            ? "Your name and birthdate are recorded with your candidate file and used to resume your application later."
            : "Enter the same name and birthdate you registered with to load your existing record."}
        </p>
      </div>
      {mode === "new" && (
        <>
          <div className="space-y-2">
            <Label htmlFor={`email-${mode}`} className="text-sm font-semibold">
              Email address <span className="font-normal text-muted-foreground">(optional)</span>
            </Label>
            <Input
              id={`email-${mode}`}
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              className="h-11 bg-card"
              aria-invalid={Boolean(errors.email)}
            />
            {errors.email && <p className="text-sm text-destructive">{errors.email}</p>}
            <p className="text-xs text-muted-foreground">
              We'll send a confirmation receipt and updates about your application here.
            </p>
          </div>
          <div className="space-y-2">
            <Label className="text-sm font-semibold">
              Resume <span className="font-normal text-muted-foreground">(optional)</span>
            </Label>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
              className="hidden"
              onChange={handleResumePick}
            />
            {resumeFile ? (
              <div className="flex items-center gap-3 rounded-lg border border-border/80 bg-secondary/40 px-4 py-3">
                <FileUp className="h-5 w-5 shrink-0 text-[oklch(0.5_0.17_27)]" />
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-semibold">{resumeFile.name}</div>
                  <div className="text-xs text-muted-foreground">
                    {(resumeFile.size / 1024).toFixed(0)} KB · attached to your record
                  </div>
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setResumeFile(null);
                    if (fileInputRef.current) fileInputRef.current.value = "";
                  }}
                  className="btn-press shrink-0"
                  aria-label="Remove resume"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            ) : (
              <Button
                type="button"
                variant="outline"
                onClick={() => fileInputRef.current?.click()}
                className="btn-press w-full gap-2 bg-card border-dashed"
              >
                <FileUp className="h-4 w-4" /> Upload resume (PDF, Word, JPG, PNG · max 10 MB)
              </Button>
            )}
            {errors.resume && <p className="text-sm text-destructive">{errors.resume}</p>}
          </div>
        </>
      )}
      <Button
        type="submit"
        size="lg"
        disabled={registerMutation.isPending || uploadResumeMutation.isPending}
        className="btn-press w-full gap-2 font-semibold"
      >
        {registerMutation.isPending || uploadResumeMutation.isPending ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <ArrowRight className="h-4 w-4" />
        )}
        {mode === "new" ? "Create my candidate record" : "Load my record"}
      </Button>
    </form>
  );

  return (
    <PageShell>
      <section className="container py-14 sm:py-20">
        <div className="mx-auto grid max-w-5xl gap-10 lg:grid-cols-[1fr_1.1fr] lg:items-center">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: [0.23, 1, 0.32, 1] }}
          >
            <BrandMark size="lg" />
            <h1 className="mt-6 font-display text-3xl sm:text-4xl font-semibold text-balance">
              Candidate registration
            </h1>
            <p className="mt-4 text-muted-foreground leading-relaxed">
              Everything starts with your candidate record. Once registered, you can take the ECI
              aptitude assessment and complete the required safety training — your progress is saved
              as you go.
            </p>
            <ul className="mt-6 space-y-3 text-sm text-muted-foreground">
              <li className="flex gap-3">
                <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-[oklch(0.62_0.19_27)]" />
                Your name and birthdate identify your record — no account or password needed.
              </li>
              <li className="flex gap-3">
                <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-[oklch(0.62_0.19_27)]" />
                Assessment and training results are saved to your file automatically.
              </li>
              <li className="flex gap-3">
                <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-[oklch(0.62_0.19_27)]" />
                You can leave and return at any time using the same details.
              </li>
            </ul>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1, ease: [0.23, 1, 0.32, 1] }}
          >
            <Card className="border-border/80 shadow-lg shadow-primary/5">
              <CardContent className="p-6 sm:p-8">
                <Tabs value={tab} onValueChange={setTab}>
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="new" className="gap-2">
                      <UserRoundPlus className="h-4 w-4" /> New candidate
                    </TabsTrigger>
                    <TabsTrigger value="resume" className="gap-2">
                      <RotateCcw className="h-4 w-4" /> Returning
                    </TabsTrigger>
                  </TabsList>
                  <TabsContent value="new" className="pt-6">
                    {form("new")}
                  </TabsContent>
                  <TabsContent value="resume" className="pt-6">
                    {form("resume")}
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </section>
    </PageShell>
  );
}
