# DNS Resolution Failure

**Severity:** P1
**Affected layer:** Network / Service discovery

## Summary
Runbook: DNS Resolution Failure (Severity: P1, Layer: Network / Service discovery)

Section: Summary
A service can no longer resolve the hostname of a dependency (database, API, or internal service). Because DNS sits underneath nearly every network call, a resolution failure looks like widespread, simultaneous connectivity loss to one or more dependencies.

## Symptoms
Runbook: DNS Resolution Failure (Severity: P1, Layer: Network / Service discovery)

Section: Symptoms
- Logs contain `Name or service not known`, `Temporary failure in name resolution`, or `no such host`.
- Errors appear suddenly and affect all calls to a specific dependency at once.
- Direct connections by IP succeed while connections by hostname fail.
- `error_rate` jumps to a step change rather than a gradual climb.

## Likely causes
Runbook: DNS Resolution Failure (Severity: P1, Layer: Network / Service discovery)

Section: Likely Causes
- An expired or misconfigured DNS record.
- A DNS server / resolver outage or overload.
- A bad change to internal service-discovery (e.g. Consul, CoreDNS, Route 53).
- DNS cache poisoning or TTL expiry exposing a stale record.

## Diagnosis
Runbook: DNS Resolution Failure (Severity: P1, Layer: Network / Service discovery)

Section: Diagnosis
1. Attempt to resolve the failing hostname from the affected host.
2. Test resolution against an alternate resolver to isolate server vs record.
3. Confirm whether connecting by IP works (isolates DNS vs the dependency itself).
4. Check recent changes to DNS records or service-discovery config.

## Immediate mitigation
Runbook: DNS Resolution Failure (Severity: P1, Layer: Network / Service discovery)

Section: Immediate Mitigation
- Point at a healthy alternate resolver if the resolver is the problem.
- Revert the offending DNS / service-discovery change.
- As a last resort, add a temporary hosts-file entry to bypass DNS for the critical dependency.

## Root-cause fix
Runbook: DNS Resolution Failure (Severity: P1, Layer: Network / Service discovery)

Section: Root-cause fix
- Correct the DNS record or restore the resolver.
- Add redundant resolvers and reasonable TTLs.
- Gate DNS changes behind review and staged rollout.

## Prevention
Runbook: DNS Resolution Failure (Severity: P1, Layer: Network / Service discovery)

Section: Prevention
- Monitor resolution success rate and resolver latency.
- Alert on DNS record changes to critical hostnames.

## Related runbooks
Runbook: DNS Resolution Failure (Severity: P1, Layer: Network / Service discovery)

Section: Related runbooks
- `ssl-certificate-expiry.md`
- `rate-limit-throttling.md`
