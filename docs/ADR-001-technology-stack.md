# ADR-001: GitHub + SQLite + Static Site

Status: Accepted

## Decision
Use a private personal GitHub repository, GitHub Codespaces, SQLite, and a generated static site published with GitHub Pages.

## Consequences
- Minimal recurring cost
- Familiar SQL model
- Strong version history
- No production database server
- Build step required to publish database content as static JSON
- Browser and employer-device activity may still be logged or cached
