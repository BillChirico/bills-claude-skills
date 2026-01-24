---
name: github-pr-resolver
description: "Resolve GitHub PR review comments and fix failing CI checks. Creates todo list to track ALL threads across ALL pages, processes each with individual commits, and verifies zero unresolved remain."
---

# GitHub PR Resolver

Process **ALL** PR review comments, make fixes, resolve threads, and fix CI failures.

## Critical Rules

1. **Fetch ALL pages** - GitHub returns max 100 items per request. Always paginate until `hasNextPage: false`
2. **Track with todos** - Create a `TaskCreate` item for each unresolved thread before processing
3. **One commit per thread** - Never batch fixes into a single commit
4. **Verify after push** - Re-fetch ALL pages to confirm zero unresolved threads remain

## API Access

**Prefer GitHub MCP when available**, fall back to `gh` CLI.

| Operation | MCP Tool | CLI Fallback |
|-----------|----------|--------------|
| Read PR | `mcp__github__pull_request_read` | `gh pr view` |
| Resolve thread | `mcp__github__pull_request_review_write` | `gh api graphql` mutation |
| Check status | Included in PR read | `gh pr checks` |

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
  subject: "<path>:<line> - <summary>"
  description: "Thread ID: <id>\nAuthor: <author>\nComment: <body>"
  activeForm: "Resolving <path>:<line>"
```

Verify with `TaskList` - count must match total unresolved from Step 1.

### Step 3: Process Each Thread

For each todo item:

```
1. TaskUpdate(taskId, status: "in_progress")
2. Read file, make the fix
3. git add <file> && git commit -m "<type>(<scope>): <description>"
4. Resolve thread on GitHub (MCP or GraphQL mutation)
5. TaskUpdate(taskId, status: "completed")
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

### Step 4: Fix CI Failures

For each failing check, fix and commit separately:

```bash
# Lint
npm run lint -- --fix && git add . && git commit -m "fix(lint): resolve linting errors"

# Tests
# Fix failing tests
git add . && git commit -m "fix(tests): update failing assertions"

# Build/Types
# Fix errors
git add . && git commit -m "fix(build): resolve build errors"
```

### Step 5: Push

```bash
git push origin $(gh pr view <PR> --json headRefName -q '.headRefName')
```

### Step 6: Verify

Re-fetch ALL pages (same as Step 1) and confirm:
- Zero unresolved threads across ALL pages
- `TaskList` shows all items completed
- CI checks are running

**If any threads remain unresolved, go back to Step 3.**

## Commit Convention

| Comment Pattern | Commit Type |
|----------------|-------------|
| Bug fix, null check, validation | `fix` |
| Add, implement, missing | `feat` |
| Rename, refactor, change X to Y | `refactor` |
| Documentation, comments | `docs` |
| Performance | `perf` |
| Style, formatting | `style` |

**Scope:** Extract from path - `src/services/User.ts` → `services`

## Completion Checklist

- [ ] Fetched ALL pages (paginated until `hasNextPage: false`)
- [ ] Created todo for each unresolved thread
- [ ] All todos show `completed`
- [ ] Each thread has its own commit
- [ ] Changes pushed
- [ ] Re-verified: zero unresolved across ALL pages
