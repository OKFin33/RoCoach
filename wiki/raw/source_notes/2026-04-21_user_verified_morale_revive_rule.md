# 2026-04-21 User-Verified Morale And Revive Rule

## Source Type

Direct user correction during Battle Wiki dogfood testing.

## Confirmed Rule

- In PvP, a spirit fainting causes morale/magic loss.
- Revive effects do not erase that loss.
- If the revived spirit faints again, morale/magic is deducted again.

## Context

This correction was raised while reviewing why balance teams may include
寂灭骨龙. The previous inference correctly identified 不朽 as a long-game value
engine, but left the morale/magic interaction unresolved. The user confirmed
the precise practical rule above.

## Wiki Handling

Use this as a B-layer mechanics note until executable engine handling exists.
Exact UI wording and edge cases should still be checked against future
A-layer/engine sources.
