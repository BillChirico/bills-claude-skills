---
name: github-pr-resolver
description: "Resolve GitHub PR review comments and fix failing CI checks. Creates todo list to track ALL threads across ALL pages, processes each with individual commits, marks each resolved immediately, and verifies all resolved + CI passing before completion."
---

# GitHub PR Resolver

Process **ALL** PR review comments, make fixes, resolve threads immediately, and ensure CI passes.

## Critical Rules

1. **Fetch ALL pages** - GitHub returns max 100 items per request. Always paginate until `hasNextPage: false`
2. **Track with todos** - Create a `TaskCreate` item for each unresolved thread before processing
3. **One commit per thread** - Never batch fixes into a single commit
4. **Resolve immediately** - Mark each thread resolved on GitHub RIGHT AFTER fixing it, not at the end
5. **CI must pass** - Task is NOT complete until all CI checks are green. Fix failures and retry.
6. **PARALLEL AGENTS (MANDATORY)** - You MUST spawn all agents in ONE message with MULTIPLE Task tool calls. Sequential messages = sequential execution (WRONG). Single message with multiple Tasks = parallel execution (CORRECT).

## API Access

**Prefer GitHub MCP when available**, fall back to `gh` CLI.

| Operation      | MCP Tool                                 | CLI Fallback              |
| -------------- | ---------------------------------------- | ------------------------- |
| Read PR        | `mcp__github__pull_request_read`         | `gh pr view`              |
| Resolve thread | `mcp__github__pull_request_review_write` | `gh api graphql` mutation |
| Check status   | Included in PR read                      | `gh pr checks`            |

## Workflow

### Step 1: Fetch ALL Threads (with Pagination)

```
1. Fetch PR details and review threads
2. Check hasNextPage - if true, fetch next page with cursor
3. Repeat until hasNextPage is false
4. Count total unresolved threads across ALL pages
```

**MCP:**

```
mcp__github__pull_request_read(owner, repo, pullNumber)
→ Check response for pagination, fetch additional pages if needed
```

**CLI (GraphQL):**

```bash
gh api graphql -f query='
query($owner: String!, $repo: String!, $prNumber: Int!, $cursor: String) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $prNumber) {
      reviewThreads(first: 100, after: $cursor) {
        pageInfo { hasNextPage, endCursor }
        nodes {
          id, isResolved, path, line
          comments(first: 10) { nodes { body, author { login } } }
        }
      }
    }
  }
}' -f owner=OWNER -f repo=REPO -F prNumber=NUMBER
```

### Step 2: Create Todo List

For each unresolved thread (`isResolved: false`), create a tracking item:

```
TaskCreate:
  subject: "[#] <path>:<line> - <summary> (@<author>)"
  description: |
    Thread ID: <id>
    Author: @<author>
    Link: https://github.com/<owner>/<repo>/pull/<prNumber>#discussion_r<commentId>
    Comment: <body>
  activeForm: "Resolving <path>:<line> (@<author>)"
```

**Building the comment link:**

- Extract `commentId` from the first comment's `id` field (the numeric portion after the last `/` or the `databaseId`)
- Format: `https://github.com/<owner>/<repo>/pull/<prNumber>#discussion_r<commentId>`

**GraphQL to get comment IDs:**

```bash
gh api graphql -f query='
query($owner: String!, $repo: String!, $prNumber: Int!, $cursor: String) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $prNumber) {
      reviewThreads(first: 100, after: $cursor) {
        pageInfo { hasNextPage, endCursor }
        nodes {
          id, isResolved, path, line
          comments(first: 1) {
            nodes {
              databaseId
              body
              author { login }
            }
          }
        }
      }
    }
  }
}' -f owner=OWNER -f repo=REPO -F prNumber=NUMBER
```

Verify with `TaskList` - count must match total unresolved from Step 1.

### Step 3: Process Threads in Parallel with Agents

> **CRITICAL: TRUE PARALLEL EXECUTION IS MANDATORY**
>
> You MUST spawn ALL agents in a **SINGLE message** with **MULTIPLE Task tool invocations**.
> If you call Task tools sequentially in separate messages, they run one-at-a-time (WRONG).
> Only by including multiple Task calls in ONE response do they execute concurrently (CORRECT).

**Workflow:**

```
1. Group threads by file (threads in the same file go to one agent)
2. Build ALL Task invocations for all file groups
3. SEND ALL TASK INVOCATIONS IN A SINGLE MESSAGE ← MANDATORY for parallelism
4. Each agent independently:
   a. TaskUpdate(taskId, status: "in_progress")
   b. Read file, make fix
   c. git add [file] && git commit -m "[type]([scope]): [description]"
   d. Resolve thread on GitHub immediately
   e. Verify isResolved: true
   f. TaskUpdate(taskId, status: "completed")
5. Monitor agents with TaskOutput, wait for all to complete
6. Handle any failures by re-processing those threads
```

**MANDATORY: Multiple Task Invocations in Single Message**

When you have 3 files to fix, you MUST send ONE message containing THREE Task tool invocations:

```
YOUR SINGLE RESPONSE MUST CONTAIN:
┌──────────────────────────────────────────────────────────────┐
│  Task #1: subagent_type="general-purpose"                    │
│           run_in_background=true                             │
│           description="Fix PR thread in src/utils.ts"        │
│           prompt="[agent instructions for file 1]"           │
├──────────────────────────────────────────────────────────────┤
│  Task #2: subagent_type="general-purpose"                    │
│           run_in_background=true                             │
│           description="Fix PR thread in src/api.ts"          │
│           prompt="[agent instructions for file 2]"           │
├──────────────────────────────────────────────────────────────┤
│  Task #3: subagent_type="general-purpose"                    │
│           run_in_background=true                             │
│           description="Fix PR thread in src/models.ts"       │
│           prompt="[agent instructions for file 3]"           │
└──────────────────────────────────────────────────────────────┘
```

**Agent prompt template:**

```
Fix PR review thread and resolve it.

Repository: [owner]/[repo]
PR Number: [prNumber]
Branch: [branch]

Thread Details:
- Todo ID: [taskId]
- Thread ID: [threadId]
- File: [path]
- Line: [line]
- Comment: [body]
- Author: @[author]

Instructions:
1. Mark todo as in_progress: TaskUpdate(taskId: "[taskId]", status: "in_progress")
2. Read the file and understand the context
3. Make the fix requested in the comment
4. Commit: git add [path] && git commit -m "[type]([scope]): [description]"
5. Resolve thread on GitHub using gh CLI:
   gh api graphql -f query='mutation { resolveReviewThread(input: {threadId: "[threadId]"}) { thread { isResolved } } }'
6. Verify resolution succeeded
7. Mark todo completed: TaskUpdate(taskId: "[taskId]", status: "completed")
8. Report success or failure
```

**Parallelization rules:**

- **ALL independent file agents MUST be spawned in ONE message** - This is the ONLY way to run them in parallel
- Threads in the same file: send to a single agent to avoid conflicts
- Each agent commits and resolves independently
- Use `run_in_background: true` for parallel execution
- Monitor with `TaskOutput(task_id, block: false)` to check progress

**WRONG (sequential - do NOT do this):**
```
Message 1: Task for file A
Message 2: Task for file B  ← waits for A to finish first
Message 3: Task for file C  ← waits for B to finish first
```

**CORRECT (parallel - do THIS):**
```
Message 1: Task for file A + Task for file B + Task for file C  ← all run concurrently
```

**Resolve thread (MCP):**

```
mcp__github__pull_request_review_write(owner, repo, pullNumber, threadId, action: "RESOLVE")
```

**Resolve thread (CLI):**

```bash
gh api graphql -f query='
mutation($threadId: ID!) {
  resolveReviewThread(input: {threadId: $threadId}) {
    thread { id, isResolved }
  }
}' -f threadId="<THREAD_ID>"
```

**Verify resolution succeeded:**

```bash
gh api graphql -f query='
query($threadId: ID!) {
  node(id: $threadId) {
    ... on PullRequestReviewThread { isResolved }
  }
}' -f threadId="<THREAD_ID>"
```

### Step 4: Monitor Agents and Push Changes

**Wait for all agents to complete:**

```
1. Collect all agent task_ids from Step 3
2. Poll each with TaskOutput(task_id, block: false) or wait with block: true
3. Check TaskList - all todos should be "completed"
4. If any agent failed, re-spawn for those threads
```

**Push all commits:**

```bash
git push origin $(gh pr view <PR> --json headRefName -q '.headRefName')
```

**Handle conflicts (rare with file-based grouping):**

```bash
# If push fails due to conflicts from parallel commits
git pull --rebase origin <branch>
git push origin <branch>
```

### Step 5: Wait for CI and Fix Failures

**This is a loop - repeat until all checks pass:**

```
1. Wait for CI checks to complete (not just "running")
2. Check status of ALL checks
3. If ANY check fails:
   a. Identify the failure (lint, test, build, types, etc.)
   b. Fix the issue
   c. Commit with appropriate message
   d. Push
   e. Go back to step 1
4. Only proceed when ALL checks show "success" or "skipped"
```

**Check CI status:**

```bash
# Wait for checks to complete (poll until no "pending" or "in_progress")
gh pr checks <PR> --watch

# Or check status directly
gh pr checks <PR> --json name,state,conclusion
```

**Fix patterns for common CI failures:**

```bash
# Lint failures
npm run lint -- --fix && git add . && git commit -m "fix(lint): resolve linting errors"

# Type errors
# Fix the type issues in code
git add . && git commit -m "fix(types): resolve TypeScript errors"

# Test failures
# Fix failing tests or update assertions
git add . && git commit -m "fix(tests): update failing test assertions"

# Build failures
# Fix build issues
git add . && git commit -m "fix(build): resolve build errors"
```

**After each fix, push and wait again:**

```bash
git push origin $(gh pr view <PR> --json headRefName -q '.headRefName')
# Then loop back: wait for CI, check results
```

### Step 6: Final Verification

Only proceed here when Step 5 confirms all CI checks pass.

**Verify ALL of the following:**

1. **Zero unresolved threads** - Re-fetch ALL pages (paginate until `hasNextPage: false`):

   ```bash
   gh api graphql -f query='...' # Same query as Step 1
   # Count threads where isResolved: false - must be 0
   ```

2. **All todos completed** - `TaskList` shows all items with status `completed`

3. **All CI checks passing**:
   ```bash
   gh pr checks <PR> --json name,conclusion | jq 'all(.conclusion == "success" or .conclusion == "skipped")'
   # Must return true
   ```

**If verification fails:**

- Unresolved threads remain → Go back to Step 3
- CI checks failing → Go back to Step 5
- Todos incomplete → Review what was missed

## Commit Convention

| Comment Pattern                 | Commit Type |
| ------------------------------- | ----------- |
| Bug fix, null check, validation | `fix`       |
| Add, implement, missing         | `feat`      |
| Rename, refactor, change X to Y | `refactor`  |
| Documentation, comments         | `docs`      |
| Performance                     | `perf`      |
| Style, formatting               | `style`     |

**Scope:** Extract from path - `src/services/User.ts` → `services`

## Completion Checklist

**The task is NOT complete until ALL boxes can be checked:**

- [ ] Fetched ALL pages (paginated until `hasNextPage: false`)
- [ ] Created todo for each unresolved thread
- [ ] Spawned agents for independent files in parallel (single message, multiple Task calls)
- [ ] All agents completed successfully (monitored via TaskOutput)
- [ ] Each thread was resolved on GitHub **immediately** after fixing
- [ ] All todos show `completed`
- [ ] Each thread has its own commit
- [ ] Changes pushed
- [ ] **ALL CI checks are passing** (success or skipped, no failures)
- [ ] Re-verified: zero unresolved threads across ALL pages
- [ ] Re-verified: CI status shows all green

**DO NOT mark task complete if CI is still running or failing. Wait and fix.**
