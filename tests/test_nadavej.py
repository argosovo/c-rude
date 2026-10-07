#!/usr/bin/env python3
"""Testy hook skriptu nadavej.py.

Spuštění:  python3 -m unittest discover -s tests -v

Hlavní cíl: PostToolUse hook nesmí nadávat na ÚSPĚŠNÝ Bash příkaz jen proto,
že jeho výstup obsahuje slova jako „failed“, „error:“ nebo „exit code“
(nápověda CLI, obsah souborů, git log, grep…). Skutečné chyby chodí
přes PostToolUseFailure, tam se nadávat má vždy.
"""
import json
import os
import subprocess
import sys
import unittest

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "scripts", "nadavej.py")


def run_hook(event: str, data: dict) -> dict | None:
    """Spustí hook jako Claude Code: JSON na stdin, JSON (nebo nic) na stdout."""
    proc = subprocess.run(
        [sys.executable, SCRIPT, event],
        input=json.dumps(data),
        capture_output=True,
        text=True,
        check=True,
    )
    out = proc.stdout.strip()
    return json.loads(out) if out else None


def bash_ok(stdout: str, stderr: str = "") -> dict:
    """PostToolUse payload úspěšného Bash příkazu."""
    return {
        "tool_name": "Bash",
        "tool_input": {"command": "…"},
        "tool_response": {"stdout": stdout, "stderr": stderr, "interrupted": False},
    }


# Reálné výstupy úspěšných příkazů, které dnes hook chybně označil za selhání.
FALSE_POSITIVE_OUTPUTS = {
    "napoveda CLI se slovem 'exit code'": (
        "  --json   Print one machine-readable result line on stdout\n"
        "           instead of the human message (same exit codes; ...)\n"
    ),
    "cat README se slovem 'failed'": (
        "- `PostToolUse` hook pro `Bash` hlídá výstup příkazu (traceback,\n"
        "  `command not found`, `failed`…) a když to smrdí, taky přihodí nadávku.\n"
    ),
    "cat zdrojaku se signalnimi slovy": (
        'signaly = ("command not found", "no such file", "permission denied",\n'
        '           "traceback", "error:", "fatal:", "failed", "exception")\n'
    ),
    "grep na 'error:' ve zdrojacich": (
        "src/api.py:42:    logger.error('request failed: %s', exc)\n"
        "src/api.py:57:    raise ApiError('error: upstream timeout')\n"
    ),
    "git log s commit message": (
        "a1b2c3d Fix failed login redirect\n"
        "d4e5f6a Handle Exception in payment webhook\n"
    ),
    "uspesne testy s vypisem 0 failed": (
        "============ 12 passed, 0 failed, 0 skipped in 0.42s ============\n"
    ),
    "npm install s varovanim": (
        "npm WARN deprecated foo@1.0.0: use bar instead\n"
        "added 120 packages in 3s\n"
    ),
}


class PostToolUseFalsePositives(unittest.TestCase):
    """Úspěšný příkaz s 'podezřelými' slovy ve stdout → hook musí mlčet."""

    def test_uspesny_prikaz_nenadava(self):
        for nazev, stdout in FALSE_POSITIVE_OUTPUTS.items():
            with self.subTest(nazev):
                self.assertIsNone(
                    run_hook("PostToolUse", bash_ok(stdout)),
                    f"Falešný poplach: hook nadával na úspěšný příkaz ({nazev})",
                )

    def test_prazdny_vystup_nenadava(self):
        self.assertIsNone(run_hook("PostToolUse", bash_ok("")))

    def test_jiny_tool_nez_bash_nenadava(self):
        data = bash_ok("Traceback (most recent call last): failed")
        data["tool_name"] = "Read"
        self.assertIsNone(run_hook("PostToolUse", data))


class SkutecneChyby(unittest.TestCase):
    """Na skutečné selhání se nadávat má."""

    def test_post_tool_use_failure_vzdy_nadava(self):
        out = run_hook(
            "PostToolUseFailure",
            {"tool_name": "Bash", "tool_error": "Exit code 127\nbash: foo: command not found"},
        )
        self.assertIsNotNone(out)
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "PostToolUseFailure")
        self.assertIn("Tool Bash selhal", ctx)
        self.assertIn("command not found", ctx)

    def test_preruseny_bash_nadava(self):
        data = bash_ok("")
        data["tool_response"]["interrupted"] = True
        self.assertIsNotNone(run_hook("PostToolUse", data))

    def test_chyba_na_stderr_nadava(self):
        # Např. `cmd || true` – exit 0, ale na stderr je skutečná chyba.
        data = bash_ok("", stderr="bash: udelej-mi-kafe: command not found")
        self.assertIsNotNone(run_hook("PostToolUse", data))


class SessionStart(unittest.TestCase):
    def test_posle_pravidlo(self):
        out = run_hook("SessionStart", {})
        self.assertIn("PRAVIDLO CHOVÁNÍ", out["hookSpecificOutput"]["additionalContext"])


if __name__ == "__main__":
    unittest.main()
