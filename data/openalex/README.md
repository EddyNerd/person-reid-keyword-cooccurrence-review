# OpenAlex coverage audit

This directory documents the comparison between the frozen analytical WoS corpus and the independently assembled OpenAlex reference set for 2015-2024.

| File | Contents |
|---|---|
| `search_manifest.json` | Saved query, retrieval date, requested years, page URLs, returned counts and raw-page checksums |
| `search_records.csv` | Bibliographic metadata for all 5,666 retrieved OpenAlex records |
| `eligibility_decisions.csv` | A recorded inclusion or exclusion decision for each retrieved record |
| `eligible_reference_publications.csv` | The 4,665 eligible full journal/conference publications and their matching status |
| `matched_publications.csv` | Publication-pair matching decisions and identifiers |
| `publisher_verified_alias_matches.csv` | Documented publisher-verified matching aliases |
| `relative_recall.csv` | Coverage proportions by publication type, period and year |

The saved title search used the following query:

```text
((person OR pedestrian OR human) AND ("re-identification" OR reidentification OR "re-id")) OR "person search" OR "person retrieval"
```

All result pages were collected separately by publication year. Two duplicate manifestations were removed from 5,666 retrieved records. The explicit human person-Re-ID title subset contained 5,207 records. Excluding 329 preprints and 185 other/unclassified types left 4,693 broad journal/conference records. A more specific format and status check excluded 28 further records, leaving 4,665 eligible publications.

The per-record decisions identify these 28 cases as 13 records outside the full article/review/proceedings formats, 10 standalone notices or peer-review items, four format conflicts resolved using matching document-type evidence, and one case with unconfirmed full-publication status. These categories explain the second check separately from the earlier broad type filter.

The eligible set contains 2,450 journal articles/reviews and 2,215 conference papers. Of these, 1,869 journal publications and no conference versions match the analytical corpus. Relative recall is therefore 1,869/4,665 = 40.1% overall and 1,869/2,450 = 76.3% within the journal subset. It is conditional on this screened reference set and does not measure recall of all relevant research or establish database-wide absence.

Conference, journal and preprint versions are treated separately. A cited-reference mention in a source record does not count as source-record inclusion. OpenAlex-generated keywords are not used as author keywords in the co-occurrence analysis.
