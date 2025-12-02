# Bill's Claude Skills

A collection of custom skills for [Claude Code](https://claude.ai/code) that extend Claude's capabilities with specialized workflows and utilities.

## Quick Start

```bash
# 1. Add the marketplace
/plugin marketplace add BillChirico/bills-claude-skills

# 2. Install a skill
/plugin install github-pr-resolver@bills-claude-skills

# 3. Set up GitHub token
export GITHUB_TOKEN="your_token"

# 4. Use it!
/resolve-pr https://github.com/owner/repo/pull/123

# Or initialize a new workspace
/init-workspace feat user-auth
```

## What are Claude Skills?

Skills are structured prompts and helper utilities that give Claude Code specialized knowledge for specific tasks. Each skill includes:

- **Workflow documentation** - Step-by-step instructions Claude follows
- **Helper scripts** - Utilities Claude can import and execute
- **Reference materials** - API docs and patterns for complex integrations

## Available Skills

### GitHub PR Resolver

Automates pull request review resolution by processing comments, making fixes, and resolving threads.

**Capabilities:**
- Fetch PR context (review threads, check statuses)
- Parse and apply code suggestions from reviewers
- Fix failing CI checks (lint, tests, build, formatting)
- Resolve conversation threads via GitHub GraphQL API
- Commit changes using conventional commit format

**Use when:**
- A PR has review comments that need addressing
- CI/CD checks are failing
- You want to quickly iterate on PR feedback

[View skill documentation →](github-pr-resolver/SKILL.md)

### Git Workspace Init

Initialize isolated git worktrees with proper branch naming following [conventional branch](https://conventional-branch.github.io/) conventions.

**Capabilities:**
- Generate branch names from task type and description
- Create git worktrees for parallel development
- Push new branches to remote with tracking
- Support for all conventional types (feat, fix, hotfix, docs, refactor, etc.)

**Use when:**
- Starting work on a new feature
- Beginning a bug fix or hotfix
- Creating an isolated workspace for any task
- Working on multiple branches simultaneously

[View skill documentation →](git-workspace-init/SKILL.md)

## Installation

### Prerequisites

- [Claude Code CLI](https://claude.ai/code) installed
- Python 3.8+ (for helper scripts)
- GitHub personal access token with `repo` scope

### Option 1: Install via Claude Code Plugin System (Recommended)

The easiest way to install these skills is through Claude Code's plugin system.

**Step 1: Add this marketplace**

In Claude Code, run:
```
/plugin marketplace add BillChirico/bills-claude-skills
```

**Step 2: Install the GitHub PR Resolver skill**

```
/plugin install github-pr-resolver@bills-claude-skills
```

Or browse all available skills interactively:
```
/plugin
```

**Managing installed skills:**
```
/plugin disable github-pr-resolver@bills-claude-skills   # Temporarily disable
/plugin enable github-pr-resolver@bills-claude-skills    # Re-enable
/plugin uninstall github-pr-resolver@bills-claude-skills # Remove completely
```

**Managing this marketplace:**
```
/plugin marketplace list                        # View all configured marketplaces
/plugin marketplace update bills-claude-skills  # Pull latest skills from this repo
/plugin marketplace remove bills-claude-skills  # Remove marketplace and its skills
```

### Option 2: Manual Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/BillChirico/bills-claude-skills.git
   ```

2. Install Python dependencies:
   ```bash
   pip install requests
   ```

3. Copy skills to your Claude Code skills directory:
   ```bash
   # For personal skills (available in all projects)
   cp -r github-pr-resolver ~/.claude/skills/

   # Or for project-specific skills
   cp -r github-pr-resolver /path/to/your/project/.claude/skills/
   ```

### Environment Setup

Regardless of installation method, set up your GitHub token:
```bash
export GITHUB_TOKEN="your_personal_access_token"
```

Add to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.) for persistence:
```bash
echo 'export GITHUB_TOKEN="your_personal_access_token"' >> ~/.zshrc
```

## Usage

### Using the GitHub PR Resolver

**Via slash command (if configured):**
```
/resolve-pr https://github.com/owner/repo/pull/123
```

**Via direct invocation:**
```
Use the github-pr-resolver skill to resolve feedback on PR #123
```

### Using Git Workspace Init

**Via slash command:**
```
/init-workspace <type> <description>
```

**Examples:**
```bash
# Start a new feature
/init-workspace feat user-authentication

# Fix a bug
/init-workspace fix login-validation-error

# Create a hotfix
/init-workspace hotfix security-patch

# Documentation updates
/init-workspace docs api-reference
```

**Supported types:** `feat`, `fix`, `hotfix`, `docs`, `refactor`, `test`, `chore`, `perf`, `ci`, `style`

**Via direct invocation:**
```
Use the git-workspace-init skill to create a workspace for adding user authentication
```

## Contributing

Contributions are welcome! To add a new skill:

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/my-new-skill`
3. Add your skill following the structure above
4. Test the skill with Claude Code
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

Bill Chirico
