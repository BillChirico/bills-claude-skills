---
name: github-pr-resolver
description: "Automate GitHub pull request review resolution by processing ALL review comments and fixing ALL failing CI checks. Use when: (1) A PR has review comments that need to be addressed and resolved, (2) CI/CD checks are failing and need fixes, (3) You want to process all PR feedback and mark conversations as resolved, (4) You need to iterate on PR feedback quickly. IMPORTANT: This skill processes EVERY comment - no skipping allowed. Always fetches fresh data from GitHub. The only acceptable end state is zero unresolved threads. COMMIT CADENCE: Each thread gets its own commit (fix → commit → resolve → next). Never batch commits at the end."
---

# GitHub PR Resolver

Automate the process of addressing pull request review feedback by processing **ALL** comments, making code fixes, resolving **EVERY** conversation thread, and fixing **ALL** failing CI checks.

**This skill does NOT skip any comments. Every unresolved thread must be addressed and resolved.**

## GitHub API Access

This skill supports two methods for interacting with GitHub. **Prefer MCP when available.**

### Option 1: GitHub MCP Server (Preferred)

When the GitHub MCP server (`mcp__github__*` tools) is available, use it for all GitHub operations. MCP provides structured data and better error handling.

**Check availability:** Look for tools like `mcp__github__pull_request_read` in your available tools.

**Key MCP tools for this workflow:**
- `mcp__github__pull_request_read` - Get PR details, reviews, and comments
- `mcp__github__pull_request_review_write` - Submit reviews and resolve threads
- `mcp__github__list_commits` - List commits on a branch
- `mcp__github__get_file_contents` - Read file contents from the repo

### Option 2: GitHub CLI (Fallback)

When MCP is not available, fall back to the `gh` CLI.

```bash
# Verify gh CLI is installed and authenticated
gh auth status

# If not authenticated, run:
gh auth login
```

Token requires `repo` scope for full repository access.

## ⚠️ PAGINATION REQUIREMENT (NON-NEGOTIABLE)

**PRs almost always have multiple pages of review threads.** GitHub's API returns max 100 items per request.

**YOU MUST:**
1. **Always check for additional pages** - Look for `hasNextPage: true` or pagination indicators
2. **Fetch ALL pages** before processing ANY threads
3. **Verify ALL pages** after resolution - re-fetch with pagination to confirm zero unresolved
4. **Never assume page 1 is complete** - PRs with active reviews typically have 2+ pages

**The task is NOT complete until:**
- ✅ ALL pages have been fetched (not just page 1)
- ✅ ALL unresolved threads from ALL pages have been processed
- ✅ Re-verification with pagination confirms zero unresolved threads across ALL pages

**Using MCP:** Check if the response includes pagination info. If `hasNextPage` is true or there's a cursor/page token, you MUST fetch subsequent pages.

**Using CLI:** Always loop until `hasNextPage` is `false`. See pagination examples below.

## Workflow Overview

1. **Fetch ALL PR context** → Get ALL review threads (ALL pages) and check statuses
2. **Create todo list** → Use `TaskCreate` to create a todo item for EACH unresolved thread
3. **Process ALL unresolved threads** → For EACH todo: fix → commit → resolve → mark complete
4. **Fix ALL failing checks** → Address every failure, **commit per check type**
5. **Push changes** → Single push after all commits
6. **Verify** → Re-fetch from GitHub (ALL pages) and confirm ALL threads resolved

**COMMIT CADENCE (NON-NEGOTIABLE):**
- **Each review thread** = 1 commit (fix → `git add` → `git commit` → resolve thread → next thread)
- **Each CI check type** = 1 commit (lint fixes, test fixes, build fixes are separate commits)
- **NEVER batch all changes into a single commit at the end**

**CRITICAL REQUIREMENTS:**
- **Always fetch fresh data from GitHub.** Never use cached or previously fetched context.
- **Process EVERY unresolved comment.** Do NOT skip any threads. Each comment must be addressed and resolved.
- **Zero unresolved threads** is the only acceptable end state.
- **⚠️ PAGINATION IS MANDATORY:** PRs typically have MULTIPLE PAGES of comments. You MUST fetch ALL pages before considering threads complete. The task is NOT done until you have verified ALL pages have zero unresolved threads.

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

## Step 1: Fetch PR Context (Always Fresh)

**CRITICAL: Always fetch fresh data from GitHub. Never reuse previously fetched context data.**

### 1.1 Get PR Details

**Using MCP (preferred):**
```
Use mcp__github__pull_request_read with:
- owner: repository owner
- repo: repository name
- pullNumber: PR number
```

This returns PR metadata including title, state, head/base branches, author, and URL.

**Using CLI (fallback):**
```bash
gh pr view <PR_NUMBER> --json number,title,state,headRefName,baseRefName,author,url
```

### 1.2 Get Review Threads (ALL PAGES)

**⚠️ CRITICAL: You MUST fetch ALL pages of review threads, not just the first page.**

**Using MCP (preferred):**
```
Use mcp__github__pull_request_read with:
- owner: repository owner
- repo: repository name
- pullNumber: PR number

The response includes review threads with:
- Thread ID for resolution
- isResolved status
- File path and line number
- All comments in the thread

⚠️ CHECK FOR PAGINATION: If the response includes:
- hasNextPage: true
- A cursor or page token
- Truncation indicators

You MUST make additional requests to fetch ALL pages.
Count total threads across ALL pages before proceeding.
```

**Using CLI (fallback - GraphQL with Pagination):**

Use GraphQL to fetch review threads with resolution status. **The API returns max 100 items per request, so pagination is required for PRs with many threads.**

```bash
# First page (no cursor)
gh api graphql -f query='
query($owner: String!, $repo: String!, $prNumber: Int!, $cursor: String) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $prNumber) {
      reviewThreads(first: 100, after: $cursor) {
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          id
          isResolved
          isOutdated
          path
          line
          comments(first: 100) {
            nodes {
              id
              databaseId
              body
              author { login }
              createdAt
              path
              line
              diffHunk
            }
          }
        }
      }
    }
  }
}' -f owner=OWNER -f repo=REPO -F prNumber=PR_NUMBER
```

**Handling pagination (CLI only):**

```bash
# Check if more pages exist
HAS_NEXT=$(echo "$RESULT" | jq '.data.repository.pullRequest.reviewThreads.pageInfo.hasNextPage')
END_CURSOR=$(echo "$RESULT" | jq -r '.data.repository.pullRequest.reviewThreads.pageInfo.endCursor')

# If hasNextPage is true, fetch next page with cursor
if [ "$HAS_NEXT" = "true" ]; then
  gh api graphql -f query='...' -f owner=OWNER -f repo=REPO -F prNumber=PR_NUMBER -f cursor="$END_CURSOR"
fi
```

**IMPORTANT: Continue fetching pages until `hasNextPage` is `false`. Collect ALL threads before processing.**

### 1.3 Get Check Status

**Using MCP (preferred):**
```
Use mcp__github__pull_request_read - check statuses are included in the PR response.
```

**Using CLI (fallback):**
```bash
# Get all checks for the PR
gh pr checks <PR_NUMBER>

# For detailed check information
gh pr checks <PR_NUMBER> --json name,state,conclusion,description
```

### 1.4 Parse the Context

After fetching, identify:
- **Unresolved threads**: Where `isResolved: false`
- **Failing checks**: Where `conclusion` is `failure`, `cancelled`, `timed_out`, or `action_required`

**Using CLI to count (if needed):**
```bash
# Count unresolved threads
echo "Unresolved threads: $(echo "$THREADS_JSON" | jq '[.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == false)] | length')"

# List failing checks
gh pr checks <PR_NUMBER> --json name,conclusion | jq '.[] | select(.conclusion == "failure")'
```

## Step 2: Create Todo List for ALL Threads

**MANDATORY: Before processing ANY thread, create a todo item for EACH unresolved thread.**

This ensures no thread is missed and provides clear progress tracking.

### 2.1 Extract All Unresolved Threads

After fetching ALL pages in Step 1, compile a list of all unresolved threads:

```
For each thread where isResolved == false:
- Thread ID (for resolution)
- File path
- Line number
- First comment body (summary of what's requested)
- Comment author
```

### 2.2 Create Todo Items with TaskCreate

Use the `TaskCreate` tool to create a todo item for EACH unresolved thread:

```
For each unresolved thread, call TaskCreate with:
- subject: "<file_path>:<line> - <brief_summary>"
- description: Full comment body, thread ID, author
- activeForm: "Resolving <file_path>:<line>"
```

**Example todo items:**
```
TaskCreate:
  subject: "src/auth/login.ts:42 - Add null check for token"
  description: |
    Thread ID: PRRT_xxx
    Author: @reviewer
    Comment: "We should add a null check here before accessing token.value"
    File: src/auth/login.ts
    Line: 42
  activeForm: "Resolving src/auth/login.ts:42"

TaskCreate:
  subject: "src/api/client.ts:156 - Rename method per suggestion"
  description: |
    Thread ID: PRRT_yyy
    Author: @reviewer
    Comment: "```suggestion\nconst fetchUserData = async () => {\n```"
    File: src/api/client.ts
    Line: 156
  activeForm: "Resolving src/api/client.ts:156"
```

### 2.3 Verify Todo List Completeness

After creating all todos:
1. Call `TaskList` to see all created items
2. Verify count matches the total unresolved threads from Step 1
3. If counts don't match, you missed threads - go back and add them

**The todo list is your source of truth. Every unresolved thread MUST have a corresponding todo item.**

## Step 3: Process ALL Review Threads

**MANDATORY: Process EVERY todo item. Do NOT skip any.**

### 3.0 Processing Loop

For each todo item in your TaskList:
1. Call `TaskUpdate` to set status to `in_progress`
2. Read the thread details from the todo description
3. Make the fix (Steps 3.1-3.4)
4. Commit the fix (Step 3.5)
5. Resolve the thread on GitHub (Step 3.6)
6. Call `TaskUpdate` to set status to `completed`
7. Move to next todo item

### 3.1 Understand the Comment

Use the thread details stored in the todo item:
- File path
- Line number
- Comment body (what's requested)
- Thread ID (for resolution)

### 3.2 Identify Fix Type

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

### 3.3 Apply Code Suggestions

For comments with explicit suggestions, extract and apply:

```bash
# Suggestion blocks look like:
# ```suggestion
# replacement code here
# ```

# Extract suggestion content and apply to the file at the specified line
```

### 3.4 Make the Fix

1. Open the file at `path`
2. Navigate to `line`
3. Apply the required change
4. Save the file

### 3.5 Commit the Fix (IMMEDIATELY - DO NOT BATCH)

**CRITICAL: Commit IMMEDIATELY after EACH fix. Do NOT wait until the end. Do NOT batch commits.**

After making each fix, commit it immediately with a conventional commit message:

```bash
# Stage only the affected file
git add <path>

# Commit with conventional message
git commit -m "<type>(<scope>): <description>"
```

**Example commits:**
- `refactor(services): rename getUser to fetchUser`
- `fix(auth): add null check for token`
- `feat(api): add retry logic per review`
- `docs(utils): add JSDoc for helper function`

### 3.6 Resolve the Thread

After committing, resolve the thread.

**Using MCP (preferred):**
```
Use mcp__github__pull_request_review_write with:
- owner: repository owner
- repo: repository name
- pullNumber: PR number
- threadId: the thread's GraphQL ID
- action: "RESOLVE"
```

**Using CLI (fallback):**
```bash
gh api graphql -f query='
mutation($threadId: ID!) {
  resolveReviewThread(input: {threadId: $threadId}) {
    thread {
      id
      isResolved
    }
  }
}' -f threadId="<THREAD_ID>"
```

### 3.7 Mark Todo Complete

After resolving the thread on GitHub:

```
Call TaskUpdate with:
- taskId: the todo item's ID
- status: "completed"
```

### 3.8 Continue Until All Todos Complete

1. Call `TaskList` to see remaining items
2. Pick the next `pending` todo item
3. Repeat Steps 3.0-3.7

**Do NOT move to Step 4 until:**
- ALL todo items show status `completed`
- `TaskList` shows zero pending items for review threads

## Step 4: Fix Failing Checks

### 4.1 Analyze Failures

```bash
# List all failing checks
gh pr checks <PR_NUMBER> --json name,state,conclusion,description | jq '.[] | select(.conclusion == "failure")'

# View workflow run logs for details
gh run view <RUN_ID> --log-failed
```

### 4.2 Common Check Fixes

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

### 4.3 Commit Each Check Fix

After fixing each check type, commit separately:

```bash
# After fixing lint errors
git add .
git commit -m "fix(lint): resolve linting errors"

# After fixing test failures
git add .
git commit -m "fix(tests): update failing assertions"

# After fixing build/type errors
git add .
git commit -m "fix(build): resolve build errors"

# After fixing formatting
git add .
git commit -m "style(format): apply formatting"
```

### 4.4 Re-run Checks Locally

Before pushing, verify fixes locally:

```bash
# Run the same commands CI runs
npm run lint
npm run test
npm run build
```

## Step 5: Push All Commits

After all review threads and CI checks have been addressed with individual commits, push once:

```bash
# Get the branch name
BRANCH=$(gh pr view <PR_NUMBER> --json headRefName -q '.headRefName')

# Push all commits to PR branch
git push origin $BRANCH
```

This triggers a single CI run for all changes rather than multiple runs per commit.

## Step 6: Verify Resolution (Always Re-fetch ALL PAGES)

After pushing, **ALWAYS fetch fresh data from GitHub to verify** - never rely on previously fetched context.

**⚠️ VERIFICATION MUST CHECK ALL PAGES - NOT JUST PAGE 1**

### Verification Checklist

- [ ] Fetched page 1 of review threads
- [ ] Checked `hasNextPage` - if true, fetched page 2
- [ ] Continued fetching until `hasNextPage` is false
- [ ] Counted unresolved threads across ALL pages combined
- [ ] Confirmed total unresolved = 0
- [ ] CI checks are re-running

**Using MCP (preferred):**
```
Use mcp__github__pull_request_read again with:
- owner: repository owner
- repo: repository name
- pullNumber: PR number

⚠️ CHECK FOR PAGINATION in the response!
If hasNextPage is true, fetch the next page.
Continue until ALL pages are fetched.

Count threads where isResolved is false across ALL pages.
Must be zero across ALL pages combined.
```

**Using CLI (fallback):**
```bash
# Re-fetch ALL threads with pagination loop
ALL_THREADS="[]"
CURSOR=""

while true; do
  RESULT=$(gh api graphql -f query='
  query($owner: String!, $repo: String!, $prNumber: Int!, $cursor: String) {
    repository(owner: $owner, name: $repo) {
      pullRequest(number: $prNumber) {
        reviewThreads(first: 100, after: $cursor) {
          pageInfo {
            hasNextPage
            endCursor
          }
          nodes {
            id
            isResolved
          }
        }
      }
    }
  }' -f owner=OWNER -f repo=REPO -F prNumber=PR_NUMBER ${CURSOR:+-f cursor=$CURSOR})

  # Append threads from this page
  PAGE_THREADS=$(echo $RESULT | jq '.data.repository.pullRequest.reviewThreads.nodes')
  ALL_THREADS=$(echo "$ALL_THREADS $PAGE_THREADS" | jq -s 'add')

  # Check for next page - MUST continue if hasNextPage is true
  HAS_NEXT=$(echo $RESULT | jq -r '.data.repository.pullRequest.reviewThreads.pageInfo.hasNextPage')
  if [ "$HAS_NEXT" != "true" ]; then
    break
  fi
  CURSOR=$(echo $RESULT | jq -r '.data.repository.pullRequest.reviewThreads.pageInfo.endCursor')
  echo "Fetching next page (cursor: $CURSOR)..."
done

# Count unresolved across ALL pages
TOTAL=$(echo $ALL_THREADS | jq 'length')
UNRESOLVED=$(echo $ALL_THREADS | jq '[.[] | select(.isResolved == false)] | length')
echo "Total threads (all pages): $TOTAL"
echo "Remaining unresolved: $UNRESOLVED"

# Check CI status
gh pr checks <PR_NUMBER>
```

**IMPORTANT:**
- Verification MUST use fresh API calls to ensure you see the actual current state on GitHub.
- **Verification MUST fetch ALL pages** - checking only page 1 is NOT sufficient.
- **If ANY unresolved threads remain on ANY page, the task is NOT complete.** Go back and process them.
- The only acceptable end state is **zero unresolved threads across ALL pages**.

## Complete Example

**Note:** The todo list tracking (Step 2) is done using Claude's `TaskCreate`, `TaskUpdate`, and `TaskList` tools - not bash commands. The bash script below shows the GitHub API and git operations.

```bash
#!/bin/bash
# Complete workflow to resolve ALL PR feedback

PR_NUMBER=$1
REPO="owner/repo"  # Or extract from current git remote
OWNER=${REPO%/*}
REPO_NAME=${REPO#*/}

# 1. Fetch fresh context from GitHub
echo "Fetching PR #$PR_NUMBER..."
PR_INFO=$(gh pr view $PR_NUMBER --json number,title,headRefName,baseRefName)
BRANCH=$(echo $PR_INFO | jq -r '.headRefName')
echo "PR: $(echo $PR_INFO | jq -r '.title')"
echo "Branch: $BRANCH"

# Fetch ALL review threads with pagination
ALL_THREADS="[]"
CURSOR=""

while true; do
  if [ -z "$CURSOR" ]; then
    CURSOR_ARG=""
  else
    CURSOR_ARG="-f cursor=$CURSOR"
  fi

  RESULT=$(gh api graphql -f query='
query($owner: String!, $repo: String!, $prNumber: Int!, $cursor: String) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $prNumber) {
      reviewThreads(first: 100, after: $cursor) {
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          id
          isResolved
          path
          line
          comments(first: 100) {
            nodes {
              body
              author { login }
            }
          }
        }
      }
    }
  }
}' -f owner=$OWNER -f repo=$REPO_NAME -F prNumber=$PR_NUMBER $CURSOR_ARG)

  # Append threads from this page
  PAGE_THREADS=$(echo $RESULT | jq '.data.repository.pullRequest.reviewThreads.nodes')
  ALL_THREADS=$(echo "$ALL_THREADS $PAGE_THREADS" | jq -s 'add')

  # Check for next page
  HAS_NEXT=$(echo $RESULT | jq -r '.data.repository.pullRequest.reviewThreads.pageInfo.hasNextPage')
  if [ "$HAS_NEXT" != "true" ]; then
    break
  fi
  CURSOR=$(echo $RESULT | jq -r '.data.repository.pullRequest.reviewThreads.pageInfo.endCursor')
done

UNRESOLVED_COUNT=$(echo $ALL_THREADS | jq '[.[] | select(.isResolved == false)] | length')
TOTAL_COUNT=$(echo $ALL_THREADS | jq 'length')
echo "Total threads: $TOTAL_COUNT"
echo "Unresolved threads: $UNRESOLVED_COUNT"

# 2. Checkout PR branch
git fetch origin $BRANCH
git checkout $BRANCH

# 3. Process EACH unresolved thread (Claude does this interactively)
# For each thread:
#   - Read the comment
#   - Make the fix
#   - git add <file>
#   - git commit -m "<type>(<scope>): <description>"
#   - gh api graphql ... resolve mutation
#   - Move to next thread

# 4. Fix failing checks (one commit per check type)
gh pr checks $PR_NUMBER --json name,conclusion | jq '.[] | select(.conclusion == "failure")'
# Fix each failing check type and commit separately

# 5. Push all commits
git push origin $BRANCH

# 6. Verify - re-fetch ALL pages and confirm zero unresolved
# (Use same pagination loop as above)
if [ "$REMAINING" -gt 0 ]; then
    echo "⚠️  WARNING: $REMAINING threads still unresolved!"
    echo "Must go back and process remaining threads."
else
    echo "✅ All threads resolved!"
fi
```

## Completion Criteria

**The task is NOT complete until ALL of the following are true:**

| Criterion | Verification |
|-----------|--------------|
| ✅ All pages fetched | Continued pagination until `hasNextPage` is `false` |
| ✅ Todo list created | `TaskCreate` called for EACH unresolved thread |
| ✅ All todos completed | `TaskList` shows zero pending items |
| ✅ Zero unresolved threads | Counted across ALL pages, not just page 1 |
| ✅ Each thread committed | One commit per resolved thread |
| ✅ Changes pushed | `git push` completed successfully |
| ✅ Re-verified with fresh fetch | Fresh API call (with pagination) confirms zero unresolved |

**Common mistakes that make the task INCOMPLETE:**
- ❌ Only checking page 1 of review threads
- ❌ Not creating a todo list to track all threads
- ❌ Assuming MCP returns all threads without checking pagination
- ❌ Not re-fetching after push to verify resolution
- ❌ Batching all fixes into one commit instead of per-thread
- ❌ Skipping "nit" or "consider" comments (these still require resolution)

## Reference

See `references/github_api_reference.md` for:
- Detailed comment intent patterns
- CI check types and common fixes
- API rate limits and error handling
- Git workflow best practices
