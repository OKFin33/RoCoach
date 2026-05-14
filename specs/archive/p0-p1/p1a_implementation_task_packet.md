Executor: 主开发线程
Read /Users/okfin3/project/GitHub/OKFin33/Roco/specs/p1a_synthesis_implementation_spec.md first.

Status: IMPLEMENT

Task:
Implement the bounded `P1a` synthesis layer exactly as specified, without starting `P1b` or later persona pipeline work.

Scope:
- add `agent_core/synthesis.py` as the dedicated synthesis boundary
- extend `agent_core/contracts.py` with typed synthesis models and optional response payload support
- insert synthesis into `agent_core/orchestrator.py` between runtime output and persona rendering
- adjust `agent_core/adapters/advisor.py` so it provides normalized analytical substrate for synthesis input building
- update compatibility surfaces only where required by the accepted spec
- add or update tests for synthesis ordering, grounding preservation, warning/refusal preservation, and response compatibility

Do not:
- implement `P1b Reply + Why` presentation behavior beyond carrying synthesis data needed for later stages
- add persona registry, source adapter, ingestion, or managed persona creation work
- add case retrieval, embeddings, web-in-loop, session persistence, or new product tasks
- rewrite `advisor/runtime.py`, battle engine, battle-dex, API infrastructure, or mobile architecture outside narrow compatibility needs
- let doctrine alter facts, confidence semantics, warning visibility, or refusals

Deliverables:
- `agent_core/synthesis.py`
- `agent_core/contracts.py`
- `agent_core/orchestrator.py`
- `agent_core/adapters/advisor.py`
- `agent_core/persona.py` only if compatibility adjustments are strictly required
- `api/contracts.py` only if schema exposure is strictly required
- `tests/test_agent_core_contracts.py`
- `tests/test_agent_core_orchestrator.py`
- `tests/test_api.py`

Validation:
- `.venv/bin/python -m unittest tests.test_agent_core_contracts`
- `.venv/bin/python -m unittest tests.test_agent_core_orchestrator`
- `.venv/bin/python -m unittest tests.test_api`
- `.venv/bin/python -m unittest discover -s tests`

Return format:
- Status
- Files changed
- Result
- Validation
- Scope confirmation
