<div align="center">

<h1>
  <img src="https://api.iconify.design/vscode-icons:file-type-claude.svg" alt="Claude" width="60" height="60" style="vertical-align: middle;" />
  Bill's Claude Skills
</h1>

<p align="center">
  <b>⚡ Supercharge Claude Code with specialized workflows</b>
</p>

<p align="center">
  <a href="https://opensource.org/licenses/MIT">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT" />
  </a>
  <a href="https://claude.ai/code">
    <img src="https://img.shields.io/badge/Claude-Code-8B5CF6?logo=anthropic" alt="Claude Code" />
  </a>
  <img src="https://img.shields.io/badge/Skills-2-blue?logo=git&logoColor=white" alt="Skills" />
  <img src="https://img.shields.io/badge/Automation-GitHub_PR-green?logo=github&logoColor=white" alt="PR Automation" />
</p>

<p align="center">
  <b>🎯 Automate PR reviews</b> • <b>🌳 Git worktree workflows</b> • <b>🚀 Boost productivity</b>
</p>

</div>

<br />

## ⚡ Quick Start

```bash
# 1. Add the marketplace
/plugin marketplace add BillChirico/bills-claude-skills

# 2. Install a skill
/plugin install github-pr-resolver@bills-claude-skills

# 3. Authenticate with GitHub CLI
gh auth login

# 4. Use it!
/resolve-pr https://github.com/owner/repo/pull/123

# Or initialize a new workspace
/init-workspace feat user-auth
```

---

## 🤔 What are Claude Skills?

Skills are **structured prompts and documentation** that give Claude Code specialized knowledge for specific tasks. Think of them as expert plugins for your AI coding assistant.

<table>
<tr>
<td width="33%" align="center">

📚 **Workflow Docs**

Step-by-step instructions Claude follows

</td>
<td width="33%" align="center">

⚡ **Slash Commands**

Quick triggers for instant invocation

</td>
<td width="33%" align="center">

📖 **References**

API docs & patterns for complex tasks

</td>
</tr>
</table>

---

## 🛠️ Available Skills

### <img src="https://api.iconify.design/octicon:git-pull-request-16.svg" width="24" height="24" style="vertical-align: middle;" /> GitHub PR Resolver

**Automate PR review resolution** by processing comments, making fixes, and resolving threads.

<details>
<summary><b>✨ Capabilities</b></summary>

- 🔍 Fetch PR context (review threads, check statuses) via GitHub CLI
- 💬 Parse and apply code suggestions from reviewers
- ✅ Fix failing CI checks (lint, tests, build, formatting)
- 🔄 Resolve conversation threads via GitHub GraphQL API
- 📝 Commit changes using conventional commit format (one commit per fix)

</details>

<details>
<summary><b>🎯 Use Cases</b></summary>

- ✓ A PR has review comments that need addressing
- ✓ CI/CD checks are failing
- ✓ You want to quickly iterate on PR feedback

</details>

**[📖 View full documentation →](github-pr-resolver/SKILL.md)**

---

### <img src="https://api.iconify.design/octicon:git-branch-16.svg" width="24" height="24" style="vertical-align: middle;" /> Git Workspace Init

**Initialize isolated git worktrees** with proper branch naming following [conventional branch](https://conventional-branch.github.io/) conventions.

<details>
<summary><b>✨ Capabilities</b></summary>

- 🏷️ Generate branch names from task type and description
- 🌳 Create git worktrees for parallel development
- 🚀 Push new branches to remote with tracking
- 🎨 Support for all conventional types (feat, fix, hotfix, docs, refactor, etc.)

</details>

<details>
<summary><b>🎯 Use Cases</b></summary>

- ✓ Starting work on a new feature
- ✓ Beginning a bug fix or hotfix
- ✓ Creating an isolated workspace for any task
- ✓ Working on multiple branches simultaneously

</details>

**[📖 View full documentation →](git-workspace-init/SKILL.md)**

---

## 📦 Installation

### 📋 Prerequisites

<table>
<tr>
<td width="50%">

**Claude Code CLI**
```bash
# Install from claude.ai/code
```

</td>
<td width="50%">

**GitHub CLI**
```bash
gh auth login
```

</td>
</tr>
</table>

### 🎯 Option 1: Install via Plugin System (Recommended)

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

2. Copy skills to your Claude Code skills directory:
   ```bash
   # For personal skills (available in all projects)
   cp -r github-pr-resolver ~/.claude/skills/

   # Or for project-specific skills
   cp -r github-pr-resolver /path/to/your/project/.claude/skills/
   ```

### Environment Setup

Ensure GitHub CLI is authenticated:
```bash
# Check authentication status
gh auth status

# If not authenticated, run:
gh auth login
```

The token requires `repo` scope for full repository access.

## 🚀 Usage

### GitHub PR Resolver

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

---

## 🤝 Contributing

**Contributions are welcome!** Help make Claude Code even more powerful.

<details>
<summary><b>How to contribute a new skill</b></summary>

1. 🍴 Fork the repository
2. 🌿 Create a feature branch: `git checkout -b feat/my-new-skill`
3. ✍️ Add your skill following the structure above
4. 🧪 Test the skill with Claude Code
5. 🚀 Submit a pull request

</details>

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

<div align="center">

**Made with ❤️ by [Bill Chirico](https://github.com/BillChirico)**

*Star ⭐ this repo if you find it helpful!*

</div>
