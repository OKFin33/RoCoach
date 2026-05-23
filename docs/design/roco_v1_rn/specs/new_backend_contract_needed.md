# New Backend Contract Needed

## Summary

The current backend supports conversational presentation, not typed UI artifact cards.

Existing fields are enough for:

- normal Agent reply bubble
- generic `AnalysisCard`
- visible warnings
- collapsible detail sections
- followup prompt chips

Existing fields are not enough for:

- exact strategy-summary rows
- typed species cards
- damage calculation cards
- dex snippets
- team matrix cards
- stable card actions

## Required If Production Wants Exact Cards

Add a public contract, not raw tool payload consumption.

Sketch only, not approved schema:

```ts
type UiArtifact = {
  id: string;
  kind:
    | "analysis_summary"
    | "species_profile"
    | "damage_calc"
    | "dex_snippet"
    | "team_matrix";
  title: string;
  summary?: string;
  rows?: Array<{
    id: string;
    label: string;
    value: string;
    tone?: "neutral" | "good" | "warning" | "danger";
  }>;
  sections?: Array<{
    id: string;
    label: string;
    content: string;
    default_visibility: "collapsed" | "expanded";
  }>;
  actions?: Array<{
    id: string;
    label: string;
    action: string;
  }>;
};
```

Potential location:

```ts
response.presentation.ui_artifacts?: UiArtifact[]
```

Hard rules:

- UI artifacts are public presentation data.
- UI artifacts must not expose internal tool names unless product copy wants them.
- UI artifacts must not expose artifact paths, env vars, prompt internals, raw provider responses, or internal selector strings.
- Tool traces remain inspectable/debug detail, not default card data.

## Message Rewrite / Regenerate Contract Gap

Prototype behavior:

- rewrite latest user message inline
- submit rewrite
- remove following messages
- regenerate Agent reply from that node

Backend gap:

- current simple chat/session flow may not represent branch nodes or server-side rewrite.

If V1 only needs simple behavior:

- UI can treat rewrite as local replacement plus a new `/chat` request.
- This is the chosen V1 behavior for latest-user-message rewrite.
- The UI must not present it as true branch history.

Regenerate:

- Keep disabled/greyed as a visible seam unless backend adds a regenerate endpoint or node-aware replay contract.

If production needs true branch semantics:

```ts
type RewriteMessageRequest = {
  session_id: string;
  message_id: string;
  replacement_text: string;
  persona_selector?: PersonaSelector | null;
};
```

This is not required for the current visual handoff, but it should not be faked as complete.
