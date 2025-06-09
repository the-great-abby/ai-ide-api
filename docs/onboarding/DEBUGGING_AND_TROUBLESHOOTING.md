# Debugging & Troubleshooting Guide

This guide helps new contributors quickly diagnose and fix common issues in both backend and frontend. It covers logs, error messages, debugging tools, and common pitfalls.

---

## 1. Overview
- **Purpose:** Help new contributors quickly diagnose and fix common issues in both backend and frontend.
- **Scope:** Covers logs, error messages, debugging tools, and common pitfalls.

---

## 2. General Debugging Principles
- **Read the error message carefully.**
- **Check the logs** (backend and frontend).
- **Reproduce the issue** with a minimal test case.
- **Ask for help if you're stuck!**

---

## 3. Backend Debugging (FastAPI, Python)

### A. Logs
- All logs are written using the Python `logging` module (see `logging_config.py`).
- Look for `ERROR` or `CRITICAL` messages in the logs.

### B. Common Error Messages
| Error Message                  | Likely Cause                        | Solution                                  |
|-------------------------------|-------------------------------------|-------------------------------------------|
| "Connection refused"           | Service not running, wrong host/port| Use Docker service names, check containers |
| "ModuleNotFoundError"          | Missing dependency                  | Run `pip install -r requirements.txt`     |
| "KeyError"/"AttributeError"    | Typo or missing field               | Check your code and data structures       |
| "HTTP 422 Unprocessable Entity"| Bad request data                    | Check your API payload/schema             |

### C. Debugging Tools
- **Breakpoints:** Use `import pdb; pdb.set_trace()` in Python to pause execution and inspect variables.
- **Unit/Integration Tests:** Run tests with `make -f Makefile.ai ai-test PYTEST_ARGS="-x"` to catch issues early.

---

## 4. Frontend Debugging (React, JS/TS)

### A. Browser DevTools
- Use Chrome/Firefox DevTools to inspect network requests, console errors, and component state.

### B. Common Error Messages
| Error Message                  | Likely Cause                        | Solution                                  |
|-------------------------------|-------------------------------------|-------------------------------------------|
| "Network Error"                | Backend not running, CORS issue     | Start backend, check API URL              |
| "404 Not Found"                | Wrong endpoint or route             | Check API docs and frontend code          |
| "TypeError: undefined is not a function" | Typo or missing import         | Check your code and imports               |

### C. Debugging Tools
- **React DevTools:** Inspect component tree and props/state.
- **Console.log:** Add `console.log()` statements to trace values.

---

## 5. Docker & Environment Issues

| Symptom                        | Likely Cause                        | Solution                                  |
|-------------------------------|-------------------------------------|-------------------------------------------|
| "Cannot connect to database"   | DB container not running            | Run `make up` or `make -f Makefile.ai ai-env-up` |
| "Port already in use"          | Another process using port          | Use a different port, stop other process  |
| "File permission denied"       | Wrong file ownership/permissions    | Run `sudo chown -R $USER:$USER .`         |

---

## 6. Testing Failures
- **Run with `-x` flag** to stop on first failure:  
  `make -f Makefile.ai ai-test PYTEST_ARGS="-x"`
- **Check test logs** for stack traces and error messages.
- **Use fixtures** for setup/teardown and tokens.

---

## 7. When to Ask for Help
- If you've tried the above and are still stuck, ask in Slack/Discord, open a GitHub Issue, or request a pairing session.
- Include error messages, what you've tried, and relevant code snippets.

---

## 8. Further Reading
- [Python Debugging with pdb](https://docs.python.org/3/library/pdb.html)
- [React Debugging Tools](https://react.dev/learn/debugging)
- [FastAPI Error Handling](https://fastapi.tiangolo.com/tutorial/handling-errors/)

---

*See something missing? Please add your tips or examples!* 