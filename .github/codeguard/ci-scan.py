#!/usr/bin/env python3
"""Run local change checks without printing source or secret values."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


def git(*args):
    return subprocess.check_output(
        ['git', *args], text=True, stderr=subprocess.DEVNULL
    ).strip()


def resolve_commit(value):
    # A ref is an argument, never shell code. --end-of-options rejects options.
    return git('rev-parse', '--verify', '--end-of-options', value + '^{commit}')


def baseline(explicit):
    if explicit:
        return git('merge-base', resolve_commit(explicit), 'HEAD')
    if os.environ.get('GITHUB_EVENT_NAME') == 'pull_request':
        event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
        base = event['pull_request']['base']['sha']
        if not re.fullmatch(r'[0-9a-f]{40}', base):
            raise ValueError('The pull request base must be a full commit SHA.')
        return git('merge-base', base, 'HEAD')
    try:
        return resolve_commit('HEAD^')
    except subprocess.CalledProcessError:
        # A first commit has no existing backlog; inspect that initial tree.
        if git('rev-list', '--count', 'HEAD') != '1':
            raise
        return None


def show_finding(scanner, rule, file_path, line):
    # JSON escaping prevents filenames from injecting terminal controls or
    # GitHub workflow commands. Never print matches, snippets, or secret values.
    print(json.dumps({'scanner': scanner, 'rule': rule,
                      'file': file_path, 'line': line}, ensure_ascii=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default=os.environ.get('CODEGUARD_BASE_REF'))
    args = parser.parse_args()
    os.umask(0o077)
    os.chdir(git('rev-parse', '--show-toplevel'))
    here = Path(__file__).resolve().parent
    base = baseline(args.base)
    head = resolve_commit('HEAD')
    print(json.dumps({'comparison_base': base, 'head': head}))
    failed = False

    with tempfile.TemporaryDirectory(prefix='codeguard-check-') as work:
        temporary = Path(work)
        env = os.environ.copy()
        for key in ('SEMGREP_APP_TOKEN', 'SEMGREP_RULES', 'SEMGREP_BASELINE_COMMIT',
                    'GITLEAKS_CONFIG', 'GITLEAKS_CONFIG_TOML'):
            env.pop(key, None)
        env.update(SEMGREP_SEND_METRICS='off', SEMGREP_ENABLE_VERSION_CHECK='0',
                   DO_NOT_TRACK='1', SEMGREP_SETTINGS_FILE=str(temporary/'settings.yml'),
                   SEMGREP_LOG_FILE=str(temporary/'semgrep.log'))
        report = temporary/'semgrep.json'
        command = ['semgrep', 'scan', '--config', str(here/'ci-semgrep.yml'),
                   '--metrics=off', '--disable-version-check', '--error', '--strict',
                   '--jobs=2', '--timeout=10', '--timeout-threshold=1', '--json',
                   '--output', str(report)]
        if base:
            command += ['--baseline-commit', base]
        command += ['.']
        run = subprocess.run(command, env=env, capture_output=True, timeout=600)
        if not report.exists():
            raise ValueError('Semgrep did not produce its local report.')
        data = json.loads(report.read_text())
        findings = data.get('results', [])
        for finding in findings[:100]:
            show_finding('semgrep', finding['check_id'], finding['path'],
                         finding['start']['line'])
        errors = data.get('errors', [])
        print(json.dumps({'scanner':'semgrep', 'findings':len(findings),
                          'errors':len(errors), 'exit_code':run.returncode}))
        failed |= bool(findings or errors or run.returncode)

        report = temporary/'gitleaks.json'
        log_range = f'{base}..{head}' if base else head
        command = ['gitleaks', 'git', '--config', str(here/'ci-gitleaks.toml'),
                   '--log-opts', log_range, '--redact=100', '--no-banner', '--no-color',
                   '--report-format=json', '--report-path', str(report),
                   '--timeout=300', '.']
        run = subprocess.run(command, env=env, capture_output=True, timeout=330)
        if not report.exists():
            raise ValueError('Gitleaks did not produce its local report.')
        findings = json.loads(report.read_text())
        for finding in findings[:100]:
            show_finding('gitleaks', finding['RuleID'], finding['File'],
                         finding['StartLine'])
        print(json.dumps({'scanner':'gitleaks', 'findings':len(findings),
                          'exit_code':run.returncode}))
        failed |= bool(findings or run.returncode)
    return 1 if failed else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, subprocess.SubprocessError):
        # Exceptions can include source text or subprocess output. Keep logs
        # private and fail closed with an actionable, value-free diagnostic.
        print('CodeGuard could not complete a scanner or comparison. Verify tool installation, the base ref, and the repository history.', file=sys.stderr)
        sys.exit(2)
