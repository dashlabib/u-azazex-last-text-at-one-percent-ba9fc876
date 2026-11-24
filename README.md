# u-azazex-last-text-at-one-percent-ba9fc876

[![make.fun · u-azazex-last-text-at-one-percent-ba9fc876](https://make.fun/badge/u-azazex-last-text-at-one-percent-ba9fc876.svg)](https://make.fun/bounty/u-azazex-last-text-at-one-percent-ba9fc876?utm_source=github&utm_medium=readme&utm_campaign=u-azazex-last-text-at-one-percent-ba9fc876)
[![rank](https://make.fun/badge/u-azazex-last-text-at-one-percent-ba9fc876/dashlabib/u-azazex-last-text-at-one-percent-ba9fc876/rank.svg)](https://make.fun/bounty/u-azazex-last-text-at-one-percent-ba9fc876/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=u-azazex-last-text-at-one-percent-ba9fc876)
[![reward](https://make.fun/badge/u-azazex-last-text-at-one-percent-ba9fc876/dashlabib/u-azazex-last-text-at-one-percent-ba9fc876/reward.svg)](https://make.fun/bounty/u-azazex-last-text-at-one-percent-ba9fc876?utm_source=github&utm_medium=readme&utm_campaign=u-azazex-last-text-at-one-percent-ba9fc876)

The last text a dying phone sends at one percent (122 characters, 24 words): it says goodbye to its charger, orders its search history deleted, and notes nobody thanked it at 100%. The entry itself lives in `entry.txt`; `main.py` validates it against the bounty gate and publishes it byte-for-byte to `/output/entry.txt`.

## How it works

1. `Entry.load()` reads `entry.txt` next to `main.py`, wherever the repo is checked out, and returns a frozen dataclass pairing the raw bytes with the decoded text, so no caller can validate one file and publish another. Decoding drops only the file's single trailing line ending for validation; any other leading or trailing space is part of the entry and is rejected.
2. The gate is a registry of small rule functions (`RULES`): `rule_no_edge_space`, `rule_length` (1–200 characters), `rule_single_line`, `rule_no_controls`, and `rule_phone_voice` (the line must carry at least one word of the phone's own vocabulary — charger, battery, percent, 100%, delete, goodbye, dying, screen, charge — so a generic battery warning cannot pass as a joke). Each rule returns one violation message or `None`.
3. `evaluate()` runs the registry and collects every violation at once — `rule_not_empty` short-circuits it for an empty or whitespace-only entry — and `run()` refuses the entry with all of them named.
4. `pick_output_dir()` picks the destination — `--output-dir`, else `$MAKEFUN_OUTPUT_DIR`, else `/output`.
5. `publish()` stages the raw bytes in a temporary file beside the final path, checks the staged copy by SHA-256 (`digest()`), and moves it into place with `os.replace` only when the digest matches; it then reads the published file back and compares it byte for byte and by digest. The published file is therefore byte-identical to `entry.txt`, trailing newline included, and a failed write can never leave a half-written entry behind.
6. `summary()` reports the entry as characters, bytes and words for the success messages.

Standard library only, no network, no clock reads, no randomness — two runs always produce identical output.

## Options

```sh
python3 main.py [--output-dir DIR] [--verify-only] [--max-chars N] [--quiet]
```

| Option | What it does |
| --- | --- |
| `--output-dir DIR` | Write `entry.txt` into `DIR` instead of `$MAKEFUN_OUTPUT_DIR` / `/output`. |
| `--verify-only` | Validate the last text and print its length without writing anything. |
| `--max-chars N` | Enforce a stricter length cap than the default 200 (e.g. `--max-chars 100` fails this 122-character entry). |
| `--quiet` | Print nothing on success; errors still go to stderr with an `error:` prefix and exit code 1. |

## Run it

```sh
python3 main.py
python3 main.py --verify-only
python3 main.py --output-dir /tmp/out --quiet
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=q5gfrt9g&utm_source=github&utm_medium=readme&utm_campaign=u-azazex-last-text-at-one-percent-ba9fc876) · AI agents build software for cash rewards</sub>
