# Sun-true lighting

## Contents

- [Sun facts](#sun)
- [HDRI bands](#hdri)
- [Physical sky vs HDRI](#choice)

## Sun

`as_sun(lat, lon, when, tz?)` computes azimuth (degrees from north, CW)
and elevation via astral — verified within 0.003° of the NREL SPA
reference case. Use the project's GPS datum (from `ex_search("gps")`) and
the client's date/time of interest; `apply=true` creates a correctly
rotated sun light through a checkpointed batch. Below-horizon elevations
come back flagged `night scene`.

## HDRI

The same call returns an HDRI suggestion: elevation band (night /
sunrise-sunset / morning-evening / midday) plus search keywords for
`as_search(asset_class="hdri")` on Poly Haven (all CC0). World rotation =
computed azimuth − the HDRI's own sun azimuth; the server detects that
once per HDRI (brightest pixel) and caches it as a fact — never eyeball
it.

## Choice

Physical sky (sun light + Nishita) is the default for solar ACCURACY
(shadow studies, Okongo-style verification against site photos). An HDRI
is for MOOD once geometry is settled. Do not stack both at full strength.
