# GitHub PR Review Resolution Reference

## Understanding Review Comments

### Comment Types

**Inline comments**: Attached to specific lines in files
- Have `path` and `line` properties
- Include `diff_hunk` showing surrounding context
- May be part of a thread with multiple replies

**General comments**: Top-level review comments
- Not attached to specific code lines
- Often contain overall review feedback

**Suggested changes**: Comments with code suggestions
```markdown
```suggestion
// Fixed code here
```​
```

### Parsing Comment Intent

Common patterns to identify what needs fixing:

| Pattern | Intent | Action |
|---------|--------|--------|
| "Typo in..." | Spelling/grammar fix | Correct the typo |
| "Rename to..." | Variable/function rename | Rename as specified |
| "Missing..." | Something needs to be added | Add the missing element |
| "Remove..." | Something should be deleted | Remove the specified code |
| "Consider..." | Suggestion, not required | Evaluate and apply if appropriate |
| "Nit:" | Minor style issue | Fix the style issue |
| "LGTM" | Approved, no changes | No action needed |
| Code block in comment | Suggested replacement | Apply the suggested code |

### Extracting Suggestions

When a comment contains a suggestion block:

```python
import re

def extract_suggestion(comment_body: str) -> str | None:
    """Extract code from a suggestion block."""
    pattern = r"```suggestion\n(.*?)```"
    match = re.search(pattern, comment_body, re.DOTALL)
    if match:
        return match.group(1).rstrip()
    return None
```

## Understanding Check Failures

### Common CI/CD Checks

| Check Name Pattern | Type | Common Fixes |
|-------------------|------|--------------|
| `lint`, `eslint`, `pylint` | Linting | Format code, fix style issues |
| `test`, `jest`, `pytest` | Tests | Fix failing tests, update snapshots |
| `build`, `compile` | Build | Fix compilation errors |
| `typecheck`, `tsc` | Type checking | Fix type errors |
| `coverage` | Code coverage | Add more tests |
| `security`, `codeql` | Security | Fix vulnerabilities |
| `format`, `prettier` | Formatting | Run formatter |

### Interpreting Check Output

Check run output typically contains:
- `output.title`: Brief summary of result
- `output.summary`: Detailed description with error counts
- `output.annotations`: Specific file/line issues

### Common Fix Patterns

**Linting failures:**
```bash
# Run the project's linter with auto-fix
npm run lint -- --fix
# or
ruff check --fix .
```

**Test failures:**
1. Read test output to identify failing tests
2. Check if failure is in test or implementation
3. Fix the root cause
4. Re-run tests to verify

**Type errors:**
1. Identify missing types or incorrect types
2. Add proper type annotations
3. Update function signatures

**Build failures:**
1. Check for syntax errors
2. Verify import paths
3. Ensure all dependencies are installed

## Thread Resolution Workflow

### GraphQL Thread Structure

Threads contain:
- `id`: GraphQL node ID for mutations
- `isResolved`: Boolean indicating resolution status
- `path`: File path
- `line`: Line number
- `comments`: Array of comments in thread

### Resolution Best Practice

1. **Address the comment**: Make the requested change
2. **Reply (optional)**: Add a reply explaining what was done
3. **Resolve**: Call the resolve mutation
4. **Push**: Commit and push the changes

### Resolution Order

Process threads in this order:
1. Threads with explicit code suggestions
2. Threads requesting specific changes
3. Discussion threads (may not need code changes)
4. Outdated threads (may already be fixed)

## Git Workflow for PR Updates

### Fetching PR Branch

```bash
# Fetch the PR branch
git fetch origin pull/{pr_number}/head:{local_branch_name}
git checkout {local_branch_name}
```

### Pushing Fixes

```bash
# Stage changes
git add .

# Commit with meaningful message
git commit -m "fix: address review feedback

- Fixed typo in function name
- Added missing null check
- Updated type annotations"

# Push to the PR branch
git push origin {branch_name}
```

### Force Push Considerations

After rebasing or amending:
```bash
git push origin {branch_name} --force-with-lease
```

## API Rate Limits

GitHub API has rate limits:
- Authenticated: 5000 requests/hour
- GraphQL: 5000 points/hour (some queries cost more)

### Efficient API Usage

1. Use GraphQL for fetching threads (single request vs multiple)
2. Batch operations where possible
3. Cache responses when appropriate
4. Check `X-RateLimit-Remaining` header

## Error Handling

### Common Errors

| Status | Meaning | Resolution |
|--------|---------|------------|
| 401 | Bad credentials | Check GITHUB_TOKEN |
| 403 | Forbidden | Check token permissions |
| 404 | Not found | Verify repo/PR exists |
| 422 | Validation failed | Check request body |

### Token Permissions

Required scopes for PR resolution:
- `repo`: Full repository access
- `write:discussion`: For resolving threads

## Environment Variables

Required:
- `GITHUB_TOKEN`: Personal access token or fine-grained token

Optional:
- `GITHUB_REPO`: Default repository in `owner/repo` format
