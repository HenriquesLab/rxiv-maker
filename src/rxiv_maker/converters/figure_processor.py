"""Figure processing for markdown to LaTeX conversion.

This module handles conversion of markdown figures to LaTeX figure environments,
including figure attributes, captions, and references.
"""

import os
import re
from typing import Any, Dict, Optional, Tuple

from .types import (
    FigureAttributes,
    FigureId,
    FigurePath,
    LatexContent,
    MarkdownContent,
)


def convert_figures_to_latex(text: MarkdownContent, is_supplementary: bool = False) -> LatexContent:
    r"""Convert markdown figures to LaTeX figure environments.

    Args:
        text: The text containing markdown figures
        is_supplementary: If True, enables supplementary content processing

    Returns:
        Text with figures converted to LaTeX format
    """
    # First protect code blocks from figure processing
    protected_blocks: list[str] = []

    # Protect fenced code blocks FIRST (before inline code)
    def protect_fenced_code(match: re.Match[str]) -> str:
        protected_blocks.append(match.group(0))
        return f"__CODE_BLOCK_{len(protected_blocks) - 1}__"

    text = re.sub(r"```.*?```", protect_fenced_code, text, flags=re.DOTALL)

    # Protect inline code (backticks) AFTER fenced code blocks
    def protect_inline_code(match: re.Match[str]) -> str:
        protected_blocks.append(match.group(0))
        return f"__CODE_BLOCK_{len(protected_blocks) - 1}__"

    text = re.sub(r"`[^`]+`", protect_inline_code, text)

    # Process different figure formats
    text = _process_new_figure_format(text)
    text = _process_figure_with_attributes(text)
    text = _process_figure_without_attributes(text)

    # Restore protected code blocks
    for i, block in enumerate(protected_blocks):
        text = text.replace(f"__CODE_BLOCK_{i}__", block)

    return text


def convert_figure_references_to_latex(text: MarkdownContent) -> LatexContent:
    r"""Convert figure references from @fig:id and @sfig:id to LaTeX.

    Converts @fig:id to Fig. \\ref{fig:id} and @sfig:id to Fig. \\ref{sfig:id}.
    Handles panel references like @fig:Figure1 A to produce Fig. \\ref{fig:Figure1}A (no space).

    Args:
        text: Text containing figure references

    Returns:
        Text with figure references converted to LaTeX format with "Figure" prefix
    """
    # Convert @fig:id followed by space and panel letter to Figure \ref{fig:id}PanelLetter (no space)
    # Use empty group {} to prevent LaTeX from inserting unwanted spaces after \ref{}
    text = re.sub(r"@fig:([a-zA-Z0-9_-]+)\s+([A-Z])", r"Fig. \\ref{fig:\1}{}\2", text)

    # Convert @fig:id to Figure \ref{fig:id} (remaining basic references)
    text = re.sub(r"@fig:([a-zA-Z0-9_-]+)", r"Fig. \\ref{fig:\1}", text)

    # Convert @sfig:id followed by space and panel letter to Figure \ref{sfig:id}PanelLetter (no space)
    # Use empty group {} to prevent LaTeX from inserting unwanted spaces after \ref{}
    text = re.sub(r"@sfig:([a-zA-Z0-9_-]+)\s+([A-Z])", r"Fig. \\ref{sfig:\1}{}\2", text)

    # Convert @sfig:id to Figure \ref{sfig:id} (supplementary figures)
    text = re.sub(r"@sfig:([a-zA-Z0-9_-]+)", r"Fig. \\ref{sfig:\1}", text)

    return text


def convert_equation_references_to_latex(text: MarkdownContent) -> LatexContent:
    r"""Convert equation references from @eq:id to LaTeX.

    Converts @eq:id to \\eqref{eq:id} for proper equation referencing.

    Args:
        text: Text containing equation references

    Returns:
        Text with equation references converted to LaTeX format
    """
    # Convert @eq:id to \eqref{eq:id} for numbered equations
    text = re.sub(r"@eq:([a-zA-Z0-9_-]+)", r"\\eqref{eq:\1}", text)

    return text


def parse_figure_attributes(attr_string: str) -> FigureAttributes:
    r"""Parse figure attributes like {#fig:1 tex_position="!ht" width="0.8"}.

    Args:
        attr_string: String containing figure attributes

    Returns:
        Dictionary of parsed attributes
    """
    attributes: FigureAttributes = {}

    # Extract ID (starts with #)
    id_match = re.search(r"#([a-zA-Z0-9_:-]+)", attr_string)
    if id_match:
        attributes["id"] = id_match.group(1)

    # Extract other attributes (key="value" or key=value)
    attr_matches = re.findall(r'(\w+)=(["\'])([^"\']*)\2', attr_string)
    for match in attr_matches:
        key, _, value = match
        attributes[key] = value

    return attributes


def create_latex_figure_environment(
    path: str,
    caption: str,
    attributes: Optional[Dict[str, Any]] = None,
) -> str:
    if attributes is None:
        attributes = {}

    # ---------- small helpers ----------
    def _b(k: str, d=False) -> bool:
        v = attributes.get(k, d)
        if isinstance(v, bool):
            return v
        return str(v).strip().lower() in {"1", "true", "yes", "y", "on"}

    def _s(k: str, d: Optional[str] = None) -> Optional[str]:
        v = attributes.get(k, d)
        return None if v is None else str(v)

    # ---------- path ----------
    latex_path = path.replace("FIGURES/", "Figures/")
    if latex_path.lower().endswith(".svg"):
        latex_path = latex_path[:-4] + ".png"
    tex_path = f'"{latex_path}"' if " " in latex_path else latex_path

    # ---------- attributes ----------
    user_pos = _s("tex_position")
    user_width = attributes.get("width")
    max_height = attributes.get("max_height")
    raw_id = _s("id")
    caption_width = _s("caption_width", r"0.95\textwidth")
    barrier = _b("barrier", False)
    inline = _b("inline", False)
    landscape = _b("landscape", False)
    strict_width = _b("strict_width", False)
    is_span_req = (attributes.get("span") == "2col") or _b("twocolumn", False)
    fit = (_s("fit") or "").lower()
    if _b("fullpage", False):
        fit = "page"
    singlecol_p = _b("singlecol_floatpage", False)  # keep 1-col [p] only if you *really* want it

    # ---------- caption markdown -> LaTeX ----------
    processed_caption = re.sub(r"\*\*([^*]+)\*\*", r"\\textbf{\1}", caption)
    processed_caption = re.sub(r"\*([^*]+)\*", r"\\textit{\1}", processed_caption)

    # ---------- placement sanitizers ----------
    def _strip_br(s: Optional[str]) -> str:
        return s[1:-1] if s and s.startswith("[") and s.endswith("]") else (s or "")

    def _pos_single(pos: Optional[str]) -> str:
        if not pos:
            return "[!htbp]"
        core = _strip_br(pos)
        filt = "".join(c for c in core if c in "htbp!")
        return f"[{filt or '!htbp'}]"

    def _pos_star(pos: Optional[str]) -> str:
        if not pos:
            return "[!tbp]"
        core = _strip_br(pos)
        filt = "".join(c for c in core if c in "tbp!")  # drop h/H
        return f"[{filt or '!tbp'}]"

    # ---------- length parsing ----------
    ABS_DIM = re.compile(r"^[0-9]*\.?[0-9]+\s*(pt|bp|mm|cm|in|ex|em|dd|pc|sp)$")

    def _parse_len(expr, rel_unit: str) -> Tuple[str, str]:
        if expr is None:
            return rel_unit, ("rel-line" if rel_unit == r"\linewidth" else "rel-text")
        s = str(expr).strip()
        if s in (r"\linewidth", r"\columnwidth"):
            return s, "rel-line"
        if s in (r"\textwidth", r"\textheight"):
            return s, ("rel-text" if "width" in s else "rel-height")
        m = re.fullmatch(r"([0-9]*\.?[0-9]+)\s*\\(line|column|text)(width|height)", s)
        if m:
            f = min(float(m.group(1)), 1.0)
            unit = "\\" + m.group(2) + m.group(3)
            kind = (
                "rel-line"
                if m.group(2) in ("line", "column")
                else ("rel-text" if m.group(3) == "width" else "rel-height")
            )
            return f"{f:.3f}{unit}", kind
        if s.endswith("%") and re.fullmatch(r"[0-9]*\.?[0-9]+%", s):
            f = min(float(s[:-1]) / 100.0, 1.0)
            kind = (
                "rel-line" if rel_unit == r"\linewidth" else ("rel-text" if rel_unit == r"\textwidth" else "rel-height")
            )
            return f"{f:.3f}{rel_unit}", kind
        if re.fullmatch(r"[0-9]*\.?[0-9]+", s):
            f = min(float(s), 1.0)
            kind = (
                "rel-line" if rel_unit == r"\linewidth" else ("rel-text" if rel_unit == r"\textwidth" else "rel-height")
            )
            return f"{f:.3f}{rel_unit}", kind
        if ABS_DIM.match(s):
            return s, "abs"
        return s, "unit"

    def _parse_height(h):
        if h is None:
            return None
        expr, _ = _parse_len(h, r"\textheight")
        return expr

    # ========================= inline (non-float) =========================
    if inline:
        w_expr, _ = _parse_len(user_width, r"\linewidth")
        h_expr = _parse_height(max_height)
        inc = [f"width={w_expr}", "keepaspectratio", "draft=false"]
        if h_expr:
            inc.append(f"height={h_expr}")
        if _b("clip"):
            inc.append("clip")
        if _s("trim"):
            inc.append(f"trim={_s('trim')}")
        if _s("angle"):
            inc.append(f"angle={_s('angle')}")
        if _s("page"):
            inc.append(f"page={_s('page')}")
        opts = "[" + ",".join(inc) + "]"
        out = [
            r"\begin{center}",
            r"\makebox[\linewidth][c]{",
            f"  \\includegraphics{opts}{{{tex_path}}}",
            r"}",
            # Local caption: left/justified, never center
            r"\begingroup",
            r"\captionsetup{justification=raggedright,singlelinecheck=false}",
            r"\setlength{\abovecaptionskip}{6pt}\setlength{\belowcaptionskip}{6pt}",
            f"\\captionof{{figure}}{{{processed_caption}}}",
            (f"\\label{{{raw_id}}}" if raw_id else ""),
            r"\endgroup",
            r"\end{center}",
        ]
        if barrier:
            out.append(r"\FloatBarrier")
        out.append("")
        return "\n".join([line for line in out if line != ""])

    # ========================= float mode =========================
    figure_env, rel_unit, position = "figure", r"\linewidth", _pos_single(user_pos)
    w_expr, w_kind = _parse_len(user_width, rel_unit)

    # Upgrade to two-column if requested or width ties to \textwidth
    if is_span_req or r"\textwidth" in (user_width or "") or r"\textwidth" in w_expr:
        figure_env, rel_unit, position = "figure*", r"\textwidth", _pos_star(user_pos)
        w_expr, w_kind = _parse_len(user_width, rel_unit)

    # Full-page: default to two-column float page unless explicitly forced single-column
    if _strip_br(user_pos) == "p":
        if singlecol_p:
            figure_env, rel_unit, position = "figure", r"\textwidth", "[p]"
        else:
            figure_env, rel_unit, position = "figure*", r"\textwidth", "[p]"
        w_expr, w_kind = _parse_len(user_width, rel_unit)

    # Landscape
    env_name = ("sidewaysfigure*" if figure_env == "figure*" else "sidewaysfigure") if landscape else figure_env

    # Single-column safety clamp
    if env_name in {"figure", "sidewaysfigure"} and not strict_width:
        if w_kind in {"rel-text", "abs"} or r"\textwidth" in w_expr:
            w_expr = r"\linewidth"

    # Fit presets
    h_expr = _parse_height(max_height)
    if (fit == "page") and position == "[p]":
        w_expr = r"\textwidth"
        h_expr = h_expr or r"0.95\textheight"
    elif fit == "width":
        w_expr = r"\textwidth" if env_name.endswith("*") or position == "[p]" else r"\linewidth"
    elif fit == "height":
        h_expr = h_expr or (r"0.95\textheight" if position == "[p]" else r"\textheight")

    # Caption body for starred/page floats: use a top-aligned parbox WITHOUT centering.
    # Note: cap_body is prepared but not used in current implementation

    is_star_or_floatpage = env_name.endswith("*") or (position == "[p]")
    cap_width_for_env = caption_width if is_star_or_floatpage else r"\linewidth"

    local_caption = (
        r"\begingroup"
        rf"\captionsetup{{width={cap_width_for_env},singlelinecheck=false,justification=justified}}"
        r"\setlength{\abovecaptionskip}{6pt}\setlength{\belowcaptionskip}{6pt}"
        r"\ifdefined\justifying\justifying\fi"
        f"\\caption{{{processed_caption}}}" + (f"\\label{{{raw_id}}}" if raw_id else "") + r"\endgroup"
    )

    # includegraphics options
    inc = [f"width={w_expr}", "keepaspectratio", "draft=false"]
    if h_expr:
        inc.append(f"height={h_expr}")
    if _b("clip"):
        inc.append("clip")
    if _s("trim"):
        inc.append(f"trim={_s('trim')}")
    if _s("angle"):
        inc.append(f"angle={_s('angle')}")
    if _s("page"):
        inc.append(f"page={_s('page')}")
    opts = "[" + ",".join(inc) + "]"

    # Wrapper width: \textwidth for starred or [p]; \linewidth otherwise
    wrapper_width = r"\textwidth" if is_star_or_floatpage else r"\linewidth"
    lines = [
        f"\n\\begin{{{env_name}}}{position}",
        r"\centering",
        rf"\makebox[{wrapper_width}][c]{{",
        f"  \\includegraphics{opts}{{{tex_path}}}",
        r"}",
        local_caption,
        f"\\end{{{env_name}}}",
    ]

    if barrier:
        lines.append(r"\FloatBarrier")
    lines.append("")
    return "\n".join(lines)


def _process_new_figure_format(text: MarkdownContent) -> LatexContent:
    r"""Process the new figure format:

    ![](path)
    {attributes} Caption text (may be multi-line until the next blank line)

    Examples:
      ![](FIGURES/Fig1.pdf)
      {#fig:Figure1 width="\textwidth" tex_position="p"} **Title**.
    """
    import re

    # Allow: plain path, or quoted path "..." / '...'
    # Attributes may contain quoted values and spaces.
    # Caption is everything up to the next blank line (two consecutive newlines) or EOF.
    pattern = re.compile(
        r"""
        ^[ \t]*                          # optional leading spaces
        !\[\]                            # literal ![]
        \(
            (?P<path>                    # path can be quoted or unquoted (no newline)
                "(?:[^"\\]|\\.)+"        # double-quoted path (allow escaped chars)
                |'(?:[^'\\]|\\.)+'       # single-quoted path
                |[^)\r\n]+               # unquoted path without ) or newline
            )
        \)
        [ \t]*\r?\n                      # newline after )
        [ \t]*\{                         # start attributes line (allow leading spaces)
            (?P<attrs>                   # attributes content (no need to be ultra-fancy)
                (?:
                    [^{}\r\n"']+         # anything except braces/quotes/newlines
                    |"(?:[^"\\]|\\.)*"   # double-quoted chunks
                    |'(?:[^'\\]|\\.)*'   # single-quoted chunks
                    |\s+                 # spaces/tabs
                )*
            )
        \}[ \t]*                         # end attributes
        (?P<caption>                     # caption until the next blank line or EOF
            (?s:.*?)                     # DOTALL, non-greedy
        )
        (?=(?:\r?\n){2,}|\Z)             # stop at a blank line (>=2 newlines) or end
        """,
        re.MULTILINE | re.VERBOSE,
    )

    def _strip_quotes(s: str) -> str:
        if (len(s) >= 2) and ((s[0] == s[-1]) and s[0] in ("'", '"')):
            return s[1:-1]
        return s

    def _repl(m: re.Match[str]) -> str:
        path = _strip_quotes(m.group("path").strip())
        attr_string = m.group("attrs").strip()
        caption_text = m.group("caption").strip()

        try:
            attributes = parse_figure_attributes(attr_string)
        except Exception:
            # If attributes parsing fails, keep original block untouched
            return m.group(0)

        try:
            return create_latex_figure_environment(path, caption_text, attributes)
        except Exception:
            # If LaTeX emission fails, keep original block untouched
            return m.group(0)

    return pattern.sub(_repl, text)


def _process_figure_without_attributes(text: MarkdownContent) -> LatexContent:
    """Process figures without attributes: ![caption](path) or ![caption](path "title")."""
    import re

    # Matches:
    #   ![caption](path)
    #   ![caption](path "optional title")
    #   ![caption]("quoted path with spaces")
    # Does NOT match if immediately followed by {attributes} (handled upstream).
    pattern = re.compile(
        r"""
        !\[
            (?P<cap>(?:\\\]|[^\]])*)      # caption (allow escaped ])
        \]
        \(
            [ \t]*
            (?P<path>                     # path: quoted or unquoted (no newline)
                "(?:[^"\\]|\\.)+"         # double-quoted path
                |'(?:[^'\\]|\\.)+'        # single-quoted path
                |[^)\s][^)\r\n]*          # unquoted path (no leading space, up to ) or EOL)
            )
            (?:[ \t]+                     # optional title (ignored; used only if caption empty)
               (?P<title>
                    "(?:[^"\\]|\\.)*"     # "title"
                    |'(?:[^'\\]|\\.)*'    # 'title'
               )
            )?
            [ \t]*
        \)
        (?![ \t]*\{)                      # don't consume cases with immediate {attributes}
        """,
        re.VERBOSE,
    )

    def _strip_quotes(s: str) -> str:
        s = s.strip()
        if len(s) >= 2 and ((s[0] == s[-1]) and s[0] in ('"', "'")):
            return s[1:-1]
        return s

    def _repl(m: re.Match[str]) -> str:
        raw_cap = (m.group("cap") or "").strip()
        raw_path = (m.group("path") or "").strip()
        raw_title = (m.group("title") or "").strip()

        path = _strip_quotes(raw_path)
        caption = raw_cap if raw_cap else _strip_quotes(raw_title)

        # Validate path before emitting LaTeX. If invalid, leave original markdown untouched.
        try:
            ok = validate_figure_path(path)
        except Exception:
            ok = False
        if not ok:
            return m.group(0)

        try:
            return create_latex_figure_environment(path, caption)
        except Exception:
            return m.group(0)

    return pattern.sub(_repl, text)


def validate_figure_path(path: FigurePath) -> bool:
    r"""Validate a figure path for LaTeX inclusion.

    Rules:
      - Allow common image/vector formats (png, jpg, jpeg, pdf, svg, eps).
      - Allow extensionless paths (LaTeX can resolve via \DeclareGraphicsExtensions).
      - Allow http/https in case an upstream step resolves/downloads.
    """
    if not isinstance(path, str):
        return False
    s = path.strip().strip('"').strip("'")
    if not s:
        return False

    # Remote URLs are allowed (caller may prefetch/replace).
    if s.startswith(("http://", "https://")):
        return True

    # If extensionless, allow (LaTeX may infer extensions or your pipeline may add them).
    root, ext = os.path.splitext(s)
    if ext == "":
        return True

    valid_extensions = {".png", ".jpg", ".jpeg", ".pdf", ".svg", ".eps"}
    return ext.lower() in valid_extensions


def _process_figure_with_attributes(text: MarkdownContent) -> LatexContent:
    """Process figures with attributes: ![caption](path){attributes}."""

    def process_figure_with_attributes(match: re.Match[str]) -> str:
        caption = match.group(1)
        path = match.group(2)
        attr_string = match.group(3)

        # Parse attributes
        attributes = parse_figure_attributes(attr_string)
        return create_latex_figure_environment(path, caption, attributes)

    # Handle figures with attributes (old format)
    return re.sub(r"!\[([^\]]*)\]\(([^)]+)\)\{([^}]+)\}", process_figure_with_attributes, text)


def extract_figure_ids_from_text(text: MarkdownContent) -> list[FigureId]:
    """Extract all figure IDs from markdown text.

    Args:
        text: Text to extract figure IDs from

    Returns:
        List of unique figure IDs found in the text
    """
    figure_ids: list[FigureId] = []

    # Find figure attribute blocks
    attr_matches = re.findall(r"\{#([a-zA-Z0-9_:-]+)[^}]*\}", text)
    for match in attr_matches:
        if (match.startswith("fig:") or match.startswith("sfig:")) and match not in figure_ids:
            figure_ids.append(match)

    return figure_ids
