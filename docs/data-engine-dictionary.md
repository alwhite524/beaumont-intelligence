# Data Engine Dictionary — Sprint 2.1

## Tenancy

- `tenant`: Product/customer boundary. MBF is Tenant 1.
- `workspace`: Campaign or client workspace within a tenant.

## Core

- `project`: Reusable project record.
- `project_phase`: Ordered phases such as Stewart Park Phase I and Phase II.
- `project_feature`: Searchable project components such as splash pad or bandshell.

## Meetings

- `meeting`: Public meeting, minutes, and video metadata.
- `agenda_item`: Agenda-level business.
- `council_action`: Exact motions, movers, seconds, results, and vote details.
- `video_segment`: Verified video ranges and direct timestamp links.
- `project_meeting` / `project_agenda_item`: Project relationships.

## Evidence

- `document`: Primary and secondary source metadata.
- `media`: Renderings, photos, maps, and video assets.
- `evidence_link`: Universal Evidence Explorer junction linking claims/questions to evidence.
- `claim`: Atomic factual statement.
- `verified_question`: Resident-facing sourced Q&A.

## Commercial / project administration

- `organization`, `person`: Agencies, vendors, consultants, officials.
- `funding_source`, `funding_event`: Funding history without overwriting earlier amounts.
- `contract`, `contract_amendment`: Contract lifecycle and amendments.

## Operations

- `topic`, `entity_topic`: Generic tagging across entity types.
- `research_task`: Verification and research backlog.
- `source_audit`: Link status, redirects, and content hashes.
- `search_index`: FTS5 index used by search and future AI retrieval.
