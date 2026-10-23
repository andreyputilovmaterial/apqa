# APQA — Help

## What is a QC rule?

A QC rule is a named check that verifies a piece of your project data against an
expected result. Each rule has three parts:

1. **Left side** — a pipeline of commands that reads and transforms source data.
2. **Comparison operator** — how the left side is compared to the right side
   (equal to, not equal to, less than, greater than, contains, …).
3. **Right side** — a pipeline of commands that produces the expected value.

For example, the rule *“Title details count equals 15”* could be written as:

```
get-content Specs.xlsx | select-sheet "Title Details" | select-column "B" | count  =  15
```

- The **left side** opens the Excel file, picks the “Title Details” sheet and
  column **B**, and counts the entries.
- The **operator** is *equal to*.
- The **right side** is the number `15`.

## Commands (cmdlets)

A pipeline is made of small commands, similar to PowerShell cmdlets:

- **Source commands** read data — from Excel, SPSS, CSV, text files, databases, etc.
- **Middle commands** process data — select a column or sheet, map a collection,
  count entries, convert to text, and so on.
- **Final commands** produce a single value for comparison.

Each command can take parameters — a file name, a sheet name, a column, or a flag.

## Editing rules

Start the desktop app to open the rule editor for the chosen project. From there
you can:

- **Add** a new rule,
- **Edit** an existing rule,
- **Rename** a rule,
- **Delete** a rule.

Your changes are saved to the project's rules database file.

## Project database file

Rules are stored in the project's **database file**, in one of two formats:

- **SQLite** (`.sqlite3` or `.sqlite`) — the default. A small local database file.
- **YAML** (`.yaml` or `.yml`) — a plain text file you can read and edit by hand.

The format is chosen by the file extension. To start a new project, create an
empty file with the extension you want (for example, `project.sqlite3`).

## Global aliases

You can define project-wide **aliases** that give a short name to a long, reused
value (usually a file path). For example, define
`/project/p123/data/datafile.db` as `PROCESSED_DATA`, then use `PROCESSED_DATA`
as a command parameter instead of repeating the full path everywhere. Aliases are
stored in the same database file as the rules and are shown in their own section
above the rule list.

## Running the QC tests

Once your rules are defined, run the tests to check the project data against them.
The result is a report of passed and failed rules, in the same style as a standard
test runner.

## Pages

- **Home** — manage the QC rule list.
- **About** — application information.
- **Version** — the application version.
- **Help** — this page.