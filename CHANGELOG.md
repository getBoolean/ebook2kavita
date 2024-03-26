## 0.1.0

- **Breaking (Feat):** eBooks are now classified using specific subfolders and filenames to split them into Kavita series.
  - Existing target library created with a previous version will need to be wiped, otherwise there will be orphaned files and series.
  - Classifications:
    - Light Novel
    - Web Novel
    - Short Story/Stories
    - Side Story/Stories
    - Spin-off Series
    - Fan Translation
    - Official Translation
- **Breaking:** CLI arguments have been changed to be named arguments instead of positional arguments.
- **Feat:** Added conversion for non-EPUB eBook files.
- **Feat:** Use modified date to determine if eBooks need to be added.
- **Fix:** eBooks are now added recursively instead of using a hardcoded file structure.
- **Fix:** Add additional input argument validation.
- **Fix:** Numerous edge cases, incluging "Classroom of the Elite" `Year #` is now added as a series part number.

## 0.0.1

- Initial release
