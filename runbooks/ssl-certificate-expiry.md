# SSL/TLS Certificate Expiry

**Severity:** P1
**Affected layer:** Network / Transport security

## Summary
Runbook: SSL/TLS Certificate Expiry (Severity: P1, Layer: Network / Transport security)

Section: Summary
A TLS certificate used by a service (or one of its dependencies) expires. Clients refuse to complete the handshake, so every secured connection fails at once — a sharp, total cutover rather than a gradual degradation.

## Symptoms
Runbook: SSL/TLS Certificate Expiry (Severity: P1, Layer: Network / Transport security)

Section: Symptoms
- Logs contain `certificate has expired`, `certificate verify failed`, or `SSL handshake failed`.
- All HTTPS calls to the affected endpoint fail simultaneously.
- The failure timestamp lines up exactly with a certificate `notAfter` date.
- Browsers/clients show `NET::ERR_CERT_DATE_INVALID` or equivalent.

## Likely causes
Runbook: SSL/TLS Certificate Expiry (Severity: P1, Layer: Network / Transport security)

Section: Likely causes
- A certificate that was never renewed (manual process missed).
- Auto-renewal (e.g. cert-manager, certbot) silently failing.
- A renewed certificate that was issued but not deployed/reloaded.
- An intermediate/chain certificate expiring rather than the leaf.

## Diagnosis
Runbook: SSL/TLS Certificate Expiry (Severity: P1, Layer: Network / Transport security)

Section: Diagnosis
1. Inspect the served certificate's expiry date and chain.
2. Confirm the failure start matches the expiry timestamp.
3. Check whether a renewed cert exists but wasn't loaded by the service.
4. Verify the full chain, not just the leaf certificate.

## Immediate mitigation
Runbook: SSL/TLS Certificate Expiry (Severity: P1, Layer: Network / Transport security)

Section: Immediate mitigation
- Deploy the renewed certificate and reload/restart the TLS terminator.
- If no renewed cert exists, issue one immediately (ACME or internal CA).
- Roll out the new cert to all instances/load balancers serving the endpoint.

## Root-cause fix
Runbook: SSL/TLS Certificate Expiry (Severity: P1, Layer: Network / Transport security)

Section: Root-cause fix
- Fix and verify automated renewal end to end (issue → deploy → reload).
- Ensure the reload step is part of renewal, not just issuance.

## Prevention
Runbook: SSL/TLS Certificate Expiry (Severity: P1, Layer: Network / Transport security)

Section: Prevention
- Alert on certificates 30/14/7 days before expiry.
- Monitor the actually-served certificate, not just the stored one.

## Related runbooks
Runbook: SSL/TLS Certificate Expiry (Severity: P1, Layer: Network / Transport security)

Section: Related runbooks
- `dns-resolution-failure.md`
- `deployment-bad-rollout.md`
