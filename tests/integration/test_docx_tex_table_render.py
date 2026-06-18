"""Integration test for rendering a {{tex}} table to a PNG image.

Exercises the real ``prepare_table_latex`` -> pdflatex -> pdftoppm pipeline.
The function name contains "latex" so conftest auto-marks it ``requires_latex``
(it skips cleanly where no LaTeX toolchain is installed).
"""

from rxiv_maker.exporters.docx_writer import DocxWriter

SIMPLE_STABLE = (
    "\\begin{stable}[h!]\n"
    "\\small\n"
    "\\begin{tabular}{|l|l|}\n"
    "\\hline\n"
    "\\textbf{Col A} & \\textbf{Col B} \\\\\n"
    "\\hline\n"
    "alpha & beta \\\\\n"
    "\\hline\n"
    "\\end{tabular}\n"
    "\\caption{Demo.}\n"
    "\\label{stable:demo}\n"
    "\\end{stable}"
)


def test_latex_table_renders_to_png():
    writer = DocxWriter.__new__(DocxWriter)  # only the render method is needed
    png = DocxWriter._render_tex_table_to_image(writer, SIMPLE_STABLE)
    assert png is not None, "expected a rendered PNG from a valid tabular"
    assert png.exists() and png.stat().st_size > 0
    from PIL import Image

    width, height = Image.open(str(png)).size
    assert width > 50 and height > 20
