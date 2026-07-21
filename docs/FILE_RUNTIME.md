# File Runtime

TStack file runtime is the first transactional local executor foundation.

It can:

- read an existing file organize plan
- require an approved `filesystem.move` runtime request
- dry-run planned moves by default
- apply moves only with `--apply`
- write a transaction manifest
- undo an applied transaction from the manifest

```bash
tstack file organize-plan ~/Downloads --format json --output plan.json
tstack runtime request filesystem.move "Organize Downloads" --target ~/Downloads --format json --output request.json
tstack runtime decide request.json --approved --approver Mosin --reason "Reviewed." --format json --output decision.json
tstack file-runtime apply plan.json request.json decision.json --apply --manifest transaction.json
tstack file-runtime undo transaction.json
```

The runtime refuses destination conflicts, absolute move paths, path escapes, unapproved decisions, and non-`filesystem.move` capability requests.
