# SQL Security

SQL security depends on parameterized queries, access control, safe migrations, and data protection.

## High-Risk Patterns

- SQL injection through string concatenation.
- Overprivileged database users.
- Missing migration rollback plan.
- Sensitive data stored without protection.
- Destructive changes without backup evidence.

TStack should mark injection risks, unreviewed destructive migrations, or missing rollback evidence as high risk.
