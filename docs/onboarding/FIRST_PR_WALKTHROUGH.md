# First PR (Merge Request) Walkthrough

This guide walks you through making your first contribution to the project—step by step. Whether you're fixing a typo, updating docs, or adding a feature, this process will help you get your changes reviewed and merged with confidence.

---

## 1. Overview
- **Purpose:** Help new contributors make their first PR (merge request) with confidence.
- **Scope:** Covers the full workflow: clone, branch, edit, commit, push, open PR, respond to review, and merge.

---

## 2. Prerequisites
- Git installed and configured
- GitHub (or GitLab) account with access to the repo
- Project cloned locally
- Familiarity with basic git commands (see [GitHub Docs](https://docs.github.com/en/get-started/quickstart))

---

## 3. Step-by-Step: Making Your First PR

### 1. **Fork and Clone the Repo**
- Click "Fork" on GitHub (if required), then:
  ```bash
  git clone <your-fork-url>
  cd <project-dir>
  ```

### 2. **Create a New Branch**
- Name your branch after your change (e.g., `fix-typo-in-readme`):
  ```bash
  git checkout -b fix-typo-in-readme
  ```

### 3. **Make Your Changes**
- Edit the relevant file(s) (e.g., fix a typo in `README.md`).

### 4. **Commit Your Changes**
- Stage and commit with a clear message:
  ```bash
  git add README.md
  git commit -m "Fix typo in README"
  ```

### 5. **Push Your Branch**
  ```bash
  git push origin fix-typo-in-readme
  ```

### 6. **Open a Pull Request (PR)**
- Go to your fork on GitHub and click "Compare & pull request."
- Fill in the PR template (describe what you changed and why).
- Submit the PR for review.

### 7. **Respond to Review**
- Reviewers may leave comments or request changes.
- Make updates as needed, then push more commits to your branch.
- Mark conversations as resolved when done.

### 8. **Merge Your PR**
- Once approved, you or a maintainer can merge the PR.
- Celebrate your first contribution!

---

## 4. Tips for a Successful PR
- Keep changes focused and small (one thing per PR).
- Write clear, descriptive commit messages and PR descriptions.
- Follow the project's code style and best practices.
- Add or update tests/docs as needed.
- Be responsive to feedback and ask questions if unsure.

---

## 5. What Happens After Merging?
- Your changes become part of the main codebase.
- CI/CD may run tests and deploy updates.
- You'll be credited as a contributor!
- You can tackle another issue or suggest improvements.

---

## 6. Further Reading
- [GitHub PR Quickstart](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests)
- [Project Contribution Guidelines](CONTRIBUTING.md) (if available)
- [Debugging & Troubleshooting Guide](DEBUGGING_AND_TROUBLESHOOTING.md)

---

*See something missing? Please add your tips or examples!* 