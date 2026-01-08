## 2024-05-23 - Optimized Hierarchy Traversal in Cinema 4D
**Learning:** `GetChildren()` in Cinema 4D Python API returns a new list of all children, causing O(N) memory allocation per node visit. Using `GetDown()` and `GetNext()` allows for O(Depth) traversal with constant allocation per step.
**Action:** Replace `GetChildren()` recursive/stack usage with iterative `GetDown()`/`GetNext()` traversal for large hierarchies.
