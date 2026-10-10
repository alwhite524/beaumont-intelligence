# January-March 2022 Council source intake

Six user-supplied City agenda packets were imported on October 10, 2026.
Their original pages are preserved in Cloudflare R2. Each supporting document
opens in the site's document viewer; full packets remain available as backups.

| Meeting | Packet pages | Numbered regular-session items | Supporting documents | Transcript video ID |
|---|---:|---:|---:|---|
| 2022-01-04 | 833 | 9 | 26 | Not supplied |
| 2022-01-18 | 806 | 21 | 58 | WQQgg6Y-Idw |
| 2022-02-01 | 842 | 16 | 34 | KqzikDSwHGw |
| 2022-02-15 | 470 | 21 | 46 | X2YV91fwPOw |
| 2022-03-01 | 721 | 18 | 53 | JlzlPmUnCp4 |
| 2022-03-15 | 389 | 18 | 41 | Not supplied |

The 270 newly archived PDFs comprise 258 supporting documents, six published
agendas and six complete packets. The R2 sync verified object sizes and checksum
metadata. Every new URL was checked for a PDF signature and production-origin
CORS permission. Localhost is not an allowed R2 origin, so a local preview alone
cannot confirm inline PDF rendering under the production origin.

## Provenance and limits

- Document boundaries come from the packet bookmarks. Validation checks that
  the agenda and extracted documents cover every packet page without gaps or
  overlap. This is not a completeness audit against the City's historical HTML
  agenda. No original City download URL was supplied or invented.
- All four transcripts use complete English automatic-caption files retrieved
  from YouTube. Rolling-caption repetition is removed; timestamps and wording
  remain a research aid, not certified transcription. All four caption tracks
  include the meeting adjournment. Browser exports were truncated and were not
  used as the final transcripts. March 1 captions were available through direct
  retrieval despite the browser export reporting none; local ASR was stopped.
- The February 1 video is titled February 2 on YouTube. Opening captions at
  2:08 and 2:30 identify February 1, consistent with the agenda and minutes.
- January 18 Item 17's staff report prints January 18, 2021. It remains unchanged
  within the January 18, 2022 packet.
- Outcomes are maintained separately in `2022-q1-meeting-review.json`, based on
  the minutes already cataloged in `minutes-register.json`. Original agenda
  recommendations are retained. Approximate video links come from captions;
  audiovisual playback has not been independently checked.
- The March 15 minutes swap items 11 and 12. Outcomes are matched by subject to
  the original agenda: item 11 is Nvoicepay; item 12 is Noble Creek Vistas.
- Where minutes omit consent details, caption evidence is labeled separately;
  unidentified movers and seconders are not inferred.
- All seven service areas were considered when mapping agenda subjects. Specific
  findings were added to the relevant budget, police, Stewart Park and downtown
  pages. Other subjects remain discoverable through agenda and Research Library
  searches without implying a connection to an unrelated project center.

## Rebuild

`import_2022_agenda_packets.py` requires the six original files in Downloads and
creates ignored PDF artifacts plus the six agenda datasets. It does not replace
the separate review dataset. `import_youtube_vtt.py` converts a downloaded VTT
with `--date` and `--video-id` arguments. Temporary captions, audio and tools
remain in ignored `tmp/`.

After reviewing data, run:

```text
python scripts/build_2022_interactive_agendas.py
python scripts/build_recent_center_findings.py
python scripts/build_council_meeting_sources.py
python scripts/build_research_library_index.py
```

Validation covers page continuity, R2 manifest identities, the March reordered
items, video-date provenance, caption conversion, Research Library routing and
existing minutes links. Browser checks cover agenda search, expanded outcomes,
viewer invocation and transcript search.
