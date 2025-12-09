# Citation Styles and Inline DOI Resolution

> 💡 **New to citations in rxiv-maker?** Start with the [10-minute tutorial](https://rxiv-maker.henriqueslab.org/getting-started/citations-tutorial/) on the website for hands-on practice.
>
> This document is a comprehensive technical reference for developers and power users.

This document describes two powerful citation management features in Rxiv-Maker:
1. **Multiple Citation Styles** - Choose between numbered and author-date citations
2. **Inline DOI Resolution** - Automatically convert DOIs into proper citations


---

## Citation Styles

### Overview

Rxiv-Maker supports two citation styles:
- **Numbered citations** (default): `[1, 2, 3]`
- **Author-date citations**: `(Smith, 2024; Jones, 2023)`

### Configuration

Add the `citation_style` option to your `00_CONFIG.yml`:

```yaml
# Citation style: "numbered" or "author-date"
citation_style: "author-date"
```

### Examples

**Numbered Citations (default):**
```markdown
Recent studies [@smith2024; @jones2023] show significant results.
```

**Output:** Recent studies [1, 2] show significant results.

---

**Author-Date Citations:**
```markdown
Recent studies [@smith2024; @jones2023] show significant results.
```

**Output:** Recent studies (Smith, 2024; Jones, 2023) show significant results.

### How It Works

Rxiv-Maker uses the `natbib` LaTeX package with conditional loading:
- **Numbered mode**: `\RequirePackage[...,numbers,...]`
- **Author-date mode**: `\RequirePackage[...,authoryear,...]`

The template processor reads your config and sets the appropriate mode before LaTeX compilation.

---

## Inline DOI Resolution

### Overview

Instead of manually creating BibTeX entries for every reference, you can paste DOIs directly in your manuscript. Rxiv-Maker will:
1. **Detect** DOIs and DOI URLs in your markdown files
2. **Fetch** metadata from CrossRef/DataCite APIs
3. **Generate** BibTeX entries automatically
4. **Update** your markdown files to replace DOIs with proper citation keys

### Configuration

Enable inline DOI resolution in your `00_CONFIG.yml`:

```yaml
# Auto-resolve inline DOIs to citations
enable_inline_doi_resolution: true
```

**⚠️ Important:** This feature modifies your source markdown files. Make sure your work is committed to git before running.

### Supported DOI Formats

Rxiv-Maker recognizes several DOI formats:

1. **Bare DOIs:**
   ```markdown
   According to 10.1038/nature12373, this approach works well.
   ```

2. **DOI URLs:**
   ```markdown
   See https://doi.org/10.1038/nature12373 for details.
   ```

3. **Multiple DOIs:**
   ```markdown
   Multiple studies (10.1038/nature12373, 10.1126/science.1234567)
   and https://doi.org/10.1371/journal.pone.0123456 confirm this.
   ```

### Example Workflow

**Before DOI Resolution:**

`01_ARTICLE.md`:
```markdown
# Introduction

Recent advances in microscopy 10.1038/nmeth.2019 have enabled new
imaging approaches. This builds on prior work (https://doi.org/10.1126/science.1234567)
and extends it significantly.
```

`03_REFERENCES.bib`:
```bibtex
% Empty or has other references
```

**Run PDF generation:**
```bash
rxiv pdf
```

**After DOI Resolution:**

`01_ARTICLE.md` (automatically updated):
```markdown
# Introduction

Recent advances in microscopy @wang2013 have enabled new
imaging approaches. This builds on prior work (@smith2012)
and extends it significantly.
```

`03_REFERENCES.bib` (automatically updated):
```bibtex
@article{wang2013,
  title = {Advances in Microscopy},
  author = {Wang, John and others},
  journal = {Nature Methods},
  year = {2013},
  volume = {10},
  pages = {123-456},
  doi = {10.1038/nmeth.2019}
}

@article{smith2012,
  title = {Imaging Approaches},
  author = {Smith, Jane and others},
  journal = {Science},
  year = {2012},
  volume = {337},
  pages = {789-801},
  doi = {10.1126/science.1234567}
}
```

### Citation Key Generation

Citation keys are automatically generated using the format: `{firstauthor}{year}`

Examples:
- `10.1038/nature12373` → `@smith2024`
- `10.1126/science.1234567` → `@jones2023`
- `10.1371/journal.pone.0123456` → `@brown2022`

If a key already exists, a suffix is added (e.g., `smith2024_2`).

### Build Process Integration

DOI resolution happens automatically during PDF generation:

```
1. Setup output directory
2. Generate figures
3. Execute manuscript code blocks
4. ✨ Resolve inline DOIs (if enabled) ✨
5. Validate manuscript
6. Generate LaTeX
7. Compile PDF
```

### Logging and Feedback

Rxiv-Maker provides detailed feedback during DOI resolution:

```bash
$ rxiv pdf
...
[STEP] Resolving inline DOIs in markdown files...
[INFO] Found 3 DOI(s), resolved 3, failed 0
[INFO] Updated 1 markdown file(s) with resolved citations
...
```

### Error Handling

DOI resolution failures are non-fatal:
- ✅ Warnings are logged for failed DOIs
- ✅ Build continues normally
- ✅ Failed DOIs remain as-is in the text

Common failure reasons:
- **Invalid DOI format**: Not recognized as a valid DOI
- **API timeout**: CrossRef/DataCite API is slow or unavailable
- **DOI not found**: DOI doesn't exist in the registries

### Caching

Fetched DOI metadata is cached in `.rxiv_cache/doi/` to:
- Avoid redundant API calls
- Speed up subsequent builds
- Work offline with previously-fetched DOIs

### Best Practices

1. **Commit before enabling**: Since markdown files are modified, commit your work first
2. **Review changes**: Check the git diff after the first run to verify citations
3. **Manual cleanup**: You may want to rename auto-generated keys to be more memorable
4. **Test with a few DOIs first**: Start with 1-2 DOIs to verify behavior

### Limitations

1. **Not detected in existing citations**: DOIs inside `@citationkey` or `{doi = {...}}` are ignored
2. **Requires internet**: First resolution needs API access (but results are cached)
3. **Modifies source files**: Markdown files are updated in-place
4. **No undo**: Use git to revert changes if needed

---

## Combining Both Features

You can use both features together:

```yaml
citation_style: "author-date"
enable_inline_doi_resolution: true
```

This gives you:
- **Convenient input**: Just paste DOIs in your markdown
- **Flexible output**: Choose your preferred citation style
- **Automatic management**: Bibliography entries are created and formatted automatically

**Example:**

Input markdown:
```markdown
As shown in 10.1038/nature12373, the approach is valid.
```

After DOI resolution:
```markdown
As shown in @smith2024, the approach is valid.
```

With author-date style:
```
As shown in Smith (2024), the approach is valid.
```

With numbered style:
```
As shown in [1], the approach is valid.
```

---

## Troubleshooting

### DOI Resolution Not Working

**Problem**: DOIs are not being resolved.

**Solutions**:
1. Check config: `enable_inline_doi_resolution: true` must be set
2. Check DOI format: Must be valid format `10.xxxx/yyyy`
3. Check internet connection: First resolution requires API access
4. Check logs: Look for specific error messages

### Citations Not Appearing

**Problem**: DOIs are resolved but citations don't appear in PDF.

**Solutions**:
1. Check bibliography file: Verify entries were added to `03_REFERENCES.bib`
2. Check markdown: Verify DOIs were replaced with `@citationkey`
3. Run validation: `rxiv validate` to check for issues

### Wrong Citation Style

**Problem**: Citations appear in wrong format.

**Solutions**:
1. Check config: Verify `citation_style` is set to desired value
2. Rebuild: Delete output directory and run `rxiv pdf` again
3. Check LaTeX logs: Look for natbib errors in output

### Duplicate Citations

**Problem**: Same reference appears multiple times with different keys.

**Solution**:
- Manual cleanup required: Edit `03_REFERENCES.bib` and markdown to consolidate duplicates

---

## Advanced Usage

### Selective DOI Resolution

To resolve DOIs in only some files:

1. Disable global resolution: `enable_inline_doi_resolution: false`
2. Use Python API directly:

```python
from rxiv_maker.utils.doi_resolver import DOIResolver

resolver = DOIResolver("MANUSCRIPT")
results = resolver.process_markdown_file(
    Path("MANUSCRIPT/01_ARTICLE.md"),
    update_file=True
)
print(f"Resolved {results['dois_resolved']} DOIs")
```

### Custom Citation Keys

After automatic resolution, you can manually rename citation keys:

1. Edit `03_REFERENCES.bib`: Change the entry key
2. Edit markdown files: Update `@oldkey` to `@newkey`
3. Rebuild: Run `rxiv pdf`

---

## Technical Details

### DOI Detection Regex

```regex
(?:https?://)?(?:dx\.)?doi\.org/(10\.\d{4,9}/[-._;()/:A-Z0-9]+)|
(?<!\w)(10\.\d{4,9}/[-._;()/:A-Z0-9]+)(?![}@])
```

### Metadata Sources

1. **CrossRef** (primary): Most journal articles
2. **DataCite** (fallback): Research data, preprints
3. **Cache** (fastest): Previously-fetched DOIs

### File Modifications

DOI resolution modifies only:
- `01_ARTICLE.md`
- `02_SUPPLEMENTARY_INFO.md` (if exists)
- `03_REFERENCES.bib`

All other files remain unchanged.

---

## See Also

- [BibTeX Management](bibliography.md) - Managing bibliography files
- [Citation Syntax](citation-syntax.md) - Full citation markdown syntax
- [Configuration Reference](configuration.md) - All config options
