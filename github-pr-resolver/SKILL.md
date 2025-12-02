---
name: github-pr-resolver
description: "Automate GitHub pull request review resolution by processing ALL review comments and fixing ALL failing CI checks. Use when: (1) A PR has review comments that need to be addressed and resolved, (2) CI/CD checks are failing and need fixes, (3) You want to process all PR feedback and mark conversations as resolved, (4) You need to iterate on PR feedback quickly. IMPORTANT: This skill processes EVERY comment - no skipping allowed. Always fetches fresh data from GitHub. The only acceptable end state is zero unresolved threads."
---

# GitHub PR Resolver

Automate the process of addressing pull request review feedback by processing **ALL** comments, making code fixes, resolving **EVERY** conversation thread, and fixing **ALL** failing CI checks.

**This skill does NOT skip any comments. Every unresolved thread must be addressed and resolved.**

## Prerequisites

```bash
# Set environment variable
export GITHUB_TOKEN="your_personal_access_token"

# Install dependencies
pip install requests --break-system-packages
```

Token requires `repo` scope for full repository access.

## Workflow Overview

1. **Fetch PR context** → Get all review threads and check statuses (always fresh from GitHub)
2. **Process ALL unresolved threads** → Fix EVERY comment, **commit individually**, and resolve each one
3. **Fix ALL failing checks** → Address every failure, **commit per check type**
4. **Push changes** → Single push after all commits
5. **Verify** → Re-fetch from GitHub and confirm ALL threads resolved and ALL checks passing

**CRITICAL REQUIREMENTS:**
- **Always fetch fresh data from GitHub.** Never use cached or previously fetched context.
- **Process EVERY unresolved comment.** Do NOT skip any threads. Each comment must be addressed and resolved.
- **Zero unresolved threads** is the only acceptable end state.

## Commit Convention

Each change gets its own commit using conventional commit format:

```
<type>(<scope>): <description>
```

**Type inference from comment:**

| Comment Pattern | Commit Type |
|----------------|-------------|
| Bug fix, null check, error handling, validation | `fix` |
| Add, include, missing, implement | `feat` |
| Rename, refactor, suggestion, change X to Y | `refactor` |
| Documentation, comments, README | `docs` |
| Performance, optimize | `perf` |
| Style, indent, whitespace | `style` |

**Scope from file path:**
- Extract directory/module name: `src/services/UserService.ts` → `services`
- Skip common prefixes: `src`, `lib`, `app`
- Root files use filename: `index.ts` → `index`

**CI check commits:**
- Lint fixes → `fix(lint): resolve linting errors`
- Test fixes → `fix(tests): update failing assertions`
- Build/type errors → `fix(build): resolve build errors`
- Formatting → `style(format): apply formatting`

## Helper Functions

```python
import os
import re

def infer_commit_type(comment: str) -> str:
    """Infer conventional commit type from review comment."""
    comment_lower = comment.lower()

    if any(word in comment_lower for word in ["bug", "null", "error", "fix", "handle", "check", "validate"]):
        return "fix"
    if any(word in comment_lower for word in ["add", "include", "missing", "implement", "new"]):
        return "feat"
    if any(word in comment_lower for word in ["doc", "comment", "readme", "describe"]):
        return "docs"
    if any(word in comment_lower for word in ["perf", "optim", "slow", "fast"]):
        return "perf"
    if any(word in comment_lower for word in ["style", "indent", "whitespace", "format"]):
        return "style"
    # Default for renames, suggestions, general changes
    return "refactor"


def extract_scope(file_path: str) -> str:
    """Extract scope (directory/module) from file path."""
    dir_name = os.path.dirname(file_path)

    if not dir_name or dir_name == ".":
        # Root file - use filename without extension
        return os.path.splitext(os.path.basename(file_path))[0]

    # Get the most specific directory, skipping common prefixes
    parts = dir_name.replace("\\", "/").split("/")
    skip = {"src", "lib", "app", "packages"}

    for part in reversed(parts):
        if part and part not in skip:
            return part

    return parts[-1] if parts else "root"


def extract_suggestion(body: str) -> str | None:
    """Extract code from GitHub suggestion block."""
    pattern = r"```suggestion\n(.*?)```"
    match = re.search(pattern, body, re.DOTALL)
    return match.group(1).rstrip() if match else None
```

## Step 1: Fetch PR Context (Always Fresh)

**CRITICAL: Always call `get_full_pr_context()` to fetch fresh data from GitHub. Never reuse previously fetched context data.**

```python
from scripts.github_pr_client import get_full_pr_context

# Using PR URL - ALWAYS fetches fresh data from GitHub API
context = get_full_pr_context("https://github.com/owner/repo/pull/123")

# Or using PR number with repo - ALWAYS fetches fresh data
context = get_full_pr_context("123", repo="owner/repo")

# Access context data (freshly fetched)
pr = context["pr"]
unresolved = context["unresolved_threads"]
failing = context["failing_checks"]
client = context["client"]

print(f"PR #{pr.number}: {pr.title}")
print(f"Branch: {pr.head_ref}")
print(f"Unresolved threads: {len(unresolved)}")
print(f"Failing checks: {len(failing)}")
```

**Note:** Each call to `get_full_pr_context()` makes fresh API calls to GitHub. There is no caching - data is always retrieved live.

## Step 2: Process ALL Review Threads

**MANDATORY: Process EVERY unresolved thread. Do NOT skip any comments.**

For each unresolved thread (iterate through ALL of them):

### 2.1 Understand the Comment

Extract the first comment (thread initiator) and understand what's requested:

```python
for thread in unresolved:
    path = thread["path"]
    line = thread["line"]
    first_comment = thread["comments"][0]
    body = first_comment["body"]
    thread_id = thread["thread_id"]
    
    print(f"File: {path}:{line}")
    print(f"Comment: {body}")
```

### 2.2 Identify Fix Type

**ALL comments require action. Determine the appropriate fix:**

| Comment Pattern | Action Required |
|----------------|-----------------|
| Contains ` ```suggestion ` | Apply the suggested code directly |
| "Typo", "rename", "change X to Y" | Make the specific text change |
| "Add...", "Include...", "Missing..." | Add the requested code/content |
| "Remove...", "Delete..." | Remove the specified code |
| "Consider...", "Maybe...", "Nit:" | Apply the improvement (these are still requests) |
| Question or discussion | Address with code fix or reply, then resolve |

**No comment is optional. Every thread must be addressed and resolved.**

### 2.3 Apply Code Suggestions

For comments with explicit suggestions:

```python
import re

def extract_suggestion(body: str) -> str | None:
    """Extract code from suggestion block."""
    pattern = r"```suggestion\n(.*?)```"
    match = re.search(pattern, body, re.DOTALL)
    return match.group(1).rstrip() if match else None

suggestion = extract_suggestion(body)
if suggestion:
    # Apply the suggestion to the file at the specified line
    pass
```

### 2.4 Make the Fix

1. Open the file at `thread["path"]`
2. Navigate to line `thread["line"]`
3. Apply the required change
4. Save the file

### 2.5 Commit the Fix

After making each fix, commit it immediately with a conventional commit message:

```python
import subprocess

# Determine commit type and scope
commit_type = infer_commit_type(body)
scope = extract_scope(path)
description = "..."  # Generate concise description of the change

# Stage only the affected file
subprocess.run(["git", "add", path], check=True)

# Commit with conventional message
commit_msg = f"{commit_type}({scope}): {description}"
subprocess.run(["git", "commit", "-m", commit_msg], check=True)

print(f"📦 Committed: {commit_msg}")
```

**Example commits:**
- `refactor(services): rename getUser to fetchUser`
- `fix(auth): add null check for token`
- `feat(api): add retry logic per review`
- `docs(utils): add JSDoc for helper function`

### 2.6 Resolve the Thread

After committing:

```python
# Resolve via GraphQL
client.resolve_thread(thread_id)
print(f"✅ Resolved thread at {path}:{line}")
```

## Step 3: Fix Failing Checks

### 3.1 Analyze Failures

```python
for check in failing:
    print(f"❌ {check.name}: {check.conclusion}")
    if check.output_summary:
        print(f"   Summary: {check.output_summary}")
```

### 3.2 Common Check Fixes

**Linting (eslint, pylint, ruff):**
```bash
# JavaScript/TypeScript
npm run lint -- --fix
npx eslint . --fix

# Python
ruff check --fix .
black .
```

**Type Checking (tsc, mypy, pyright):**
- Fix type errors shown in check output
- Add missing type annotations
- Update incorrect types

**Tests (jest, pytest, vitest):**
- Read test output to identify failures
- Fix the failing test or the implementation
- Update snapshots if needed: `npm test -- -u`

**Formatting (prettier, black):**
```bash
npx prettier --write .
black .
```

**Build (webpack, vite, tsc):**
- Fix syntax errors
- Resolve import issues
- Ensure dependencies are installed

### 3.3 Commit Each Check Fix

After fixing each check type, commit separately:

```python
import subprocess

# After fixing lint errors
subprocess.run(["git", "add", "."], check=True)
subprocess.run(["git", "commit", "-m", "fix(lint): resolve linting errors"], check=True)

# After fixing test failures
subprocess.run(["git", "add", "."], check=True)
subprocess.run(["git", "commit", "-m", "fix(tests): update failing assertions"], check=True)

# After fixing build/type errors
subprocess.run(["git", "add", "."], check=True)
subprocess.run(["git", "commit", "-m", "fix(build): resolve build errors"], check=True)

# After fixing formatting
subprocess.run(["git", "add", "."], check=True)
subprocess.run(["git", "commit", "-m", "style(format): apply formatting"], check=True)
```

### 3.4 Re-run Checks Locally

Before pushing, verify fixes locally:

```bash
# Run the same commands CI runs
npm run lint
npm run test
npm run build
```

## Step 4: Push All Commits

After all review threads and CI checks have been addressed with individual commits, push once:

```bash
# Push all commits to PR branch
git push origin {branch_name}
```

This triggers a single CI run for all changes rather than multiple runs per commit.

## Step 5: Verify Resolution (Always Re-fetch)

After pushing, the PR will update. **ALWAYS fetch fresh data from GitHub to verify** - never rely on previously fetched context:

1. **ALL threads show as resolved** (zero unresolved remaining)
2. CI checks are re-running
3. No new failures introduced

```python
# ALWAYS re-fetch fresh context from GitHub to verify current state
context = get_full_pr_context(pr_url)  # Fresh API call, not cached
unresolved_count = len(context['unresolved_threads'])
failing_count = len(context['failing_checks'])

print(f"Remaining unresolved: {unresolved_count}")
print(f"Remaining failures: {failing_count}")

# CRITICAL: If any threads remain unresolved, go back and fix them
if unresolved_count > 0:
    print("⚠️  INCOMPLETE: Still have unresolved threads. Must process ALL of them.")
    # Go back to Step 2 and process remaining threads
```

**IMPORTANT:**
- Verification MUST use a fresh `get_full_pr_context()` call to ensure you see the actual current state on GitHub.
- **If ANY unresolved threads remain, the task is NOT complete.** Go back and process them.
- The only acceptable end state is **zero unresolved threads**.

## Complete Example

```python
from scripts.github_pr_client import get_full_pr_context
import subprocess
import os

def infer_commit_type(comment: str) -> str:
    """Infer conventional commit type from review comment."""
    comment_lower = comment.lower()

    if any(word in comment_lower for word in ["bug", "null", "error", "fix", "handle", "check", "validate"]):
        return "fix"
    if any(word in comment_lower for word in ["add", "include", "missing", "implement", "new"]):
        return "feat"
    if any(word in comment_lower for word in ["doc", "comment", "readme", "describe"]):
        return "docs"
    if any(word in comment_lower for word in ["perf", "optim", "slow", "fast"]):
        return "perf"
    if any(word in comment_lower for word in ["style", "indent", "whitespace", "format"]):
        return "style"
    return "refactor"


def extract_scope(file_path: str) -> str:
    """Extract scope (directory/module) from file path."""
    dir_name = os.path.dirname(file_path)

    if not dir_name or dir_name == ".":
        return os.path.splitext(os.path.basename(file_path))[0]

    parts = dir_name.replace("\\", "/").split("/")
    skip = {"src", "lib", "app", "packages"}

    for part in reversed(parts):
        if part and part not in skip:
            return part

    return parts[-1] if parts else "root"


def resolve_pr(pr_url: str):
    """Complete workflow to resolve ALL PR feedback with per-change commits.

    IMPORTANT: This function processes EVERY unresolved thread. No comments are skipped.
    """

    # 1. Fetch FRESH context from GitHub (always live, never cached)
    ctx = get_full_pr_context(pr_url)  # Makes fresh API calls
    pr = ctx["pr"]
    client = ctx["client"]
    repo = ctx["repo"]

    total_threads = len(ctx["unresolved_threads"])
    print(f"Processing PR #{pr.number}: {pr.title}")
    print(f"Found {total_threads} unresolved threads - will process ALL of them")

    # 2. Checkout PR branch
    subprocess.run(["git", "fetch", "origin", pr.head_ref], check=True)
    subprocess.run(["git", "checkout", pr.head_ref], check=True)

    # 3. Process EVERY unresolved thread (one commit per thread) - NO SKIPPING
    processed_count = 0
    for thread in ctx["unresolved_threads"]:
        processed_count += 1
        path = thread["path"]
        line = thread["line"]
        comment = thread["comments"][0]["body"]

        print(f"\n📝 Processing thread {processed_count}/{total_threads}: {path}:{line}")
        print(f"   Comment: {comment[:100]}...")

        # TODO: Analyze comment and make fix
        # ... (Claude will do this interactively)

        # Commit this specific change
        commit_type = infer_commit_type(comment)
        scope = extract_scope(path)
        description = "..."  # Claude generates contextually

        subprocess.run(["git", "add", path], check=True)
        commit_msg = f"{commit_type}({scope}): {description}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        print(f"   📦 Committed: {commit_msg}")

        # Resolve the thread
        client.resolve_thread(thread["thread_id"])
        print(f"   ✅ Resolved ({processed_count}/{total_threads})")

    print(f"\n✅ Processed all {processed_count} threads")

    # 4. Fix failing checks (one commit per check type)
    lint_fixed = False
    test_fixed = False
    build_fixed = False

    for check in ctx["failing_checks"]:
        print(f"\n🔧 Fixing: {check.name}")

        if "lint" in check.name.lower() and not lint_fixed:
            subprocess.run(["npm", "run", "lint", "--", "--fix"], check=False)
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", "fix(lint): resolve linting errors"], check=True)
            lint_fixed = True

        elif "test" in check.name.lower() and not test_fixed:
            # ... fix tests ...
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", "fix(tests): update failing assertions"], check=True)
            test_fixed = True

        elif ("build" in check.name.lower() or "type" in check.name.lower()) and not build_fixed:
            # ... fix build ...
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", "fix(build): resolve build errors"], check=True)
            build_fixed = True

    # 5. Run local validation
    subprocess.run(["npm", "run", "lint"], check=False)
    subprocess.run(["npm", "run", "test"], check=False)
    subprocess.run(["npm", "run", "build"], check=False)

    # 6. Push all commits at once
    subprocess.run(["git", "push", "origin", pr.head_ref], check=True)

    # 7. VERIFY: Re-fetch and confirm zero unresolved threads
    print("\n🔍 Verifying all threads are resolved...")
    ctx = get_full_pr_context(pr_url)  # Fresh fetch to verify
    remaining = len(ctx["unresolved_threads"])

    if remaining > 0:
        print(f"⚠️  WARNING: {remaining} threads still unresolved!")
        print("Must go back and process remaining threads.")
        # Recursively process any remaining threads
        return resolve_pr(pr_url)

    print(f"\n✅ PR updated successfully! All {total_threads} threads resolved.")
```

## Reference

See `references/github_api_reference.md` for:
- Detailed comment intent patterns
- CI check types and common fixes
- API rate limits and error handling
- Git workflow best practices
