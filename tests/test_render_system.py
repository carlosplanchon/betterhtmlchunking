#!/usr/bin/env python3

from betterhtmlchunking.main import DomRepresentation
from betterhtmlchunking.tree_regions_system import ReprLengthComparisionBy


def _dom(html, max_length, mode=ReprLengthComparisionBy.HTML_LENGTH):
    dom = DomRepresentation(
        MAX_NODE_REPR_LENGTH=max_length,
        website_code=html,
        repr_length_compared_by=mode,
    )
    dom.start()
    return dom


LARGE_HTML = "<html><body>" + "".join(
    f"<section><h2>Section {i}</h2>"
    f"<p>Paragraph with a fair amount of readable content number {i}.</p>"
    f"</section>"
    for i in range(10)
) + "</body></html>"


class TestRenderSystemCoherence:
    """RenderSystem output is consistent with the A'' size metric."""

    def test_per_xpath_render_length_equals_html_length(self):
        """Each rendered node's HTML length equals its stored html_length."""
        dom = _dom(LARGE_HTML, max_length=120)
        rs = dom.render_system
        tr = dom.tree_representation
        checked = 0
        for roi_idx, per_xpath in rs.html_render_with_pos_xpath.items():
            for xpath, rendered in per_xpath.items():
                assert len(rendered) == tr.tree.get_node(xpath).data.html_length
                checked += 1
        assert checked > 0

    def test_chunk_html_is_join_of_parts(self):
        """Chunk HTML equals its per-xpath parts joined with newlines."""
        dom = _dom(LARGE_HTML, max_length=120)
        rs = dom.render_system
        for roi_idx in rs.html_render_roi:
            expected = "\n".join(rs.html_render_with_pos_xpath[roi_idx].values())
            assert rs.html_render_roi[roi_idx] == expected

    def test_large_document_splits_into_multiple_chunks(self):
        """A large document with a small max length yields several chunks."""
        dom = _dom(LARGE_HTML, max_length=120)
        assert len(dom.render_system.html_render_roi) >= 2


class TestRenderSystemOutput:
    """RenderSystem output is clean, compact HTML (no bs4 prettify inflation)."""

    def test_single_chunk_renders_compact_html(self):
        """A small document fitting one chunk renders as compact HTML."""
        html = "<html><body><div><p>deep</p></div></body></html>"
        dom = _dom(html, max_length=10000)
        assert dom.render_system.html_render_roi[0] == (
            "<html><body><div><p>deep</p></div></body></html>"
        )

    def test_entities_preserved_in_render(self):
        html = "<html><body><p>a &amp; b</p></body></html>"
        dom = _dom(html, max_length=1000)
        assert "&amp;" in dom.render_system.html_render_roi[0]

    def test_text_render_present_and_readable(self):
        html = "<html><body><article><p>Readable text here</p></article></body></html>"
        dom = _dom(html, max_length=1000)
        assert "Readable text here" in dom.render_system.text_render_roi[0]

    def test_text_length_mode_pipeline(self):
        """TEXT_LENGTH mode produces chunks and readable text."""
        dom = _dom(
            LARGE_HTML,
            max_length=200,
            mode=ReprLengthComparisionBy.TEXT_LENGTH,
        )
        assert len(dom.render_system.text_render_roi) >= 1
        joined = "\n".join(dom.render_system.text_render_roi.values())
        assert "Paragraph with a fair amount" in joined
