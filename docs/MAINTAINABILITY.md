# Maintainability Audit

TStack includes a report-only maintainability audit for module size and test/source balance.

```bash
tstack maintainability audit .
tstack maintainability audit . --format json
```

The audit flags modules that are becoming too large and recommends refactoring boundaries before more behavior is added.

## Verdicts

- `PASS` means no configured size risk was detected.
- `REVIEW` means at least one module should be refactored or the test/source ratio is low.
- `HOLD` means a module is large enough that future changes should be blocked until a split plan exists.

The command does not edit code. It only reports evidence and recommendations.
