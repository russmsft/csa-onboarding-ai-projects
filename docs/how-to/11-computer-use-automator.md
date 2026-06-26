# 11 — Computer-Use Automator: Let GPT-5.4 Drive the Browser

GPT-5.4's computer-use capability lets you point a model at a screenshot and say "fill in this form." This guide builds the agent loop: screenshot → model decides action → Playwright executes → repeat — with a safety confirmation step before every click.

---

## What You're Building

A Python agent loop using Playwright for browser automation. The agent takes a screenshot, sends it to GPT-5.4 via the Responses API (computer-use tool), receives an action (click, type, scroll, key), asks you to confirm before executing, then repeats. Credentials are stored in Azure Key Vault — never in code. This is genuinely powerful and genuinely dangerous without the confirmation step.

---

## Prerequisites

- Microsoft Foundry project with **GPT-5.4** deployed (computer-use requires GPT-5.4 or higher)
- Azure Key Vault for credential storage
- Python 3.11+
- `playwright`, `azure-ai-projects`, `azure-keyvault-secrets`, `azure-identity`, `Pillow`

```bash
pip install azure-ai-projects azure-identity azure-keyvault-secrets \
  playwright Pillow python-dotenv

# Install Playwright browsers
playwright install chromium
```

> **Safety warning:** Computer-use agents can take irreversible actions — form submissions, file deletions, purchases. Never run without the confirmation step in production. Add a dry-run mode for testing.

---

## Architecture

![Computer-Use Automator architecture: Python script (credentials from Key Vault) → Playwright screenshot → Responses API GPT-5.4 computer_use → human approval → Playwright executes action in a loop](images/11-computer-use-automator-architecture.png)

---

## Step-by-Step Build

### Step 1 — Store credentials in Key Vault

```bash
KV_NAME="computer-use-kv"

az keyvault create \
  --name $KV_NAME \
  --resource-group $RG \
  --location eastus2 \
  --enable-rbac-authorization true

# Grant yourself Secret Officer role
az role assignment create \
  --assignee $(az ad signed-in-user show --query id -o tsv) \
  --role "Key Vault Secrets Officer" \
  --scope $(az keyvault show --name $KV_NAME --query id -o tsv)

# Store credentials (never hardcode these)
az keyvault secret set --vault-name $KV_NAME --name "target-username" --value "your-username"
az keyvault secret set --vault-name $KV_NAME --name "target-password" --value "your-password"
```

### Step 2 — Key Vault helper

```python
# keyvault.py
import os
from functools import lru_cache
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

@lru_cache(maxsize=None)
def get_secret(secret_name: str) -> str:
    """Fetch a secret from Key Vault. Cached after first fetch."""
    kv_url = f"https://{os.environ['KEY_VAULT_NAME']}.vault.azure.net"
    client = SecretClient(vault_url=kv_url, credential=DefaultAzureCredential())
    return client.get_secret(secret_name).value
```

### Step 3 — Playwright screenshot helper

```python
# browser.py
import asyncio
import base64
import io
from PIL import Image
from playwright.async_api import async_playwright, Page, Browser

_browser: Browser | None = None
_page: Page | None = None


async def init_browser(headless: bool = False) -> Page:
    """Launch Chromium and return a page. headless=False lets you watch."""
    global _browser, _page
    pw = await async_playwright().start()
    _browser = await pw.chromium.launch(
        headless=headless,
        args=["--window-size=1280,800"]
    )
    context = await _browser.new_context(
        viewport={"width": 1280, "height": 800}
    )
    _page = await context.new_page()
    return _page


async def take_screenshot(page: Page) -> tuple[bytes, str]:
    """Take screenshot, return (PNG bytes, base64 string)."""
    png_bytes = await page.screenshot(type="png")
    b64 = base64.b64encode(png_bytes).decode()
    return png_bytes, b64


async def execute_action(page: Page, action: dict) -> str:
    """Execute a computer-use action on the Playwright page."""
    action_type = action.get("type")

    if action_type == "click":
        x, y = action["coordinate"]
        await page.mouse.click(x, y)
        return f"Clicked at ({x}, {y})"

    elif action_type == "type":
        await page.keyboard.type(action["text"], delay=50)
        return f"Typed: {action['text'][:50]}..."

    elif action_type == "key":
        keys = action["key"].split("+")
        if len(keys) > 1:
            await page.keyboard.press("+".join(keys))
        else:
            await page.keyboard.press(keys[0])
        return f"Pressed key: {action['key']}"

    elif action_type == "scroll":
        x, y = action["coordinate"]
        direction = action.get("direction", "down")
        delta = 300 if direction == "down" else -300
        await page.mouse.move(x, y)
        await page.mouse.wheel(0, delta)
        return f"Scrolled {direction} at ({x}, {y})"

    elif action_type == "screenshot":
        return "Screenshot taken (no action)"

    else:
        return f"Unknown action type: {action_type}"
```

### Step 4 — The agent loop

```python
# agent_loop.py
import os
import json
import asyncio
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from browser import init_browser, take_screenshot, execute_action

load_dotenv()

PROJECT_ENDPOINT = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
ai_client = AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=DefaultAzureCredential())
openai = ai_client.get_openai_client()


async def run_computer_use_agent(
    task: str,
    start_url: str,
    max_steps: int = 20,
    require_confirmation: bool = True
) -> dict:
    """
    Main agent loop: screenshot → GPT-5.4 → action → confirm → execute → repeat.
    """
    page = await init_browser(headless=False)  # headless=False so you can watch
    await page.goto(start_url)
    await page.wait_for_load_state("networkidle")

    messages = [{"role": "user", "content": task}]
    step = 0
    actions_taken = []

    print(f"\nTask: {task}")
    print(f"Starting at: {start_url}")
    print("-" * 60)

    while step < max_steps:
        step += 1
        print(f"\nStep {step}/{max_steps}")

        # Take current screenshot
        _, screenshot_b64 = await take_screenshot(page)

        # Add screenshot to messages
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "input_image",
                    "image_url": f"data:image/png;base64,{screenshot_b64}"
                }
            ]
        })

        # Call GPT-5.4 with computer_use_preview tool
        response = openai.responses.create(
            model="gpt-5.4",
            input=messages,
            tools=[{"type": "computer_use_preview",
                    "display_width_px": 1280,
                    "display_height_px": 800,
                    "environment": "browser"}],
            truncation="auto"
        )

        # Parse the response
        output = response.output
        text_output = ""
        action = None

        for item in output:
            if item.type == "text":
                text_output = item.text
                print(f"Agent reasoning: {text_output[:200]}")
            elif item.type == "computer_use":
                action = item.action

        # Check if agent signals completion
        if not action or "task_complete" in text_output.lower():
            print(f"\nAgent complete: {text_output}")
            break

        # Format action for display
        action_dict = action.model_dump() if hasattr(action, "model_dump") else action
        print(f"Proposed action: {json.dumps(action_dict, indent=2)}")

        # Confirmation step — never skip this in production
        if require_confirmation:
            response_str = input("\nExecute this action? [y/n/abort] ").strip().lower()
            if response_str == "abort":
                print("Aborted by user.")
                break
            elif response_str != "y":
                print("Skipping action.")
                # Add rejection to conversation
                messages.append({
                    "role": "user",
                    "content": "That action was rejected. Try a different approach."
                })
                continue

        # Execute action
        result = await execute_action(page, action_dict)
        print(f"Executed: {result}")
        actions_taken.append({"step": step, "action": action_dict, "result": result})

        # Wait for page to settle
        await asyncio.sleep(1)
        try:
            await page.wait_for_load_state("networkidle", timeout=3000)
        except Exception:
            pass  # Page might not have navigated

        # Add action result to conversation
        messages.append({
            "role": "assistant",
            "content": output
        })
        messages.append({
            "role": "tool",
            "content": [{"type": "tool_result",
                         "tool_use_id": getattr(item, "id", ""),
                         "content": result}]
        })

    return {
        "steps_taken": step,
        "actions": actions_taken,
        "final_text": text_output
    }
```

### Step 5 — Example: automated form fill

```python
# main.py
import asyncio
from keyvault import get_secret
from agent_loop import run_computer_use_agent

async def main():
    # Example: fill a standard web form
    # Credentials come from Key Vault — not hardcoded
    username = get_secret("target-username")

    task = (
        f"Log into the portal using username '{username}'. "
        "The password is in the password field. "
        "After login, navigate to Settings → Profile and update "
        "the phone number to '555-0123'. Click Save. "
        "Confirm the change was saved successfully."
    )

    result = await run_computer_use_agent(
        task=task,
        start_url="https://your-internal-portal.example.com",
        max_steps=15,
        require_confirmation=True  # Never set to False without careful review
    )

    print(f"\nCompleted in {result['steps_taken']} steps")
    print(f"Actions taken: {len(result['actions'])}")

if __name__ == "__main__":
    asyncio.run(main())
```

```bash
python main.py
```

---

## Test It

Start with a safe public site to validate the loop works before touching anything real:

```python
# Safe test: navigate Wikipedia
result = await run_computer_use_agent(
    task="Go to Wikipedia and search for 'Azure AI Foundry'. Tell me the first paragraph of the article.",
    start_url="https://www.wikipedia.org",
    max_steps=5,
    require_confirmation=True
)
```

**Verify the confirmation step works:** The agent should pause and ask `[y/n/abort]` before every action. If it doesn't, check that `require_confirmation=True` is set.

---

## Common Mistakes

- **Running headless in production.** Always run `headless=False` during development so you can see what the agent is doing. Switch to headless only after extensive testing.
- **Credentials in the task string.** Never put actual passwords in the task description — it ends up in model context and logs. Use Key Vault to fetch them and inject only at execution time.
- **Agent loops infinitely.** Always set a `max_steps` limit. 20 is a reasonable default. Add a hard timeout as a second safety net.
- **Screenshot quality.** If the model misidentifies elements, increase the viewport (1920x1080) and ensure DPI scaling is disabled in headless mode.

---

## Extend It

1. **Audit trail:** Log every screenshot and action to Azure Blob Storage. This gives you a full audit trail for compliance and debugging.
2. **Parallel browser sessions:** Run multiple agent instances in parallel for batch processing (e.g., update 100 records across a legacy system overnight).
3. **Error recovery:** Detect when the agent is stuck (same screenshot for 3 consecutive steps) and inject a recovery message: "You appear to be stuck. Try navigating to the home page and starting over."

---

## Resources

- [GPT-5.4 computer-use (Responses API)](https://learn.microsoft.com/azure/ai-foundry/openai/concepts/models)
- [Playwright Python docs](https://playwright.dev/python/docs/intro)
- [Azure Key Vault secrets](https://learn.microsoft.com/azure/key-vault/secrets/quick-create-python)
- [Responses API reference](https://learn.microsoft.com/azure/ai-foundry/openai/how-to/responses)
