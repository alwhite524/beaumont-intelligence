# Budget question preview

The interface is limited to `budget.html` and `budget-questions.html`. It runs in the browser and uses `budget-answers-data.json`; it does not send questions to an external service or represent keyword matching as AI generation.

The initial evidence snapshot contains Budget Council findings, financial source-register metadata, Beaumont Nights source discovery and reviewed budget summaries. The generator preserves evidence limits. A catalog title or URL does not mean the PDF has been read. There is no complete transaction ledger, reconciled Beaumont Nights three-year total or live financial-system connection.

The preview returns reviewed summaries for supported questions, related source records otherwise, and a specific coverage explanation for Beaumont Nights spending questions. Relative years and gross versus net cost need clarification before a defensible total can be produced. Fiscal and calendar years must not be silently combined.

Charts use a curated comparable dataset only. The initial group compares FY 2026–27 planned all-fund revenue ($168M) and expenditure ($162.5M), citing the June 16 adoption record. It is not actual spending. Charts include the underlying accessible data table. General Fund questions do not receive the all-funds chart, and missing event data never generates a chart.

Rebuild after changing collected records:

```text
python scripts/build_research_library_index.py
python scripts/build_budget_answers.py
python scripts/install_budget_question_interface.py
```

The latter two commands are also included in `build_all.py`. Run `node --test tests/budget-answers.test.mjs` for the focused financial-evidence checks.

## AI integration pending approval

Automatic approval review rejected adding a live endpoint because the proposed flow sends visitor questions and selected internal budget-record excerpts to OpenAI, and that payload/destination had not been specifically approved. No endpoint or provider call was added. Approval is pending for that precise flow. API credentials must never be placed in browser files or committed to the repository.

After approval, the remaining implementation is a server-side answer endpoint with server-held credentials, limited evidence retrieval, structured cited answers, validation, timeouts and host-managed request limits. Hosting and API secrets must be configured separately; static hosting alone cannot hold a private API key. The API design was checked against [OpenAI structured-output documentation](https://developers.openai.com/api/docs/guides/structured-outputs).
