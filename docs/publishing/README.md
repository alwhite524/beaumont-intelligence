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
