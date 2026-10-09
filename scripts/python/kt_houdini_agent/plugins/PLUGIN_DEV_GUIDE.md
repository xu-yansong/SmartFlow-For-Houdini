# Houdini Agent Plugin Development Guide

## Quick Start

1. Create a `.py` file in this `plugins/` directory (files starting with `_` are ignored)
2. Define a `PLUGIN_INFO` dict and a `register(ctx)` function
3. Restart Houdini Agent or click "Reload All" in Plugin Manager

## Architecture Overview

The plugin system integrates with the unified ToolRegistry which manages all tools:

- Core Tools (38+): Built-in Houdini operations
- Skills (9+): Pre-optimized Python analysis scripts
- Plugin Tools: Tools registered by plugins via ctx.register_tool()
- User Skills: User-defined skills in a custom directory

Plugin Manager UI has 3 tabs: Plugins, Tools, Skills.

## Plugin File Structure

```python
PLUGIN_INFO = {
    "name": "My Plugin",
    "version": "1.0.0",
    "author": "Your Name",
    "description": "What it does",
    "settings": [
        {"key": "my_option", "type": "bool", "label": "Enable Feature", "default": True},
    ],
}

def register(ctx):
    ctx.log("My Plugin loaded!")
```

## PluginContext API

### Event Hooks

`ctx.on(event_name, callback, priority=0)`

Events: on_before_request, on_after_response, on_before_tool, on_after_tool, on_content_chunk, on_session_start, on_session_end.

Always include `**kwargs` in callbacks for forward compatibility.

### Custom Tools

```python
ctx.register_tool(name="my_tool", description="desc", schema={...}, handler=fn)
```

Tools auto-register to ToolRegistry, available in Agent/Ask/Plan modes.

### UI Buttons

`ctx.register_button(icon="icon", tooltip="tip", callback=fn)`

### Settings

`ctx.get_setting(key, default=None)` and `ctx.set_setting(key, value)`

### Logging

`ctx.log(msg)` - Prefixed with [Plugin:Name]

## Decorator API

```python
from houdini_agent.utils.hooks import hook, tool, ui_button

@hook("on_after_tool")
def my_hook(tool_name, args, result, **kwargs):
    pass

@tool(name="my_tool", description="desc")
def handler(args):
    return {"success": True}
```

## User Skills

Set path in config/houdini_ai.ini under [skills] user_skill_dir, or use Plugin Manager Skills tab.

## Notes

- Files starting with _ are not auto-loaded
- Avoid blocking operations
- Use ctx.log() for logging
- Tool handlers return {"success": True/False, "result": "..."}
- See _example_plugin.py for complete example
