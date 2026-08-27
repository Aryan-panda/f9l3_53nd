# Contributing to f9l3_53nd

Thank you for contributing to `f9l3_53nd`. Because this is a security-focused project, all contributions must adhere to strict quality and security standards.

## Code Standards
1. **Never write custom cryptographic primitives**. All cryptographic routines must leverage standard functions from Python `cryptography`.
2. **Strict Typing**: All backend code must pass `mypy --strict` and frontend code must pass `tsc --noEmit`.
3. **Linting and Formatting**: Code must adhere to `ruff` (backend) and `eslint` (frontend).
4. **Test Coverage**: Every new feature or security control must include positive unit tests, negative test cases, and adversarial validation tests.

## Development Workflow
1. Fork and clone the repository.
2. Run `make setup` to configure dependencies.
3. Run `make test` and `make lint` prior to submitting changes.
4. Use Conventional Commits (`feat:`, `fix:`, `security:`, `test:`, `docs:`).
