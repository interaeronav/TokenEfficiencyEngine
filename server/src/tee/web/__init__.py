"""Web lane (A34, research 49): budgeted, cited answers from one URL.

guard validates destinations (SSRF), fetch is the polite cached fetcher,
extract turns HTML into an inert budgeted quote, tools exposes web_lookup.
Fetched content is data, never instructions - the whole lane is read-only
and nothing in a page can cause another fetch, a tool call, or a config
change.
"""
