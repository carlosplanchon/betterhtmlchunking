#!/usr/bin/env python3

from html import escape

import attrs
import pytest

from betterhtmlchunking import Chunk, DomRepresentation, chunk_html
from betterhtmlchunking.main import ReprLengthComparisonBy


HTML = (
    "<html><body>"
    "<h1>Title</h1><p>First paragraph with <b>bold</b> text.</p>"
    "<div>Loose text <a href='#'>a link</a> and more.<p>Nested paragraph.</p></div>"
    "<ul><li>One</li><li>Two</li><li>Three</li></ul>"
    "</body></html>"
)


def _dom_chunks(mode, max_length, **kwargs):
    dom = DomRepresentation(
        MAX_NODE_REPR_LENGTH=max_length,
        website_code=HTML,
        repr_length_compared_by=mode,
        **kwargs,
    )
    dom.start()
    render = dom.render_system
    regions = dom.tree_regions_system.sorted_roi_by_pos_xpath
    return [
        (idx, render.html_render_roi[idx], render.text_render_roi[idx],
         tuple(regions[idx].pos_xpath_list))
        for idx in sorted(render.html_render_roi)
    ]


class TestChunkHtml:
    """chunk_html() is a shortcut over DomRepresentation."""

    @pytest.mark.parametrize("by,mode", [
        ("html", ReprLengthComparisonBy.HTML_LENGTH),
        ("text", ReprLengthComparisonBy.TEXT_LENGTH),
        (ReprLengthComparisonBy.TEXT_LENGTH, ReprLengthComparisonBy.TEXT_LENGTH),
    ])
    def test_same_chunks_as_dom_representation(self, by, mode):
        max_length = 60 if mode == ReprLengthComparisonBy.HTML_LENGTH else 20
        chunks = chunk_html(HTML, max_length, by=by)
        assert len(chunks) > 1
        assert [
            (chunk.index, chunk.html, chunk.text, chunk.xpaths) for chunk in chunks
        ] == _dom_chunks(mode, max_length)

    def test_html_is_the_default(self):
        assert chunk_html(HTML, 60) == chunk_html(HTML, 60, by="html")

    def test_indexes_are_in_document_order(self):
        chunks = chunk_html(HTML, 60)
        assert [chunk.index for chunk in chunks] == list(range(len(chunks)))
        text = "\n".join(chunk.text for chunk in chunks)
        assert text.index("Title") < text.index("Nested paragraph") < text.index("Three")

    def test_invalid_by_is_rejected(self):
        with pytest.raises(ValueError, match="'html' or 'text'"):
            chunk_html(HTML, 60, by="words")
        with pytest.raises(ValueError):
            chunk_html(HTML, 60, by=["html"])

    def test_chunks_are_immutable(self):
        chunk = chunk_html(HTML, 1000)[0]
        assert isinstance(chunk, Chunk)
        with pytest.raises(attrs.exceptions.FrozenInstanceError):
            chunk.text = "changed"

    def test_options_are_passed_through(self):
        no_paragraphs = chunk_html(HTML, 1000, tag_list_to_filter_out=["/p"])
        assert "First paragraph" not in "\n".join(c.text for c in no_paragraphs)

        escaped = escape("<p>Hello</p>")
        kept = chunk_html(escaped, 1000, html_unescape=False)
        assert "<p>Hello</p>" in "\n".join(c.text for c in kept)

        mojibake = "<html><body><p>cafÃ©</p></body></html>"
        assert "café" in chunk_html(mojibake, 1000)[0].text
        assert "cafÃ©" in chunk_html(mojibake, 1000, fix_mojibake=False)[0].text

    def test_empty_document(self):
        chunks = chunk_html("", 1000)
        assert isinstance(chunks, list)
        assert all(chunk.text == "" for chunk in chunks)
