# Analyst Evidence Coverage

Join an analyst briefing question list to an evidence catalog and produce a Markdown coverage matrix. The report shows the evidence behind each answer, highlights gaps, and records who owns follow-up.

## Run locally

Use Python 3.10 or later. Clone this repository or download and extract the ZIP, then run this command from the project folder. No packages, web server, or API key are required.

```sh
python report.py examples/questions.csv examples/evidence.csv --as-of 2027-03-01
```

The example has **two covered questions and two gaps**. Inventory coverage has one current item even though a second item is expired. Approval history has only draft evidence. Data export has no linked evidence.

## How it works

The questions CSV contains `question_id`, `topic`, `question`, and `follow_up_owner`. The evidence CSV contains `evidence_id`, `question_id`, `title`, `reference`, `status`, and `valid_until`. Question and evidence IDs must be unique in their respective files. Each evidence row must point to an existing question.

A question is covered if at least one linked item is `approved`, has a reference, and has a `valid_until` date on or after the report date. Draft, archived, expired, undated, and unreferenced evidence stays visible with its gaps. The app reads approval and validity from the catalog. Reviewers assess the material and decide what can be shared.

## Output and errors

Reports go to standard output by default. Add `--output brief.md` to save a new file. The command refuses to overwrite an existing report. Invalid CSVs and dates produce a diagnostic on standard error and exit with code 2. The explicit report date makes repeated runs reproducible.

## Project files

- [`report.py`](report.py) contains the CLI, input validation, and report rendering.
- [`examples/`](examples/) contains fictional CSV fixtures.

Use `python report.py --help` for the CLI options. Run the example above to check the report counts against the expected outcome.

## Project context

The workflow reflects analyst relations for the Holistic AI platform, where briefing questions about product capabilities lead to requests for evidence and named follow-ups. This is an independent portfolio project using fictional data without employer materials or customer records.
