import { useState } from "react";
import { ArrowUpRight, Download, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { trpc } from "@/lib/trpc";
import { toast } from "sonner";
import type { inferRouterOutputs } from "@trpc/server";
import type { recruitmeRouter } from "../../../server/recruitme";

type Workspace = inferRouterOutputs<typeof recruitmeRouter>["workspace"];

export default function RecruitMePanels({
  section,
  data,
  refresh,
}: {
  section: string;
  data: Workspace | undefined;
  refresh: () => void;
}) {
  const [apolloKey, setApolloKey] = useState("");
  const connectApollo = trpc.recruitme.connectApollo.useMutation({
    onSuccess: () => {
      toast.success("Apollo connected. Select it in your search profile.");
      refresh();
    },
    onError: e => toast.error(e.message),
    onSettled: () => {
      setApolloKey("");
      connectApollo.reset();
    },
  });

  if (section === "Credits") {
    const format = (value: number | null, unit: string) =>
      value === null
        ? "Unavailable"
        : unit === "USD"
          ? `$${value.toFixed(3)}`
          : value.toLocaleString();
    return (
      <section className="rm-panel">
        <h2>Provider credits and balances</h2>
        <p className="rm-muted">
          Latest recorded balances. Provider balances include account-wide
          usage; local estimates include only RecruitMe. Balance checks are
          separate from search charges.
        </p>
        {!data?.credits.length ? (
          <p>Credit information has not synchronized yet.</p>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table className="rm-table">
              <thead>
                <tr>
                  <th>Provider</th>
                  <th>Remaining</th>
                  <th>Allowance</th>
                  <th>Source</th>
                  <th>Renewal</th>
                  <th>Last checked</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                {data.credits.map(c => (
                  <tr key={c.id}>
                    <td>
                      {data.sources.find(s => s.id === c.id)?.name ?? c.id}
                    </td>
                    <td>
                      {format(c.remaining, c.unit)}
                      {c.remaining !== null && c.unit !== "USD"
                        ? ` ${c.unit}`
                        : ""}
                    </td>
                    <td>{format(c.limit, c.unit)}</td>
                    <td>
                      {c.basis === "provider"
                        ? "Provider reported"
                        : c.basis === "local"
                          ? "Local estimate"
                          : "Unavailable"}
                    </td>
                    <td>{c.renewsAt ?? "Not reported"}</td>
                    <td>
                      {c.checkedAt ? (
                        <>
                          {new Date(c.checkedAt).toLocaleString()}
                          {Date.now() - Date.parse(c.checkedAt) > 3600000 && (
                            <strong> · Out of date</strong>
                          )}
                        </>
                      ) : (
                        "Not checked"
                      )}
                    </td>
                    <td>{c.note}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <p className="rm-muted">
          Refreshing the workspace loads the latest saved check; it does not
          contact every provider. Unknown balances are never shown as zero.
        </p>
      </section>
    );
  }

  if (section === "Search runs") {
    return (
      <section className="rm-panel">
        <div className="rm-panel-heading">
          <h2>Search history</h2>
          <Button variant="outline" onClick={refresh}>
            Refresh
          </Button>
        </div>
        <p className="rm-muted">
          {data?.connection.ready
            ? "Searches execute on the configured worker. New launches are available from job profile controls."
            : "Search launches remain disabled until the worker control bridge is validated and a fresh snapshot is available."}
        </p>
        {!data?.runs?.length ? (
          <p>No worker history has been synchronized.</p>
        ) : (
          <div className="rm-table-wrap">
            <table className="rm-table">
              <thead>
                <tr>
                  <th>Run</th>
                  <th>Status</th>
                  <th>Pages</th>
                  <th>Verified</th>
                  <th>Search budget & usage</th>
                </tr>
              </thead>
              <tbody>
                {data.runs.map(r => (
                  <tr key={r.id}>
                    <td>
                      <strong>{r.id}</strong>
                      <small>{new Date(r.createdAt).toLocaleString()}</small>
                      <small>{r.stopReason}</small>
                    </td>
                    <td>{r.status}</td>
                    <td>{r.pages}</td>
                    <td>{r.verified}</td>
                    <td>
                      ${r.spend.toFixed(3)} committed
                      {r.cap != null && (
                        <>
                          {" "}
                          / ${r.cap.toFixed(2)} cap
                          <meter
                            className="rm-spend-meter"
                            aria-label={`${r.id} budget used`}
                            min={0}
                            max={r.cap || 1}
                            value={r.spend}
                          />
                          <small>
                            ${Math.max(0, r.cap - r.spend).toFixed(3)} remaining
                          </small>
                        </>
                      )}
                      {r.reserved != null && (
                        <small>
                          ${r.reserved.toFixed(3)} pending / unconfirmed,
                          included above
                        </small>
                      )}
                      {r.providerSpend?.map(p => (
                        <small key={p.id}>
                          {p.id}: ${p.spend.toFixed(3)}
                        </small>
                      ))}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    );
  }

  if (section === "Reports") {
    return (
      <section className="rm-panel">
        <h2>Download your research record</h2>
        <p className="rm-muted">
          Export synchronized run history, spending, and evidence with source
          URLs and original signal dates. Unverified records remain labeled.
        </p>
        <Button
          className="rm-space"
          disabled={!data?.snapshotAt}
          onClick={() => {
            if (!data) return;
            const url = URL.createObjectURL(
              new Blob(
                [
                  JSON.stringify(
                    {
                      asOf: data.snapshotAt,
                      budgets: data.budgets,
                      runs: data.runs,
                      candidates: data.candidates,
                    },
                    null,
                    2
                  ),
                ],
                { type: "application/json" }
              )
            );
            const a = document.createElement("a");
            a.href = url;
            a.download = "recruitme-evidence-report.json";
            a.click();
            URL.revokeObjectURL(url);
          }}
        >
          <Download size={16} />
          Export evidence report
        </Button>
      </section>
    );
  }

  if (section === "Sources") {
    return (
      <>
        <section className="rm-panel">
          <h2>Data service connections</h2>
          <p className="rm-muted">
            An adapter can be built without an account being connected. Account
            setup, pricing approval, and worker limits must pass before it runs.
            Free credits never erase recorded spending.
          </p>
        </section>
        <div className="rm-source-grid">
          {data?.sources.map(s => (
            <article className="rm-panel" key={s.id}>
              <div className="rm-panel-heading">
                <span className="rm-tag">{s.category}</span>
                <Play size={17} />
              </div>
              <h2 className="rm-space">{s.name}</h2>
              <p className="rm-muted">{s.model}</p>
              <p className="rm-source-detail">{s.detail}</p>
              <div className="rm-source-status">
                <strong>
                  {s.worker?.credentialReady === false
                    ? "Credential needed"
                    : s.worker?.enabled && s.worker?.approved
                      ? "Enabled in saved worker configuration"
                      : s.status}
                </strong>
                <small>
                  {s.worker
                    ? `${s.worker.health} · $${s.worker.spend.toFixed(3)} recorded`
                    : "Not connected to worker"}
                </small>
                {s.worker?.unitCost != null && (
                  <small>
                    ${s.worker.unitCost.toFixed(4)} maximum reserved per request
                  </small>
                )}
              </div>
              <a
                className="rm-source-link"
                target="_blank"
                rel="noopener noreferrer"
                href={s.url}
              >
                Open provider <ArrowUpRight size={14} />
              </a>
              <small className="rm-muted">
                Credentials are installed securely on the server. No automatic
                purchases.
              </small>
              {s.id === "apollo" && (
                <form
                  className="rm-space"
                  onSubmit={e => {
                    e.preventDefault();
                    connectApollo.mutate({ apiKey: apolloKey });
                  }}
                >
                  <label>
                    Apollo API key
                    <Input
                      type="password"
                      autoComplete="new-password"
                      value={apolloKey}
                      minLength={8}
                      maxLength={512}
                      required
                      disabled={!data.connection.bridge.apolloSetupReady}
                      onChange={e => setApolloKey(e.target.value)}
                      aria-label="Apollo API key"
                    />
                  </label>
                  <Button
                    className="rm-space"
                    type="submit"
                    disabled={
                      connectApollo.isPending ||
                      !data.connection.bridge.apolloSetupReady
                    }
                  >
                    {connectApollo.isPending ? "Connecting…" : "Connect Apollo"}
                  </Button>
                  {!data.connection.bridge.apolloSetupReady && (
                    <p className="rm-muted">
                      Secure connection is awaiting server permission setup.
                    </p>
                  )}
                  <p className="rm-muted">
                    Stored encrypted. Used for zero-credit people search.
                    Partial records remain unverified.
                  </p>
                </form>
              )}
            </article>
          ))}
        </div>
      </>
    );
  }

  return null;
}
