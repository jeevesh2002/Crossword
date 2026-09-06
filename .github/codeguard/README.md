# Project CodeGuard

This repository vendors Project CodeGuard 1.4.0 security guidance from the CoSAI Project CodeGuard maintainers. Upstream: https://github.com/cosai-oasis/project-codeguard, pinned to commit `7e19e207bd67abbd3d04ae664441595410df1157`. The official converter generated these files; rule text is unmodified. The CC BY 4.0 attribution license is included in this directory.

- Codex and compatible agents discover `.agents/skills/codeguard/SKILL.md`.
- GitHub Copilot uses scoped rules in `.github/instructions/`.
- Codex and GitHub Copilot include the optional `codeguard-reviewer` agent. Request an explicit CodeGuard security review to produce a redacted SARIF report.
- The rules guide code generation and review. Installing rules does not prove the application is free of vulnerabilities.

Keep the source commit and generated rules together when updating. Preserve repository-specific instructions and existing security workflows.
