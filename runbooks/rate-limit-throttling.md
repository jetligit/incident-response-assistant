# Upstream Rate Limiting / Throttling

**Severity:** P2
**Affected layer:** Application ↔ External dependency

## Summary
Runbook: Upstream Rate Limiting / Throttling (Severity: P2, Layer: Application ↔ External dependency)

Section: Summary
A service exceeds the request quota of an upstream API or dependency and starts receiving throttling responses. Requests fail or slow down not because of a local fault but because a dependency is deliberately rejecting excess load.

## Symptoms
Runbook: Upstream Rate Limiting / Throttling (Severity: P2, Layer: Application ↔ External dependency)

Section: Symptoms
- Logs contain HTTP `429 Too Many Requests` or provider-specific `RateLimitExceeded`.
- `error_rate` rises specifically on calls to one external dependency.
- Errors correlate with a traffic spike or a new high-volume code path.
- Responses include `Retry-After` headers.

## Likely causes
Runbook: Upstream Rate Limiting / Throttling (Severity: P2, Layer: Application ↔ External dependency)

Section: Likely causes
- A legitimate traffic increase pushing past the quota.
- A retry storm amplifying request volume against the limit.
- A new feature or batch job making more calls than expected.
- A quota reduction on the provider side.

## Diagnosis
Runbook: Upstream Rate Limiting / Throttling (Severity: P2, Layer: Application ↔ External dependency)

Section: Diagnosis
1. Confirm the 429s are concentrated on a single upstream dependency.
2. Check whether request volume to that dependency genuinely increased.
3. Determine if retries are compounding the problem (retries on 429 without backoff).
4. Compare current call rate against the documented quota.

## Immediate mitigation
Runbook: Upstream Rate Limiting / Throttling (Severity: P2, Layer: Application ↔ External dependency)

Section: Immediate mitigation
- Honor `Retry-After` and add exponential backoff with jitter.
- Throttle or queue outbound requests locally to stay under the quota.
- Pause non-critical batch jobs hitting the same dependency.

## Root-cause fix
Runbook: Upstream Rate Limiting / Throttling (Severity: P2, Layer: Application ↔ External dependency)

Section: Root-cause fix
- Add client-side rate limiting aligned to the provider quota.
- Cache responses to reduce call volume.
- Request a quota increase if demand is legitimate and sustained.

## Prevention
Runbook: Upstream Rate Limiting / Throttling (Severity: P2, Layer: Application ↔ External dependency)

Section: Prevention
- Track outbound call rate per dependency against its quota.
- Never retry 429s without backoff.

## Related runbooks
Runbook: Upstream Rate Limiting / Throttling (Severity: P2, Layer: Application ↔ External dependency)

Section: Related runbooks
- `connection-pool-exhaustion.md`
- `message-queue-backlog.md`
