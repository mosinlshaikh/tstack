# Human Language Understanding

TStack includes a human-language foundation for mixed English, Hindi, Hinglish, Urdu, and many other world languages.

The goal is practical: users may type imperfect instructions, and TStack should still infer a safe intent.

## Commands

List the language registry:

```bash
tstack human languages
tstack human languages --format json
```

Parse a typo-tolerant instruction:

```bash
tstack human intent "scrap se deploment tak sabkuch handel karo aur ui ux desing bhi"
```

## Safety Boundary

The parser can suggest a command, but it does not execute it automatically.

- Typo normalization is allowed.
- Hinglish and mixed-language instructions are supported.
- Suggested commands remain approval-gated.
- Private scraping, SSH, code changes, and deployment are not executed from parsed text alone.

This makes TStack more natural to use without weakening the human approval model.
