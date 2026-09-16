import { useState } from "react";
import {
  ArrowUpRight,
  BriefcaseBusiness,
  FileText,
  LayoutDashboard,
  Plus,
  Search,
  Settings2,
  Plug,
  ShieldCheck,
  Users,
  Save,
  Download,
  Play,
  Square,
} from "lucide-react";
import { useAuth } from "@/_core/hooks/useAuth";
import { startLogin } from "@/const";
import { trpc } from "@/lib/trpc";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  initialProfile,
  discoveryProviderIds,
  type JobProfile,
} from "@shared/recruitme";
import { toast } from "sonner";
import "./recruitme.css";
import RecruitMePanels from "./RecruitMePanels";
import RecruitMeCandidates from "./RecruitMeCandidates";
import { type WorkflowStatus } from "./recruitme-model";

const sections = [
  "Overview",
  "Job profiles",
  "Search runs",
  "Candidates",
  "Reports",
  "Sources",
  "Credits",
  "Settings",
] as const;
const icons = [
  LayoutDashboard,
  BriefcaseBusiness,
  Search,
  Users,
  FileText,
  Plug,
  ShieldCheck,
  Settings2,
];

export default function RecruitMe() {
  const { user, loading } = useAuth();
  const [section, setSection] = useState<(typeof sections)[number]>("Overview");
  const [draft, setDraft] = useState<JobProfile | null>(null);

  const allowed = user?.role === "admin";
  const workspace = trpc.recruitme.workspace.useQuery(undefined, {
    enabled: allowed,
    refetchInterval: 20000,
  });
  const status = trpc.recruitme.status.useQuery(undefined, {
    enabled: allowed,
    refetchInterval: 20000,
  });
  const workflow = trpc.recruitme.setCandidateStatus.useMutation({
    onSuccess: () => {
      workspace.refetch();
      toast.success("Candidate status saved");
    },
    onError: e => {
      workspace.refetch();
      toast.error(e.message);
    },
  });
  const save = trpc.recruitme.saveProfile.useMutation({
    onSuccess: saved => {
      setDraft(saved);
      workspace.refetch();
      toast.success("Job profile saved");
    },
    onError: e => toast.error(e.message),
  });
  const launch = trpc.recruitme.launch.useMutation({
    onSuccess: result => {
      toast.success(`Launch accepted: ${result.runId}`);
      workspace.refetch();
      status.refetch();
    },
    onError: e => toast.error(e.message),
  });
  const stop = trpc.recruitme.stop.useMutation({
    onSuccess: result => {
      toast.success(result.message ?? `Stop requested for ${result.runId}`);
      workspace.refetch();
      status.refetch();
    },
    onError: e => toast.error(e.message),
  });

  const profiles = workspace.data?.profiles ?? [];

  function edit(profile: JobProfile) {
    setDraft({ ...profile });
    setSection("Job profiles");
  }

  function newProfile() {
    edit({
      ...initialProfile,
      id: crypto.randomUUID(),
      revision: 0,
      title: "",
      roles: "",
      locations: "",
      fitTerms: "",
      juniorRoles: "",
      maximumHourlyPay: null,
      minimumYears: 0,
      startDate: "",
      relocation: "",
      notes: "",
    });
  }

  function launchDraft() {
    if (!draft) return;
    const saved = profiles.find(p => p.id === draft.id);
    if (!saved || JSON.stringify(saved) !== JSON.stringify(draft)) {
      toast.error("Save your profile and budget before launching.");
      return;
    }
    launch.mutate({ profileId: draft.id });
  }

  function stopRun() {
    if (!status.data?.activeRunId) return;
    stop.mutate({ runId: status.data.activeRunId });
  }

  function download() {
    if (!draft) return;
    const blob = new Blob([JSON.stringify(draft, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "recruitme-job-profile.json";
    a.click();
    URL.revokeObjectURL(url);
  }

  if (loading) return <main className="rm-login">Loading your workspace…</main>;

  if (!allowed) {
    return (
      <main className="rm-login">
        <div className="rm-mark">R</div>
        <h1>RecruitMe</h1>
        <p>Your recruiting research workspace.</p>
        <p>Staff administrator access is required.</p>
        {!user && (
          <Button onClick={() => startLogin()}>Sign in to RecruitMe</Button>
        )}
      </main>
    );
  }

  const isControlReady = Boolean(workspace.data?.connection.ready);

  return (
    <div className="rm-app">
      <aside className="rm-sidebar">
        <a className="rm-logo" href="/recruitme">
          <span className="rm-mark">R</span>RecruitMe
          <span className="rm-beta">POC</span>
        </a>
        <p className="rm-nav-label">RECRUITING WORKSPACE</p>
        <nav aria-label="RecruitMe navigation">
          {sections.map((s, i) => {
            const Icon = icons[i];
            return (
              <button
                key={s}
                aria-current={section === s ? "page" : undefined}
                className={section === s ? "active" : ""}
                onClick={() => setSection(s)}
              >
                <Icon size={18} />
                {s}
              </button>
            );
          })}
        </nav>
        <div className="rm-side-bottom">
          <ShieldCheck size={22} />
          <strong>Evidence before volume</strong>
          <p>Every strong lead needs fit and a credible job-change signal.</p>
          <a href="https://hire.ecinc.us/admin/results">
            Candidate Portal <ArrowUpRight size={14} />
          </a>
        </div>
      </aside>

      <main className="rm-main">
        <header className="rm-top">
          <span>
            Workspace <span className="rm-slash">/</span> {section}
          </span>
          <span className="rm-user">{user?.name || "Administrator"}</span>
        </header>

        <div className="rm-content">
          <div className="rm-heading">
            <div>
              <p className="rm-eyebrow">RESEARCH THAT LEADS SOMEWHERE</p>
              <h1>
                {section === "Overview" ? "Recruiting overview" : section}
              </h1>
              <p className="rm-muted">
                {section === "Overview"
                  ? "Define the role. Find the evidence. Focus on the right people."
                  : "Review evidence, manage your pipeline, and keep research in context."}
              </p>
            </div>
            <Button onClick={newProfile}>
              <Plus size={16} /> New job profile
            </Button>
          </div>

          {workspace.isError && (
            <div role="alert" className="rm-notice">
              Could not load your workspace.{" "}
              <button onClick={() => workspace.refetch()}>Try again</button>
            </div>
          )}
          {workspace.isLoading && <p>Loading saved profiles…</p>}

          {section === "Settings" && (
            <div className="rm-notice">
              <span className="rm-dot" />
              <div>
                <strong>
                  {workspace.data?.connection.label ||
                    "Checking worker connection"}
                </strong>
                <p>
                  {workspace.data?.connection.detail ||
                    "Live status is not yet available."}
                </p>
                {status.data && (
                  <p>
                    Worker status: {status.data.status} ·{" "}
                    {status.data.online ? "online" : "offline"}
                    {status.data.running && status.data.activeRunId
                      ? ` · active run ${status.data.activeRunId}`
                      : ""}
                  </p>
                )}
              </div>
            </div>
          )}

          {section === "Overview" && (
            <>
              <div className="rm-stats">
                {[
                  [
                    "Candidates",
                    String(workspace.data?.candidates.length ?? 0),
                    "Synchronized research records",
                  ],
                  [
                    "Needs evidence review",
                    String(
                      workspace.data?.candidates.filter(c => !c.verified)
                        .length ?? 0
                    ),
                    "Unverified research records",
                  ],
                  [
                    "Search runs",
                    String(workspace.data?.runs.length ?? 0),
                    "Recorded search history",
                  ],
                  [
                    "Recorded spend",
                    workspace.data?.budgets.pocSpend == null
                      ? "Unavailable"
                      : `$${workspace.data.budgets.pocSpend.toFixed(3)}`,
                    "Conservative ledger including reservations",
                  ],
                ].map(([label, value, sub]) => (
                  <article key={label}>
                    <p>{label}</p>
                    <h2>{value}</h2>
                    <small>{sub}</small>
                  </article>
                ))}
              </div>
              <div className="rm-actions rm-overview-actions">
                <Button onClick={() => setSection("Candidates")}>
                  <Users size={16} />
                  Review candidates
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setSection("Search runs")}
                >
                  <Search size={16} />
                  View search history
                </Button>
              </div>
              <div className="rm-grid">
                <section className="rm-panel">
                  <div className="rm-panel-heading">
                    <h2>Positions to research</h2>
                    <span>{profiles.length} saved</span>
                  </div>
                  {profiles.map(p => (
                    <button
                      key={p.id}
                      className="rm-profile-row"
                      onClick={() => edit(p)}
                    >
                      <span className="rm-icon">
                        <BriefcaseBusiness size={20} />
                      </span>
                      <span>
                        <strong>{p.title}</strong>
                        <small>{p.locations}</small>
                        <small>
                          {p.maximumHourlyPay
                            ? `Up to $${p.maximumHourlyPay}/hour · `
                            : ""}
                          {p.durationMinutes} minute limit · ${p.runCap} cap
                        </small>
                      </span>
                      <ArrowUpRight size={18} />
                    </button>
                  ))}
                </section>
                <section className="rm-panel rm-dark">
                  <span className="rm-eyebrow">QUALITY STANDARD</span>
                  <h2>
                    Experience alone
                    <br />
                    isn't a recruiting signal.
                  </h2>
                  <p>
                    A/B leads need strong role fit and attributable
                    employment-change interest. Signal dates, source URLs and
                    unresolved questions stay visible.
                  </p>
                  <div className="rm-pills">
                    <span>A · Excellent</span>
                    <span>B · Strong</span>
                    <span>C · Provisional</span>
                    <span>D · Investigated</span>
                  </div>
                </section>
              </div>
              <div className="rm-actions">
                <Button onClick={() => setSection("Job profiles")}>
                  <Plus size={16} />
                  Open profiles
                </Button>
                {isControlReady && draft && (
                  <Button
                    onClick={launchDraft}
                    disabled={launch.isPending || !draft}
                  >
                    <Play size={16} />
                    {launch.isPending
                      ? "Queuing launch…"
                      : "Launch selected profile"}
                  </Button>
                )}
                {status.data?.running && status.data.activeRunId && (
                  <Button
                    variant="outline"
                    onClick={stopRun}
                    disabled={stop.isPending}
                  >
                    <Square size={16} />
                    {stop.isPending ? "Stopping…" : "Stop active run"}
                  </Button>
                )}
              </div>
              <section className="rm-panel">
                <h2>A simple, controlled workflow</h2>
                <div className="rm-workflow">
                  {[
                    "Define a reusable job profile",
                    "Run governed research",
                    "Review signals and evidence",
                    "Export the strongest prospects",
                  ].map((s, i) => (
                    <div key={s}>
                      <b>{`0${i + 1}`}</b>
                      <p>{s}</p>
                    </div>
                  ))}
                </div>
              </section>
            </>
          )}

          {section === "Job profiles" && (
            <div className="rm-editor">
              <section className="rm-panel">
                {profiles.map(p => (
                  <button
                    className="rm-profile-row"
                    key={p.id}
                    onClick={() => edit(p)}
                  >
                    {p.title}
                    <ArrowUpRight size={16} />
                  </button>
                ))}
              </section>
              <section className="rm-panel">
                {!draft ? (
                  <p>Select a profile or create one for any position.</p>
                ) : (
                  <form
                    onSubmit={e => {
                      e.preventDefault();
                      save.mutate(draft);
                    }}
                  >
                    <h2>{draft.title || "New job profile"}</h2>
                    <div className="rm-form-grid">
                      {(
                        [
                          ["title", "Profile title"],
                          ["roles", "Experienced role names (comma-separated)"],
                          ["juniorRoles", "Junior role names (optional)"],
                          ["locations", "Search locations"],
                          ["fitTerms", "Required-fit search terms"],
                          ["startDate", "Desired start"],
                          ["relocation", "Relocation requirements"],
                        ] as const
                      ).map(([key, label]) => (
                        <label key={key}>
                          {label}
                          <Input
                            value={draft[key]}
                            maxLength={key === "title" ? 120 : 400}
                            onChange={e =>
                              setDraft({ ...draft, [key]: e.target.value })
                            }
                            required={[
                              "title",
                              "roles",
                              "locations",
                              "fitTerms",
                            ].includes(key)}
                          />
                        </label>
                      ))}
                      <label>
                        Maximum hourly pay (optional)
                        <Input
                          type="number"
                          min="1"
                          max="1000"
                          value={draft.maximumHourlyPay ?? ""}
                          onChange={e =>
                            setDraft({
                              ...draft,
                              maximumHourlyPay: e.target.value
                                ? Number(e.target.value)
                                : null,
                            })
                          }
                        />
                      </label>
                      <label>
                        Annual salary target (optional)
                        <Input
                          type="number"
                          min="1"
                          max="1000000"
                          value={draft.maximumAnnualPay ?? ""}
                          onChange={e =>
                            setDraft({
                              ...draft,
                              maximumAnnualPay: e.target.value
                                ? Number(e.target.value)
                                : null,
                            })
                          }
                        />
                      </label>
                      <label>
                        Experienced minimum years
                        <Input
                          type="number"
                          min="0"
                          max="50"
                          value={draft.minimumYears}
                          onChange={e =>
                            setDraft({
                              ...draft,
                              minimumYears: Number(e.target.value),
                            })
                          }
                        />
                      </label>
                      <label>
                        Search budget ($, 0 = free only, maximum 5)
                        <Input
                          type="number"
                          min="0"
                          step="0.01"
                          max="5"
                          value={draft.runCap}
                          onChange={e =>
                            setDraft({
                              ...draft,
                              runCap: Number(e.target.value),
                            })
                          }
                        />
                      </label>
                      <label>
                        Runtime (minutes, maximum 30)
                        <Input
                          type="number"
                          min="1"
                          max="30"
                          value={draft.durationMinutes}
                          onChange={e =>
                            setDraft({
                              ...draft,
                              durationMinutes: Number(e.target.value),
                            })
                          }
                        />
                      </label>
                      <label className="rm-check">
                        <input
                          type="checkbox"
                          checked={draft.travelPay}
                          onChange={e =>
                            setDraft({ ...draft, travelPay: e.target.checked })
                          }
                        />{" "}
                        Travel pay offered
                      </label>
                      <label className="rm-wide">
                        Qualification notes
                        <textarea
                          maxLength={2000}
                          value={draft.notes}
                          onChange={e =>
                            setDraft({ ...draft, notes: e.target.value })
                          }
                        />
                      </label>
                    </div>
                    <fieldset className="rm-panel rm-space">
                      <legend>Data services and per-search allocations</legend>
                      <p className="rm-muted">
                        Free sources run first. Connected paid sources share the
                        search budget. Each allocation is an additional ceiling,
                        not an extra charge. Discovery includes undated pages;
                        availability still requires dated evidence.
                      </p>
                      {discoveryProviderIds.map(id => {
                        const source = workspace.data?.sources.find(
                          s => s.id === id
                        );
                        const selected = draft.searchProviders.find(
                          p => p.id === id
                        );
                        const free =
                          id === "exa_free" ||
                          id === "pdl_free" ||
                          id === "apollo";
                        return (
                          <div className="rm-allocation" key={id}>
                            <label className="rm-check">
                              <input
                                type="checkbox"
                                checked={!!selected}
                                onChange={e =>
                                  setDraft({
                                    ...draft,
                                    searchProviders: e.target.checked
                                      ? [
                                          ...draft.searchProviders,
                                          { id, budget: free ? 0 : 1 },
                                        ]
                                      : draft.searchProviders.filter(
                                          p => p.id !== id
                                        ),
                                  })
                                }
                              />
                              {source?.name ?? id}
                            </label>
                            <span className="rm-muted">
                              {source?.worker?.credentialReady === false
                                ? "Credential needed"
                                : source?.worker?.enabled
                                  ? source.worker.health
                                  : "Setup needed"}
                            </span>
                            {free ? (
                              <span>$0 / free account required</span>
                            ) : (
                              <label>
                                Maximum $
                                <Input
                                  aria-label={`${source?.name ?? id} search allocation`}
                                  type="number"
                                  min="0"
                                  max="5"
                                  step="0.01"
                                  disabled={!selected || draft.runCap === 0}
                                  value={selected?.budget ?? 0}
                                  onChange={e =>
                                    setDraft({
                                      ...draft,
                                      searchProviders:
                                        draft.searchProviders.map(p =>
                                          p.id === id
                                            ? {
                                                ...p,
                                                budget: Number(e.target.value),
                                              }
                                            : p
                                        ),
                                    })
                                  }
                                />
                              </label>
                            )}
                          </div>
                        );
                      })}
                    </fieldset>
                    <div className="rm-actions">
                      <Button disabled={save.isPending} type="submit">
                        <Save size={16} />
                        {save.isPending ? "Saving…" : "Save profile"}
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        onClick={download}
                      >
                        <Download size={16} /> Export profile
                      </Button>
                      {isControlReady && (
                        <Button
                          type="button"
                          variant="outline"
                          onClick={launchDraft}
                          disabled={launch.isPending}
                        >
                          <Play size={16} />
                          {launch.isPending
                            ? "Queuing run…"
                            : "Launch from this profile"}
                        </Button>
                      )}
                      {status.data?.running && status.data.activeRunId && (
                        <Button
                          type="button"
                          variant="outline"
                          onClick={stopRun}
                          disabled={stop.isPending}
                        >
                          <Square size={16} />
                          {stop.isPending ? "Stopping..." : "Stop active run"}
                        </Button>
                      )}
                    </div>
                  </form>
                )}
              </section>
            </div>
          )}

          {section === "Candidates" && (
            <RecruitMeCandidates
              data={workspace.data}
              statuses={workspace.data?.statuses ?? {}}
              saving={workflow.isPending}
              onStatusChange={(key, status) =>
                workflow.mutate({
                  key,
                  status,
                  expectedStatus: workspace.data?.statuses[key] ?? "New",
                })
              }
              loading={workspace.isLoading}
              error={workspace.isError}
              refresh={() => {
                workspace.refetch();
              }}
            />
          )}

          <RecruitMePanels
            section={section}
            data={workspace.data}
            refresh={() => {
              workspace.refetch();
            }}
          />

          {section === "Settings" && (
            <section className="rm-panel">
              <h2>Safeguards & connections</h2>
              <div className="rm-settings">
                {[
                  ["Bridge control", isControlReady ? "Enabled" : "Disabled"],
                  [
                    "Snapshot path",
                    workspace.data?.connection?.bridge?.snapshotPath ??
                      "Not configured",
                  ],
                  [
                    "Exa / Tavily credentials",
                    "Server-side only; never returned to the browser",
                  ],
                  ["Optional enrichment", "Stops at $20 session spend"],
                  [
                    "Final $5 of session budget",
                    "High-value candidate research only",
                  ],
                  [
                    "Provider failures",
                    "No uncontrolled retries; unknown prices fail closed",
                  ],
                  [
                    "Outreach & purchases",
                    "No automatic outreach, subscriptions or credit purchases",
                  ],
                  [
                    "Profile history",
                    `${workspace.data?.audit.length ?? 0} saved changes recorded`,
                  ],
                ].map(([k, v]) => (
                  <div key={k}>
                    <strong>{k}</strong>
                    <span>{v}</span>
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>
      </main>
    </div>
  );
}
