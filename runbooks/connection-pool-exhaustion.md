# Database Connection Pool Exhaustion

**Severity:** P1 / P2
**Affected layer:** Application ↔ Database

## Summary
Runbook: Database Connection Pool Exhaustion (Severity: P1/P2, Layer: Application ↔ Database)

Section: Summary
A service holds a fixed-size pool of reusable database connections. When every connection is checked out and busy, new requests must wait for one to free up. Under load this manifests as request timeouts, climbing latency, and rising error rates — even though the database itself is healthy.

## Symptoms
Runbook: Database Connection Pool Exhaustion (Severity: P1/P2, Layer: Application ↔ Database)

Section: Symptoms
- `db.active_connections` flatlines at a round number (the configured pool max) and stays pinned there.
- `latency.p99_ms` climbs sharply shortly after the connection count plateaus.
- `error_rate` spikes as queued requests exceed their timeout.
- Logs contain `Timeout waiting for connection from pool` or `connection acquisition timed out`.
- The database's own CPU, memory, and disk look normal — the bottleneck is the pool, not the DB.

## Likely causes
Runbook: Database Connection Pool Exhaustion (Severity: P1/P2, Layer: Application ↔ Database)

Section: Likely causes:
- A legitimate traffic spike that exceeded provisioned pool capacity.
- A retry storm from an upstream caller multiplying request volume.
- Slow queries holding connections longer than usual, reducing effective pool throughput.
- A connection leak: code paths that borrow a connection but never return it.

## Diagnosis
Runbook: Database Connection Pool Exhaustion (Severity: P1/P2, Layer: Application ↔ Database)

Section: Diagnosis:
1. Confirm `db.active_connections` is flat at the pool max (not merely high).
2. Correlate the plateau timestamp with the start of the latency/error spike.
3. Check upstream services for a spike in request volume or retries.
4. Inspect slow-query logs to rule out a single slow statement hogging connections.
5. Check for unclosed connections (leak) by watching whether the count recovers when traffic drops.

## Immediate mitigation
Runbook: Database Connection Pool Exhaustion (Severity: P1/P2, Layer: Application ↔ Database)

Immediate Mitigation:
- Increase the pool size as a short-term measure to relieve pressure.
- If a retry storm is suspected, enable backpressure / request queuing at the edge.
- Restart the affected service instance only if a connection leak is confirmed and growing.

## Root-cause fix
Runbook: Database Connection Pool Exhaustion (Severity: P1/P2, Layer: Application ↔ Database)

Section: Root-cause fix
- Right-size the pool against realistic peak load with headroom.
- Fix any code paths leaking connections (ensure connections are released in `finally`).
- Add circuit breakers / exponential backoff upstream to prevent retry storms.

## Prevention
Runbook: Database Connection Pool Exhaustion (Severity: P1/P2, Layer: Application ↔ Database)

Section: Prevention
- Alert on `db.active_connections` approaching (not just hitting) the pool max.
- Load-test to establish the pool size needed for peak traffic.
- Add connection-acquisition-time as a tracked metric.

## Related runbooks
Runbook: Database Connection Pool Exhaustion (Severity: P1/P2, Layer: Application ↔ Database)

Section: Related runbooks
- `message-queue-backlog.md`
- `high-cpu-saturation.md`
