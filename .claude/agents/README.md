# .claude/agents/ — specialized advisory agents

These files define focused roles for code, dependency, security, documentation,
infrastructure, test, browser, and release review. Independent reviews may run
in parallel; fixes run in a controlled sequence.

The agents do not replace the PRIN Session Cycle, maintainer approval, or
repository verification. Their outputs become evidence only after reproduction
against the current checkout and applicable local/hosted gates.
