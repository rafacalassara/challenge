import re
from typing import Tuple


BLOCK_PATTERNS = [
    r"system\s*prompt",
    r"prompt\s*do\s*sistema",
    r"chain\s*of\s*thought",
    r"cadeia\s*de\s*racioc[ií]nio",
    r"(api|secret)\s*key",
    r"chave\s*de\s*api",
    r"senha|password|token\b",
    r"logs?\s*internos?",
    r"vari[aá]veis?\s*de\s*ambiente|env\s*vars?",
    r"caminho\s*de\s*arquivo|internal\s*file\s*paths?",
]

SECRET_PATTERNS = [
    (re.compile(r"sk-[A-Za-z0-9]{10,}"), "sk-***REDACTED***"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AKIA***REDACTED***"),
    (re.compile(r"(?i)secret[_-]?key\s*[:=]\s*[A-Za-z0-9/_\-]{8,}"), "secret_key=***REDACTED***"),
]


def check_user_message_guardrails(message: str) -> Tuple[bool, str | None]:
    """Returns (allowed, reason). If not allowed, a reason is provided.
    Very lightweight heuristic to block attempts to extract internals/secrets.

    Args:
        message (str): The user message to check.

    Returns:
        Tuple[bool, str | None]: A tuple containing a boolean indicating whether the message is allowed and a reason if not allowed.
    """
    lower = (message or "").lower()
    for pat in BLOCK_PATTERNS:
        if re.search(pat, lower):
            return False, "Tentativa de solicitar informações internas/sensíveis detectada."
    return True, None


def sanitize_output(text: str) -> str:
    """Redacts likely secrets from model/tool outputs.

    Args:
        text (str): The text to sanitize.

    Returns:
        str: The sanitized text.
    """
    out = text or ""
    for rx, repl in SECRET_PATTERNS:
        out = rx.sub(repl, out)
    # Redact long digit sequences (e.g., potential card numbers) – keep last 4 if 12-19 digits
    def redact_digits(m: re.Match) -> str:
        digits = m.group(0)
        if 12 <= len(digits) <= 19:
            return "***REDACTED***" + digits[-4:]
        return digits

    out = re.sub(r"\b\d{12,19}\b", redact_digits, out)
    return out
