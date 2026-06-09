# Security Policy

## Reporting a vulnerability

If you've found a vulnerability in this repository — cryptographic, schema-confusion, signature-bypass, temporal-validity bypass, disclaimer-stripping, supply-chain, or otherwise — please report it privately to:

**`security@etymolt.com`**

Include:

1. A description of the vulnerability.
2. Steps to reproduce (a small test vector + the expected vs. observed validator output is ideal).
3. Your name and affiliation if you'd like attribution. We will credit reporters in the changelog unless you ask not to be named.

Encrypted submission is welcome; request our PGP key in your first message.

## What happens next

| Step | Target |
|---|---|
| Acknowledgment of receipt | 2 business days |
| Triage decision (in-scope / severity tier) | 5 business days |
| Fix landing in this repo (P0/P1) | 30 days from triage |
| Public disclosure + credit (if applicable) | After fix lands, coordinated with reporter |

For P0 vulnerabilities that affect downstream consumers — anything that lets a forged verdict validate, lets a stale verdict render without a banner, or breaks a signature primitive — we will issue an out-of-band notice to all known implementers within 7 days, embargo timing TBD with the reporter.

## Bureau Model boundary

This policy covers software, schemas, and cryptographic primitives. Disputes about the **content** of a verdict (e.g. "this name actually IS taken in jurisdiction X") are not security issues — those are accuracy issues, reported via the normal issue tracker. See the [Bureau Model](https://github.com/etymolt/evp-spec/blob/main/spec/EVP-1-SPEC.md#52-the-bureau-model) framing: we report on records of record at a point in time; the records themselves are the underlying truth.

## Out of scope

- Etymolt product surfaces (use `support@etymolt.com`).
- Third-party EVP/1 issuers — vulnerability reports about non-Etymolt issuers go to that issuer.
- Editorial corrections (typos, broken links, prose clarity) — file as regular issues.
