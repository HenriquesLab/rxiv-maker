# Comment Security in rxiv-maker

## Overview

rxiv-maker implements comprehensive comment filtering to ensure that commented content is **never processed as active content**. This is critical for security, as users may believe they have "commented out" dangerous code when it could still be executed.

## Comment Types and Filtering

### HTML/Markdown Comments (`<!-- -->`)

HTML comments are **completely removed** from the document before any processing occurs. This prevents:

- Tables inside comments from being rendered
- Citations inside comments from being processed  
- Executable blocks inside comments from running
- Any other markdown elements from being processed

**Example:**
```markdown
Regular content.

<!--
| Dangerous | Table | Should Not Appear |
|-----------|-------|-------------------|
| Row 1     | @malicious_citation | Data |

{{py:exec
import os
os.system("rm -rf /")
}}
-->

More content.
```

**Result:** Only "Regular content." and "More content." will appear in the output. Everything inside the `<!-- -->` comment is completely removed.

### Python Comments (`#`) in Executable Blocks

Python comments within `{{py:exec}}` blocks are filtered out before code execution. This applies to:

- Full-line comments starting with `#`
- Inline comments (everything after `#` on a line)
- Comments are intelligently parsed to avoid filtering `#` inside strings

**Example:**
```markdown
{{py:exec
# This comment will be filtered out
import math
x = 5  # This inline comment is also filtered
# dangerous_function()  # This won't execute
result = math.sqrt(x)
}}
```

**Result:** Only the actual Python code executes. All comments are removed before execution.

### LaTeX Comments (`%`) in TeX Blocks

LaTeX comments within `{{tex:...}}` blocks are filtered out before processing. This includes:

- Full-line comments starting with `%`
- Inline comments (everything after `%` on a line)  
- Properly handles escaped `\%` (which is not a comment)

**Example:**
```markdown
{{tex:
% This comment will be filtered
\\textbf{Bold Text} % Inline comment filtered
\\text{Price: 5\\% tax} % The \\% is preserved, this comment is filtered
}}
```

**Result:** Only `\\textbf{Bold Text}` and `\\text{Price: 5\\% tax}` are processed.

## Security Benefits

### Prevents Accidental Code Execution

Users often comment out code believing it won't execute:

```markdown
<!-- I'm commenting this out so it won't run
{{py:exec
import subprocess
subprocess.run(["rm", "-rf", "/"], check=True)
}}
-->
```

**Before the fix:** This dangerous code would still execute!
**After the fix:** The entire HTML comment is removed before processing.

### Prevents Data Leakage

Commented tables and citations won't accidentally appear in PDFs:

```markdown
<!-- Draft table - don't include yet
| Confidential | Internal Data | Classification |
|--------------|---------------|----------------|
| Project X    | @secret_doc   | Top Secret     |
-->
```

**Result:** No table appears in the output, no citations are processed.

### Prevents LaTeX Injection

Commented LaTeX commands won't be processed:

```markdown
{{tex:
% \\input{/etc/passwd}  % Dangerous file inclusion
\\textbf{Safe content}
}}
```

**Result:** Only the safe `\\textbf{Safe content}` is processed.

## Best Practices

### For Users

1. **Use HTML comments for large blocks:** When commenting out entire sections, use `<!-- -->`.

2. **Use appropriate comment syntax within blocks:**
   - Use `#` for Python code within `{{py:exec}}` blocks
   - Use `%` for LaTeX within `{{tex:...}}` blocks

3. **Don't rely on comments for security:** While the system filters comments, write secure code in the first place.

4. **Test your manuscripts:** Use `rxiv pdf` to verify that commented content doesn't appear.

### For Developers

1. **Comment filtering is automatic:** No manual intervention required.

2. **Comments are filtered early:** HTML comments are removed before any other processing.

3. **Line numbers are preserved:** Python comment filtering preserves line numbers for accurate error reporting.

4. **Performance impact is minimal:** Comment filtering adds negligible overhead.

## Technical Implementation

### Processing Order

1. **HTML Comment Removal** (first priority)
   - Completely removes `<!-- -->` blocks and their content
   - Happens before table processing, citation processing, etc.
   - Prevents any commented markdown from being processed

2. **Python Comment Filtering**
   - Applied within `{{py:exec}}` blocks before code execution
   - Intelligently parses strings to avoid filtering `#` inside quotes
   - Preserves line numbers for error reporting

3. **LaTeX Comment Filtering**  
   - Applied within `{{tex:...}}` blocks before LaTeX processing
   - Handles escaped `\%` correctly (preserves as literal %)
   - Removes both full-line and inline comments

### Security Architecture

```
Markdown Input
     ↓
HTML Comment Removal (SECURITY BARRIER)
     ↓
Standard Processing (tables, citations, etc.)
     ↓
Python Block Processing
     ↓
Python Comment Filtering (SECURITY BARRIER)
     ↓
LaTeX Block Processing  
     ↓
LaTeX Comment Filtering (SECURITY BARRIER)
     ↓
Final Output
```

## Limitations and Edge Cases

### Multiline Strings in Python

Python comment filtering works line-by-line. Content inside multiline strings (`'''` or `"""`) may have `#` symbols that should be preserved, but the current implementation may filter some of these. This is acceptable for the security goals.

### Nested HTML Comments

Perfect nested comment parsing is complex. The system uses a simple first-match approach:
- `<!-- outer <!-- inner --> remaining -->` will remove from first `<!--` to first `-->`
- This is acceptable for security purposes

### Malformed Comments

Malformed comments (like unclosed `<!--`) are left as-is rather than breaking the document. This graceful degradation prioritizes document stability.

## Migration Notes

### Existing Manuscripts

Most existing manuscripts will work unchanged. However:

1. **Tables in HTML comments will disappear** - this is the intended fix
2. **Citations in HTML comments will disappear** - this is the intended fix  
3. **Executable blocks in HTML comments won't execute** - this is the intended security fix

### Testing Manuscripts

After upgrading, test your manuscripts:

```bash
rxiv pdf your_manuscript/
```

Check the output PDF to ensure:
- No unwanted tables appear (good!)
- No unwanted citations appear (good!)
- Regular content still processes correctly
- Intentionally commented content is properly hidden

## FAQ

**Q: Will this break my existing manuscripts?**
A: Most manuscripts will work unchanged. The main change is that content inside HTML comments will no longer appear in PDFs, which is the intended security fix.

**Q: Can I still use comments for documentation?**
A: Yes! Use HTML comments (`<!-- -->`) for manuscript documentation that shouldn't appear in the PDF.

**Q: What if I need a literal `#` or `%` in my code?**
A: 
- For Python: Put `#` inside strings: `message = "Use #hashtags"`
- For LaTeX: Escape `%` with backslash: `\%` becomes a literal percent sign

**Q: Does this affect performance?**
A: Comment filtering adds minimal overhead (typically <1% of total processing time).

**Q: Can I disable comment filtering?**
A: No, comment filtering is a security feature and cannot be disabled. This ensures all manuscripts are processed securely.

## Reporting Issues

If you discover comment-related security issues or unexpected behavior:

1. Check that you're using the latest version of rxiv-maker
2. Create a minimal test case demonstrating the issue
3. Report the issue at: https://github.com/HenriquesLab/rxiv-maker/issues

For security-sensitive issues, consider reporting privately to the maintainers.