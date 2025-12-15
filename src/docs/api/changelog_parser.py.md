<!-- markdownlint-disable -->

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/rxiv_maker/utils/changelog_parser.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `changelog_parser.py`
Parse and extract information from CHANGELOG.md. 

This module provides functionality to fetch, parse, and format changelog entries for display in update notifications and CLI commands. 

**Global Variables**
---------------
- **BREAKING_PATTERNS**
- **DEFAULT_CHANGELOG_URL**

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/rxiv_maker/utils/changelog_parser.py#L48"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `fetch_changelog`

```python
fetch_changelog(
    url: str = 'https://raw.githubusercontent.com/HenriquesLab/rxiv-maker/main/CHANGELOG.md',
    timeout: int = 5
) → str
```

Fetch CHANGELOG.md content from URL. 



**Args:**
 
 - <b>`url`</b>:  URL to fetch changelog from 
 - <b>`timeout`</b>:  Request timeout in seconds 



**Returns:**
 Raw changelog content as string 



**Raises:**
 
 - <b>`URLError`</b>:  If network request fails 
 - <b>`HTTPError`</b>:  If HTTP request returns error status 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/rxiv_maker/utils/changelog_parser.py#L67"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `parse_version_entry`

```python
parse_version_entry(content: str, version: str) → Optional[ChangelogEntry]
```

Parse a specific version's changelog entry. 



**Args:**
 
 - <b>`content`</b>:  Full CHANGELOG.md content 
 - <b>`version`</b>:  Version to extract (e.g., "1.13.0" or "v1.13.0") 



**Returns:**
 ChangelogEntry if found, None otherwise 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/rxiv_maker/utils/changelog_parser.py#L113"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `parse_sections`

```python
parse_sections(content: str) → Dict[str, List[str]]
```

Parse changelog sections (Added, Changed, Fixed, etc.). 



**Args:**
 
 - <b>`content`</b>:  Changelog entry content 



**Returns:**
 Dictionary mapping section names to lists of changes 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/rxiv_maker/utils/changelog_parser.py#L153"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `extract_highlights`

```python
extract_highlights(
    entry: ChangelogEntry,
    limit: int = 3
) → List[Tuple[str, str]]
```

Extract the most important highlights from a changelog entry. 

Prioritizes: Added > Changed > Fixed > Others 



**Args:**
 
 - <b>`entry`</b>:  Changelog entry to extract from 
 - <b>`limit`</b>:  Maximum number of highlights to return 



**Returns:**
 List of (emoji, description) tuples 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/rxiv_maker/utils/changelog_parser.py#L203"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `detect_breaking_changes`

```python
detect_breaking_changes(entry: ChangelogEntry) → List[str]
```

Detect breaking changes in a changelog entry. 



**Args:**
 
 - <b>`entry`</b>:  Changelog entry to check 



**Returns:**
 List of breaking change descriptions 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/rxiv_maker/utils/changelog_parser.py#L234"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_versions_between`

```python
get_versions_between(content: str, current: str, latest: str) → List[str]
```

Get all versions between current and latest (inclusive of latest). 



**Args:**
 
 - <b>`content`</b>:  Full CHANGELOG.md content 
 - <b>`current`</b>:  Current version (e.g., "1.10.0") 
 - <b>`latest`</b>:  Latest version (e.g., "1.13.0") 



**Returns:**
 List of version strings in chronological order (oldest to newest) 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/rxiv_maker/utils/changelog_parser.py#L270"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `format_summary`

```python
format_summary(
    entries: List[ChangelogEntry],
    show_breaking: bool = True,
    highlights_per_version: int = 3
) → str
```

Format changelog entries for terminal display with rich markup. 



**Args:**
 
 - <b>`entries`</b>:  List of changelog entries to format 
 - <b>`show_breaking`</b>:  Whether to show breaking changes prominently 
 - <b>`highlights_per_version`</b>:  Number of highlights per version 



**Returns:**
 Formatted string for terminal display with rich markup 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/rxiv_maker/utils/changelog_parser.py#L323"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `fetch_and_format_changelog`

```python
fetch_and_format_changelog(
    current_version: str,
    latest_version: str,
    changelog_url: str = 'https://raw.githubusercontent.com/HenriquesLab/rxiv-maker/main/CHANGELOG.md',
    highlights_per_version: int = 3
) → Tuple[Optional[str], Optional[str]]
```

Fetch changelog and format summary for version range. 

This is the main convenience function that combines all steps. 



**Args:**
 
 - <b>`current_version`</b>:  Current installed version 
 - <b>`latest_version`</b>:  Latest available version 
 - <b>`changelog_url`</b>:  URL to fetch changelog from 
 - <b>`highlights_per_version`</b>:  Number of highlights per version 



**Returns:**
 Tuple of (formatted_summary, error_message) If successful, returns (summary, None) If failed, returns (None, error_message) 


---

## <kbd>class</kbd> `ChangelogEntry`
Represents a complete changelog entry for a specific version. 





---

## <kbd>class</kbd> `ChangelogSection`
Represents a section in a changelog entry (Added, Changed, Fixed, etc.). 





