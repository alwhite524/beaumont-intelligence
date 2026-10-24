# Budget question preview

The interface is limited to `budget.html` and `budget-questions.html`. Its local fallback uses `budget-answers-data.json`. When the server reports AI enabled, a submitted question and up to ten selected evidence excerpts are sent server-side to OpenAI. The interface identifies AI answers separately from local reviewed summaries and record matching. This data flow was explicitly approved by the user.

The initial evidence snapshot contains Budget Council findings, financial source-register metadata, Beaumont Nights source discovery and reviewed budget summaries. The generator preserves evidence limits. A catalog title or URL does not mean the PDF has been read. There is no complete transaction ledger, reconciled Beaumont Nights three-year total or live financial-system connection.

The preview returns reviewed summaries for supported questions, related source records otherwise, and a specific coverage explanation for Beaumont Nights spending questions. Relative years and gross versus net cost need clarification before a defensible total can be produced. Fiscal and calendar years must not be silently combined.

Charts use a curated comparable dataset only. The initial group compares FY 2026–27 planned all-fund revenue ($168M) and expenditure ($162.5M), citing the June 16 adoption record. It is not actual spending. Charts include the underlying accessible data table. General Fund questions do not receive the all-funds chart, and missing event data never generates a chart.

Rebuild after changing collected records:

```text
python scripts/build_research_library_index.py
python scripts/build_budget_answers.py
python scripts/install_budget_question_interface.py
```

The latter two commands are also included in `build_all.py`. Run `node --test tests/budget-answers.test.mjs tests/budget-api.test.mjs` for financial-evidence, endpoint and transport checks. Provider responses in tests are mocked; passing tests does not establish answer quality on a live model.

## Secure AI endpoint

`server/budget-api.mjs` handles `/api/budget-ask`, and `server/budget-worker.mjs` adapts it to Cloudflare Workers. The Worker bundles the generated evidence snapshot. Rebuild the corpus before bundling a deployment; the server does not accept client-provided evidence, model names, provider URLs, chart values or source URLs.

The API requires all five settings before it can call the provider: `BUDGET_AI_ENABLED=true`, `OPENAI_API_KEY`, `OPENAI_MODEL`, `BUDGET_RATE_LIMITER`, and `BUDGET_GLOBAL_LIMITER`. It also requires a same-origin POST and Cloudflare's trusted client-IP header. Missing limits or identity fail closed. Question bodies are capped at 5,000 bytes and questions at 1,000 characters. Provider calls have a 25-second timeout and an 1,800-token output limit. Error responses do not expose provider details or secrets. There is no application logging of prompts or answers. `store:false` disables response storage through the Responses API; it does not make a broader promise about provider retention policies.

The model receives only the question, evidence date, selected record text and limitations, and chart-group descriptions. Citation validation checks that references belong to the supplied evidence; it does not prove that every generated statement is factually entailed. Prompt instructions preserve source limitations and prohibit unsupported expenditure totals. The existing evidence corpus still needs expansion before comprehensive event-spending questions can be answered.

## Hosting preparation and activation

No deployment or live provider request has been performed. The existing static hosting setup remains unchanged. `wrangler.budget.example.toml` is an opt-in Workers configuration example, not a committed active deployment configuration and not a Pages Functions configuration. It can serve the existing `docs` assets alongside the API in a separate staging Worker. Alternatively, adapt the handler to the site's existing backend and preserve the same-origin `/api/budget-ask` path. Static hosting alone cannot hold a private API key.

With Cloudflare Workers and Wrangler available:

1. Copy `wrangler.budget.example.toml` to the ignored `wrangler.budget.toml`. Choose the staging Worker name and account-specific rate-limit namespace IDs; do not overwrite a live deployment's configuration.
2. Set `OPENAI_MODEL` in `[vars]` to a model available in the API project that supports Responses API structured outputs. No model is silently chosen by this feature.
3. Store the key using `wrangler secret put OPENAI_API_KEY --config wrangler.budget.toml`. Never put it in a browser file, Git, chat message or public environment variable. Local `.dev.vars` files are ignored.
4. Configure per-client and shared rate bindings. The example allows six questions per minute per client and sixty per minute on the shared key. Cloudflare rate limits are approximate and local to each Cloudflare location, including the shared key: they are not a hard worldwide spending cap. Configure provider project budgets/alerts and hosting controls before enabling public traffic.
5. Deploy a staging Worker with AI disabled, verify static assets and `/api/budget-ask` returning `{"enabled":false}`, then enable `BUDGET_AI_ENABLED` only after secrets, model access and both bindings are confirmed. Test cited answers, unsupported Beaumont Nights totals, charts, fallback and limit handling before any deliberate production rollout.

The client checks availability before sending a question. If disabled, no question POST is sent; the local preview still works. Provider errors, timeouts and quotas fall back to local records with an explicit status message. No browser API key is needed.

Implementation references: [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs), [Cloudflare rate-limit bindings](https://developers.cloudflare.com/workers/runtime-apis/bindings/rate-limit/).
