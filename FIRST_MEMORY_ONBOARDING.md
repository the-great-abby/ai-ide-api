# 🧠 First Memory Node Onboarding

_All commands below are copy-paste ready for your convenience._

Welcome aboard! This onboarding path is for anyone—internal or external—who wants a focused, step-by-step guide to getting the memory system working and adding their first memory node.

---

## Why This Path?
- The memory system is a core feature of the project, powering AI context, search, and collaboration.
- Getting your first memory node working is a rite of passage and a great way to learn the ropes.

---

## What is a Memory Node?
A memory node consists of a 'namespace' (a category or group for your memory, e.g., 'onboarding') and 'content' (the actual information you want to store).

## Before You Begin
No manual database migrations are needed—`make dev-up` handles all setup for you.

## How to Celebrate
To add your achievement to the Pirate's Log, submit a Pull Request (PR) adding your entry to `PIRATES_LOG.md`, or open an issue and a crew member will help you log it.

---

## First Memory Node Checklist

1. **Start the dev environment:**
   ```bash
   make dev-up
   ```
2. **Check that the API and memory endpoints are running:**
   - Visit [http://localhost:9103/docs](http://localhost:9103/docs) (**port 9103**) and look for `/memory/nodes` endpoints.
3. **Add your first memory node (using curl):**
   ```bash
   curl -X POST http://localhost:9103/memory/nodes \
     -H 'Content-Type: application/json' \
     -d '{"namespace": "onboarding", "content": "My first memory node!", "meta": "{\"tags\":[\"onboarding\"]}"}'
   ```
   - Or use the API docs "Try it out" button.
4. **Verify your memory node exists:**
   ```bash
   curl http://localhost:9103/memory/nodes?namespace=onboarding | jq .
   # If you don't have jq installed, you can just run:
   curl http://localhost:9103/memory/nodes?namespace=onboarding
   # Or install jq with: brew install jq (macOS) or sudo apt-get install jq (Linux)
   ```
5. **(Optional) Explore more:**
   - Try adding an edge, searching, or traversing the memory graph (see the Memory System Guide for examples).
6. **Celebrate your achievement:**
   - Add an entry to the [Pirate's Log](PIRATES_LOG.md) sharing your success!

---

## Troubleshooting
- If you get stuck, check the troubleshooting section in ONBOARDING.md.
- Ask your buddy for help or look for real examples in the Pirate's Log.
- Common issues:
  - API not running? Make sure you ran `make dev-up`.
  - Endpoint not found? Double-check the URL and **port 9103**.
  - Error in response? Check your JSON formatting and required fields.

## Common Errors and Solutions

| Error/Symptom                        | Likely Cause                                 | Solution                                                      |
|--------------------------------------|----------------------------------------------|---------------------------------------------------------------|
| API not running                      | Forgot to start environment                  | Run `make dev-up`                                             |
| Endpoint not found (404)             | Wrong port or URL                            | Use `http://localhost:9103` and check the endpoint spelling    |
| Connection refused                   | Service not started or wrong port            | Ensure `make dev-up` is running and port 9103 is used         |
| Error in response (400/422)          | Malformed JSON or missing required fields    | Double-check your curl command and JSON formatting            |
| jq: command not found                | jq not installed                             | Install jq or use plain curl output                           |
| Unsure where to add Pirate's Log     | Not clear on process                         | Submit a PR to `PIRATES_LOG.md` or open an issue              |

---

**Pro tip:** Every challenge is a chance to learn and improve the ship for the next crew. Don't forget to log your first memory node in the Pirate's Log! 