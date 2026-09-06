# Local security checks

This optional workflow runs Semgrep Community Edition 1.176.1 and Gitleaks 8.30.1
on GitHub pull requests and manual `workflow_dispatch` runs. It uses ordinary
GitHub Actions features in personal public or private repositories. It requires
Actions to be enabled and uses the account's normal Actions minutes; GitHub
Advanced Security, a Semgrep account, a Gitleaks license key, and external service
tokens are not required.

## What is checked

The six local Semgrep rules detect Python/JavaScript `eval`, explicit Python and
JavaScript TLS verification bypasses, unsafe Python YAML loaders, and DES/RC4/ECB
Java ciphers. These are focused security checks informed by Project CodeGuard
1.4.0; they are locally authored rules, not an official CodeGuard scanner or a
complete implementation of all CodeGuard guidance. Legitimate uses of flagged
primitives need a reviewed rule adjustment. Dependency vulnerabilities remain
the responsibility of Dependabot and each project's dependency checks.

For a pull request, the comparison starts at the merge base of the PR base SHA
and checked-out head. Semgrep suppresses findings already present at that
baseline. Gitleaks scans commits introduced by the PR, including a synthetic
secret added and then removed within the PR. Existing findings in unrelated,
unchanged history do not block a safe change. A new or touched credential can
still fail the check.

A manual run checks the previous commit by default. Its optional `base_ref`
input selects an older comparison commit or ref. An initial repository commit
has no backlog and is scanned as a whole. Invalid or unavailable refs fail the
run; they are not silently treated as an empty diff.

## Privacy and permissions

The job has only `contents: read`, does not persist checkout credentials, and
does not install or execute the repository's application. Scanners use local
rules, with Semgrep metrics and version checks disabled. They do not log in,
fetch a hosted rule registry, upload source, upload SARIF, or create artifacts.
Tool installation downloads public packages and release archives.

Only rule identifiers, file paths, line numbers, counts, and exit statuses are
printed. Gitleaks runs with full redaction. Scanner JSON stays in a private
temporary directory and is deleted after the run, including on failure; source
snippets and secret values are not printed. Installation and GitHub's own runner
logs remain subject to the repository's normal Actions access controls.

Gitleaks extends the bundled default detectors. Its exceptions apply only to
the named vendored CodeGuard Markdown guidance and reviewer files. It does not
exclude general documentation, application code, all of `.github`, or all tests.
Semgrep's normal language/file selection and Git ignore behavior still apply.

## Integration

Copy the supplied `repo-bundle/.github` files into the target repository on a
review branch. Preserve existing security workflows and compare any colliding
file before replacing it. The existing CodeGuard `README.md` and `LICENSE.md`
are separate files and are not replaced by this bundle. No `push` or scheduled
trigger is installed.

Validate the resulting workflow with Actionlint and run a test PR. The check is
named **Local security checks**. Adding it as a required branch-protection check
is a separate repository policy choice; this bundle does not modify protection
settings. GitHub's usual fork-workflow approval rules still apply.

With the pinned scanner versions installed, run the same check locally from a
clean Git checkout:

```sh
python .github/codeguard/ci-scan.py --base HEAD~1
```

The full source bundle includes disposable vulnerable/safe fixture and Git
history smoke tests under `validation/`. They are intentionally not copied into
application repositories. Those tests verify all six rules, safe-change behavior
with a legacy backlog, new-secret redaction, narrow guidance exceptions, and
failure on a missing baseline. Actionlint validates the workflow syntax.

## Provenance and updates

The workflow's two actions are pinned to verified upstream commit SHAs. Gitleaks
is pinned by release version and SHA-256 of its Linux x64 archive. Semgrep's
package is pinned to 1.176.1; its transitive Python packages are resolved by pip
from PyPI at installation time. Tool source references and verification details
are in `ci-provenance.json`. Revalidate the pins and smoke tests when updating.

Relevant upstream documentation: [Semgrep CLI](https://docs.semgrep.dev/cli-reference),
[Gitleaks 8.30.1](https://github.com/gitleaks/gitleaks/blob/v8.30.1/README.md), and
[Project CodeGuard](https://github.com/cosai-oasis/project-codeguard/tree/7e19e207bd67abbd3d04ae664441595410df1157).
