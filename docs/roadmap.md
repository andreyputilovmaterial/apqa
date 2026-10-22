# TODOs

This sections is to capture everything that comes to mind that should ideally be updated. Tasks listed here are not necessarily the highest priority.

- Review syntax warnings (see "Linter warnings 22 oct 2026" below)
- Make foldable groups for qc rules - otherwise it would be an enornous list
- Also make way more compact view of qc rule list - current view is way too spacious. Only 3 rules fit the screen by default, not suitable for maintaining big number of rules.
- Continue implementation - edit qc rule, test run the qc rule, add or remove qc rules, etc...
- Implement exact cmdlets and providers - that read Excel, CSV, SPSS, retrieve rows, object fields, etc...
- Go ahead and try on real oproject, and then update the list here with all key findings.
- Format navbar links so that they stay aligned on the right and open new page in a popup when clicked.

## Linter warnings 22 oct 2026

```
[{
	"resource": "/Users/andrej/work/apqa/src/frontend/app_js/src/app.js",
	"owner": "typescript",
	"code": "1109",
	"severity": 8,
	"message": "Expression expected.",
	"source": "ts",
	"startLineNumber": 71,
	"startColumn": 7,
	"endLineNumber": 71,
	"endColumn": 8,
	"modelVersionId": 1,
	"origin": "extHost1"
},{
	"resource": "/Users/andrej/work/apqa/src/frontend/app_js/src/app.js",
	"owner": "typescript",
	"code": "1005",
	"severity": 8,
	"message": "',' expected.",
	"source": "ts",
	"startLineNumber": 71,
	"startColumn": 8,
	"endLineNumber": 71,
	"endColumn": 9,
	"modelVersionId": 1,
	"origin": "extHost1"
},{
	"resource": "/Users/andrej/work/apqa/src/frontend/app_js/src/app.js",
	"owner": "typescript",
	"code": "1005",
	"severity": 8,
	"message": "',' expected.",
	"source": "ts",
	"startLineNumber": 73,
	"startColumn": 3,
	"endLineNumber": 73,
	"endColumn": 4,
	"modelVersionId": 1,
	"origin": "extHost1"
},{
	"resource": "/Users/andrej/work/apqa/src/frontend/app_js/src/app.js",
	"owner": "typescript",
	"code": "1128",
	"severity": 8,
	"message": "Declaration or statement expected.",
	"source": "ts",
	"startLineNumber": 94,
	"startColumn": 1,
	"endLineNumber": 94,
	"endColumn": 2,
	"modelVersionId": 1,
	"origin": "extHost1"
},{
	"resource": "/Users/andrej/work/apqa/src/frontend/app_js/src/app.js",
	"owner": "typescript",
	"code": "1128",
	"severity": 8,
	"message": "Declaration or statement expected.",
	"source": "ts",
	"startLineNumber": 94,
	"startColumn": 2,
	"endLineNumber": 94,
	"endColumn": 3,
	"modelVersionId": 1,
	"origin": "extHost1"
},{
	"resource": "/Users/andrej/work/apqa/src/frontend/app_js/src/common_components/records_filter/index.js",
	"owner": "typescript",
	"code": "1005",
	"severity": 8,
	"message": "'}' expected.",
	"source": "ts",
	"startLineNumber": 120,
	"startColumn": 7,
	"endLineNumber": 120,
	"endColumn": 7,
	"relatedInformation": [
		{
			"startLineNumber": 80,
			"startColumn": 16,
			"endLineNumber": 80,
			"endColumn": 17,
			"message": "The parser expected to find a '}' to match the '{' token here.",
			"resource": "/Users/andrej/work/apqa/src/frontend/app_js/src/common_components/records_filter/index.js"
		}
	],
	"modelVersionId": 1,
	"origin": "extHost1"
}]
```