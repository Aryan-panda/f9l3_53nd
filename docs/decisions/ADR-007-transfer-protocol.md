# ADR-007: Transfer State Machine & Replay Protection Protocol

## Status
Accepted

## Context
File transfers across untrusted networks can fail at multiple points (upload abort, network drop, tag mismatch, digest verification failure). The system requires a deterministic finite state machine to prevent ambiguous execution states, replay attacks, and incomplete transfers.

## Decision
We define an explicit **Transfer Finite State Machine**:
- States: `CREATED`, `VALIDATING`, `HASHING`, `ENCRYPTING`, `READY`, `TRANSFERRING`, `RECEIVED`, `AUTHENTICATING`, `DECRYPTING`, `VERIFYING`, `COMPLETED`, `FAILED`, `QUARANTINED`, `REJECTED`, `REPLAY_DETECTED`.
- State transitions are strictly validated in code via `TransferStateMachine.validate_transition(current, target)`.
- Terminal states (`COMPLETED`, `FAILED`, `QUARANTINED`, `REJECTED`, `REPLAY_DETECTED`) cannot transition to any active state.
- Duplicate submissions of existing transfer IDs trigger the `REPLAY_DETECTED` state.

## Alternatives Considered & Rejected
- **Implicit Boolean Flags (`is_completed: bool`)**: Fails to capture intermediate cryptographic states and prevents forensic inspection of failure points.
- **Unchecked String State Updates**: Allows race conditions where an aborted transfer could be falsely marked completed.

## Security Impact
- Enforces fail-closed invariants: no file payload can reach `COMPLETED` without passing both AEAD tag authentication and SHA-256 verification.
- Tampered payloads transition deterministically to `QUARANTINED`.

## Consequences
- State transitions require atomic database updates and emit audit events.
