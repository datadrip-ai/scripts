# Regex Cheatsheet for File Filters

This cheatsheet helps you craft regex patterns for the `advanced_dir.bat` pre/post filters, which use `findstr /r` (case-insensitive). Use these to match file names (e.g., `.*\.exe|.*\.dll`).

## Basic Syntax
| Pattern | Description | Example | Matches |
|---------|-------------|---------|---------|
| `.`     | Any character (except newline) | `te.t` | `text`, `test` |
| `*`     | Zero or more of the previous | `te*st` | `tst`, `test`, `teeeest` |
| `+`     | One or more of the previous | `te+st` | `test`, `teeeest` |
| `?`     | Zero or one of the previous | `te?st` | `tst`, `test` |
| `^`     | Start of string | `^note` | `notepad.exe`, not `subnote.txt` |
| `$`     | End of string | `\.exe$` | `notepad.exe`, not `notepad.exe.bak` |
| `\|`    | OR operator | `\.exe\|\.dll` | `notepad.exe`, `kernel32.dll` |
| `[]`    | Character class | `[tn]est` | `test`, `nest` |
| `[^]`   | Negated class | `[^tn]est` | `rest`, not `test` |
| `\`     | Escape special characters | `\.` | Literal `.` (e.g., `note\.txt`) |

## Common Patterns
| Pattern | Description | Example |
|---------|-------------|---------|
| `.*\.exe` | Any `.exe` file | `notepad.exe`, `regedit.exe` |
| `.*\.(exe\|dll)` | `.exe` or `.dll` files | `notepad.exe`, `kernel32.dll` |
| `^note.*` | Files starting with “note” | `notepad.exe`, `notes.txt` |
| `.*\.jpg$` | `.jpg` files | `photo.jpg`, not `photo.jpg.bak` |
| `[0-9]+.*` | Files starting with numbers | `123file.txt`, `2023.doc` |
| `[^.]*\.txt` | `.txt` files without dots in name | `note.txt`, not `note.v2.txt` |

## Tips for `advanced_dir.bat`
- **Case-Insensitive**: No need for `/c:` prefix; `findstr /i` is used.
- **Escape Characters**: Use `^` before `|`, `.`, `*`, etc., in CMD (e.g., `.*\.exe^|.*\.dll`).
- **Test Patterns**: Try simple patterns first (e.g., `.*\.exe`) before complex ones.
- **Examples**:
  - `.*\.(exe\|dll\|txt)`: Match `.exe`, `.dll`, `.txt`.
  - `^[^.]*\.jpg`: JPEGs without dots in the name.
  - `.*[0-9]+\.mp4`: Videos with numbers in the name.

## Resources
- [Microsoft `findstr` Docs](https://docs.microsoft.com/en-us/windows-server/administration/windows-commands/findstr)
- [Regex101](https://regex101.com/) (test patterns, select PCRE flavor)
- [Regular-Expressions.info](https://www.regular-expressions.info/)

Use this to build precise filters for your reverse engineering tasks (e.g., `.*\.exe^|.*\.dll` for Notepad.exe and its DLLs).