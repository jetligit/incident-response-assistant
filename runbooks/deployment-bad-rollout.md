# Bad Deployment / Regression Rollout

**Severity:** P1 / P2
**Affected layer:** Application (release)

## Summary

A newly deployed version introduces a regression — a bug, performance cliff, or misconfiguration. The defining clue is timing: error rate or latency degrades at almost exactly the deploy timestamp.

## Symptoms

- `error_rate` or `latency.p99_ms` step-changes at the moment of a deploy.
- New error signatures in logs that did not exist before the release.
- Degradation tracks the rollout (worsens as more instances take the new version).
- A canary or subset of hosts shows the problem first.

## Likely causes

- A code regression that passed tests but fails on real traffic/data.
- A bad or missing configuration / environment variable in the new release.
- An incompatible schema or migration shipped with the deploy.
- A dependency version bump with breaking behavior.

## Diagnosis

1. Line up the degradation start with the deployment timeline.
2. Compare error signatures before vs after the deploy.
3. Check whether only new-version instances are affected.
4. Review the diff and config changes included in the release.

## Remediation

### Immediate mitigation
- Roll back to the last known-good version immediately — this is the default first move.
- If rollback is not possible, disable the offending feature via flag.
- Halt the rollout to stop further instances taking the bad version.

### Root-cause fix
- Identify and fix the regression, then re-deploy through canary.
- Add the missing test/config validation that would have caught it.
- Fix forward only when rollback is genuinely unsafe (e.g. irreversible migration).

## Prevention

- Use canary / progressive rollouts with automated health gates.
- Add deploy markers to dashboards so timing correlation is obvious.

## Related runbooks

- `high-cpu-saturation.md`
- `memory-leak-oom.md`
