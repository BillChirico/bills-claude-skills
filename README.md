# Bill's Claude Skills

Custom skills for Claude Code that automate common workflows.

## Installation

```bash
# Add marketplace
/plugin marketplace add BillChirico/bills-claude-skills

# Install a skill
/plugin install github-pr-resolver@bills-claude-skills

# Authenticate GitHub CLI (required)
gh auth login
```

## Skills

### GitHub PR Resolver

Resolves all PR review comments and ensures CI passes.

```bash
/resolve-pr https://github.com/owner/repo/pull/123
```

**What it does:**
- Fetches all review threads (paginated)
- Creates todo list with author names and comment links
- Fixes issues in parallel (groups by file)
- Resolves each thread immediately after fixing
- Verifies resolution succeeded
- Waits for CI to pass, fixes failures if needed
- Final verification: zero unresolved + all CI green

[View full documentation →](github-pr-resolver/SKILL.md)

---

### Git Workspace Init

Creates isolated git worktrees with conventional branch naming.

```bash
/init-workspace <type> <description>

# Examples
/init-workspace feat user-authentication
/init-workspace fix login-validation-error
/init-workspace hotfix security-patch
```

**Types:** `feat`, `fix`, `hotfix`, `docs`, `refactor`, `test`, `chore`, `perf`, `ci`, `style`

[View full documentation →](git-workspace-init/SKILL.md)

---

## Prerequisites

- [Claude Code CLI](https://claude.ai/code)
- [GitHub CLI](https://cli.github.com/) with `repo` scope

## License

MIT
