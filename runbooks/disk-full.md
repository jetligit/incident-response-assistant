# Disk Full / Low Disk Space

**Severity:** P1 / P2
**Affected layer:** Host / Storage

## Summary
Runbook: Disk Full / Low Disk Space (Severity: P1/P2, Layer: Host / Storage)

Section: Summary
A host or volume runs out of free disk space. Writes begin to fail, which cascades into crashed processes, corrupted state, and unwritable logs — often making the incident harder to diagnose because the logs themselves stop.

## Symptoms
Runbook: Disk Full / Low Disk Space (Severity: P1/P2, Layer: Host / Storage)

Section: Symptoms
- `disk.used_percent` at or near 100% on the affected host.
- Logs contain `No space left on device` (errno 28).
- Database or application processes crash or refuse new writes.
- Log files stop updating (the logger itself can't write).

## Likely causes
Runbook: Disk Full / Low Disk Space (Severity: P1/P2, Layer: Host / Storage)

Section: Likely Causes
- Unrotated or unbounded log files growing without limit.
- A runaway process writing temp files or core dumps.
- Old build artifacts, container images, or backups never cleaned up.
- A data volume genuinely outgrowing its provisioned size.

## Diagnosis
Runbook: Disk Full / Low Disk Space (Severity: P1/P2, Layer: Host / Storage)

Section: Diagnosis
1. Identify the full volume and how fast it filled (sudden vs gradual).
2. Find the largest directories/files to locate the consumer.
3. Determine whether it is a leak (one process) or organic growth (capacity).
4. Check whether log rotation is configured and running.

## Immediate mitigation
Runbook: Disk Full / Low Disk Space (Severity: P1/P2, Layer: Host / Storage)

Section: Immediate Mitigation
- Delete or compress obviously safe-to-remove files (rotated logs, temp files, old artifacts).
- Truncate (do not `rm` an open file) actively-written logs to reclaim space immediately.
- Restart processes that crashed due to failed writes, once space is reclaimed.

## Root-cause fix
Runbook: Disk Full / Low Disk Space (Severity: P1/P2, Layer: Host / Storage)

Section: Root-cause fix
- Configure and enforce log rotation with size/age caps.
- Add cleanup jobs for artifacts, images, and backups.
- Expand the volume if growth is legitimate.

## Prevention
Runbook: Disk Full / Low Disk Space (Severity: P1/P2, Layer: Host / Storage)

Section: Prevention
- Alert on `disk.used_percent` at 80% (warning) and 90% (critical), before it fills.
- Set retention policies on all log and backup destinations.

## Related runbooks
Runbook: Disk Full / Low Disk Space (Severity: P1/P2, Layer: Host / Storage)

Section: Related runbooks
- `memory-leak-oom.md`
- `deployment-bad-rollout.md`
