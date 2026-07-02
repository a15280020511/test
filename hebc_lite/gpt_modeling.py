from __future__ import annotations

from typing import Any

from .schemas import Task
from .router import MESA_KEYWORDS


def build_modeling_result(task: Task, mesa_needed: bool = False, mesa_reason: str | None = None) -> dict[str, Any]:
    question = task.question.lower()
    return {
        "variables": _build_variables(task),
        "assumptions": _build_assumptions(task),
        "causal_chain": [
            "Environment and constraints define the option space.",
            "Resources, cost, compliance, and physical load shape net return and sustainability.",
            "High-uncertainty variables require warning indicators and stop-loss rules.",
            "The final path should prefer low legal risk, low sunk cost, and reversible testing.",
        ],
        "scenario_tree": {
            "base_case": "Use conservative assumptions and validate with a small trial.",
            "upside_case": "If key variables improve, scale only after evidence is collected.",
            "downside_case": "If return, compliance, or health variables worsen, trigger stop-loss.",
        },
        "risk_factors": _build_risks(task),
        "decision_options": _build_options(task),
        "mesa_recommendation": {
            "needed": mesa_needed,
            "reason": mesa_reason,
            "matched_keywords": sorted(k for k in MESA_KEYWORDS if k in question),
        },
        "uncertainties": [
            "Without real cost and demand data, the result is structured judgment rather than strict numerical simulation.",
            "External model output is evidence or review input, not final truth.",
        ],
    }


def _build_variables(task: Task) -> list[dict[str, str]]:
    variables = [
        {"name": "net_income", "description": "Income after cost, deposits, rent, platform fees, and time cost."},
        {"name": "compliance_risk", "description": "License, platform rule, contract, and work constraint risk."},
        {"name": "health_load", "description": "Sleep, physical load, accident risk, and long-term sustainability."},
        {"name": "maintenance_cost", "description": "Learning, equipment, deposits, accounts, and time management."},
        {"name": "reversibility", "description": "Ability to exit after trial without high sunk cost."},
    ]
    for item in task.constraints.must_have:
        variables.append({"name": item, "description": "User-required decision variable."})
    return variables


def _build_assumptions(task: Task) -> list[str]:
    assumptions = [
        "Prefer low maintenance, low cost, and low legal risk.",
        "Do not assume high deposit, vehicle purchase, or long-term heavy labor is acceptable unless explicitly allowed.",
        "Version one uses structural modeling first and does not disguise language reasoning as strict numerical simulation.",
    ]
    for avoid in task.constraints.avoid:
        assumptions.append(f"Hard avoid constraint: {avoid}.")
    return assumptions


def _build_risks(task: Task) -> list[dict[str, str]]:
    return [
        {"risk": "overconfidence", "control": "Require red-team objections and disconfirming variables."},
        {"risk": "hidden_cost", "control": "Include deposits, equipment, commute, and sleep loss in total cost."},
        {"risk": "model_error", "control": "Expose uncertainty instead of pretending certainty."},
        {"risk": "illegal_path", "control": "Reject unlicensed or high-risk routes."},
    ]


def _build_options(task: Task) -> list[dict[str, str]]:
    return [
        {"option": "status_quo", "description": "Keep the current path as a low-risk baseline."},
        {"option": "small_trial", "description": "Run a low-deposit, short-cycle, reversible test."},
        {"option": "reject_high_risk", "description": "Reject high-deposit, illegal, or sleep-damaging routes."},
    ]
