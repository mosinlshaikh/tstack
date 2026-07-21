# JavaScript Security

JavaScript security depends on runtime validation, browser safety, dependency controls, and secret handling.

## High-Risk Patterns

- XSS through unsafe HTML rendering.
- `eval()` or dynamic code execution.
- Secrets shipped to browser bundles.
- Prototype pollution exposure.
- SQL, NoSQL, or shell command injection.
- Missing dependency lockfile.

TStack should mark leaked secrets, unsafe rendering, and unreviewed dynamic execution as high risk.
