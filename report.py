"""Generate a Markdown briefing report from fictional or user-supplied CSV data."""

import argparse
import csv
from datetime import date
from pathlib import Path


def read_csv(path, required):
    """Yield validated rows with their CSV line numbers."""
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, strict=True)
        headers = reader.fieldnames or []
        missing = set(required).difference(headers)
        if missing:
            raise ValueError(f"{path}: missing columns: {', '.join(sorted(missing))}")
        if len(headers) != len(set(headers)):
            raise ValueError(f"{path}: duplicate column names")
        for record in reader:
            line = reader.line_num
            if None in record or any(value is None for value in record.values()):
                raise ValueError(f"{path}:{line}: wrong number of fields")
            yield line, {key: value.strip() for key, value in record.items()}


def parse_date(value, label):
    try:
        if len(value) != 10:
            raise ValueError
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"{label}: expected YYYY-MM-DD") from None


def unique_id(value, seen, label):
    if not value or value in seen:
        raise ValueError(f"{label}: ID must be nonempty and unique")
    seen.add(value)


def table_row(*cells):
    escaped = []
    for cell in cells:
        value = str(cell).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        escaped.append(value.replace("\\", "&#92;").replace("|", "&#124;").replace("\r", " ").replace("\n", " "))
    return "| " + " | ".join(escaped) + " |"


QUESTION_FIELDS = ("question_id", "topic", "question", "follow_up_owner")
EVIDENCE_FIELDS = ("evidence_id", "question_id", "title", "reference", "status", "valid_until")
STATUSES = {"draft", "approved", "archived"}


def add_arguments(parser):
    parser.add_argument("questions", type=Path, help="Analyst questions CSV")
    parser.add_argument("evidence", type=Path, help="Evidence catalog CSV")


def build_report(args, as_of):
    questions = {}
    question_ids = set()
    for line, row in read_csv(args.questions, QUESTION_FIELDS):
        label = f"{args.questions}:{line}"
        unique_id(row["question_id"], question_ids, label)
        if not row["topic"] or not row["question"]:
            raise ValueError(f"{label}: topic and question are required")
        questions[row["question_id"]] = row

    seen = set()
    catalog = {key: [] for key in questions}
    for line, row in read_csv(args.evidence, EVIDENCE_FIELDS):
        label = f"{args.evidence}:{line}"
        unique_id(row["evidence_id"], seen, label)
        question_id = row["question_id"]
        if question_id not in questions:
            raise ValueError(f"{label}: unknown question_id {question_id!r}")
        if not row["title"] or row["status"] not in STATUSES:
            raise ValueError(f"{label}: title and a valid status are required")
        expires = parse_date(row["valid_until"], label + " valid_until") if row["valid_until"] else None
        gaps = []
        if row["status"] != "approved":
            gaps.append(row["status"])
        if not row["reference"]:
            gaps.append("missing reference")
        if not expires:
            gaps.append("missing expiry date")
        elif expires < as_of:
            gaps.append("expired")
        catalog[question_id].append((row, gaps))

    output = ["# Analyst evidence coverage", "", f"As of {as_of.isoformat()}", "",
              "| Topic | Question | Follow-up owner | Coverage | Evidence |",
              "| --- | --- | --- | --- | --- |"]
    covered = 0
    for key, question in sorted(questions.items(), key=lambda pair: (pair[1]["topic"].casefold(), pair[0])):
        items = sorted(catalog[key], key=lambda item: item[0]["evidence_id"])
        ready = any(not gaps for _, gaps in items)
        covered += ready
        evidence = []
        for row, gaps in items:
            status = ", ".join(gaps) if gaps else "current"
            evidence.append(f'{row["evidence_id"]} {row["title"]} ({status}) — {row["reference"] or "no reference"}')
        output.append(table_row(question["topic"], question["question"], question["follow_up_owner"] or "Unassigned",
                                "Covered" if ready else "Gap", "; ".join(evidence) or "No evidence listed"))
    output[4:4] = [f"- Questions: {len(questions)}", f"- Covered: {covered}",
                   f"- Gaps: {len(questions) - covered}", ""]
    return "\n".join(output) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_arguments(parser)
    parser.add_argument("--as-of", required=True, metavar="YYYY-MM-DD", help="Report date")
    parser.add_argument("--output", type=Path, help="Write Markdown to a new file instead of stdout")
    args = parser.parse_args()
    try:
        report = build_report(args, parse_date(args.as_of, "--as-of"))
        if args.output:
            with args.output.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(report)
        else:
            print(report, end="")
    except (ValueError, OSError, csv.Error) as error:
        parser.exit(2, f"error: {error}\n")


if __name__ == "__main__":
    main()
