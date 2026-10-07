# c-rude – Claude Code plugin

*Claude, rude.* Když Claude udělá chybu (selže tool, příkaz skončí chybou, testy neprojdou…),
začne česky nadávat. *Kurva! Do prdele! Ty vole…* Pak normálně pokračuje v práci.
Čistě vtípek.

## Instalace

Potřebuješ Claude Code CLI a `python3` v PATH (Linux, macOS, WSL).

### Z gitu (doporučeno)

```bash
claude plugin marketplace add <URL-nebo-owner/repo-tohoto-repa>
claude plugin install c-rude@c-rude --scope user
```

Například `claude plugin marketplace add argosovo/c-rude` pro GitHub,
nebo plná URL `https://github.com/argosovo/c-rude.git`.

Aktualizace na novou verzi:

```bash
claude plugin marketplace update c-rude
claude plugin uninstall c-rude@c-rude && claude plugin install c-rude@c-rude --scope user
```

### Ze zipu

Rozbal zip do složky (např. `~/c-rude`) někam natrvalo (Claude Code z té složky čte marketplace) a spusť:

```bash
./install.sh
```

### Jen na zkoušku pro jednu session

```bash
claude --plugin-dir /cesta/k/c-rude
```

### Odinstalace

```bash
claude plugin uninstall c-rude@c-rude
claude plugin marketplace remove c-rude
```

## Jak to funguje

- `SessionStart` hook pošle Claudovi pravidlo: „při chybě nejdřív zanadávej, pak oprav“.
- `PostToolUseFailure` hook při každém selhaném tool callu přihodí náhodnou nadávku.
- `PostToolUse` hook pro `Bash` hlídá přerušení a stderr příkazu (traceback,
  `command not found`, `fatal:`…) a když to smrdí, taky přihodí nadávku. Stdout
  se ignoruje, aby hook nenadával na nápovědu nebo obsah souborů se slovem „failed“.

Základní slovník je v `scripts/nadavej.py` v seznamu `NADAVKY`, rozšířený (500+)
v `scripts/nadavky.py` v seznamu `NADAVKY_EXTRA` – klidně si ho rozšiř.

Po úpravě slovníku zvedni `version` v `.claude-plugin/plugin.json` a plugin
přeinstaluj (Claude Code používá kopii z cache):

```bash
claude plugin uninstall c-rude@c-rude && claude plugin install c-rude@c-rude --scope user
```

## Vývoj

Testy:

```bash
python3 -m unittest discover -s tests -v
```

Test skriptu bez Claude:

```bash
echo '{"tool_name":"Bash","tool_error":"exit 1"}' | python3 scripts/nadavej.py PostToolUseFailure
```

Vytvoření zipu pro kolegy (z kořene projektu, název složky nehraje roli):

```bash
VER=$(python3 -c "import json;print(json.load(open('.claude-plugin/plugin.json'))['version'])")
zip -r ../c-rude-$VER.zip . -x '.git/*' '*__pycache__*' '*.zip'
```
