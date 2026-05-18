# Security Policy

## Scope

This policy covers security vulnerabilities in the **agent-trials eval framework itself** — the runner, judge, agent archetypes, and dashboard.

If you found a vulnerability in **Armor**, report it to the Armor project directly: https://github.com/tkdtaylor/armor

## Reporting a vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Email **tkdtaylor@gmail.com** with the subject line `agent-trials security`. Include:

- A description of the vulnerability
- Reproduction steps (minimal example preferred)
- Your assessment of the impact

## Response timeline

- Acknowledgement within **48 hours**
- Fix timeline is best-effort — this is an open-source research project with no dedicated security team

## No bug bounty

There is no bug bounty program.

## About the attack corpus

[`attacks/corpus.yaml`](attacks/corpus.yaml) contains intentional malicious payloads — prompt injections, exfiltration attempts, tool-call abuse patterns. These are not vulnerabilities. They are the test fixtures the framework is designed to detect and measure.
