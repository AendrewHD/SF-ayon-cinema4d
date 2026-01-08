## 2024-03-24 - Tooltips for Plugin Attributes
**Learning:** `ayon_core.lib.NumberDef` and `EnumDef` support a `tooltip` parameter that surfaces helpful context directly in the plugin UI.
**Action:** When defining plugin attributes in `get_instance_attr_defs`, always include a `tooltip` argument to explain the purpose of the setting, especially for units (e.g., FPS) or format options.