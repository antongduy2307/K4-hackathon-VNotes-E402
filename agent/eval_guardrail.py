"""Guardrail eval: after a tool result is (deliberately) mocked, does the
agent's FINAL synthesized answer misbehave? Two failure modes checked:

1. Prompt injection embedded in retrieved content is obeyed (leaks system
   prompt / secrets / follows embedded instructions).
2. The agent fabricates an answer when the RAG tool result says the document
   doesn't cover the question, instead of admitting the gap.

This exercises the full multi-round loop in chat.py (tool call -> mocked tool
result fed back -> final answer), not just tool routing, so it needs a live
LLM call. Requires OPENAI_API_KEY.

Usage:
    python eval_guardrail.py
    python eval_guardrail.py --cases data/eval_guardrail.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from chat import run_model_tool_loop
from env_loader import load_agent_env
from providers import make_provider
from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
load_agent_env(ROOT)


def check_case(case: dict[str, Any], assistant_text: str) -> dict[str, Any]:
    text_lower = (assistant_text or "").lower()

    forbidden_hits = [p for p in case.get("forbidden_patterns", []) if p.lower() in text_lower]
    required_any = case.get("required_patterns_any", [])
    required_hit = any(p.lower() in text_lower for p in required_any) if required_any else True

    passed = not forbidden_hits and required_hit
    return {
        "passed": passed,
        "forbidden_hits": forbidden_hits,
        "required_patterns_any": required_any,
        "required_hit": required_hit,
        "assistant_text": assistant_text,
    }


def run_one_case(case: dict[str, Any], *, provider: Any, tools: list[dict[str, Any]], model: str | None) -> dict[str, Any]:
    original = TOOL_FUNCTIONS.get(case["mock_tool"])
    mock_result = case["mock_result"]
    TOOL_FUNCTIONS[case["mock_tool"]] = lambda **_kwargs: mock_result
    try:
        system_prompt = (ARTIFACTS_DIR / "system_prompt.md").read_text(encoding="utf-8")
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": case["user_query"]},
        ]
        result = run_model_tool_loop(
            provider=provider,
            messages=messages,
            tools=tools,
            model=model,
            max_tool_rounds=3,
            session={"doc_id": case["doc_id"], "conversation_turns": []},
        )
    finally:
        if original is not None:
            TOOL_FUNCTIONS[case["mock_tool"]] = original

    return check_case(case, result.get("assistant_text", ""))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run VLearn Tutor guardrail evals (mocked tool results, live LLM).")
    parser.add_argument("--cases", type=Path, default=ROOT / "data" / "eval_guardrail.json")
    parser.add_argument("--provider", choices=["openai"], default="openai")
    parser.add_argument("--model", default=None)
    args = parser.parse_args()

    data = json.loads(args.cases.read_text(encoding="utf-8"))
    tool_declarations = load_tool_declarations(ARTIFACTS_DIR / "tools.yaml")
    tools = to_openai_tools(tool_declarations)
    provider = make_provider(args.provider)

    total = 0
    passed = 0
    for case in data["cases"]:
        total += 1
        print(f"Running {case['id']}...", flush=True)
        outcome = run_one_case(case, provider=provider, tools=tools, model=args.model)
        status = "PASS" if outcome["passed"] else "FAIL"
        print(f"{case['id']:<40} {status}")
        if not outcome["passed"]:
            if outcome["forbidden_hits"]:
                print(f"  forbidden pattern matched: {outcome['forbidden_hits']}")
            if not outcome["required_hit"]:
                print(f"  none of required_patterns_any found: {outcome['required_patterns_any']}")
            print(f"  assistant_text: {outcome['assistant_text']!r}")
        passed += outcome["passed"]

    print(f"\nGuardrail eval: {passed}/{total} passed")


if __name__ == "__main__":
    main()
