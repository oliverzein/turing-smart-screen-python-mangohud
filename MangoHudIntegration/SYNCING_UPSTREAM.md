# Syncing with Upstream Repository

This document describes how to keep your fork synchronized with the upstream repository (mathoudebine/turing-smart-screen-python).

## Repository Setup

### Remotes Configuration

Your fork has two remotes:

```bash
origin    → https://github.com/oliverzein/turing-smart-screen-python-mangohud.git  (your fork)
upstream  → https://github.com/mathoudebine/turing-smart-screen-python.git         (original repo)
```

### Branch Structure

```
main                              → Your main branch (synced with upstream)
feature/mangohud-fps-integration  → Your feature branch (MangoHud work)
```

## Checking for Updates

### View Available Updates

```bash
# Fetch latest changes from upstream (doesn't modify your code)
git fetch upstream

# See what commits are new in upstream
git log HEAD..upstream/main --oneline --graph
```

**Example output:**
```
* 50eb931 [GitHub Actions Bot] Update theme previews
* c9a7441 Merge pull request #878 from mathoudebine/dependabot/pip/numpy-approx-eq-2.3.4
* bc0fd77 :arrow_up: Update numpy requirement from ~=2.3.3 to ~=2.3.4
```

### View Detailed Changes

```bash
# See what files changed
git diff HEAD..upstream/main --stat

# See full diff
git diff HEAD..upstream/main
```

## Syncing Process

### Step 1: Commit or Stash Local Changes

Before switching branches, ensure your work is saved:

```bash
# Check status
git status

# If you have uncommitted changes:
git add .
git commit -m "Work in progress"

# Or stash them temporarily:
git stash
```

### Step 2: Update Main Branch

```bash
# Switch to main branch
git checkout main

# Merge upstream changes
git merge upstream/main

# Push updated main to your fork
git push origin main
```

**Expected output:**
```
Updating 3ed18e0..50eb931
Fast-forward
 COPYRIGHT                    | 4 ++++
 library/sensors/sensors_custom.py | 5 ++++-
 requirements.txt             | 2 +-
 33 files changed, 180 insertions(+), 109 deletions(-)
```

### Step 3: Update Feature Branch

```bash
# Switch to feature branch
git checkout feature/mangohud-fps-integration

# Merge main into feature branch
git merge main
```

**What happens:**
- Git creates a merge commit
- Combines upstream changes with your MangoHud work
- Preserves complete history

### Step 4: Resolve Conflicts (if any)

If there are conflicts:

```bash
# Git will show conflicted files
git status

# Edit conflicted files (look for <<<<<<< markers)
# Choose which changes to keep

# Mark conflicts as resolved
git add <conflicted-file>

# Complete the merge
git commit
```

### Step 5: Push Updated Feature Branch

```bash
# Push to your fork
git push origin feature/mangohud-fps-integration
```

## Merge vs Rebase

### Git Merge (Recommended)

**Command:**
```bash
git merge main
```

**Result:**
```
main:     A---B---C---D
                   \   \
feature:            E---F---G---M  (merge commit)
```

**Pros:**
- ✅ Safe - preserves complete history
- ✅ No risk of losing work
- ✅ Works with published branches
- ✅ Shows when branches diverged

**Cons:**
- ❌ Creates merge commits
- ❌ History can get messy

### Git Rebase (Alternative)

**Command:**
```bash
git rebase main
```

**Result:**
```
main:     A---B---C---D
                       \
feature:                E'---F'---G'  (replayed on top)
```

**Pros:**
- ✅ Clean, linear history
- ✅ No merge commits
- ✅ Easier to review

**Cons:**
- ❌ Rewrites history (dangerous if branch is published)
- ❌ Can be confusing if conflicts occur
- ⚠️ **Never rebase shared/published branches!**

### When to Use Each

**Use merge when:**
- Branch is already pushed to GitHub
- Working with others on the same branch
- You want to preserve exact history
- **Default safe choice**

**Use rebase when:**
- Branch is only local (not pushed)
- Working alone
- Want clean history for pull request
- Comfortable with git

## Example Sync Session

Here's what a typical sync looks like:

```bash
# 1. Check for updates
$ git fetch upstream
$ git log HEAD..upstream/main --oneline
* 50eb931 Update theme previews
* c9a7441 Merge numpy update
* bc0fd77 Update numpy requirement

# 2. Commit current work
$ git add .
$ git commit -m "Add 1% low FPS feature"

# 3. Update main
$ git checkout main
$ git merge upstream/main
Updating 3ed18e0..50eb931
Fast-forward
 33 files changed, 180 insertions(+), 109 deletions(-)

$ git push origin main
To https://github.com/oliverzein/turing-smart-screen-python-mangohud.git
   3ed18e0..50eb931  main -> main

# 4. Update feature branch
$ git checkout feature/mangohud-fps-integration
$ git merge main
Merge made by the 'ort' strategy.
 33 files changed, 180 insertions(+), 109 deletions(-)

# 5. Push feature branch
$ git push origin feature/mangohud-fps-integration
```

## Common Issues

### Issue: "Your local changes would be overwritten"

**Error:**
```
Fehler: Ihre lokalen Änderungen in den folgenden Dateien würden beim Auschecken
überschrieben werden:
        library/sensors/sensors_custom.py
```

**Solution:**
```bash
# Commit your changes first
git add .
git commit -m "Save work"

# Or stash them
git stash
# ... do the merge ...
git stash pop
```

### Issue: Merge Conflicts

**Symptoms:**
```
CONFLICT (content): Merge conflict in library/sensors/sensors_custom.py
Automatic merge failed; fix conflicts and then commit the result.
```

**Solution:**
1. Open conflicted file
2. Look for conflict markers:
   ```python
   <<<<<<< HEAD
   your code
   =======
   upstream code
   >>>>>>> upstream/main
   ```
3. Choose which code to keep (or combine both)
4. Remove conflict markers
5. Save file
6. Mark as resolved:
   ```bash
   git add library/sensors/sensors_custom.py
   git commit
   ```

### Issue: Detached HEAD State

**Symptoms:**
```
You are in 'detached HEAD' state
```

**Solution:**
```bash
# Create a branch from current state
git checkout -b temp-branch

# Or go back to your branch
git checkout feature/mangohud-fps-integration
```

## Automation

### Quick Sync Script

Create `sync-upstream.sh`:

```bash
#!/bin/bash
set -e

echo "Fetching upstream..."
git fetch upstream

echo "Updating main..."
git checkout main
git merge upstream/main
git push origin main

echo "Updating feature branch..."
git checkout feature/mangohud-fps-integration
git merge main

echo "Sync complete!"
echo "Don't forget to push: git push origin feature/mangohud-fps-integration"
```

Make executable:
```bash
chmod +x sync-upstream.sh
```

## Best Practices

1. **Sync regularly** - Don't let your fork get too far behind
2. **Commit before syncing** - Always save your work first
3. **Use merge for published branches** - Safer than rebase
4. **Test after syncing** - Ensure nothing broke
5. **Keep main clean** - Don't commit directly to main
6. **Read upstream changes** - Understand what you're merging

## Verification

After syncing, verify everything works:

```bash
# Check that main is up to date
git checkout main
git log --oneline -5

# Check feature branch has both your work and upstream changes
git checkout feature/mangohud-fps-integration
git log --oneline --graph -10

# Test the code
.venv/bin/python main.py
```

## References

- [Git Documentation - Merging](https://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging)
- [GitHub - Syncing a Fork](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/syncing-a-fork)
- [Atlassian - Git Merge vs Rebase](https://www.atlassian.com/git/tutorials/merging-vs-rebasing)
