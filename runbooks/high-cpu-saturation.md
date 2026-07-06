# High CPU Saturation

**Severity:** P2
**Affected layer:** Host / Application

## Summary
Runbook: High CPU Saturation (Severity: P2, Layer: Host / Application)

Section: Summary
A service consumes nearly all available CPU, so requests queue behind the work and latency rises across the board. Unlike a crash, the service stays "up" but becomes progressively unresponsive.

## Symptoms
Runbook: High CPU Saturation (Severity: P2, Layer: Host / Application)

Section: Symptoms
- `cpu.used_percent` sustained near 100% on the affected hosts.
- `latency.p99_ms` rises broadly across endpoints (not isolated to one).
- Throughput plateaus or drops despite incoming demand.
- Health checks begin timing out, triggering false-positive restarts.

## Likely causes
Runbook: High CPU Saturation (Severity: P2, Layer: Host / Application)

Section: Likely causes
- A traffic increase beyond the service's capacity.
- An inefficient code path or hot loop introduced by a recent deploy.
- A poorly-indexed query or N+1 pattern doing excess work per request.
- Garbage-collection thrash under memory pressure.

## Diagnosis
Runbook: High CPU Saturation (Severity: P2, Layer: Host / Application)

Section: Diagnosis
1. Confirm CPU is the bottleneck (vs memory or I/O wait).
2. Correlate the saturation start with any recent deploy.
3. Profile or sample stacks to find the hot path.
4. Check whether traffic genuinely increased or work-per-request increased.

## Immediate mitigation
Runbook: High CPU Saturation (Severity: P2, Layer: Host / Application)

Section: Immediate Mitigation
- Scale out horizontally (add instances) to spread load.
- Shed non-critical load (disable expensive optional features) if scaling is slow.
- Roll back the suspect deploy if saturation began right after it.

## Root-cause fix
Runbook: High CPU Saturation (Severity: P2, Layer: Host / Application)

Section: Root-cause fix
- Optimize the hot code path or query identified by profiling.
- Add autoscaling tied to CPU utilization.
- Add caching for repeated expensive computations.

## Prevention
Runbook: High CPU Saturation (Severity: P2, Layer: Host / Application)

Section: Prevention
- Alert on sustained CPU above 80%.
- Capacity-plan against peak, not average, traffic.

## Related runbooks
Runbook: High CPU Saturation (Severity: P2, Layer: Host / Application)

Section: Related runbooks
- `connection-pool-exhaustion.md`
- `deployment-bad-rollout.md`
