# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a collection of custom Claude Code skills. Skills are self-contained modules that provide Claude with specialized capabilities through structured workflows and documentation.

## Structure

```
bills-claude-skills/
├── .claude-plugin/
│   └── marketplace.json    # Plugin registry configuration
├── github-pr-resolver/     # PR review resolution skill
│   ├── SKILL.md           # Skill definition and workflow
│   ├── commands/
│   │   └── resolve-pr.md  # Slash command definition
│   └── references/
│       └── github_api_reference.md
├── git-workspace-init/     # Git worktree initialization skill
│   ├── SKILL.md           # Skill definition and workflow
│   └── commands/
│       └── init-workspace.md  # Slash command: /init-workspace <type> <description>
└── README.md               # Usage documentation
```

## Skills Architecture

Each skill follows this pattern:
- **SKILL.md**: Frontmatter with `name` and `description`, followed by workflow documentation
- **commands/**: Slash command definitions (e.g., `/resolve-pr`, `/init-workspace`)
- **references/**: Supporting documentation for complex APIs or workflows

## Working with Skills

### Prerequisites

The `github-pr-resolver` skill requires the GitHub CLI:

```bash
# Verify gh CLI is installed and authenticated
gh auth status

# If not authenticated, run:
gh auth login
```

Token requires `repo` scope for full repository access.

## Commit Convention

This repository uses conventional commits: `<type>(<scope>): <description>`

Types: `feat`, `fix`, `docs`, `refactor`, `style`, `perf`, `test`, `chore`
