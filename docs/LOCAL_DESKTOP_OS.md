# TStack Local Agentic Desktop OS

TStack can be designed as a local-first desktop system that uses the installed PC's resources by default.

Product definition:

```text
TStack Local Agentic Desktop OS - a permission-controlled AI system that can operate files, applications, browser workflows, development tools, and local knowledge while using external APIs only when necessary and approved.
```

## Default Rule

```text
Local capability available -> use local system
Local capability unavailable -> ask permission for external service
Approved external service -> load key from encrypted vault
Use minimum required scope -> never expose keys in logs
```

## First Build

Start with:

- File Manager Agent.
- Desktop Control Agent.
- Browser Automation Agent.
- Permission Controller.
- Audit and Rollback.

Then connect:

- Website Builder Agent.
- Developer Agent.
- Local Learning Brain.
- Voice Agent.

## Browser Backend

The browser should run locally:

```text
TStack UI -> Local Agent Runtime -> Browser Controller -> Local Chromium -> Internet
```

Recommended:

- Chromium/WebView.
- Playwright automation service.
- Separate browser profile.
- Headless mode for normal tasks.
- Visible mode for login, CAPTCHA, payment, and sensitive steps.

## Security Controls

- Allowlisted applications and directories.
- Protected folders.
- OS keychain or credential manager.
- Domain allowlist.
- Download scanning.
- Prompt-injection protection.
- Browser content treated as untrusted input.
- Append-only audit log.
- Before-change snapshot.
- Undo/rollback.
- Emergency stop.
- Timeout and maximum-action limits.

## Command

```bash
tstack desktop blueprint
tstack desktop blueprint --format json
```
