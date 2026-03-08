# Design Doc: Telemetry Lock Cleanup

The `bot/utils/telemetry.py` file uses `asyncio.Lock()`, but some of its functions are synchronous and attempting to use `acquire()` or `release()` methods which are incompatible with the async stack in their current form. This design aims to clean up these synchronous lock operations and replace them with TODOs for future async migration.

## Architecture

- **File**: `bot/utils/telemetry.py`
- **Scope**: Synchronous functions that interact with `_file_lock`.

## Components

### 1. `log_event`
- Remove `finally: _file_lock.release()`.
- Maintain existing `# TODO: migrate to asyncio.Lock properly`.

### 2. `export_events`
- Add `# TODO: migrate to asyncio.Lock properly` at the beginning of the function.
- Remove `finally: _file_lock.release()`.

### 3. `get_summary`
- Remove the synchronous acquisition block.
- Add `# TODO: migrate to asyncio.Lock properly`.
- Remove `finally: _file_lock.release()`.

### 4. `_atomic_write`
- Ensure no lock acquisition/release exists as per prompt instructions (it currently has none, but I will verify during implementation).

## Data Flow
Telemetry data will still be written to `EVENTS_LOG_PATH` using `_atomic_write`. Without the lock, concurrent writes might occur if multiple synchronous processes call these functions simultaneously, but since the bot is migrating to an async stack, this is a temporary state until full migration.

## Error Handling
The existing try-except blocks will remain to handle file I/O and JSON parsing errors.

## Testing
- Verify that `log_event`, `export_events`, and `get_summary` do not throw `TypeError` or `AttributeError` when called.
- Ensure telemetry data is still recorded.
