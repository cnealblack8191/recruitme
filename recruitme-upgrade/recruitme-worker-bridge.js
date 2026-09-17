#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

const action = process.argv[2];
const allowedActions = ["launch", "stop", "status", "activate_apollo", "review"];

if (!allowedActions.includes(action)) {
  console.error("Invalid action. Use launch, stop, status, activate_apollo, or review.");
  process.exit(1);
}

function readInput() {
  try {
    const raw = fs.readFileSync(0, "utf8").trim();
    if (!raw) return {};
    return JSON.parse(raw);
  } catch {
    return {};
  }
}

function getenv(names, fallback) {
  for (const name of names) {
    const value = process.env[name];
    if (value && value.trim()) {
      return value;
    }
  }
  return fallback;
}

function shQuote(value) {
  if (value === undefined || value === null) return "''";
  return `'${String(value).replace(/'/g, `'\"'\"'`)}`;
}

function readJsonFromOutput(stdout) {
  try { return JSON.parse(String(stdout || "").trim()); } catch { /* Allow a final JSON line after diagnostics. */ }
  const lines = String(stdout || "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .reverse();
  for (const line of lines) {
    try {
      return JSON.parse(line);
    } catch {
      // keep scanning for the next candidate line
    }
  }
  return null;
}

const cfg = {
  documentName: getenv(["RECRUITME_SSM_DOCUMENT"], "AWS-RunShellScript"),
  region: getenv(["RECRUITME_AWS_REGION", "AWS_REGION"], "us-east-1"),
  instanceId: getenv(["WORKER_INSTANCE_ID", "RECRUITME_WORKER_INSTANCE_ID"], ""),
  authMethod: getenv(["AUTH_METHOD", "RECRUITME_AUTH_METHOD", "AWS_AUTH_METHOD"], "aws_profile").toLowerCase(),
  awsProfile: getenv(["AWS_PROFILE", "RECRUITME_AWS_PROFILE"], ""),
  pythonBinary: getenv(["RECRUITME_PYTHON_BIN", "PYTHON_BIN"], "python3"),
  scriptRoot: getenv(["RECRUITME_WORKER_SCRIPT_ROOT", "WORKER_SCRIPT_ROOT"], "/opt/recruitme"),
  launchScript: getenv(["LAUNCH_SCRIPT", "RECRUITME_LAUNCH_SCRIPT", "RECRUITME_BRIDGE_LAUNCH_SCRIPT"], "launch_metro_deep_remote.py"),
  stopScript: getenv(["STOP_SCRIPT", "RECRUITME_STOP_SCRIPT", "RECRUITME_BRIDGE_STOP_SCRIPT"], "stop_metro_deep_remote.py"),
  statusScript: getenv(["STATUS_SCRIPT", "RECRUITME_STATUS_SCRIPT", "RECRUITME_BRIDGE_STATUS_SCRIPT"], "status_metro_deep_remote.py"),
  reviewScript: getenv(["REVIEW_SCRIPT", "RECRUITME_REVIEW_SCRIPT", "RECRUITME_BRIDGE_REVIEW_SCRIPT"], "review_import_remote.py"),
};

if (!cfg.instanceId) {
  console.error("Missing worker instance id. Set WORKER_INSTANCE_ID or RECRUITME_WORKER_INSTANCE_ID.");
  process.exit(1);
}

if (cfg.authMethod === "aws_profile" && !cfg.awsProfile) {
  console.warn("No AWS profile set. Using CLI default profile chain.");
}

function ensureAccessKeys() {
  if (cfg.authMethod !== "access_keys") return;
  const required = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"];
  const missing = required.filter((key) => !process.env[key]);
  if (missing.length) {
    console.error(`Missing AWS access key values in env: ${missing.join(", ")}`);
    process.exit(1);
  }
}

function buildAwsArgs(base) {
  const extra = [...base];
  extra.push("--region", cfg.region);
  if (cfg.authMethod === "aws_profile" && cfg.awsProfile) {
    extra.push("--profile", cfg.awsProfile);
  }
  return extra;
}

function runAws(args, expectJson = true) {
  const proc = spawnSync("aws", args, {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
    timeout: 30_000,
    maxBuffer: 2 * 1024 * 1024,
  });
  if (proc.error) {
    throw new Error("AWS command failed or timed out; inspect the worker status before retrying a launch.");
  }
  if (proc.status !== 0) {
    throw new Error(`AWS command failed (exit ${proc.status}); inspect the worker status before retrying a launch.`);
  }
  if (!expectJson) {
    return proc.stdout || "";
  }
  const parsed = readJsonFromOutput(proc.stdout || "");
  if (!parsed) {
    throw new Error("AWS command did not return JSON output.");
  }
  return parsed;
}

function buildRemoteCommand(scriptName, input) {
  const script = scriptName.includes("/")
    ? scriptName
    : `${cfg.scriptRoot.replace(/\/$/, "")}/recruitme-upgrade/${scriptName}`;
  const encoded = Buffer.from(JSON.stringify(input), 'utf8').toString('base64');
  return `printf %s ${shQuote(encoded)} | base64 --decode | ${shQuote(cfg.pythonBinary)} -B ${shQuote(script)}`;
}

function sendCommand(scriptName, input) {
  const parameters = cfg.documentName === 'AWS-RunShellScript' ? {
    commands: [buildRemoteCommand(scriptName, input)],
  } : { action: [action], payload: [Buffer.from(JSON.stringify(input), 'utf8').toString('base64')] };
  const outFile = path.join(process.cwd(), `.recruitme-bridge-${Date.now()}.json`);
  fs.writeFileSync(outFile, JSON.stringify(parameters));
  try {
    const commandId = runAws(buildAwsArgs([
      "ssm",
      "send-command",
      "--instance-ids",
      cfg.instanceId,
      "--document-name",
      cfg.documentName,
      "--comment",
      `recruitme-${action}`,
      "--parameters",
      `file://${outFile}`,
      "--query",
      "Command.CommandId",
      "--output",
      "text",
    ]), false);
    return String(commandId).trim();
  } finally {
    try {
      fs.unlinkSync(outFile);
    } catch {
      // ignore
    }
  }
}

function commandQuery(cmdId) {
  return runAws(buildAwsArgs([
    "ssm",
    "get-command-invocation",
    "--command-id",
    cmdId,
    "--instance-id",
    cfg.instanceId,
    "--output",
    "json",
  ]));
}

function delayMs(ms) {
  const lock = new Int32Array(new SharedArrayBuffer(4));
  Atomics.wait(lock, 0, 0, ms);
}

function waitForCommand(cmdId) {
  let attempt = 0;
  while (attempt < 120) {
    attempt += 1;
    try {
      const status = commandQuery(cmdId);
      const state = String(status.Status || "").toLowerCase();
      if (state === "success") return status;
      if (["failed", "cancelled", "timed_out", "canceled", "cancelling", "undeliverable"].includes(state)) {
        const err = [status.StandardErrorContent, status.StandardOutputContent].filter(Boolean).join("\n");
        throw new Error((err || `SSM command ended with state: ${status.Status}`).slice(0, 600));
      }
      if (state === "in_progress" || state === "pending") {
        delayMs(Math.min(1000 + attempt * 250, 5000));
        continue;
      }
      const err = [status.StandardErrorContent, status.StandardOutputContent].filter(Boolean).join("\n");
      throw new Error((err || `SSM command in unexpected state: ${status.Status}`).slice(0, 600));
    } catch (error) {
      if (attempt < 120) {
        delayMs(Math.min(1000 + attempt * 250, 5000));
        continue;
      }
      throw error;
    }
  }
  throw new Error("SSM command timed out waiting for output.");
}

function parseStatusFromText(text) {
  if (!text) return null;
  const normalized = String(text).toLowerCase();
  const online = normalized.includes("running") || normalized.includes("service active") || normalized.includes("active");
  return {
    online,
    status: online ? "RUNNING" : "IDLE",
    activeRunId: null,
    startedAt: null,
    running: online,
    detail: text.split("\n").slice(-1)[0].slice(0, 600),
    lastUpdated: new Date().toISOString(),
  };
}

function runPayload(input) {
  ensureAccessKeys();
  const script =
    action === "launch" ? cfg.launchScript
      : action === "stop" ? cfg.stopScript
        : action === "review" ? cfg.reviewScript
          : cfg.statusScript;
  const commandId = sendCommand(script, input);
  const invocation = waitForCommand(commandId);
  const output = readJsonFromOutput(invocation.StandardOutputContent || "");
  if (action === 'activate_apollo') {
    if (!output?.connected || output.provider !== 'apollo') throw new Error('Worker did not confirm the Apollo connection.');
    console.log(JSON.stringify({ connected: true, provider: 'apollo' }));
    return;
  }

  if (action === "review") {
    // A rejected submission is a normal outcome carrying the gate failures; only a
    // malformed reply is an error.
    if (!output || typeof output.accepted !== 'boolean' || (output.accepted && !output.candidateId) || (!output.accepted && !Array.isArray(output.errors))) {
      throw new Error('Worker did not return a review receipt. Refresh status before retrying.');
    }
    console.log(JSON.stringify(output));
    return;
  }

  if (action === "launch") {
    if (!output || output.accepted !== true || !output.runId) throw new Error('Worker did not confirm a launch. Check status before retrying.');
    const launchResult = output;
    console.log(JSON.stringify(launchResult));
    return;
  }

  if (action === "stop") {
    if (!output || typeof output.accepted !== 'boolean' || output.runId !== input.runId) throw new Error('Worker did not confirm the requested stop. Refresh status.');
    const stopResult = output;
    console.log(JSON.stringify(stopResult));
    return;
  }

  if (action === "status") {
    const statusResult = output;
    if (!statusResult) {
      throw new Error("Status output not machine-readable JSON.");
    }
    if (statusResult.online === undefined) statusResult.online = false;
    console.log(
      JSON.stringify({
        online: Boolean(statusResult.online),
        status: statusResult.status || "UNKNOWN",
        activeRunId: statusResult.activeRunId || null,
        startedAt: statusResult.startedAt || null,
        running: Boolean(statusResult.running),
        detail: statusResult.detail,
        lastUpdated: statusResult.lastUpdated || new Date().toISOString(),
        meter: statusResult.meter,
      })
    );
  }
}

try {
  const input = readInput();
  runPayload(input);
} catch (error) {
  console.error(String(error.message || error));
  process.exit(1);
}
