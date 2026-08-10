# Budget Center Source Register

**Issue:** BC-002 — Build Budget Source Register  
**Schema version:** 1.0  
**Status:** Initial reviewable deliverable  
**Last updated:** August 2, 2026

## Purpose

The Budget Center Source Register is the authoritative catalog of financial evidence used by Beaumont Intelligence. It separates the underlying official record from the analysis built on top of that record.

Every published financial claim should be traceable to one or more permanent Source IDs.

## Repository artifacts

- `data/budget/source-register.json` — canonical machine-readable register
- `docs/budget-sources.html` — human-readable, filterable public register
- `docs/budget.html` — Budget Center landing page

## Source record schema

| Field | Required | Description |
|---|:---:|---|
| `sourceId` | Yes | Permanent identifier such as `SRC-0001` |
| `title` | Yes | Official or clearly descriptive document title |
| `documentType` | Yes | Controlled document classification |
| `fiscalYear` | When applicable | Fiscal year represented by the source |
| `documentDate` | When available | Date printed on or assigned to the source |
| `councilMeetingDate` | When applicable | Related Council meeting date |
| `agendaItem` | When applicable | Agenda item number |
| `resolutionNumber` | When applicable | Resolution identifier |
| `department` | When known | Responsible City department or agency |
| `publisher` | Yes | Publishing government body |
| `officialUrl` | When available | Original official source URL |
| `archivePath` | After archiving | Repository or archive location |
| `retrievedDate` | After retrieval | Date the source was preserved |
| `verificationStatus` | Yes | Verified, Archived, Pending, Missing, or Superseded |
| `confidence` | Yes | Confidence in the extracted interpretation |
| `evidenceLevel` | Recommended | Evidence tier used by Beaumont Intelligence |
| `relatedTopics` | Recommended | Budget datasets or financial subjects supported |
| `relatedProjects` | Recommended | Related Intelligence Centers |
| `crossLinks` | Recommended | Related public-site pages |
| `summary` | Recommended | Plain-language description |
| `notes` | Optional | Research, provenance, or limitation notes |

## Verification statuses

| Status | Meaning |
|---|---|
| **Verified** | The official source and its identity have been confirmed. |
| **Archived** | The verified source has also been preserved locally. |
| **Pending** | The record is known or provisionally identified but still needs verification. |
| **Missing** | The source is known to exist but has not been located. |
| **Superseded** | A newer official version exists; the historical record remains preserved. |

## Confidence levels

Confidence describes the interpretation or extracted data, not whether the document itself is official.

- **High** — directly supported by clear source language.
- **Medium** — requires interpretation, reconciliation, or multiple sources.
- **Low** — preliminary, incomplete, or materially conflicting.

## Source ID rules

1. IDs use the format `SRC-0001`.
2. IDs are permanent.
3. IDs are never reused.
4. Superseded or broken-link records remain in the register.
5. One source may support many projects, datasets, or claims.
6. A collection-level placeholder should be replaced by individual source records when the underlying documents are identified.

## Financial evidence rules

- Budget authority is not the same as actual expenditure.
- Contract authorization is not proof of payment.
- Grant announcement, grant award, obligation, reimbursement, and expenditure are separate events.
- Original, amended, and current amounts must remain distinguishable.
- Interfund transfers must be identified to prevent double counting.
- Primary records take precedence over summaries and news releases.
- Official web pages should eventually receive an archived snapshot because their contents may change.

## Initial inventory

This deliverable seeds the register with official records already used in Beaumont Intelligence, including citywide financial reporting, the Capital Improvement Plan, CFD refunding, Stewart Park records, a Pennsylvania Avenue funding announcement, and ongoing Potrero research.

The initial inventory is intentionally not presented as a complete City budget-document catalog. Adopted budgets, ACFRs, CIP books, budget amendments, and workshop records still need to be entered as individual verified sources.

## Review checklist

BC-002 may move to **Review** when:

- [x] The source-register standard exists in the repository.
- [x] A valid JSON register exists.
- [x] The website can render and filter the register.
- [x] Real official source records are included.
- [x] Source-to-project cross-links are represented.
- [ ] The deliverable is committed and deployed.
- [ ] The public page is visually reviewed.
- [ ] Broken links and mobile behavior are checked.

BC-002 should move to **Done** only after the deployed page is accepted.
