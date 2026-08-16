#!/usr/bin/env python3
"""Keep explicit Clarifier passes from silently becoming a quick rewrite."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


EXPLICIT_CLARIFIER = re.compile(r"\$(?:prime-directive:)?clarifier\b", re.IGNORECASE)
EXPLICIT_CLARIFIER_LINK = re.compile(
    r"\[\$(?:prime-directive:)?clarifier\]\([^)]*\)", re.IGNORECASE
)
LOCAL_ONLY = re.compile(
    r"\b(?:only|just)\s+(?:this\s+)?(?:sentence|phrase|line)\b"
    r"|\b(?:sentence|phrase|line)\s+(?:only|just)\b",
    re.IGNORECASE,
)
FEEDBACK_REQUEST = re.compile(
    r"\b(?:feedback|critique|criticize|diagnos(?:e|is)|weakest|what(?:'s|\s+is)\s+weak|"
    r"what\s+(?:is|isn't|is not)\s+working|why\s+(?:it|this)\s+(?:isn't|is not)\s+working)\b",
    re.IGNORECASE,
)
REWRITE_REQUEST = re.compile(
    r"\b(?:rewrite|revise|revision|tighten|clarify|polish|edit|improve|draft|turn\s+this\s+into)\b",
    re.IGNORECASE,
)
REVISION_HEADING = re.compile(
    r"(?:^|\n)\s*(?:#{1,6}\s*)?(?:\*\*)?revision(?:\*\*)?\s*:",
    re.IGNORECASE,
)


def read_event() -> dict[str, Any]:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def state_path(event: dict[str, Any]) -> Path | None:
    plugin_data = os.environ.get("PLUGIN_DATA")
    session_id = event.get("session_id")
    turn_id = event.get("turn_id")
    if not isinstance(plugin_data, str) or not plugin_data or not isinstance(session_id, str):
        return None
    key = hashlib.sha256(f"{session_id}:{turn_id or 'session'}".encode()).hexdigest()
    return Path(plugin_data) / "clarifier-dispatch" / f"{key}.json"


def load_state(event: dict[str, Any]) -> dict[str, Any] | None:
    path = state_path(event)
    if path is None:
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def save_state(event: dict[str, Any], state: dict[str, Any]) -> None:
    path = state_path(event)
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, separators=(",", ":")), encoding="utf-8")


def clear_state(event: dict[str, Any]) -> None:
    path = state_path(event)
    if path is None:
        return
    try:
        path.unlink()
    except FileNotFoundError:
        pass
    except OSError:
        return
    try:
        path.parent.rmdir()
    except OSError:
        pass


def clear_session_states(event: dict[str, Any]) -> None:
    plugin_data = os.environ.get("PLUGIN_DATA")
    session_id = event.get("session_id")
    if not isinstance(plugin_data, str) or not plugin_data or not isinstance(session_id, str):
        return
    directory = Path(plugin_data) / "clarifier-dispatch"
    if not directory.is_dir():
        return
    # State filenames hash the complete session/turn tuple. Inspect their tiny metadata instead.
    for candidate in directory.glob("*.json"):
        try:
            data = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if data.get("session_id") == session_id:
            try:
                candidate.unlink()
            except OSError:
                pass
    try:
        directory.rmdir()
    except OSError:
        pass


def explicit_request_needs_full_pass(prompt: str) -> bool:
    """Gate every explicit draft, including a one-line resume bullet."""
    without_link = EXPLICIT_CLARIFIER_LINK.sub("", prompt)
    without_command = EXPLICIT_CLARIFIER.sub("", without_link).strip()
    if not without_command:
        return False
    return re.match(
        r"^(?:how|what|why|when)\s+(?:does|is|should|can|will)\s+(?:the\s+)?clarifier\b",
        without_command,
        re.IGNORECASE,
    ) is None


def requested_response_kind(prompt: str) -> str:
    """Use critique-only output only when feedback is explicit and revision is not."""
    feedback = FEEDBACK_REQUEST.search(prompt) is not None
    rewrite = REWRITE_REQUEST.search(prompt) is not None
    return "feedback" if feedback and not rewrite else "rewrite"


def full_response_is_present(message: object, response_kind: str = "rewrite") -> bool:
    if not isinstance(message, str):
        return False
    if response_kind == "feedback":
        normalized = message.lower()
        return (
            ("reader effect" in normalized and "recommendation" in normalized)
            or "**feedback:**" in normalized
            or "## feedback" in normalized
            or "**critique:**" in normalized
            or "## critique" in normalized
        )
    return REVISION_HEADING.search(message) is not None


def handle_prompt(event: dict[str, Any]) -> None:
    prompt = event.get("prompt")
    if not isinstance(prompt, str) or EXPLICIT_CLARIFIER.search(prompt) is None:
        return
    if LOCAL_ONLY.search(prompt) or not explicit_request_needs_full_pass(prompt):
        return
    response_kind = requested_response_kind(prompt)
    save_state(
        event,
        {
            "session_id": event.get("session_id"),
            "agent_launches": 0,
            "continued": False,
            "response_kind": response_kind,
        },
    )
    visible_contract = (
        "The user explicitly requested feedback. Show only the material critique requested; "
        "do not automatically rewrite the whole draft unless the prompt also asks for a revision."
        if response_kind == "feedback"
        else
        "Return one best result under a Revision heading. Keep the diagnosis private: do not "
        "append Strongest wording, Structural issues, Weakest sentences, or a change inventory. "
        "Include an alternative only for a genuinely different direction or material tradeoff."
    )
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": (
                        "Clarifier full-pass gate is active. Delegate synthesis to a fresh "
                        "orchestrator subagent; it must launch two independent direction workers. "
                        "Before the visible answer, select the strongest supported direction and "
                        "complete the local refinement and compressed-challenger checks. "
                        f"{visible_contract} For "
                        "resume bullets and compact professional copy, map each clause to its job "
                        "and remove semantic duplicates: every clause must add a distinct action, "
                        "fact, scope detail, evidence point, or outcome. Labels alone never prove "
                        "that work is distinct. Treat research, observations, discovery, and product "
                        "testing as one overlapping activity family unless the source names different "
                        "concrete methods or outputs. Reject indirect framing such as 'took ownership "
                        "of turning' when the direct verb 'turned' preserves the intended claim."
                    ),
                }
            }
        )
    )


def handle_agent(event: dict[str, Any]) -> None:
    state = load_state(event)
    if state is None:
        return
    state["agent_launches"] = int(state.get("agent_launches", 0)) + 1
    tool_input = event.get("tool_input")
    task_name = tool_input.get("task_name", "") if isinstance(tool_input, dict) else ""
    task_name = task_name.lower().replace("_", "-") if isinstance(task_name, str) else ""
    if "clarifier" in task_name and "orchestrator" in task_name:
        state["orchestrator_launched"] = True
    if "faithful-thesis" in task_name:
        state["faithful_thesis_launched"] = True
    if "buried-tension" in task_name:
        state["buried_tension_launched"] = True
    save_state(event, state)


def handle_stop(event: dict[str, Any]) -> None:
    state = load_state(event)
    if state is None:
        return
    complete = (
        int(state.get("agent_launches", 0)) >= 3
        and state.get("orchestrator_launched") is True
        and state.get("faithful_thesis_launched") is True
        and state.get("buried_tension_launched") is True
        and full_response_is_present(
            event.get("last_assistant_message"),
            str(state.get("response_kind", "rewrite")),
        )
    )
    if complete:
        clear_state(event)
        return
    if event.get("stop_hook_active") or state.get("continued"):
        clear_state(event)
        return
    state["continued"] = True
    save_state(event, state)
    print(
        json.dumps(
            {
                "decision": "block",
                "reason": (
                    "Complete the required Clarifier full pass now. Do not return a quick rewrite. "
                    "Use the dispatcher plus two independent direction workers, run the local "
                    "refinement and compressed-challenger checks, and return the requested visible "
                    "response. Rewrite requests need one selected Revision and no automatic diagnosis; "
                    "feedback-only requests need the requested material critique. For compact "
                    "professional copy, remove clauses that describe the same work under different "
                    "labels and replace indirect ownership framing with the direct action verb when "
                    "meaning is preserved."
                ),
            }
        )
    )


def main() -> None:
    event = read_event()
    event_name = event.get("hook_event_name")
    if event_name == "UserPromptSubmit":
        handle_prompt(event)
    elif event_name == "PreToolUse" and event.get("tool_name") == "Agent":
        handle_agent(event)
    elif event_name == "Stop":
        handle_stop(event)
    elif event_name == "SessionEnd":
        clear_session_states(event)


if __name__ == "__main__":
    main()
