# Onshape CAD Automation

Auditable Python tooling for inspecting an Onshape document before planning or applying CAD changes. The current milestone is intentionally **read-only**: it can confirm the configured element type and inventory assembly instances, occurrences, transforms, grounded/fixed state, mates, mate parameters, and explicit mate connectors.

## Safety status

- No mutating HTTP methods are implemented.
- Credentials are loaded at runtime and are never included in output.
- API errors report status/request IDs but not proprietary response bodies.
- Assembly commands first confirm that the selected element is actually an Assembly.
- A successful HTTP response is not treated as proof of a CAD change.

If an old Onshape key was pasted into chat, **revoke it before proceeding**. The GitHub repository may be public; do not add confidential drawings or CAD exports until its visibility is verified and appropriate.

## Target

- Document: `944558403f04d7842312d8f6`
- Workspace: `0e2895e7580dcc7747665856`
- Element: `abbe646800a37a61d13f6efc`
- [Open target in Onshape](https://cad.onshape.com/documents/944558403f04d7842312d8f6/w/0e2895e7580dcc7747665856/e/abbe646800a37a61d13f6efc)

IDs are configurable; these defaults merely identify the handed-off target and do not imply that its element type has been verified.

## Setup

Python 3.11 or newer is required.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Put a newly generated, minimally scoped Onshape access key and secret in `.env`. Required secret variables:

```dotenv
ONSHAPE_ACCESS_KEY=<fresh key>
ONSHAPE_SECRET_KEY=<fresh secret>
```

The base URL, API version, document, workspace, and element variables are documented in `.env.example`. GitHub Actions secrets do not automatically become local Codex environment variables.

## Read-only commands

Run commands from this directory:

```bash
python -m src inspect-document
python -m src inspect-assembly
python -m src list-instances
python -m src list-mates
python -m src list-connectors
```

All commands emit bounded JSON summaries instead of full response dumps. `inspect-assembly` asks Onshape to include mate features, mate connectors, non-solid instances, suppressed items, and occurrence transforms. Nothing is written to Onshape.

## Tests

The repository-mandated command is:

```bash
python3 -m unittest discover -v
```

The live test is skipped by default. After fresh credentials are configured, explicitly enable the read-only integration check:

```bash
RUN_ONSHAPE_INTEGRATION=1 python3 -m unittest discover -v
```

## Workflow toward mates and CAD edits

1. Revoke the previously exposed key and configure a fresh key locally.
2. Run `inspect-document`; verify the configured element type.
3. If it is an Assembly, inventory real instance paths, existing mates, mate connectors, transforms, suppression, and fixed state.
4. For a requested mate, resolve the user's named parts to actual instance paths and connector definitions. Report ambiguities instead of guessing.
5. Produce a dry-run plan showing mate type, connector frames, offsets/limits, expected orientation, and retained degrees of freedom.
6. Obtain explicit approval for the exact target and exact plan.
7. Create a rollback version, apply one approved operation without blind retries, then independently read back and validate the model state.

Write support is deliberately not exposed yet: it depends on live discovery and a concrete mate/modeling request. This prevents generic payloads or invented IDs from changing the wrong assembly.

## Official references

- [Onshape API-key authentication and HMAC signing](https://onshape-public.github.io/docs/auth/apikeys/)
- [Onshape document APIs](https://onshape-public.github.io/docs/api-adv/documents/)
- [Onshape assembly APIs and mate workflow](https://onshape-public.github.io/docs/api-adv/assemblies/)
- [Onshape REST API versioning and identifier model](https://onshape-public.github.io/docs/api-intro/)
