# Decision Log

## Display decisions
- 2019-06-19. Users expect to see their full name in the proxy field on
  `/abs` pages. In previous versions as well as in the legacy arXiv codebase,
  the proxy name was truncated to single word and upper-cased, under the
  assumption that the proxy would always be an abbreviated name of an
  organization (like CCSD, or VTEX). We decided to make the display rules for
  the proxy name more flexible, by checking the following conditions:
  * if the proxy name is more than one word long, display it as is, with
    `tex2utf` filtering; trail with "as proxy" instead of just "proxy". This
    condition is intended to preserve individual names.
  * if the proxy name is only one word long or starts with "ccsd", then
    upper-case it as before. In the "ccsd" case, we do not display any
    subsequent tokens, as this was how it was displayed historically; only
    "CCSD" is displayed.
  We have decided not to provide separate configuration for the CCSD case,
  since there are no other cases like this and there are unlikely to be new
  ones. Additional context for this decision is available
  [here](https://github.com/arXiv/arxiv-browse/pull/102).
