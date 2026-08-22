# Style matching

## Contents

- [The style brief](#brief)
- [How ranking uses it](#ranking)
- [Avoid-lists](#avoid)

## Brief

`as_style_brief()` derives, from media TEE already ingested:
- **palette**: ≤6 CIELAB k-means clusters from site photos, each carried
  as a NAME ("terracotta", "sage") + Lab + weight. Names are the form you
  reason in; Lab is what the server compares with.
- **terms**: style/material words from the caption pass (e.g. "rustic",
  "brick", "warm").
- **avoid**: nouns the client rejected in the audio brief ("no marble").

## Ranking

`as_search(match_style=true)` ranks server-side: keyword/tag overlap
first, then palette proximity as mean nearest-ΔE00 between the asset's
known palette and the brief (ΔE00 < 10 similar, > 28 visibly off, > 40
unrelated), then optional index-time thumbnail embeddings ([assets-embed]
extra). You never see the scores — just the ordered shortlist. Trust the
order unless a row conflicts with the avoid-list.

`as_verify(match_style=true)` re-checks applied materials: anything ΔE00
> 28 from every brief color is flagged with the offending entity.

## Avoid

The avoid-list wins over ranking. A top-ranked marble table under "no
marble" is a wrong pick. State in your reply when you drop a hit for the
avoid-list, so the record shows why.
