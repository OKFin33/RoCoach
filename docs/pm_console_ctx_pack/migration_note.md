# Migration Note

## Why This Should Leave Roco

The PM Console idea emerged inside the `Roco` project because that project had:

- multiple specialized threads
- long-running architecture work
- frequent handoff and audit loops
- enough complexity for context drag to become visible

That was a good incubation environment.

It is no longer the right long-term home.

If the console stays inside `Roco` for too long, two bad things happen:

1. the console becomes too tied to one product's artifacts
2. the abstraction never becomes reusable for other agent-native projects

## What Should Be Carried Forward

These concepts should move into the new project:

- locked execution plan
- execution state
- task packet template
- PM console thread handoff
- GUI courier rule
- role split between PM / implementation / QA / courier

## What Should Stay Behind

These belong to `Roco`, not the standalone PM Console project:

- battle-advisor domain logic
- persona doctrine specifics for tactical coaches
- Enzo-specific integration review content
- battle-dex / retrieval / runtime details
- mobile and API product implementation

The new project should keep only the control mechanics, not the Roco domain.

## Recommended New Project Positioning

Suggested positioning:

`A lightweight PM execution console for agent-native coding workflows`

Suggested initial shape:

- skill/package first
- file-driven artifacts
- host-compatible with Codex App / Codex CLI / Claude Code
- optional GUI courier support

## Recommended First Steps In The New Project

1. copy this context pack
2. rewrite artifact names to remove Roco-specific wording
3. create generic examples not tied to battle-advisor work
4. implement a thin console flow around:
   - execution state
   - task packet generation
   - gate updates
5. only after that consider:
   - helper scripts
   - richer templates
   - skill packaging
   - UI wrappers

## Final Recommendation

Do not keep iterating on the PM Console as a sidecar forever inside `Roco`.

Use `Roco` as the origin story and proof that the model works, then migrate the
console into its own project while the abstraction is still clean.
