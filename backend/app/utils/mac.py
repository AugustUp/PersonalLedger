"""MAC address normalization to AA:BB:CC:DD:EE:FF (uppercase, colon separated)."""
import re

_MAC_RE = re.compile(r"^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$")


def normalize_mac(value: str | None) -> str | None:
    """Return normalized MAC or raise ValueError if it cannot be parsed."""
    if value is None:
        return None
    s = value.strip().upper()
    if s == "":
        return None
    # strip any separators and validate 12 hex chars
    cleaned = re.sub(r"[^0-9A-Fa-f]", "", s)
    if len(cleaned) != 12 or not re.fullmatch(r"[0-9A-Fa-f]{12}", cleaned):
        raise ValueError(f"非法 MAC 地址: {value}")
    parts = [cleaned[i:i + 2] for i in range(0, 12, 2)]
    return ":".join(parts)


def normalize_ip(value: str | None) -> str | None:
    """Light validation / normalization for IPv4/IPv6."""
    if value is None:
        return None
    s = value.strip()
    if s == "":
        return None
    return s
