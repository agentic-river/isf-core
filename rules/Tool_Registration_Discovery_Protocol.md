# Tool Registration & Discovery Protocol

## Objective
To ensure that all newly created tool classes and their methods are correctly exposed to the AI agent. This protocol prevents the "hidden tool" problem where logic exists in the codebase but is not registered in the global manifest used by the LLM.

## 1. Core Requirements

Whenever a new tool class (e.g., `BrowserTools`, `CustomDataTools`) is created, you MUST perform the following registration steps:

1.  **Method Decoration:** 
    *   Every method intended for AI use MUST be decorated with `@log_tool_usage`. 
    *   This decorator automatically sets the `_is_ai_tool = True` flag, which the discovery engine looks for.

2.  **State Registration (`backend/server/state.py`):**
    *   **Import:** Add the tool class import at the top of the file.
    *   **Instantiation:** Instantiate the class inside the `ServerState.__init__` method (or ensure it's instantiated in `_lazy_init_tools`).
    *   **Provider Addition:** Add the class instance to the `providers` list inside the `_lazy_init_tools` method. This is the **CRITICAL** step for automatic discovery.

3.  **Dynamic Scripts (Exceptions):**
    *   Scripts in `browser-agents/` are automatically discovered and do not need registration in `state.py`. However, they must follow the `TASK_METADATA` and `run_task` schema.

## 2. Standard Workflow

1.  **Create Tool:** Implement your logic in `backend/core/my_new_tools.py`.
2.  **Decorate:** Use `@log_tool_usage` on public methods.
3.  **Register:**
    ```python
    # backend/server/state.py
    from backend.core.my_new_tools import MyNewTools
    
    class ServerState:
        def __init__(self, settings):
            # ...
            self.my_new_tools = MyNewTools(self.settings)
            
        def _lazy_init_tools(self):
            # ...
            providers = [
                # ... existing tools ...
                self.my_new_tools,
            ]
            self._auto_register_tools(providers)
    ```

## 3. Examples

### 🟢 Good Example
*   **Good:** Creating `FileSystemTools`, decorating `read_file`, and adding `self.fs_tools` to the `providers` list in `state.py`.

### 🔴 Bad Example
*   **Bad:** Implementing `BrowserTools` with decorated methods but forgetting to add `self.browser_tools` to the `providers` list. The AI will never "see" or call these tools.
