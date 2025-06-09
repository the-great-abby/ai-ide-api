# Welcome to Pirate Mode Onboarding! 🏴‍☠️

Arrr matey! Ye be enterin' the swashbucklin' version of the onboarding docs. If ye prefer a straight-laced, landlubber's guide, set yer course back to [ONBOARDING.md](ONBOARDING.md).

---

# 5-Minute Pirate Quickstart

Hoist the mainsail and get this ship afloat in under 5 minutes:

1. **Plunder the code repository:**
   ```bash
   git clone <repo-url>
   cd <project-dir>
   ```
2. **Summon the Docker kraken to build yer images:**
   ```bash
   make build
   ```
   *If Docker be refusin' to budge, make sure Docker Desktop be runnin', or ye'll be marooned!*
3. **Raise the dev environment from the depths:**
   ```bash
   make up
   ```
   *If port 9103 be claimed by another scallywag, try:*
   ```bash
   make up PORT=9001
   ```
4. **Chart a course to the API docs in yer browser:**
   - Set sail for [http://localhost:9103/docs](http://localhost:9103/docs) (or whatever port ye chose)
   - If the docs be missin', check Docker and yer ports, or ye may be lost at sea.
5. **Run the ship's tests to check for stowaways:**
   ```bash
   make test
   ```
   - Ye should see a bounty of test results in yer terminal.
   *If the tests mutiny, make sure ye ain't runnin' pytest directly and all containers be afloat!*
6. **Drop anchor and stop the environment when yer done:**
   ```bash
   make down
   ```

**Troubles at sea?**
- Docker not runnin'? Fire up Docker Desktop, or the kraken will get ye.
- Port in use? Use the `PORT` variable as above, or fight the other ship for it.
- Permission errors? Try `sudo chown -R $USER:$USER .` in the project directory, or walk the plank.
- Still adrift? Consult the [Troubleshooting Guide](docs/onboarding/troubleshooting.md) or send a message in a bottle.

---

Return to [ONBOARDING.md](ONBOARDING.md) for the standard, non-pirate onboarding experience. 