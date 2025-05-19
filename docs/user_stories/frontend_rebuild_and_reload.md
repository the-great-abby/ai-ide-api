# User Story: Rebuilding and Reloading the Frontend via Makefile

## Motivation
As a developer or AI agent, I want a simple, reliable way to rebuild and reload the frontend after making code changes, so that updates are reflected in the UI without manual Docker or npm commands.

## Actors
- Developer
- AI agent (automation)
- Docker Compose services

## Preconditions
- The codebase includes a Makefile with targets for managing the frontend container.
- The frontend is containerized and managed via Docker Compose.
- Code changes have been made to the frontend (e.g., React components, styles).

## Step-by-Step Actions
1. **Rebuild the frontend container:**
   - Preferred Makefile target:
     ```bash
     make -f Makefile.ai ai-admin-frontend-restart
     ```
   - This will restart the frontend container without rebuilding from scratch (fastest for most changes).

2. **If a full rebuild is needed (e.g., after dependency changes):**
   - Use the no-cache rebuild target:
     ```bash
     make -f Makefile.ai ai-admin-frontend-nocache-restart
     ```
   - This will rebuild the frontend container from scratch and restart it.

3. **Verify the frontend is running:**
   - Open the frontend in your browser (default: http://localhost:3000)
   - Confirm that your changes are visible.

## Expected Outcomes
- The frontend is rebuilt and reloaded using a single Makefile command.
- Developers and AI agents do not need to remember raw Docker or npm commands.
- The process is consistent and works in all environments.

## Best Practices
- Always use the Makefile targets for frontend management.
- Use the restart target for most code changes; use the no-cache rebuild for dependency or base image changes.
- Document this workflow in onboarding and developer docs.

## References
- Makefile.ai targets: `ai-admin-frontend-restart`, `ai-admin-frontend-nocache-restart`
- [ONBOARDING.md](../ONBOARDING.md)

## Troubleshooting: When Changes Don't Appear

Sometimes, even after running the correct Makefile targets, frontend changes may not show up in the UI. This can be confusing and has happened before. Here are common causes and steps that have helped:

### Common Causes
- **Docker build cache:** The container may use cached layers and not pick up new code.
- **Volume mounts:** Docker volumes can override built files with old files from the host.
- **Browser cache:** Browsers may serve old JS/CSS bundles. Try a hard refresh or incognito mode.
- **Build context issues:** The Docker build context may not include the latest source code.
- **Multiple containers:** Rare, but check that only one frontend container is running.

### Steps That Have Helped
1. **Full no-cache rebuild:**
   ```bash
   make -f Makefile.ai ai-admin-frontend-nocache-restart
   ```
2. **Remove all containers and volumes:**
   ```bash
   docker compose down -v
   docker system prune -af
   make -f Makefile.ai ai-admin-frontend-nocache-restart
   ```
3. **Check for volume mounts:**
   Inspect `docker-compose.yml` for any `volumes:` under the frontend service.
4. **Hard refresh the browser:**
   Use Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows/Linux), or try incognito mode.
5. **Add a visible, trivial change:**
   Edit the UI (e.g., add a new heading or emoji) to confirm the new build is running.
6. **Check container status:**
   ```bash
   make -f Makefile.ai ai-status
   ```
7. **Check container logs:**
   ```bash
   docker compose logs --tail=100 frontend
   ```

### Lessons Learned
- Sometimes, after all these steps, things "just work"—the root cause may not always be clear.
- Document what you tried, as this helps future debugging.
- If you're stuck, try a combination of the above steps and ask for help.

## Breadcrumbs & Debugging Tools

To make future troubleshooting easier, we added the following Makefile targets:

- **ai-docker-ps**: Lists all running Docker containers (names, images, status, ports).
- **ai-port-3000-procs**: Shows any processes using port 3000 (finds stray dev servers).
- **ai-docker-stop-all**: Stops all running Docker containers.
- **ai-kill-port-3000**: Kills any process using port 3000 on your host.
- **ai-playwright-build-nocache**: Forces a no-cache build of the Playwright test container to ensure the latest test code is included.

These tools help quickly diagnose issues with multiple containers, port conflicts, or stale processes.

### Real-World Debugging Adventure

During a recent session, we:
- Tried full no-cache rebuilds and restarts
- Checked for browser cache issues
- Wondered about multiple containers or stray dev servers
- Added these Makefile helpers to make future debugging much easier
- **Noticed that sometimes, after a long session, the frontend cache or Docker state resolves itself and the latest code appears—patience and repeated attempts (including no-cache builds, restarts, and time) can eventually resolve stubborn caching issues, even if the exact trigger is unclear.**

If you're stuck, try these tools and document what you find—future you will thank you! 