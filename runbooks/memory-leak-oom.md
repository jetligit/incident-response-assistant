# Memory Leak / Out-of-Memory (OOM)

**Severity:** P1 / P2
**Affected layer:** Application / Host

## Summary
Runbook: Memory Leak / Out-of-Memory (OOM) (Severity: P2, Layer: Host / Application)

Section: Summary
A process steadily consumes memory it never releases until it exhausts available RAM and is killed by the OOM killer (or crashes). The hallmark is a sawtooth or steadily-climbing memory graph with periodic restarts.

## Symptoms
Runbook: Memory Leak / Out-of-Memory (OOM) (Severity: P2, Layer: Host / Application)

Section: Symptoms
- `memory.used_percent` climbs steadily over minutes/hours, then drops sharply on restart (sawtooth).
- Logs or `dmesg` contain `Out of memory: Killed process` / `OOMKilled`.
- Container restart counts increase on a regular cadence.
- Latency degrades as the host swaps or GC pressure rises before the kill.

## Likely causes
Runbook: Memory Leak / Out-of-Memory (OOM) (Severity: P2, Layer: Host / Application)

Section: Likely causes
- An object/cache that grows unbounded (no eviction policy).
- Unclosed resources (connections, file handles, buffers) accumulating.
- A new deploy that introduced a retained reference.
- Genuine working-set growth exceeding the configured memory limit.

## Diagnosis
Runbook: Memory Leak / Out-of-Memory (OOM) (Severity: P2, Layer: Host / Application)

Section: Diagnosis
1. Confirm the climb is monotonic (leak) vs spiky (load-driven).
2. Correlate the start of the climb with a recent deploy.
3. Capture a heap snapshot/dump to find what is retained.
4. Check for unbounded caches or collections in the suspect code.

## Immediate mitigation
Runbook: Memory Leak / Out-of-Memory (OOM) (Severity: P2, Layer: Host / Application)

Section: Immediate Mitigation
- Restart the affected instance to reclaim memory and restore service.
- Stagger restarts across instances to avoid a full outage.
- Raise the memory limit temporarily if the kill cadence is too aggressive.

## Root-cause fix
Runbook: Memory Leak / Out-of-Memory (OOM) (Severity: P2, Layer: Host / Application)

Section: Root-cause fix
- Fix the leak (add eviction, close resources, drop retained references).
- Roll back the deploy if the leak was newly introduced.
- Add bounded caches with explicit max sizes and TTLs.

## Prevention
Runbook: Memory Leak / Out-of-Memory (OOM) (Severity: P2, Layer: Host / Application)

Section: Prevention
- Alert on a sustained upward memory trend, not just on OOM kills.
- Track restart cadence as a leak indicator.

## Related runbooks
Runbook: Memory Leak / Out-of-Memory (OOM) (Severity: P2, Layer: Host / Application)

Section: Related runbooks
- `disk-full.md`
- `high-cpu-saturation.md`
