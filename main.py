"""One-line museum placard for an office artifact.

The program composes a single catalogue line for a stapler, presented
as an ancient ritual object, and publishes it to
$MAKEFUN_OUTPUT_DIR/entry.txt (default /output/entry.txt).

The placard must satisfy the contest gate: UTF-8 text, 1-180
characters, one line only, not whitespace-only, and free of control
or invisible characters. The catalogue voice stays dry throughout:
a date, a material, a department, and one small omen.
"""

import os
import sys
import unicodedata

PLACARD = (
    "Stapler, c. 2019, steel and plastic. Ritual binding tool of the "
    "Accounts Department; unused since spring 2021, when the last jam "
    "was declared an omen."
)

MIN_LEN = 1
MAX_LEN = 180


def _is_control_char(ch):
    """True for C1 controls, surrogates, and Cc/Cf category characters."""
    code = ord(ch)
    if 0x0080 <= code <= 0x009F:
        return True
    if 0xD800 <= code <= 0xDFFF:
        return True
    return unicodedata.category(ch) in ("Cc", "Cf")


def _is_invisible_char(ch):
    """True for characters that must never reach the placard."""
    if ch in ("\ufeff", "\u2028", "\u2029"):
        return True
    if ch.isspace() and ch not in (" ", "\t"):
        return True
    return _is_control_char(ch)


def _check_shape(text):
    """Reject non-strings, empties, multi-line text, and bad lengths."""
    if not isinstance(text, str):
        raise ValueError("entry must be a string")
    if not text or not text.strip():
        raise ValueError("entry is empty or whitespace-only")
    if "\n" in text or "\r" in text:
        raise ValueError("entry must be a single line")
    if not (MIN_LEN <= len(text) <= MAX_LEN):
        raise ValueError(
            "entry is %d characters; gate requires %d-%d"
            % (len(text), MIN_LEN, MAX_LEN)
        )


def _check_characters(text):
    """Reject every character the gate forbids, one by one."""
    for ch in text:
        if _is_invisible_char(ch):
            raise ValueError("forbidden character U+%04X in entry" % ord(ch))
    text.encode("utf-8")  # raises if not encodable


def validate(text):
    """Check the entry against the competition gate. Raises ValueError."""
    _check_shape(text)
    _check_characters(text)
    return True


def _resolve_output_dir():
    """Resolve the output directory from the environment."""
    return os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")


def _write_atomically(out_dir, data):
    """Stage a temp file inside the output dir, then swap it into place.

    The temp file must live INSIDE the output dir: /tmp fails with EXDEV
    on bind-mounted output paths, and os.replace must stay on one fs.
    """
    target = os.path.join(out_dir, "entry.txt")
    tmp_path = os.path.join(out_dir, ".entry.txt.tmp")
    with open(tmp_path, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(tmp_path, 0o644)
    os.replace(tmp_path, target)
    os.chmod(target, 0o644)
    return target


def _verify_written(target, data):
    """Read the file back: bytes on disk must match exactly."""
    with open(target, "rb") as handle:
        written = handle.read()
    if written != data:
        raise RuntimeError("read-back mismatch after writing entry.txt")


def publish(text):
    """Validate, write, and verify the placard in the output directory."""
    validate(text)
    out_dir = _resolve_output_dir()
    os.makedirs(out_dir, exist_ok=True)
    target = _write_atomically(out_dir, text.encode("utf-8"))
    _verify_written(target, text.encode("utf-8"))
    return target


def main():
    try:
        target = publish(PLACARD)
    except (ValueError, OSError, RuntimeError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1
    print("wrote %s (%d characters)" % (target, len(PLACARD)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
