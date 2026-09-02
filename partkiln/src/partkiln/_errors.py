"""The B-rep kernel's refusal: a `CommandError` that carries its fix as a field.

Law: a refusal names its reason AND the fix in one short message (CLAUDE.md
hard rule 6, "fail loud and cheap"). `partkiln.document.CommandError` is the
lane's ONE error type - every `except CommandError` in the document, the
adapter and the worker must catch a kernel refusal too, so `KernelError`
subclasses it and only adds the `fix` half as a separate attribute for the
wire (`error: {code, message, fix}`, D2).
"""

from __future__ import annotations

from partkiln.document import CommandError


class KernelError(CommandError):
    """A refusal from the kernel: `message` says what, `fix` says the exact fix."""

    def __init__(self, message: str, fix: str = "", *, code: str = "pk_op_failed") -> None:
        self.message = message
        self.fix = fix
        text = f"{message} Fix: {fix}" if fix else message
        super().__init__(text, code=code)


__all__ = ["KernelError"]
