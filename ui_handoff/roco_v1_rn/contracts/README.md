# Contracts

## Files

- `roco_v1_ui_contract.ts`

## Usage

This contract is the first typed source for the Expo RN implementation thread.

Recommended workflow:

1. Copy/adapt the types and helper functions into `mobile/src/roco/`.
2. Keep UI-only persona ids separate from backend persona ids.
3. Use `buildAnalysisCardModel()` as the reference mapping from backend presentation fields to the generic analysis card.
4. Use `actionsForMessage()` as the reference action availability rule.

Do not import this handoff file directly from production code unless the repository owners decide `ui_handoff/` is part of the production TypeScript compile boundary.

