# QMAX metadata evidence and limits

Reviewed 2026-09-11. The current local proxy maps claude-qwen-max to
hosted_vllm/qwen3.8-max on DashScope International. Its own model-info response
supplies null limits and zero price defaults; those are not verified model facts.
The sanitized observation is evidence/qmax-route-observation.json.

[Alibaba's model specification](https://www.alibabacloud.com/help/en/model-studio/qwen3-8-max)
documents a 1,000,000-token context, 991,808 ordinary input tokens or 983,616
thinking-mode input tokens, and 131,072 output tokens. We use the lower input
limit. The Singapore/International published uncached rates are USD2 input and
USD6 output per million tokens, also listed in
[official pricing](https://www.alibabacloud.com/help/en/model-studio/model-pricing).
These are list-rate estimates, excluding caching, discounts, credits and invoice
adjustments. They do not establish the proxy's measured capacity or actual bill.

[Aider's explicit metadata and model-settings files](https://aider.chat/docs/config/adv-model-settings.html)
are the supported integration mechanism. This candidate writes them into each
worker's private directory under the exact name openai/claude-qwen-max. It keeps
the endpoint and main/weak/editor model names, paid classification and grant checks.
The separate documentation output request is capped at 2,048 tokens; this is a
bounded task policy, not the provider's capacity. Generation quality and sufficient
reasoning/output budget have not been established by the offline recognition test.

The reviewed configuration expires on 2026-09-25. Recheck routing and primary
provider facts before renewal; configured stale or mismatched metadata refuses
with a short corrective message. A profile with no metadata retains Aider's
ordinary unknown-model warning. Credential diagnostics stay enabled in both cases.

The child-only verified /usr/bin/true browser controller prevents Aider Python
browser offers from opening tabs. Printed warnings remain available. No system
browser preference, upstream proxy or installed third-party worker was changed.
