# Scenario Handler Implementation Plan

> **For Claude:** Use superpowers:fix-issue to implement this plan.

**Goal:** Create `bot/handlers/scenario_handler.py` with handler for `/scenario` command.

**Architecture:** Follow existing handler pattern from `signal_handler.py` - verify admin access, show loading, execute scenario analysis, respond with Markdown.

**Tech Stack:** Python, Telegram Bot API, SQLAlchemy

---

### Task 1: Create scenario_handler.py

**Files:**
- Create: `bot/handlers/scenario_handler.py`

**Step 1: Create the handler file**

```python
# bot/handlers/scenario_handler.py

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.core.config import settings


async def scenario_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Analiza y muestra escenarios de mercado."""
    chat_id = update.effective_chat.id

    if chat_id not in settings.admin_chat_ids:
        await update.message.reply_text("⛔ Acceso denegado.")
        return

    msg = await update.message.reply_text("Analizando escenarios de mercado... ⏳")

    try:
        container = context.bot_data["container"]
        text = await container.get_scenario_analysis.execute()

        await msg.delete()
        await update.message.reply_text(text, parse_mode="Markdown")

    except Exception as e:
        try:
            await msg.edit_text(f"⚠️ Error en el análisis:\n{str(e)}")
        except Exception:
            await msg.edit_text("⚠️ Error en el análisis.")


scenario_handlers_list = [
    CommandHandler("scenario", scenario_command),
]
```

**Step 2: Verify file created**

Run: `ls -la bot/handlers/scenario_handler.py`

---

### Task 2: Add handler to main.py

**Files:**
- Modify: `bot/main.py`

**Step 1: Import the handler**

Add at imports section:
```python
from bot.handlers.scenario_handler import scenario_handlers_list
```

**Step 2: Add to application**

Find where handlers are added and add:
```python
application.add_handlers(scenario_handlers_list)
```

---

### Task 3: Run tests

**Step 1: Run lint**

Run: `ruff check . --fix`

**Step 2: Run format**

Run: `ruff format .`

**Step 3: Run tests**

Run: `pytest tests/unit/ -v`

---

### Task 4: Commit and merge

**Step 1: Commit**

```bash
git add .
git commit -m "feat: add scenario command handler"
```

**Step 2: Merge to develop**

```bash
git checkout develop
git merge feat/scenario-handler
git push origin develop
```

**Step 3: Close issue**

```bash
gh issue close 49 --comment "Implemented in PR #XX"
```

**Step 4: Delete branch**

```bash
git branch -d feat/scenario-handler
git push origin --delete feat/scenario-handler
```
