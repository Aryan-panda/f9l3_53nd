# ADR-008: Decoupled Storage Model & Path Traversal Containment

## Status
Accepted

## Context
Handling user-uploaded files on disk introduces critical security risks: Path Traversal (CWE-22), Arbitrary File Overwrite, and Filename Collisions.

## Decision
We implement a **Decoupled Storage Engine**:
1. **Name Decoupling**: Original filenames are stored only as database metadata.
2. **UUID Storage Paths**: Physical payload paths use random UUIDs outside the web root:
   `storage/encrypted/<transfer-uuid>/payload.enc`
3. **Quarantine Isolation**: Payloads that fail verification are moved to `storage/quarantine/<transfer-uuid>/` for forensic review.
4. **Canonical Path Assertion**: Every disk path resolution verifies that `os.path.realpath(target_path)` starts with `os.path.realpath(storage_base_dir)`.

## Alternatives Considered & Rejected
- **Direct Filename on Disk (`storage/uploads/filename.pdf`)**: Vulnerable to `../../` directory traversal, character encoding attacks, and accidental file overwrites.
- **Storing Blobs in PostgreSQL (`bytea` / `lo_blob`)**: Causes massive database bloat, degrades query cache performance, and complicates streaming I/O.

## Security Impact
- Completely neutralizes path traversal attacks at the architectural layer.
- Quarantined payloads are isolated from valid download routes.

## Consequences
- Requires storage cleanup routines upon transfer deletion or failure.
