#!/usr/bin/env python3
"""Publish the dying phone's last text for the make.fun bounty
"Last Text at One Percent".

The message lives in ``entry.txt`` next to this file: the final
text a phone sends at one percent battery, under 200 characters,
in the voice of the dying phone itself — funny, a little
resentful, and in a hurry. This program reads that file as raw
bytes, decodes it as UTF-8, checks the single message against the
bounty gate (1 to 200 characters, not only white space, no
embedded line breaks, and written as a text message, not a
warning label), and publishes the raw bytes verbatim to
``entry.txt`` in the output directory. Publishing is byte-for-byte:
the trailing newline in ``entry.txt`` is formatting of the source
file and is carried over unchanged, never stripped, so the
published file is identical to the source file. After writing, the
program reads the published file back and compares bytes; a
mismatch is a hard failure.

Standard library only: no network access, no clock reads, no
randomness, so two runs always produce identical output.

The output directory is ``--output-dir`` when given, else
``$MAKEFUN_OUTPUT_DIR`` when set, else ``/output``. Pass
``--verify-only`` to check the message without writing anything.
"""

import argparse
import os
import sys
import typing
from pathlib import Path

DEFAULT_MAX_CHARS = 200
MIN_CHARS = 1
DEFAULT_OUTPUT_DIR = "/output"
ENTRY_FILENAME = "entry.txt"

# Words that mark a line as spoken by the phone itself, with a
# personality and a stake in dying, rather than a generic battery
# warning dressed up as a joke.
PHONE_WORDS = (
    "charger",
    "battery",
    "percent",
    "100%",
    "delete",
    "goodbye",
    "dying",
    "screen",
    "charge",
)


def entry_path() -> Path:
    """Return the path of the entry file shipped with this program."""
    return Path(__file__).resolve().parent / ENTRY_FILENAME


def load_raw(path: Path) -> bytes:
    """Read the entry file as raw bytes, failing loudly if unreadable."""
    try:
        return path.read_bytes()
    except FileNotFoundError:
        raise SystemExit(f"entry file not found: {path}")
    except OSError as exc:
        raise SystemExit(f"cannot read entry file {path}: {exc}")


def decode(raw: bytes) -> str:
    """Decode raw entry bytes as UTF-8 and drop the one trailing newline.

    Only the file's single trailing line ending (``\\n`` or ``\\r\\n``)
    is formatting and is removed for validation. Every other byte,
    including any leading or trailing space, is part of the entry and
    is rejected by :func:`validate` below, so a stray space cannot
    slip through unnoticed.
    """
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SystemExit(f"entry is not valid UTF-8: {exc}")
    if text.endswith("\r\n"):
        return text[:-2]
    if text.endswith("\n") or text.endswith("\r"):
        return text[:-1]
    return text


def load_entry() -> tuple:
    """Read the shipped entry file and return ``(raw_bytes, text)``.

    The raw bytes are what gets published verbatim; the decoded
    text is what the gate checks. Keeping the pair together means
    no caller can validate one file and publish another.
    """
    path = entry_path()
    raw = load_raw(path)
    return raw, decode(raw)


def fail(message: str) -> "typing.NoReturn":
    """Abort with a single clear error line on stderr (exit code 1)."""
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def shape_violations(text: str, max_chars: int) -> list:
    """Check the text's shape: length, lines, whitespace, controls.

    These are the sealed scorer's rules, independent of what the
    text says. An empty or whitespace-only text short-circuits the
    rest: no other shape rule can be judged on nothing.
    """
    problems = []
    if not text or text.isspace():
        problems.append("entry is empty or only white space")
        return problems
    if text != text.strip():
        problems.append("entry has leading or trailing whitespace")
    if len(text) < MIN_CHARS:
        problems.append(
            f"entry is {len(text)} characters, below the "
            f"{MIN_CHARS}-character minimum"
        )
    if len(text) > max_chars:
        problems.append(
            f"entry is {len(text)} characters, over the "
            f"{max_chars}-character limit"
        )
    if "\n" in text or "\r" in text:
        problems.append("entry must be a single line")
    if "\t" in text:
        problems.append("entry must not contain a tab character")
    bad = [ch for ch in text if ord(ch) < 32 or ord(ch) == 127]
    if bad:
        problems.append(
            "entry must not contain control characters "
            f"(found U+{ord(bad[0]):04X})"
        )
    return problems


def voice_violations(text: str) -> list:
    """Check the text sounds like the dying phone itself.

    A generic low-battery warning dressed up as a joke is not a
    joke: the line must carry at least one word of the phone's own
    vocabulary, with a personality and a stake in dying.
    """
    lowered = text.lower()
    if not any(word in lowered for word in PHONE_WORDS):
        return [
            "entry must sound like the dying phone itself "
            "(no charger, battery, percent, 100%, delete, "
            "goodbye, dying, screen or charge)"
        ]
    return []


def gate_violations(text: str, max_chars: int) -> list:
    """Collect every way the text breaks the bounty gate, in order.

    Shape first, then voice: each violation is a plain sentence
    naming the rule and the offending detail, so one run reports
    everything wrong at once instead of stopping at the first
    problem. An empty list means the text passes the gate.
    """
    return shape_violations(text, max_chars) + voice_violations(text)


def validate(text: str, max_chars: int = DEFAULT_MAX_CHARS) -> None:
    """Reject any entry that breaks the bounty gate, naming each reason."""
    problems = gate_violations(text, max_chars)
    if problems:
        fail("; ".join(problems))


def resolve_output_dir(args: argparse.Namespace) -> Path:
    """Pick the output directory: CLI flag beats env var beats default.

    A blank ``$MAKEFUN_OUTPUT_DIR`` counts as unset rather than as
    a directory named nothing, which would otherwise fail oddly
    downstream instead of falling back to ``/output``.
    """
    if args.output_dir:
        return Path(args.output_dir)
    env_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "").strip()
    if env_dir:
        return Path(env_dir)
    return Path(DEFAULT_OUTPUT_DIR)


def describe(raw: bytes, text: str) -> str:
    """Summarise the entry in one line for success messages.

    Characters are what the gate counts; bytes are what the file
    holds (they differ once the text leaves ASCII); words hint at
    how much the message wastes, which the judge weighs.
    """
    words = len(text.split())
    return (
        f"{len(text)} characters, {len(raw)} bytes, "
        f"{words} words"
    )


def publish(raw: bytes, out_dir: Path) -> tuple:
    """Write the raw entry bytes verbatim and verify them by re-reading.

    Returns ``(path_written, byte_count)``. The bytes go to a
    temporary file in the same directory first and are moved into
    place with :func:`os.replace` only after the temporary copy
    reads back identical, so a failed write can never leave a
    half-written ``entry.txt`` behind. Raises SystemExit if the
    directory cannot be created, the write fails, or the bytes read
    back do not match the bytes written. The destination is resolved
    first so a surprising ``--output-dir`` (a symlink escaping the
    intended tree, for instance) is visible in the success message
    rather than silently honoured.
    """
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise SystemExit(f"cannot create output directory {out_dir}: {exc}")
    out_path = out_dir.resolve() / ENTRY_FILENAME
    tmp_path = out_path.with_name(ENTRY_FILENAME + ".tmp")
    try:
        tmp_path.write_bytes(raw)
    except OSError as exc:
        raise SystemExit(f"cannot write {tmp_path}: {exc}")
    try:
        staged = tmp_path.read_bytes()
    except OSError as exc:
        raise SystemExit(f"cannot read back {tmp_path}: {exc}")
    if staged != raw:
        raise SystemExit("staged entry does not match entry.txt")
    try:
        os.replace(tmp_path, out_path)
    except OSError as exc:
        raise SystemExit(f"cannot publish {out_path}: {exc}")
    try:
        published = out_path.read_bytes()
    except OSError as exc:
        raise SystemExit(f"cannot read back {out_path}: {exc}")
    if published != raw:
        raise SystemExit("published entry does not match entry.txt")
    return out_path, len(published)


def parse_args(argv=None) -> argparse.Namespace:
    """Parse the command-line options for this publisher."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default=None,
        help="directory to write entry.txt into "
        "(default: $MAKEFUN_OUTPUT_DIR or /output)",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="validate the last text without writing it",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=DEFAULT_MAX_CHARS,
        help=f"maximum entry length in characters (default: {DEFAULT_MAX_CHARS})",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="print nothing on success (errors still go to stderr)",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    """Load, validate, and publish (or just verify) the entry."""
    args = parse_args(argv)
    if args.max_chars < MIN_CHARS:
        fail(f"--max-chars must be at least {MIN_CHARS}, got {args.max_chars}")
    raw, text = load_entry()
    validate(text, args.max_chars)
    if args.verify_only:
        if not args.quiet:
            print(f"Valid: {describe(raw, text)}")
        return 0
    out_path, byte_count = publish(raw, resolve_output_dir(args))
    if not args.quiet:
        print(f"Wrote {describe(raw, text)} to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
