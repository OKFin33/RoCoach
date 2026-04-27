# Screen References

PNG files in this directory are visual references exported from the Web/Figma Make prototype where available.

They are not implementation assets. RN engineering should implement from:

- `../tokens.json`
- `../assets/paper/paper_shell.png`
- `../assets/paper/paper_outline.png` only if extra edge contrast is needed
- `../specs/*.md`

## Required States

| State | File | Product state | Mock status |
| --- | --- | --- | --- |
| Empty chat | `chat_empty.png` | real required state | generated reference if not exported from live prototype |
| Populated chat | `chat_populated.png` | real required state | Web visual reference |
| Long analysis card | `chat_analysis_card.png` | real required state | Web mock content, real visual direction |
| Thinking/loading | `chat_thinking.png` | real required state | Web/prototype or generated reference |
| Error/retry | `chat_error.png` | real required state | generated reference until backend error examples exist |
| Keyboard opened | `keyboard_opened.png` | real required state | generated reference; exact keyboard is platform-native |
| User actions | `message_actions_user.png` | real required state | Web visual reference |
| Agent actions | `message_actions_agent.png` | real required state | Web visual reference |
| Persona wheel | `persona_wheel_open.png` | real required state | Web visual reference |
| Settings drawer | `settings_open.png` | real required state | Web visual reference |

## Coordinate Baseline

Reference viewport: 390 x 844.

Important target regions:

- paper outer bounds: x approximately 10, y approximately 10, width approximately 370
- paper content inset: use the scaled inset from `specs/layout.md`
- right drawer handle: aligned to screen right edge when closed
- composer: inside paper, bottom aligned above safe area
- Agent avatar long-press anchor: avatar center
