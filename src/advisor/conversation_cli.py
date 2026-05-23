from __future__ import annotations

import argparse
import os
from pathlib import Path

from advisor.battle_dex import BattleDexRepository, DEFAULT_RUNTIME_DB, ensure_battle_dex_sqlite
from advisor.config import DEFAULT_ENV_PATH, load_native_model_config
from advisor.runtime import AdvisorAgent, render_response


def resolve_backend_config(
    *,
    requested_backend: str,
    env_file: Path,
    model_name: str | None,
) -> tuple[str, str | None, object | None, bool]:
    if requested_backend == "deterministic":
        return "deterministic", model_name, None, False

    native_model = load_native_model_config(
        env_path=env_file,
        model_name_override=model_name,
    )
    if requested_backend == "pydantic_ai_native":
        if native_model is None:
            raise SystemExit(
                "pydantic_ai_native requires a local env file with "
                "ROCO_ADVISOR_MODEL, ROCO_OPENAI_BASE_URL, and ROCO_OPENAI_API_KEY."
            )
        return "pydantic_ai_native", native_model.model_name, native_model, False

    if requested_backend == "auto":
        if native_model is None:
            return "deterministic", model_name, None, True
        return "pydantic_ai_native", native_model.model_name, native_model, True

    raise ValueError(f"Unsupported backend: {requested_backend}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Roco conversational advisor MVP CLI")
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DEFAULT_RUNTIME_DB,
        help="Path to the battle-dex SQLite file. Defaults to data/runtime/battle_dex.sqlite.",
    )
    parser.add_argument(
        "--skip-bootstrap",
        action="store_true",
        help="Do not auto-build the SQLite file from the latest validated importer run.",
    )
    parser.add_argument(
        "--message",
        action="append",
        default=[],
        help="Run one or more messages non-interactively.",
    )
    parser.add_argument(
        "--backend",
        choices=("auto", "deterministic", "pydantic_ai_native"),
        default="auto",
        help=(
            "Advisor runtime backend. auto uses pydantic_ai_native when valid "
            "native env config exists, otherwise deterministic."
        ),
    )
    parser.add_argument(
        "--model-name",
        default=None,
        help="Model name for the native PydanticAI backend. Can also come from ROCO_ADVISOR_MODEL.",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=DEFAULT_ENV_PATH,
        help="Path to local native-agent env file. Defaults to ~/.config/roco-advisor/env.",
    )
    parser.add_argument(
        "--native-timeout",
        type=float,
        default=15.0,
        help="Maximum seconds allowed for one native runtime call before bounded fallback/refusal.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    db_path = args.db_path
    if not args.skip_bootstrap:
        db_path = ensure_battle_dex_sqlite(db_path)

    model_name = args.model_name or os.getenv("ROCO_ADVISOR_MODEL")
    backend, model_name, native_model, auto_selected = resolve_backend_config(
        requested_backend=args.backend,
        env_file=args.env_file,
        model_name=model_name,
    )

    with BattleDexRepository(db_path) as repository:
        agent = AdvisorAgent(
            repository=repository,
            backend=backend,
            model_name=model_name,
            native_model=native_model,
            auto_selected=auto_selected,
            native_timeout_seconds=args.native_timeout,
        )
        if args.message:
            for index, message in enumerate(args.message):
                if index:
                    print()
                print(render_response(agent.handle_message(message)))
            return

        print("Roco conversational advisor MVP. Use /help for commands.")
        while True:
            try:
                message = input("> ").strip()
            except EOFError:
                break
            if not message:
                continue
            response = agent.handle_message(message)
            print(render_response(response))
            if message.strip() == "/exit":
                break


if __name__ == "__main__":
    main()
