"""Unit tests for the supplementary video processor."""

from rxiv_maker.converters.supplementary_video_processor import (
    process_supplementary_video_references,
    process_supplementary_videos,
    restore_supplementary_video_placeholders,
)


def _process_and_restore(content: str) -> str:
    """Run the full define -> placeholder -> restore round trip."""
    processed = process_supplementary_videos(content)
    return restore_supplementary_video_placeholders(processed)


class TestSupplementaryVideoDefinition:
    def test_full_block_with_image_and_url(self):
        content = (
            "![still](FIGURES/SVideo1.png)\n"
            '{#svideo:workflow url="https://youtu.be/ABC"} '
            "**Complete workflow.** Example use of VLab4Mic."
        )
        out = _process_and_restore(content)
        assert "\\includegraphics[width=0.9\\linewidth]{FIGURES/SVideo1.png}" in out
        # The still image itself is a clickable link to the video.
        assert "\\href{https://youtu.be/ABC}{\\includegraphics[width=0.9\\linewidth]{FIGURES/SVideo1.png}}" in out
        assert "\\begin{center}" in out and "\\end{center}" in out
        assert "\\suppvideo{Complete workflow.}" in out
        assert "\\label{svideo:workflow}" in out
        assert "\\href{https://youtu.be/ABC}{$\\blacktriangleright$~Watch video}" in out
        # Still + caption are kept together (needspace + unbreakable minipage)
        # so they never split across a page or overflow it.
        assert "\\needspace" in out
        assert "\\begin{minipage}" in out and "\\end{minipage}" in out
        # The description is captured into the block.
        assert "Example use of VLab4Mic." in out
        # The raw directive must be gone.
        assert "{#svideo:" not in out

    def test_block_without_image(self):
        content = '{#svideo:demo url="https://youtu.be/XYZ"} **Demo title.** Body text.'
        out = _process_and_restore(content)
        assert "\\includegraphics" not in out
        assert "\\suppvideo{Demo title.}" in out
        assert "\\label{svideo:demo}" in out
        assert "Watch video" in out

    def test_block_without_url(self):
        content = "![s](FIGURES/v.png)\n{#svideo:noumdl} **No link.** Body."
        out = _process_and_restore(content)
        assert "\\suppvideo{No link.}" in out
        assert "Watch video" not in out  # no link rendered when url is absent
        assert "\\href" not in out

    def test_custom_width(self):
        content = "![s](FIGURES/v.png)\n" + r'{#svideo:wide url="u" width="0.5\linewidth"} **T.** d.'
        out = _process_and_restore(content)
        assert r"width=0.5\linewidth" in out

    def test_two_videos_get_distinct_labels(self):
        content = (
            '![a](FIGURES/v1.png)\n{#svideo:one url="u1"} **First.** d1.\n\n'
            '![b](FIGURES/v2.png)\n{#svideo:two url="u2"} **Second.** d2.\n'
        )
        out = _process_and_restore(content)
        assert "\\label{svideo:one}" in out
        assert "\\label{svideo:two}" in out
        assert out.index("svideo:one") < out.index("svideo:two")

    def test_no_videos_is_noop(self):
        content = "Just some text with @snote:foo and a ![fig](x.pdf)."
        assert _process_and_restore(content) == content


class TestSupplementaryVideoReferences:
    def test_callout_renders_with_prefix(self):
        out = process_supplementary_video_references("See (@svideo:workflow) for details.")
        assert out == "See (Supplementary Video~\\ref{svideo:workflow}) for details."

    def test_multiple_references(self):
        out = process_supplementary_video_references("@svideo:one and @svideo:two")
        assert out == "Supplementary Video~\\ref{svideo:one} and Supplementary Video~\\ref{svideo:two}"

    def test_non_svideo_at_is_untouched(self):
        text = "Email a@b and cite @key and @snote:n."
        assert process_supplementary_video_references(text) == text
