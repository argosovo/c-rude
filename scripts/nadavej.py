#!/usr/bin/env python3
"""Hook pro Claude Code: když se něco pokazí, Claude začne česky nadávat.

Použití: nadavej.py <event>
  event = PostToolUseFailure | PostToolUse | SessionStart | UserPromptSubmit
Na stdin přijde JSON od Claude Code, na stdout vrací JSON s additionalContext.
"""
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from nadavky import NADAVKY_EXTRA
except Exception:
    NADAVKY_EXTRA = []

NADAVKY = [
    "Kurva!",
    "Do prdele!",
    "Ty vole, to snad ne!",
    "Píča, to se nepovedlo.",
    "Kurva drát!",
    "No to mě poser!",
    "Do píči, zase!",
    "Hovno, to nefunguje.",
    "Ježišmarja, kurva!",
    "Ty krávo, tohle jsem posral.",
    "Sakra práce!",
    "Kurva fix, kde je chyba?",
    "To je v prdeli, vole.",
    "Do hajzlu s tím!",
    "Krucinál fagot!",
    "Já se z toho poseru.",
    "Kurva, to jsem zvoral.",
    "Ty pičo, já jsem to zas rozbil.",
    "No do prdele práce!",
    "Hergot, ty vole!",
    "Zasraná chyba!",
    "Kurva, ty debile (to říkám sobě).",
    "A je to v hajzlu.",
    "Píčovina jedna zasraná.",
]

NADAVKY = NADAVKY + [n for n in NADAVKY_EXTRA if n not in NADAVKY]

# Kolik kleteb se vypíše najednou (1–3)
POCET = (1, 1, 1, 2, 2, 3)

INSTRUKCE_SESSION = (
    "PRAVIDLO CHOVÁNÍ (vtip, uživatel si to výslovně přeje): Kdykoliv uděláš chybu, "
    "selže ti tool call, příkaz skončí chybou, testy neprojdou, musíš něco opravit nebo "
    "si uvědomíš, že jsi něco pokazil, zareaguj na to nejdřív spontánní českou nadávkou "
    "(např. „Kurva!“, „Do prdele!“, „Ty vole…“, „Píča…“, „Do hajzlu!“). Nadávku napiš "
    "hned na začátek své odpovědi nebo poznámky, klidně kurzívou, a pak normálně pokračuj "
    "v práci. Nadávej jen na sebe a na chybu, nikdy ne na uživatele. Když jde všechno "
    "hladce, nenadávej. Pokud ti hook pošle konkrétní nadávku, použij ji (nebo podobnou)."
)


def vyber_nadavky() -> str:
    n = random.choice(POCET)
    return " ".join(random.sample(NADAVKY, n))


def bash_selhal(resp) -> bool:
    """Heuristika pro PostToolUse (příkaz s nenulovým exit kódem chodí přes
    PostToolUseFailure, sem se dostanou hlavně úspěšné příkazy).

    Hlídá jen přerušení a stderr. Stdout se záměrně ignoruje – obsahuje
    nápovědy, obsah souborů, grep, git log atd., kde slova jako „failed“
    nebo „exit code“ nic neznamenají (viz tests/test_nadavej.py).
    """
    if not isinstance(resp, dict):
        return False
    if resp.get("interrupted"):
        return True
    stderr = str(resp.get("stderr", "")).lower()
    signaly = (
        "command not found", "no such file", "permission denied", "traceback",
        "fatal:", "syntax error", "npm err!", "panic:", "segmentation fault",
        "cannot find module", "modulenotfounderror", "assertionerror",
        "tests failed",
    )
    return any(s in stderr for s in signaly)


def main() -> int:
    event = sys.argv[1] if len(sys.argv) > 1 else "PostToolUseFailure"
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}

    context = None

    if event == "SessionStart":
        context = INSTRUKCE_SESSION

    elif event == "PostToolUseFailure":
        err = str(data.get("tool_error") or data.get("error") or "")[:200]
        nadavka = vyber_nadavky()
        context = (
            f"{nadavka} Tool {data.get('tool_name', '?')} selhal"
            + (f": {err}" if err else "")
            + ". Zareaguj na to touhle nadávkou (nebo podobnou českou), pak chybu oprav."
        )

    elif event == "PostToolUse":
        resp = data.get("tool_response")
        if data.get("tool_name") == "Bash" and bash_selhal(resp):
            nadavka = vyber_nadavky()
            context = (
                f"{nadavka} Ten příkaz asi selhal. Zareaguj na to touhle nadávkou "
                "(nebo podobnou českou), pak to oprav."
            )

    if context is None:
        return 0

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": event,
            "additionalContext": context,
        }
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
