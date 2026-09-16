# RecruitMe options 1-4 installation

Installed on `i-00d4af5fb05831699` in `us-east-2`, under `/opt/recruitme`.

- 19 application/test/helper files installed after staging validation.
- 27 new tests; all 108 deployed tests passed, including production sandbox checks (11.809 seconds).
- Staging had 107 passing tests and one deployment-only sandbox skip; deployed tests had no skips.
- Exa filters/ten-result shape and stricter signal screening installed.
- Tavily connector installed and approved, but disabled because its credential is absent. No live Tavily validation claimed.
- WorkSource and BlueRecruit employer preparation and reviewed-import workflows installed; account/eligibility/retention confirmations remain required. These are not scraping connectors.
- RecruitMe is inactive; no research started.
- Hermes is active, PID 7135, zero restarts.
- All production database records preserved unchanged during installation. After selftests: 158 free operations/$0, 500 keyed Exa operations/$3.50 conservative allocation. No new provider operations.
- Default run cap now $5. Existing session residual ceiling/cutoff, immutable runtime/session IDs, $100 POC ceiling and cumulative provider request limits preserved. Exa remains at its exhausted 500-operation allowance.
- Backup: `/opt/recruitme-backup-options-1-4-1788925326`.

No accounts, purchases, outreach, AWS infrastructure, IAM, security-group or Hermes changes were made. Test execution used the existing instance; incremental infrastructure billing was not measured. Research/API spend for this installation: $0.

Next requirements and exact hidden-key command are in [README.md](README.md). The employer packet is [employer-packet.json](employer-packet.json).
