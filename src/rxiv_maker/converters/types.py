"""Type definitions for markdown to LaTeX conversion."""

from typing import Union

# Type aliases for better readability
MarkdownContent = str
LatexContent = str
SectionKey = str
SectionTitle = str
CitationKey = str
FigureId = str
TableId = str
Placeholder = str

# Dictionary types
SectionDict = dict[SectionKey, LatexContent]
ProtectedContent = dict[Placeholder, str]
FigureAttributes = dict[str, str]
TableAttributes = dict[str, str]

# Content processing types
ContentProcessor = Union[str, list[str]]
ProcessingContext = dict[str, bool | str | int | ProtectedContent]

# Table-specific types
TableRow = list[str]
TableData = list[TableRow]
TableHeaders = list[str]

# Figure-specific types
FigurePath = str
FigureCaption = str
FigurePosition = str
FigureWidth = str

# Citation-specific types
CitationList = list[CitationKey]
CitationFormat = str
