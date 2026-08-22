# Police article sources

This directory contains the editable Beaumont Intelligence source for police articles that are published to Moving Beaumont Forward.

## PD Technology

Edit `pd-technology.html`, not the generated public copy at `docs/dossiers/police/flock-cameras.html`. The source intentionally contains the complete MBF page so publishing preserves the approved design, asset paths, interactions, and wording exactly.

Publish the article with:

```bash
python scripts/publish_pd_technology.py
```

Verify that the public copy is current without changing files:

```bash
python scripts/publish_pd_technology.py --check
```
