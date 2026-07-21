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

Route a human instruction into a safe plan:

```bash
tstack human run "scrap se deployment tak app banao aur ui ux design bhi"
```

## Safety Boundary

The parser can suggest a command, but it does not execute it automatically.

- Typo normalization is allowed.
- Hinglish and mixed-language instructions are supported.
- Suggested commands remain approval-gated.
- Human run mode routes into plans only.
- Private scraping, SSH, code changes, and deployment are not executed from parsed text alone.

This makes TStack more natural to use without weakening the human approval model.

## Registry Coverage

The current registry tracks 100+ major human languages and is designed to grow. It is not a claim that TStack contains complete grammar, cultural, legal, or professional translation mastery for every human language on earth. There are thousands of living languages and dialects, so TStack treats language support as a versioned registry that can be expanded and reviewed.

Current language coverage can be checked with:

```bash
tstack human languages --format json
```

The long-term goal is:

- Detect mixed-language input.
- Normalize common typing mistakes.
- Infer safe user intent.
- Suggest the right TStack command.
- Keep execution approval-gated.
