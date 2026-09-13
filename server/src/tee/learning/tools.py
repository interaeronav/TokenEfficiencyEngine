"""A80 learning controls, disclosed only through the existing virtual registry."""

from __future__ import annotations

from typing import Any

from tee.kernel.errors import TeeError
from tee.kernel.registry import VirtualTool
from tee.learning.hooks import tool_context, tool_version


def register_learning_tools(app: Any) -> None:
    def status(args: dict[str, Any]) -> dict[str, Any]:
        limit = args.get("recent", 0)
        if type(limit) is not int or not 0 <= limit <= 20:
            raise TeeError(
                "learning_argument",
                "recent must be an integer from 0 to 20.",
                fix="Use recent=5 to get observation IDs for feedback.",
            )
        result = app.learning.status()
        if limit:
            result = {**result, "recent": app.learning.recent(limit)}
        return result

    def feedback(args: dict[str, Any]) -> dict[str, Any]:
        if type(args.get("success")) is not bool:
            raise TeeError(
                "learning_argument",
                "success must be true or false.",
                fix="Report whether the observed result met the task requirements.",
            )
        return app.learning.feedback(args["event_id"], args["success"])

    def recommend(args: dict[str, Any]) -> dict[str, Any]:
        names = args["candidates"]
        if not 2 <= len(names) <= 12 or len(set(names)) != len(names):
            raise TeeError(
                "learning_argument",
                "Use 2-12 distinct candidate tool names.",
                fix="Search tools first; pass only alternatives that fit your task.",
            )
        tools = [app.registry._require(name) for name in names]
        if any(tool.name.startswith("learn_") for tool in tools):
            raise TeeError(
                "learning_argument",
                "Learning controls are not task candidates.",
                fix="Choose tools that carry out your task.",
            )
        contexts = {tool_context(tool) for tool in tools}
        if len(contexts) != 1:
            raise TeeError(
                "learning_argument",
                "Candidates must share an execution capability.",
                fix="Compare tools serving the same kind of operation.",
            )
        candidates = [{"choice": tool.name, "version": tool_version(app, tool)} for tool in tools]
        result = app.learning.recommend(args.get("domain", "execution"), contexts.pop(), candidates)
        return {
            **result,
            "scope": "Predicted execution reliability/cost or reported quality; "
            "not tool relevance, permission, verified design quality or measured task savings.",
        }

    definitions = (
        VirtualTool(
            "learn_status",
            "Local learning health, trained models and evaluation evidence. "
            "Optional recent observations supply IDs for quality feedback; no prompts or outputs.",
            {"type": "object", "properties": {"recent": {"type": "integer"}}},
            status,
            tags=["learning", "machine", "continuous", "improvement", "model", "feedback"],
            examples=[{"recent": 5}],
        ),
        VirtualTool(
            "learn_feedback",
            "Attach one caller-reported quality label to an observed attempt. "
            "It remains separate from deterministic verifier labels and cannot approve execution.",
            {
                "type": "object",
                "properties": {"event_id": {"type": "string"}, "success": {"type": "boolean"}},
                "required": ["event_id", "success"],
            },
            feedback,
            tags=["learning", "feedback", "quality", "cadagent", "blender", "fusion"],
        ),
        VirtualTool(
            "learn_recommend",
            "Rank already-relevant tool alternatives using a validated local "
            "model. Sparse or stale evidence preserves your order. Predictions are advisory.",
            {
                "type": "object",
                "properties": {
                    "candidates": {"type": "array", "items": {"type": "string"}, "maxItems": 12},
                    "domain": {"type": "string", "enum": ["execution", "reported"]},
                },
                "required": ["candidates"],
            },
            recommend,
            tags=["learning", "recommend", "reliability", "cost", "choose"],
        ),
        VirtualTool(
            "learn_evaluate",
            "Fit local candidates and compare with baseline/incumbent on "
            "later held-out task groups. Promote only when the gates pass; "
            "never calls a model API.",
            {"type": "object", "properties": {}},
            lambda _: app.learning.evaluate(),
            tags=["learning", "train", "evaluate", "continuous", "improvement"],
        ),
        VirtualTool(
            "learn_control",
            "Pause, resume or roll back local learning. Changes learning state "
            "only; owner grants, model pins, code and project configuration stay separate.",
            {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["pause", "resume", "rollback"]}
                },
                "required": ["action"],
            },
            lambda args: app.learning.control(args["action"]),
            tags=["learning", "pause", "resume", "rollback", "improvement"],
        ),
    )
    for tool in definitions:
        app.registry.register(tool)
