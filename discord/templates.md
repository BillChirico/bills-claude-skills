# Discord Formatting Templates

Copy-paste templates for common Discord formatting patterns. Replace placeholder content with your own.

## Announcements

### Feature Release
```
# 🚀 New Feature: [Feature Name]

We just shipped **[feature name]** — here's what it does:

- **[Benefit 1]** — brief description
- **[Benefit 2]** — brief description
- **[Benefit 3]** — brief description

> Try it now: [instructions or link]

-# Released [date] • Questions? Ask in <#CHANNEL_ID>
```

### Maintenance Notice
```
# ⚠️ Scheduled Maintenance

**When:** <t:UNIX_TIMESTAMP:F> (<t:UNIX_TIMESTAMP:R>)
**Duration:** ~[X] minutes
**Impact:** [what will be unavailable]

> We'll update this channel when maintenance is complete.

-# Last updated <t:UNIX_TIMESTAMP:R>
```

## Community & Moderation

### Rules / Guidelines
```
# 📋 Server Rules

### 1. Be Respectful
Treat everyone with dignity. No harassment, hate speech, or personal attacks.

### 2. Stay On Topic
Use the right channels. Check <id:browse> to find the right place.

### 3. No Spam
No unsolicited DMs, repeated messages, or self-promotion without permission.

### 4. Follow Discord TOS
> https://discord.com/terms

-# Updated <t:UNIX_TIMESTAMP:D> • Violations may result in mute or ban
```

### Welcome Message
```
# 👋 Welcome to [Server Name]!

Hey <@USER_ID>, glad you're here! Here's how to get started:

1. Read the rules in <#CHANNEL_ID>
2. Grab your roles in <id:customize>
3. Introduce yourself in <#CHANNEL_ID>
4. Check out <id:guide> for a full walkthrough

> **Need help?** Ping <@&ROLE_ID> anytime.
```

## Development & Technical

### Bug Report Template
```
## 🐛 Bug Report

**Summary:** [one-line description]

**Steps to Reproduce:**
1. Go to [location]
2. Click on [element]
3. Observe [unexpected behavior]

**Expected:** [what should happen]
**Actual:** [what happens instead]

**Environment:**
- OS: [e.g., Windows 11, macOS 14]
- Version: [e.g., v1.2.3]
- Browser: [if applicable]

```error log
paste relevant error output here
```

-# Reported by @username • <t:UNIX_TIMESTAMP:d>
```

### Code Review / PR Summary
```
## 📝 PR Summary: [PR Title]

**Branch:** `feature/branch-name` → `main`
**Changes:** [brief description]

### What Changed
- **[File/Area]** — [description of change]
- **[File/Area]** — [description of change]

### Testing
```bash
npm test           # ✅ All passing
npm run lint       # ✅ No warnings
npm run typecheck  # ✅ Clean
```

> **Review link:** [URL]

-# Ready for review • cc <@USER_ID>
```

### Changelog
```
# 📦 v[X.Y.Z] Changelog

### ✨ New
- [Feature description]
- [Feature description]

### 🐛 Fixes
- Fixed [issue description]
- Fixed [issue description]

### 🔧 Changes
- [Change description]
- [Change description]

### ⚠️ Breaking
- [Breaking change] — see ||migration guide in #channel||

-# Full diff: [link to release]
```

## Events & Scheduling

### Event Announcement
```
# 🎉 [Event Name]

**When:** <t:UNIX_TIMESTAMP:F> (<t:UNIX_TIMESTAMP:R>)
**Where:** [location / voice channel / link]
**What:** [description]

### Schedule
- <t:TIMESTAMP_1:t> — [Activity 1]
- <t:TIMESTAMP_2:t> — [Activity 2]
- <t:TIMESTAMP_3:t> — [Activity 3]

> **RSVP:** React with ✅ if you're coming!

-# Hosted by <@USER_ID>
```

## Informational

### FAQ Entry
```
### ❓ [Question goes here?]

[Clear, concise answer.]

> **Example:**
> [example or demonstration]

-# See also: <#CHANNEL_ID>
```

### Status Update
```
## 📊 Status Update — [Project/Topic]

**Status:** 🟢 On Track / 🟡 At Risk / 🔴 Blocked

### Completed
- ✅ [Task 1]
- ✅ [Task 2]

### In Progress
- 🔄 [Task 3] — [brief status]
- 🔄 [Task 4] — [brief status]

### Blocked
- ❌ [Task 5] — blocked by [reason]

> **Next milestone:** <t:UNIX_TIMESTAMP:D>

-# Updated <t:UNIX_TIMESTAMP:R>
```

## Formatting Tricks

### Separator Line
Discord doesn't support `---` for horizontal rules. Use an empty block quote or code block as a visual separator:
```
_ _
```
Or use a unicode line:
```
─────────────────────
```

### Invisible Spacing
Use `_ _` (underscore, space, underscore) for an empty line that Discord won't collapse:
```
Line 1
_ _
Line 3 (with visible gap above)
```

### Color-Coded Text via Code Blocks
Discord doesn't support colored text natively, but `diff` blocks give you colored lines:
````
```diff
+ This line is green (added)
- This line is red (removed)
! This line is orange (in some themes)
# This line is gray (comment)
```
````

### Table-Like Formatting
Discord doesn't render markdown tables. Use code blocks for alignment:
````
```
Name        Role          Status
────────    ──────────    ────────
Alice       Admin         ✅ Online
Bob         Moderator     ⚫ Offline
Charlie     Member        🟡 Idle
```
````
