# BI to MBF publishing

This directory is the deliberate editorial handoff from Beaumont Intelligence
to Moving Beaumont Forward. It is not an automatic mirror of BI research.

Add an item to `mbf-feed.json` only after its research status is **Verified**
and its publication status is **Ready to publish**. The public URL must point to
the approved MBF version, not to private BI working material.

Each version 1 item requires:

- `id`: stable publication identifier;
- `title`: public headline;
- `excerpt`: plain-text public summary;
- `url`: canonical Moving Beaumont Forward URL;
- `publishedAt`: ISO-8601 publication timestamp; and
- optional `imageUrl`: public HTTP(S) image URL.

After the MBF version is live, update the BI dossier publication status to
**Published** and record its MBF URL.

## Council Intelligence export

Beaumont Intelligence remains the canonical source for Council Intelligence.
The export copies the publication-ready landing pages, briefing archive,
individual briefing records, document viewer/catalog, shared site assets, and
rendered document pages into the sibling MBF repository.

```bash
python scripts/sync_council_intelligence_to_mbf.py
python scripts/sync_council_intelligence_to_mbf.py --check
node scripts/audit_council_intelligence_links.mjs
```

Use `--target PATH` when the MBF `public` directory is not located at the
default sibling path. The generated `.bi-council-intelligence-manifest.json`
records every exported file and checksum. Edit the BI sources, never the
generated MBF copies.
