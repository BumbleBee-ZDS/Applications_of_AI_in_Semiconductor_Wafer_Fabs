# FabGraph MVP - Project Rules

## Language & Style
- All code comments and docstrings MUST be in Chinese (Simplified).
- All variable names, function names, and class names MUST be in English.
- Use type hints for ALL function signatures (Python 3.11+).
- Use `dataclass` or `pydantic.BaseModel` for all data models.

## Architecture
- Follow layered architecture: api -> service -> repository -> model.
- Each module must have its own directory under `src/`.
- All database access must go through repository layer, no raw SQL in service layer.
- Use dependency injection pattern for service dependencies.

## Code Quality
- Maximum function length: 50 lines.
- Maximum file length: 300 lines. Split if exceeds.
- Every public function must have a docstring with Args, Returns, Raises.
- Use `logging` module, never use `print()` for output.
- All async functions must use `async/await`, no `.then()` or callbacks.

## Testing
- Use `pytest` for all tests.
- Every service module must have corresponding test in `tests/`.
- Use `pytest-asyncio` for async test functions.
- Mock all external dependencies (LLM API, database) in tests.

## Error Handling
- Use custom exception hierarchy rooted at `FabGraphError`.
- Never use bare `except:` clauses.
- All API endpoints must return structured JSON error responses.

## Git Convention
- Commit messages follow Conventional Commits: feat:, fix:, docs:, refactor:, test:.