import csv, html, re, unicodedata
from pathlib import Path

IN_FILES = [Path("urdu_moral_stories.csv"), Path("urdu_funny_stories.csv")]
OUT_FILE = Path("corpus.txt")
EOS, EOP, EOT = "\uE000", "\uE001", "\uE002"  # private-use special tokens

AD_PATTERNS = [r"\bLIVE\b", r"\bAdvertisement\b", r"Tap to unmute", r"Learn more", r"An error occurred"]
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")
SENT_RE = re.compile(r"[۔!?؟]+")
NON_URDU_RE = re.compile(r"[^\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF0-9\s،۔؟؛]+")


def clean(s: str) -> str:
    s = unicodedata.normalize("NFKC", TAG_RE.sub(" ", html.unescape(s or "")))
    for p in AD_PATTERNS:
        s = re.sub(p, " ", s, flags=re.I)
    s = s.replace(",", "،").replace(";", "؛").replace("?", "؟").replace("!", "۔").replace(".", "۔").replace("ـ", "")
    return WS_RE.sub(" ", NON_URDU_RE.sub(" ", s)).strip()


def story_to_line(content: str) -> str:
    out = []
    for para in [p.strip() for p in re.split(r"\n\s*\n|\r\n\s*\r\n|\n|\r\n", content or "") if p.strip()]:
        sent = [x.strip() for x in SENT_RE.split(clean(para)) if x.strip()]
        if sent:
            out.append(f" {EOS} ".join(sent) + f" {EOP}")
    return (" ".join(out) + f" {EOT}").strip() if out else ""


def read_contents(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            c = (row.get("content") or "").strip()  # content only (ignore title)
            if c:
                yield c


def main():
    lines = []
    for p in IN_FILES:
        if p.exists():
            lines.extend(filter(None, (story_to_line(c) for c in read_contents(p))))
    OUT_FILE.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8", newline="\n")
    print(f"Wrote {len(lines)} stories to {OUT_FILE}")


if __name__ == "__main__":
    main()
