# GitHub API Reference

Supplementary reference for the github-pr-resolver skill. See SKILL.md for the workflow.

## Comment Intent Patterns

| Pattern | Intent | Action |
|---------|--------|--------|
| ````suggestion` block | Explicit code change | Apply the suggested code directly |
| "Typo in..." | Spelling/grammar | Correct the typo |
| "Rename to..." | Variable/function rename | Rename as specified |
| "Missing..." | Something to add | Add the missing element |
| "Remove..." | Something to delete | Remove the code |
| "Consider...", "Maybe..." | Suggestion | Evaluate and apply |
| "Nit:" | Minor style issue | Fix it |
| "LGTM" | Approved | No action needed |

## CI Check Types

| Check Pattern | Type | Common Fix |
|--------------|------|------------|
| `lint`, `eslint`, `pylint`, `ruff` | Linting | `npm run lint -- --fix` or `ruff check --fix .` |
| `test`, `jest`, `pytest`, `vitest` | Tests | Fix test or implementation |
| `build`, `compile`, `tsc` | Build | Fix syntax/import errors |
| `typecheck`, `mypy`, `pyright` | Types | Add/fix type annotations |
| `format`, `prettier`, `black` | Formatting | `npx prettier --write .` or `black .` |
| `coverage` | Coverage | Add more tests |

## CLI Commands

### PR Information

```bash
# PR details
gh pr view <PR> --json number,title,state,headRefName,baseRefName,author,url

# Check status
gh pr checks <PR>
gh pr checks <PR> --json name,state,conclusion

# PR diff
gh pr diff <PR>
```

### Workflow Runs

```bash
# List runs
gh run list --branch <BRANCH>

# View run
gh run view <RUN_ID>

# Failed logs only
gh run view <RUN_ID> --log-failed
```

### GraphQL

```bash
# Query (use -f for strings, -F for numbers/booleans)
gh api graphql -f query='<QUERY>' -f var=value -F numVar=123
```

## Pagination Loop (CLI)

```bash
ALL_THREADS="[]"
CURSOR=""

while true; do
  RESULT=$(gh api graphql -f query='
  query($owner: String!, $repo: String!, $pr: Int!, $cursor: String) {
    repository(owner: $owner, name: $repo) {
      pullRequest(number: $pr) {
        reviewThreads(first: 100, after: $cursor) {
          pageInfo { hasNextPage, endCursor }
          nodes { id, isResolved, path, line }
        }
      }
    }
  }' -f owner=OWNER -f repo=REPO -F pr=NUMBER ${CURSOR:+-f cursor=$CURSOR})

  PAGE=$(echo $RESULT | jq '.data.repository.pullRequest.reviewThreads.nodes')
  ALL_THREADS=$(echo "$ALL_THREADS $PAGE" | jq -s 'add')

  HAS_NEXT=$(echo $RESULT | jq -r '.data.repository.pullRequest.reviewThreads.pageInfo.hasNextPage')
  [ "$HAS_NEXT" != "true" ] && break
  CURSOR=$(echo $RESULT | jq -r '.data.repository.pullRequest.reviewThreads.pageInfo.endCursor')
done

echo "Total: $(echo $ALL_THREADS | jq 'length')"
echo "Unresolved: $(echo $ALL_THREADS | jq '[.[] | select(.isResolved == false)] | length')"
```

## Error Handling

| Status | Meaning | Fix |
|--------|---------|-----|
| 401 | Bad credentials | `gh auth login` |
| 403 | Forbidden | Check token permissions |
| 404 | Not found | Verify repo/PR exists |
| 422 | Validation failed | Check request body |

### Token Permissions

Required scopes: `repo`, `write:discussion`

```bash
gh auth status
```

## Rate Limits

- REST: 5000 requests/hour
- GraphQL: 5000 points/hour

```bash
gh api rate_limit
```
