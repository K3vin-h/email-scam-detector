"""
download_data.py — Downloads and merges spam/ham email datasets.

Run this once before training:
    python -m ml.download_data

Output: data/processed/emails.csv
  Columns: text (the email body), label (1=scam, 0=legit)
"""
import csv
import email
import tarfile
import zipfile
from pathlib import Path

import requests

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")

# SpamAssassin public corpus — each archive contains individual raw email files.
# We download both spam and ham (legitimate) archives, then label them accordingly.
SPAMASSASSIN_ARCHIVES = [
    ("20021010_easy_ham.tar.bz2", 0),   # 0 = legitimate email
    ("20030228_easy_ham_2.tar.bz2", 0),
    ("20021010_spam.tar.bz2", 1),        # 1 = scam / spam
    ("20030228_spam_2.tar.bz2", 1),
]
SPAMASSASSIN_BASE = "https://spamassassin.apache.org/old/publiccorpus/"

# SMS Spam Collection — simpler format: tab-separated "spam/ham \t message text"
SMS_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/00228/smsspamcollection.zip"


def download_file(url: str, dest: Path) -> bool:
    """Download url to dest. Returns True on success, False on failure."""
    if dest.exists():
        print(f"  Already downloaded: {dest.name}")
        return True
    print(f"  Downloading {dest.name} ...", end=" ", flush=True)
    try:
        resp = requests.get(url, stream=True, timeout=60)
        resp.raise_for_status()
        dest.write_bytes(resp.content)
        print("done")
        return True
    except Exception as exc:
        print(f"FAILED ({exc})")
        return False


def extract_text_from_email(raw_bytes: bytes) -> str:
    """
    Parse a raw email file and return its subject + body as plain text.

    An email has two parts: headers (From, Subject, Date, etc.) and a body.
    The body can itself have multiple parts (plain text, HTML, attachments).
    We want only the plain-text part so the model reads human-readable words.
    """
    try:
        msg = email.message_from_bytes(raw_bytes)
        subject = msg.get("Subject", "")

        body = ""
        if msg.is_multipart():
            # Walk through all parts of a multi-part email.
            # We stop at the first plain-text part we find.
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        body = payload.decode("utf-8", errors="replace")
                        break
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                body = payload.decode("utf-8", errors="replace")

        return f"{subject} {body}".strip()
    except Exception:
        return ""


def load_spamassassin(archive_path: Path, label: int) -> list[tuple[str, int]]:
    """
    Extract all emails from a SpamAssassin .tar.bz2 archive.
    Returns a list of (text, label) tuples.
    """
    rows = []
    with tarfile.open(archive_path, "r:bz2") as tar:
        for member in tar.getmembers():
            # Skip directories and the "cmds" metadata file SpamAssassin includes.
            if not member.isfile() or member.name.endswith("cmds"):
                continue
            f = tar.extractfile(member)
            if f is None:
                continue
            text = extract_text_from_email(f.read())
            if text.strip():
                rows.append((text.strip(), label))
    return rows


def load_sms_spam(zip_path: Path) -> list[tuple[str, int]]:
    """
    Load the SMS Spam Collection dataset from its zip archive.
    Format inside the zip: tab-separated lines — "spam\ttext" or "ham\ttext"
    """
    rows = []
    with zipfile.ZipFile(zip_path) as zf:
        with zf.open("SMSSpamCollection") as f:
            for line in f:
                decoded = line.decode("utf-8", errors="replace").strip()
                if "\t" not in decoded:
                    continue
                label_str, text = decoded.split("\t", 1)
                label = 1 if label_str.strip() == "spam" else 0
                rows.append((text.strip(), label))
    return rows


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    all_rows: list[tuple[str, int]] = []

    # ── SpamAssassin ──────────────────────────────────────────────────────────
    print("SpamAssassin corpus:")
    for filename, label in SPAMASSASSIN_ARCHIVES:
        dest = RAW_DIR / filename
        if download_file(SPAMASSASSIN_BASE + filename, dest):
            rows = load_spamassassin(dest, label)
            tag = "spam" if label == 1 else "ham"
            print(f"    {filename}: {len(rows):,} {tag} messages")
            all_rows.extend(rows)

    # ── SMS Spam Collection (optional — skip if download fails) ───────────────
    print("\nSMS Spam Collection:")
    sms_dest = RAW_DIR / "sms_spam.zip"
    if download_file(SMS_URL, sms_dest):
        try:
            sms_rows = load_sms_spam(sms_dest)
            print(f"    sms_spam.zip: {len(sms_rows):,} messages")
            all_rows.extend(sms_rows)
        except Exception as exc:
            print(f"    Could not parse SMS data ({exc}), skipping.")

    # ── Write merged CSV ──────────────────────────────────────────────────────
    output = PROCESSED_DIR / "emails.csv"
    with open(output, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["text", "label"])
        writer.writerows(all_rows)

    total = len(all_rows)
    spam = sum(1 for _, lbl in all_rows if lbl == 1)
    ham = total - spam
    print(f"\nSaved {output}")
    print(f"  Total : {total:,} messages")
    print(f"  Spam  : {spam:,} ({spam / total:.1%})")
    print(f"  Ham   : {ham:,} ({ham / total:.1%})")


if __name__ == "__main__":
    main()
