# Design: Admin Handler Refactor

## Overview
Refactor admin.py (869 lines) into a modular admin package to improve maintainability and separation of concerns.

## Architecture
Create `handlers/admin/` package with:
- `__init__.py`: Centralized handler imports
- 5 submodules: mass_messaging, user_management, log_viewer, ad_manager, utils

## Components
- **mass_messaging.py**: Interactive conversation handlers for /ms command
- **user_management.py**: /users command and user data management
- **log_viewer.py**: /logs command with filtering and formatting
- **ad_manager.py**: /ad command with ad CRUD operations
- **utils.py**: Shared decorators and helper functions

## Data Flow
Each module handles its own data flow independently:
- Mass messaging: Conversation state → broadcast to users
- User management: Repository queries → formatted responses
- Log viewer: File reads → filtered output
- Ad manager: File I/O for ad persistence
- Utils: Pure functions without shared state

## Error Handling
- Try/except blocks with user-friendly messages
- Admin permission validation at handler entry
- Logger integration for debugging
- Graceful degradation on failures

## Testing
- Unit tests for each module in `tests/unit/handlers/admin/`
- Integration tests for complete workflows
- Maintain >80% coverage
- Validate package imports work correctly

## Implementation Notes
- Maintain existing Telegram API patterns
- Preserve async/await usage throughout
- Keep Spanish text constants and i18n placeholder
- No breaking changes to command interfaces
