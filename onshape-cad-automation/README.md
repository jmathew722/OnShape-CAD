# Onshape CAD Automation

Private Python starter project for read-only inspection and future controlled CAD editing via the Onshape REST API.

## Target document

- Document: `944558403f04d7842312d8f6`
- Workspace: `0e2895e7580dcc7747665856`
- Element: `abbe646800a37a61d13f6efc`
- [Open Onshape document](https://cad.onshape.com/documents/944558403f04d7842312d8f6/w/0e2895e7580dcc7747665856/e/abbe646800a37a61d13f6efc)

## Setup

1. **Revoke any Onshape API key exposed in chat or elsewhere**, then generate a fresh one with minimum required permissions.
2. Install Python 3.11+. Run `python -m venv .venv`, activate it, and `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and put the new Onshape credentials there. Never commit `.env`.
4. Run `python -m src.inspect_document` to test read-only document access.
5. Only after confirming the element is an Assembly, implement and review any write operations. Save a backup/version before every change.

> GitHub repository secrets are available to GitHub Actions; they do not automatically appear in your local shell or Codex environment. Configure credentials in whichever runtime executes the script.

## Safety

This scaffold performs **no CAD writes**. Mates require inspection of the actual assembly instances and mate connectors. Don't invent instance IDs or hard-code a mate until the assembly is inspected. Handle each change with a dry run, explicit confirmation, and verification.

## Codex

Read `AGENTS.md` before making changes. The first task is to implement a reliable assembly inspection command that lists instances, connector references, and existing mates, with tests, without changing the Onshape document.
