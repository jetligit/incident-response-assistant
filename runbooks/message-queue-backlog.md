# Message Queue Backlog

**Severity:** P2
**Affected layer:** Async processing (Kafka/SQS/RabbitMQ)

## Summary

Messages are produced faster than consumers can process them, so the queue depth grows without bound. Downstream effects (delayed notifications, stale data, processing lag) appear even though no component has outright failed.

## Symptoms

- `queue.depth` or consumer lag climbing steadily.
- Increasing age of the oldest unprocessed message.
- Downstream freshness SLAs slipping (e.g. notifications arriving late).
- Consumer CPU or DB at capacity while producers run normally.

## Likely causes

- A producer spike (traffic, a backfill, or a batch job) outpacing consumers.
- Consumers slowed or crashed, reducing drain rate.
- A poison message repeatedly failing and blocking a partition.
- A downstream dependency (DB, API) throttling consumer throughput.

## Diagnosis

1. Confirm queue depth is rising (production rate > consumption rate).
2. Determine whether producers spiked or consumers slowed.
3. Check consumer health, error rate, and downstream dependencies.
4. Look for a poison message stuck at the head of a partition.

## Remediation

### Immediate mitigation
- Scale out consumers to increase drain rate.
- Move a confirmed poison message to a dead-letter queue to unblock processing.
- Pause or throttle non-critical producers to let consumers catch up.

### Root-cause fix
- Right-size consumer concurrency against peak production.
- Add autoscaling on queue depth / consumer lag.
- Ensure poison messages are dead-lettered automatically after N retries.

## Prevention

- Alert on consumer lag and oldest-message age, not just queue depth.
- Load-test the consumer drain rate against expected peaks.

## Related runbooks

- `rate-limit-throttling.md`
- `connection-pool-exhaustion.md`
