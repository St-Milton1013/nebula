"""Commander construction and legality checks.

Every check returns a Finding with an explicit status. A check that cannot be
made is UNSUPPORTED, never silently skipped - the module contract requires a
caveat (NEBULA-CONTRACT-P0.md §4).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .cardtruth import CardTruth
from .importer import BASIC_LANDS, Deck

VERIFIED = "VERIFIED"
FAIL = "FAIL"
PARTIAL = "PARTIAL"
UNSUPPORTED = "UNSUPPORTED"


@dataclass
class Finding:
    code: str
    status: str
    detail: str
    cards: list[str] = field(default_factory=list)
    severity: str = "error"

    def as_dict(self) -> dict:
        return {
            "code": self.code,
            "status": self.status,
            "severity": self.severity,
            "detail": self.detail,
            "cards": self.cards,
        }


def _has_partner(rec: dict) -> bool:
    text = ((rec.get("ot") or "") + " " + " ".join(
        f.get("oracle_text", "") for f in rec.get("faces") or []
    )).lower()
    if "partner" in text or "choose a background" in text:
        return True
    for kw in rec.get("kw") or []:
        if str(kw).lower().startswith("partner"):
            return True
    return False


def _is_background(rec: dict) -> bool:
    return "background" in (rec.get("tl") or "").lower()


def check(deck: Deck, truth: CardTruth) -> dict:
    findings: list[Finding] = []

    # 1 - deck size (rule 903.5a: 100 cards total, commanders included)
    if deck.total == 100:
        findings.append(Finding("DECK_SIZE", VERIFIED, "100 cards including commanders"))
    else:
        findings.append(Finding(
            "DECK_SIZE", FAIL,
            f"{deck.total} cards including commanders; rule 903.5a requires exactly 100",
        ))

    # 2 - commander count
    n_cmd = sum(e.qty for e in deck.commanders)
    if n_cmd in (1, 2):
        findings.append(Finding("COMMANDER_COUNT", VERIFIED, f"{n_cmd} commander(s)"))
    else:
        findings.append(Finding(
            "COMMANDER_COUNT", FAIL,
            f"{n_cmd} commanders; 1 or 2 required",
            cards=deck.names("commander"),
        ))

    # 3 - partner / background legality, from Oracle text
    if n_cmd == 2:
        recs = [truth.resolve(e.name) for e in deck.commanders]
        if any(r is None for r in recs):
            findings.append(Finding(
                "COMMANDER_PAIRING", PARTIAL,
                "pairing not checked: a commander is missing from card truth",
                cards=[e.name for e, r in zip(deck.commanders, recs) if r is None],
            ))
        else:
            bg = [r for r in recs if _is_background(r)]
            partners = [r for r in recs if _has_partner(r)]
            if len(bg) == 1 and len(partners) == 1:
                findings.append(Finding(
                    "COMMANDER_PAIRING", VERIFIED,
                    "background pairing: one commander chooses a background, the other is a background",
                ))
            elif len(partners) == 2:
                findings.append(Finding(
                    "COMMANDER_PAIRING", VERIFIED,
                    "both commanders carry a partner ability",
                ))
            else:
                findings.append(Finding(
                    "COMMANDER_PAIRING", FAIL,
                    "two commanders and no partner or background ability to legalise the pairing",
                    cards=deck.names("commander"),
                ))

    # 4 - singleton (basic lands exempt)
    seen: dict[str, int] = {}
    for e in deck.mainboard:
        seen[e.name] = seen.get(e.name, 0) + e.qty
    dupes = sorted(n for n, q in seen.items() if q > 1 and n.lower() not in BASIC_LANDS)
    if dupes:
        findings.append(Finding(
            "SINGLETON", FAIL,
            "duplicate non-basic cards in the mainboard",
            cards=dupes,
        ))
    else:
        findings.append(Finding("SINGLETON", VERIFIED, "no duplicate non-basic cards"))

    # 5 - colour identity
    unresolved = [n for n in deck.names()
                  if n.lower() not in BASIC_LANDS and truth.resolve(n) is None]
    if unresolved:
        findings.append(Finding(
            "CARD_RESOLUTION", PARTIAL,
            f"{len(unresolved)} card(s) not found in card truth; identity and legality unchecked for them",
            cards=unresolved,
        ))
    else:
        findings.append(Finding("CARD_RESOLUTION", VERIFIED, "every card resolved"))

    allowed: set[str] = set()
    for e in deck.commanders:
        rec = truth.resolve(e.name)
        if rec:
            allowed |= set(rec.get("ci") or [])
    if unresolved:
        findings.append(Finding(
            "COLOR_IDENTITY", PARTIAL,
            "not fully checked: unresolved cards have no known identity",
        ))
    else:
        offenders = []
        for e in deck.entries:
            rec = truth.resolve(e.name)
            if not rec:
                continue
            outside = set(rec.get("ci") or []) - allowed
            if outside:
                offenders.append(f"{e.name} ({''.join(sorted(outside))})")
        if offenders:
            findings.append(Finding(
                "COLOR_IDENTITY", FAIL,
                f"cards outside the commanders' colour identity ({''.join(sorted(allowed)) or 'colourless'})",
                cards=offenders,
            ))
        else:
            findings.append(Finding(
                "COLOR_IDENTITY", VERIFIED,
                f"all cards within {''.join(sorted(allowed)) or 'colourless'}",
            ))

    # 6 - banned list, from card truth legalities
    banned = [e.name for e in deck.entries
              if (truth.legality(e.name) or "").lower() == "banned"]
    if banned:
        findings.append(Finding("BANNED", FAIL, "cards banned in Commander", cards=sorted(set(banned))))
    elif unresolved:
        findings.append(Finding("BANNED", PARTIAL, "not fully checked: unresolved cards have no legality data"))
    else:
        findings.append(Finding("BANNED", VERIFIED, "no card is banned in Commander"))

    # overall
    if any(f.status == FAIL for f in findings):
        status = FAIL
    elif any(f.status in (PARTIAL, UNSUPPORTED) for f in findings):
        status = PARTIAL
    else:
        status = "AVAILABLE"

    return {
        "status": status,
        "findings": [f.as_dict() for f in findings],
        "summary": {
            "fails": sum(1 for f in findings if f.status == FAIL),
            "partial": sum(1 for f in findings if f.status == PARTIAL),
        },
    }
