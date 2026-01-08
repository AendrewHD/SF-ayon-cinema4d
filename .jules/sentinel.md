## 2024-10-27 - Path Traversal in Extractors
**Vulnerability:** Publish extractors used unsanitized `instance.name` directly in file paths.
**Learning:** Even internal instance names can contain unsafe characters if derived from user input.
**Prevention:** Always use `lib.sanitize_filename` when constructing file paths from `instance.name`.
