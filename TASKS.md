# TASKS

1. [x] Make the executable run with "ib", not "ib-api", its nicer.
2. [ ] Instead of IB_RUN_INTEGRATION just run `pytest tests/integration` to run the integration tests, thats the advantage of separating folders, in `mise` have these tasks: test, test:integration, test:all.
3. [ ] Add an opt-in local session-keeper mode that calls `/tickle` every 60s, retries brokerage-session init when possible, sends websocket heartbeats, and clearly prompts for browser re-login after midnight resets or full session loss.
4. [x] The API code should be installable in another project, say using `uv`, one that is not related to the CLI.
