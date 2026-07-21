# PHP Security

PHP security depends on input validation, output escaping, safe database access, dependency hygiene, and deployment configuration.

## High-Risk Patterns

- SQL string concatenation.
- XSS from unescaped output.
- File upload without validation.
- Insecure session configuration.
- Secrets in repository files.
- Dynamic include paths from user input.

TStack should mark credential exposure, unsafe file upload handling, or unescaped output in sensitive paths as high risk.
