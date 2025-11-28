# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a collection of custom Claude Code skills. Skills are self-contained modules that provide Claude with specialized capabilities through structured workflows and helper utilities.

## Structure

```
bills-claude-skills/
├── github-pr-resolver/     # PR review resolution skill
│   ├── SKILL.md           # Skill definition and workflow
│   ├── scripts/           # Python utilities
│   │   └── github_pr_client.py
│   └── references/        # API documentation
│       └── github_api_reference.md
├── git-workspace-init/     # Git worktree initialization skill
│   └── SKILL.md           # Skill definition and workflow
```

## Skills Architecture

Each skill follows this pattern:
- **SKILL.md**: Frontmatter with `name` and `description`, followed by workflow documentation
- **scripts/**: Helper utilities that can be imported and used during skill execution
- **references/**: Supporting documentation for complex APIs or workflows

## Working with Skills

### Testing the GitHub PR Client

```bash
# Requires GITHUB_TOKEN environment variable with repo scope
export GITHUB_TOKEN="your_token"

# Test from repository root
python3 -c "from github_pr_resolver.scripts.github_pr_client import get_full_pr_context; print('Import OK')"
```

### Dependencies

Python scripts use standard library plus:
- `requests`: For GitHub API calls (`pip install requests`)

## Commit Convention

This repository uses conventional commits: `<type>(<scope>): <description>`

Types: `feat`, `fix`, `docs`, `refactor`, `style`, `perf`, `test`, `chore`
