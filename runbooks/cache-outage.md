# Cache Outage / Stampede

**Severity:** P1 / P2
**Affected layer:** Application ↔ Cache (Redis/Memcached)

## Summary
Runbook: Cache Outage / Stampede (Severity: P1/P2, Layer: Application ↔ Cache (Redis/Memcached))

Section: Summary
A caching layer (e.g. Redis) becomes unavailable or is flushed. Every request that would have been a cache hit now falls through to the database, and the sudden load surge — a "stampede" — can overwhelm the backend that the cache was protecting.

## Symptoms
Runbook: Cache Outage / Stampede (Severity: P1/P2, Layer: Application ↔ Cache (Redis/Memcached))

Section: Symptoms
- `cache.hit_rate` drops sharply toward zero.
- Database load (`db.active_connections`, query rate) spikes immediately after.
- `latency.p99_ms` rises across all cached endpoints at once.
- Logs contain `connection refused` to the cache host or `cache miss` floods.

## Likely causes
Runbook: Cache Outage / Stampede (Severity: P1/P2, Layer: Application ↔ Cache (Redis/Memcached))

Section: Likely Causes
- The cache server crashed, restarted, or was evicted/flushed.
- A network partition between the service and the cache.
- Cache memory exhaustion triggering mass eviction.
- A deploy that changed cache keys, invalidating everything at once.

## Diagnosis
Runbook: Cache Outage / Stampede (Severity: P1/P2, Layer: Application ↔ Cache (Redis/Memcached))

Section: Diagnosis
1. Confirm `cache.hit_rate` collapsed and DB load rose in lockstep.
2. Check whether the cache process is up and reachable.
3. Determine if keys changed (deploy) vs the cache being down (infra).
4. Watch for thundering-herd behavior (many identical concurrent misses).


## Immediate mitigation
Runbook: Cache Outage / Stampede (Severity: P1/P2, Layer: Application ↔ Cache (Redis/Memcached))

Section: Immediate Mitigation
- Restore/restart the cache server.
- If the DB is being overwhelmed, add request coalescing so concurrent misses for the same key result in one DB read.
- Temporarily shed load or serve stale data if available.

## Root-cause fix
Runbook: Cache Outage / Stampede (Severity: P1/P2, Layer: Application ↔ Cache (Redis/Memcached))

Section: Root-cause fix
- Add cache redundancy/failover so a single node loss is survivable.
- Implement staggered TTLs to avoid synchronized mass expiry.
- Warm the cache after restarts before reopening full traffic.

## Prevention
Runbook: Cache Outage / Stampede (Severity: P1/P2, Layer: Application ↔ Cache (Redis/Memcached))

Section: Prevention
- Alert on `cache.hit_rate` dropping below baseline.
- Use request coalescing / single-flight for hot keys by default.

## Related runbooks
Runbook: Cache Outage / Stampede (Severity: P1/P2, Layer: Application ↔ Cache (Redis/Memcached))

Section: Related Runbooks
- `connection-pool-exhaustion.md`
- `high-cpu-saturation.md`
