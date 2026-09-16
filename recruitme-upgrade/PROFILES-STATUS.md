# Reusable job profiles — local implementation status

Implemented locally; NOT deployed or launched as of September 9, 2026.

- Immutable run manifest contains a versioned job profile; resumed checkpoints retain it.
- Roles, fit terms, local areas and track definitions are configurable. Atlanta electricians is the first profile. A synthetic accountant profile verifies reuse without electrical-role code changes.
- Pay, start date, relocation and travel constraints are retained in the report. Acceptance is UNKNOWN until evidenced; no invented compensation or availability.
- First 20 discovery intents are compared sequentially through both keyed providers. Later plans mix discovery and person-specific follow-up, with provider operation limits and original deadline remaining authoritative.
- Reserved dispatch accepts exact equality with a hard ceiling only for a valid unused reservation. It rechecks price freeze, provider state/limits, runtime, resource and session controls. No spend is subtracted; subsequent reservations still stop.
- NETWORK_DISPATCH audit entries identify attempted dispatch separately from reservations and successful responses. A crash after this marker can leave uncertainty; it must not trigger an automatic duplicate.
- Junior and experienced hints are reported separately as unverified overlapping page counts. No automatic A/B promotion or person-identity merge.
- Employer materials are drafts only.

Validation: 119 tests collected, 114 passed, 5 skipped on Windows. Four skipped tests require Linux locking/timers; the fifth requires the deployed systemd sandbox. All must run on EC2 before declaring deployment verified. Provider transports in tests are synthetic.

Access blocker: AWS CLI reports its session expired. Run `aws login` locally and complete sign-in. No AWS modification or live provider request has occurred in this change.

Prepared staging command after login: `./send-script.ps1 -ScriptFile ./stage_profiles_remote.py`. It checks baseline hashes, stages code and runs offline Linux tests with PrivateNetwork=yes. It does not install the staged code or start research. Inspect results before preparing a current-state deployment and launch.

Deployment still requires: live state/config inspection; successful Linux tests; backup and locked installation; preservation of every existing ledger row; bounded Exa allowance increment (40 for the initial comparison); Tavily activation with verified credential; authorized new runtime and valid cumulative session binding; live $5/$25/$100 checks; and receipt proving service start plus first successful checkpoint. Never replay old installation scripts blindly.
