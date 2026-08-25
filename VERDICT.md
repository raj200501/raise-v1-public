# Verdict

Every result, passes and failures at the same size, each reconciling to a machine-readable
artifact under `artifacts/`.

**Status: no results yet.** The work is at Phase 0 (domain selection). This file is created
before the first measurement so that its structure is not shaped by the first number.

## Verification coverage

Every row will be classified into exactly one of:

| Class | Meaning |
|---|---|
| **primary-verifiable** | A stranger can re-derive the number from raw inputs with the shipped code. |
| **arithmetic-verifiable** | The number follows by arithmetic from a banked artifact, but the artifact itself rests on our run. |
| **neither** | Asserted from a source we cannot re-derive or re-run. |

The weakest row is published louder than the strongest.
