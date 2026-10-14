# Goals

This program is a helper application to define and manage QC rules for
user defined project. So, the user can enter rules with ui, and then run tests.

## Description of program

Two use modes:

1. Show ui and let user edit QC rules. So, it works like this: start program -> project is Disney Brand Health Study (example, specified in cli
param at start) -> It means, the database is project-p12345-disney.yaml
(local .yaml file, for now) -> program shows the ui (web interface from
localhost, for now) -> the user can enter, add, delete, modify QC rules ->
when changes are done (or while they are done), changes are saved in database
(that is that .yaml file) -> user can quit the program.
2. Run the tests based on QC rules defined in the ui in mode 1. So, it works like this: start program with pytest -> user-defined cli params are not possible (unless
I consider creating a pytest plugin, but I am not considering this), that's why
project db file is set through env variable from the caller .sh or .bat script ->
tests are running, and results are captured depending on pytest plugins used.

It means, QC rules saved in that project-p12345-disney.yaml are the fixtures and
acceptance criteria - they should provide enough information on where to read
source data from and how do results compare to expectations.

### Examples of QC rules

Examples of QC rules (as a reminder, it's not the programmer who enters the rules -
it's the user of the program):

- Counts in Wave 69 must equal 9002
- Stubs in "BrandAwareness" question match exactly to stubs in "BrandFamiliarity"
question plus "None of the above" stub
- Stubs in "TitleDetails" question match exactly to items from col "B" from
"Title Details" sheet in /path/to/project/p123456/2_admin/qre/titles_list.xlsx file.

Rules should also support common pytest modifiers - I mean, something similar to
mark xfail, or similar that might be useful.

With this architecture, when the program is started in mode when tests are started,
pytest should not discover physical tests - it should discover single entry point
that is parametrized from the database that is read.

## Details of implementation

This program, implemented in python (globally - ui can be done as web service with vue).

For now, it's a personal hobby project. It means, I have all freedom for doing
things "my way" and for experimenting.

As I want to be able to use standard approaches from programmer's world,
I create it on pytest base. The reason is that pytest has wide adoption,
has lots of plugins. I am not sure in this decision, as the only thing I
really need is zero or non-zero exit status, and some information on which
tests failed - I can do it without pytest. But I decided to start pytest-ish.

"Pytest" here is the confusing part. It can be called for 2 purposes:

1. To run tests that help us verify program functionality - no tests in
final bundle, these tests are for development only.
2. To start the program in "run QC tests" mode, with single discoverable entry point
in final bundle but not working as an entry point for pytest in the repo
during development. This is done by adding some lines to the bundle ("patching")
by `build'sh` script (see details below). Also, from coding assistances, I am getting
complaints that I do not provide harness definitions here. I think we do not need it
in distributable bundle cause we have add one single discoverable parametrized entry
point for pytest and the bottom of the bundle, and it should be enough to start the
process.

I prefer to have the final form of py bundle, made with pinliner (`src_dev_build/lib/pinliner`, a submodule).
It implies several architectural decisions:

- Only relative imports in .py files are allowed, with the exception of starter `src/launcher.py` file.
  - `src/launcher.py` is the only exception from this rule - it uses conditional logic for import statements - depending if it is called as a module, as a package, as a program.
  - If we need to import something from top level, it means we need: 1. `src/launcher.py` loads the module that is the starting point for the program (for example, `src/main_ui_program.py`), 2. the module that is the starting point for the program imports what is needed and puts it somewhere in global config object, 3. this config object is passed to a place where imported code is used. This should be only done
  when necessairy - in overall, discouraged. We should avoid importing things from
  outer level.
- It should be possible to make distributable bundle on PC without node installed.
Node and vite can be used in development to speed up development of frontend but the build process should be possible without Node installed.
  - To achieve this, for now, I am using a personal self-written js bundler (`src/frontend/bundler_engine/lib/py_js_bundler`, a submodule),
  made in py. It's at very raw state, and I am planning to extend it to implement proper parsing. I am okay to entirely move from it, if I find a working alternative.
  - Also, similar requirement comes from using my personal implementation of js bundler:
  only `.js` and `.css` files are possible in frontend apps - not `.vue` and not `.ts`.
- The application is designed to be distributed as a single self-contained bundle and does not rely on separate local files for its operation. Consequently, it does not include standalone configuration files such as .env, static assets such as JavaScript or CSS files, or auxiliary documentation files such as help.md or version.md. Any application resources required at runtime must be embedded in the bundle or made available as importable Python modules. This does not prevent the application from accessing local files. It can read external files when the user explicitly provides their full filesystem paths.
  - To achieve this, the "build.sh" script reads files with generated content (css/js assets, files that store version number generated with git describe, author name generated in .env file, and other possibly generated artifacts), puts them to .py files in GENERATED subfolder in a place where these items are needed (so that relative import works - not importing anything from top level).
  - It makes the runtime less clean, in development - "build" does not only produce
  the distributable bundle but also necessary artifacts for the program to run.
  - It also brings one more minor problem: I want build.sh to be a complete script that
  does all necessray work when project is cloned. It means, the necessary step is
  to execute "git submodule update --init --recursive" command. But if I make edits
  to submodules, experimentally while testing something, and I need to re-run build.sh
  to re-generate all included pieces in GENERATED folders, I lose my local edits
  in submodules. So it just makes testing harder, or requires committing changes in
  submodules even if they are not final, or altering the build.sh script.
- Paths to all imported modules must contain `__init__.py` files everywhere
in the patyh. Modern python does not have this requirement, but pinliner does
require this.
  - This might be an issue when using submodules created by other people -
  they might contain src folder with necessary files, but no `__init__.py` file at
  the same level as src folder itself. And creating that `__init__.py` is not
  possible, until I own the repo that is used as a submodule (or I have to fork it,
  to have that edit (adding `__init__.py`) recorded in a commit).
- To make it possible to start running tests with pytest, we are "patching" the py
bundle from `build.sh` script. Patching of final bundle is generally not allowed, cause
the bundle is made with "pinliner" (`src_dev_build/lib/pinliner`, a submodule),
and pinliner is hard-coding exact positions of where do module definitions start
and end within the bundle. But adding lines at the end is happening beyond all
modules start and end positions so does not change these positions.
- Starting the program in "run tests" mode requires `--import-mode=importlib` param - a limitation of pinliner. This is needed when calling the bundle with pytest. Adding --import-mode to development tests in unnecessary.

As this is a personal hobby project and I have the freedom of doing things "my way",
I am very positive towards separating any reusable pieces of code into submodules.
And in overall, I am using submodules with my additional developments very actively.
And even considering separating more parts and make them reusable in the future.

I am also usign my personal self-written code for runnign webserver at localhost
(`src/webserver_engine/webserve`, a submodule).
It might look that it only supports GET, at first glance - it's not true, all methods
are normally handled.

Also, for everything that might go wrong: my preference is to always fail early and make
a readable error message. Do not add too strict validation - we should always leave some
flexibility for data format, and stay python-ish. If someargument is iterable - it's
important that it is iterable, we should not require list or tuple exactly. But
if something is wrong or missing that is definitely an issue - it is always better to
detect it early and fail with reasonable message and not wait when program tries to
access missing attribute and fail with cryptic message.

### Format of QC rules

This section describes how are the QC rules represented, both in the database and
in the ui.

QC rules should be implemented as three essential parts:

1. Left side
2. Comparison op
3. Right side.

Left and right side should be implemented as a chain of cmdlets - somewhat
similar to cmdlets in powershell. And will beorganized in somewhat similar
manner of pipes.

Example:
Left side: `get-content Specs.xlsx | select-sheet "Title Details" | select-column "B" | count`, right side: 15, comparison op: equality.

Cmdlets are of 3 types:

1. Cmdlets that access and read source data - for example, extract
information from .xlsx, .sav, .csv, .txt, databases, etc.
2. Cmdlets stay in the middle of the pipe - something similar to
select-object, extract column or row from data, return a property from
an object, map a collection, transforming every element, convert to string,
count elements in collection, or similar.
3. Cmdlets that transform to final scalar data type
that can be used in comparison.

Cmdlets can have params entered by the user. Each cmdlet defines its own set of
avalable params. For example, in powershell cmdlets, we can use
`Get-Content 'myfile.txt'`, `Get-Childitem -Recurse`, and filename and "-recurse" are
the params.

All cmdlets should be defined through some global registry in a program.
Somewhat similar to plugins. Cmdlets should be extensible - if I decide to
implement support for more input source files in the future. This mostly
applies to cmdlets of type 1.

For other cmdlet types, I'd prefer to stick to minimal amount, but something
super flexible. So that every possible task can be achieved with still minimal
set of cmdlets. For example, There should not be a specific cmdlet to read
a sheet from Excel file. There should be some global thing, like read a record,
a dataframe, on abject field, or similar, that can be used equally on Excel,
SPSS, Databases, and other types of input source data. Similar processing approaches
that should not much depend on type of input data.

There will be a limited set of scalar data types that a cmdlet can return - text/string,
number (int), number (floating-point), boolean, date/time, categorical
(single-punch/single-select, within list of allowed options, for example
"male" and "female"), categorical (multi-punch/multi-select - similar to single-punch
but with possible multiple responses), or derivatives (compound types) - an object with
named fields of those types, or some fields might be of compound types again, a
collection of uniform compound objects with named fields (each object in collection
must follow same protocol), a "tuple" (from python's world - a sequence of items with
pre-defined types and of pre-defined length). Every value is always allowed to be sysmissing - that should be always an allowed value, no matter if
contraints value type definition is text, number, boolean, date, or whatever else.

The final list of "compound" data types is still to be finalized (I mentioned a record,
a collection, an object with named fields...).

Same design principles should apply both in:

1. In a way how rules are stored in the database file for the project.
2. in the ui.
3. And same dict-alike implementation of the structures described above is what
flows through the pipe.

Within compare op, sysmissing should be treated as undefined/uncertain value, that never
shows equality with anything other than other sysmissing. Comparing sysmissing to empty
set or empty collection or zero or boolean or empty string must return false.

#### Error handling within cmdlets

There should not be much validation within cmdlets. They are not designed to store
validation rules. The validation is the comparison op. However, if it can't be done
physically (there is no source object to read, no data to read from) a normal python
exception is all we need. It contains exact message with details of failure, it is
normally captured by pytest. It covers all needed.
