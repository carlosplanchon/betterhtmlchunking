#!/usr/bin/env python3

from html import escape, unescape

import pytest

from betterhtmlchunking.main import DomRepresentation, looks_html_escaped
from betterhtmlchunking.tree_regions_system import ReprLengthComparisionBy
from betterhtmlchunking.tree_representation import (
    get_element_text,
    is_text_node_xpath,
)


class TestDomRepresentation:
    """Tests for DomRepresentation - the main API."""

    def test_basic_initialization(self):
        """Test basic DomRepresentation initialization."""
        html = "<html><body><p>Test content</p></body></html>"
        dom = DomRepresentation(
            MAX_NODE_REPR_LENGTH=100,
            website_code=html,
            repr_length_compared_by=ReprLengthComparisionBy.HTML_LENGTH
        )
        assert dom is not None
        assert dom.website_code == html

    def test_compute_tree_representation(self):
        """Test computing tree representation."""
        html = "<html><body><div>Content</div></body></html>"
        dom = DomRepresentation(
            MAX_NODE_REPR_LENGTH=100,
            website_code=html,
            repr_length_compared_by=ReprLengthComparisionBy.HTML_LENGTH
        )

        dom.compute_tree_representation()

        assert dom.tree_representation is not None
        assert len(dom.tree_representation.pos_xpaths_list) > 0

    def test_compute_tree_regions_system(self):
        """Test computing tree regions system."""
        html = "<html><body><p>Paragraph 1</p><p>Paragraph 2</p></body></html>"
        dom = DomRepresentation(
            MAX_NODE_REPR_LENGTH=100,
            website_code=html,
            repr_length_compared_by=ReprLengthComparisionBy.HTML_LENGTH
        )

        dom.compute_tree_representation()
        dom.compute_tree_regions_system()

        assert dom.tree_regions_system is not None
        assert len(dom.tree_regions_system.regions_of_interest_list) >= 1

    def test_compute_render_system(self):
        """Test computing render system."""
        html = "<html><body><div>Content to render</div></body></html>"
        dom = DomRepresentation(
            MAX_NODE_REPR_LENGTH=100,
            website_code=html,
            repr_length_compared_by=ReprLengthComparisionBy.HTML_LENGTH
        )

        dom.compute_tree_representation()
        dom.compute_tree_regions_system()
        dom.compute_render_system()

        assert dom.render_system is not None

    def test_full_pipeline(self):
        """Test full processing pipeline."""
        html = """
        <html>
            <body>
                <section>
                    <h1>Title</h1>
                    <p>Paragraph content here</p>
                </section>
            </body>
        </html>
        """
        dom = DomRepresentation(
            MAX_NODE_REPR_LENGTH=150,
            website_code=html,
            repr_length_compared_by=ReprLengthComparisionBy.HTML_LENGTH
        )

        dom.compute_tree_representation()
        dom.compute_tree_regions_system()
        dom.compute_render_system()

        assert dom.tree_representation is not None
        assert dom.tree_regions_system is not None
        assert dom.render_system is not None

    def test_html_unescape_enabled(self):
        """html_unescape=True unescapes the input even when it is real HTML."""
        html = "<html><body><p>&lt;Hello&gt;</p></body></html>"
        dom = DomRepresentation(
            MAX_NODE_REPR_LENGTH=100,
            website_code=html,
            repr_length_compared_by=ReprLengthComparisionBy.HTML_LENGTH,
            html_unescape=True
        )

        assert dom.website_code == unescape(html)

    def test_html_unescape_disabled(self):
        """Test that HTML unescaping can be disabled."""
        html = "<html><body><p>&lt;Hello&gt;</p></body></html>"
        dom = DomRepresentation(
            MAX_NODE_REPR_LENGTH=100,
            website_code=html,
            repr_length_compared_by=ReprLengthComparisionBy.HTML_LENGTH,
            html_unescape=False
        )

        # HTML should NOT be unescaped
        assert dom.website_code == html

    def test_custom_tag_filter_list(self):
        """Test using custom tag filter list."""
        html = "<html><head><title>Test</title></head><body><div>Content</div></body></html>"
        dom = DomRepresentation(
            MAX_NODE_REPR_LENGTH=100,
            website_code=html,
            repr_length_compared_by=ReprLengthComparisionBy.HTML_LENGTH,
            tag_list_to_filter_out=["/head"]
        )

        dom.compute_tree_representation()

        # Head should be filtered
        assert not any("/head" in xpath for xpath in dom.tree_representation.pos_xpaths_list)

    def test_default_tag_filter_list(self):
        """Test that default tag filter list is applied."""
        html = "<html><head><title>T</title></head><body><script>alert('x')</script><div>Content</div></body></html>"
        dom = DomRepresentation(
            MAX_NODE_REPR_LENGTH=100,
            website_code=html,
            repr_length_compared_by=ReprLengthComparisionBy.HTML_LENGTH
        )

        dom.compute_tree_representation()

        # Script and head should be filtered by default
        xpaths = dom.tree_representation.pos_xpaths_list
        assert not any("/script" in xpath for xpath in xpaths)
        assert not any("/head" in xpath for xpath in xpaths)

    def test_text_length_comparison_mode(self):
        """Test using text length comparison mode."""
        html = "<html><body><p>Text content</p></body></html>"
        dom = DomRepresentation(
            MAX_NODE_REPR_LENGTH=100,
            website_code=html,
            repr_length_compared_by=ReprLengthComparisionBy.TEXT_LENGTH
        )

        dom.compute_tree_representation()
        dom.compute_tree_regions_system()

        assert dom.tree_regions_system is not None

    def test_html_length_comparison_mode(self):
        """Test using HTML length comparison mode."""
        html = "<html><body><div>Content</div></body></html>"
        dom = DomRepresentation(
            MAX_NODE_REPR_LENGTH=100,
            website_code=html,
            repr_length_compared_by=ReprLengthComparisionBy.HTML_LENGTH
        )

        dom.compute_tree_representation()
        dom.compute_tree_regions_system()

        assert dom.tree_regions_system is not None

    def test_small_max_node_repr_length(self):
        """Test with very small MAX_NODE_REPR_LENGTH."""
        html = "<html><body><p>Content</p></body></html>"
        dom = DomRepresentation(
            MAX_NODE_REPR_LENGTH=10,
            website_code=html,
            repr_length_compared_by=ReprLengthComparisionBy.HTML_LENGTH
        )

        dom.compute_tree_representation()
        dom.compute_tree_regions_system()

        # Should still create regions
        assert len(dom.tree_regions_system.regions_of_interest_list) >= 1

    def test_large_max_node_repr_length(self):
        """Test with very large MAX_NODE_REPR_LENGTH."""
        html = "<html><body><p>Content 1</p><p>Content 2</p><p>Content 3</p></body></html>"
        dom = DomRepresentation(
            MAX_NODE_REPR_LENGTH=10000,
            website_code=html,
            repr_length_compared_by=ReprLengthComparisionBy.HTML_LENGTH
        )

        dom.compute_tree_representation()
        dom.compute_tree_regions_system()

        # Should group into fewer regions
        assert dom.tree_regions_system.regions_of_interest_list is not None

    def test_complex_nested_structure(self):
        """Test with complex nested HTML structure."""
        html = """
        <html>
            <body>
                <header>
                    <nav><a href="#">Link</a></nav>
                </header>
                <main>
                    <article>
                        <h1>Article Title</h1>
                        <section>
                            <p>Paragraph 1</p>
                            <p>Paragraph 2</p>
                        </section>
                    </article>
                </main>
                <footer>
                    <p>Footer content</p>
                </footer>
            </body>
        </html>
        """
        dom = DomRepresentation(
            MAX_NODE_REPR_LENGTH=200,
            website_code=html,
            repr_length_compared_by=ReprLengthComparisionBy.HTML_LENGTH
        )

        dom.compute_tree_representation()
        dom.compute_tree_regions_system()
        dom.compute_render_system()

        assert dom.tree_representation is not None
        assert dom.tree_regions_system is not None
        assert len(dom.tree_regions_system.regions_of_interest_list) >= 1

    def test_empty_html_handling(self):
        """Test handling of empty HTML."""
        html = "<html></html>"
        dom = DomRepresentation(
            MAX_NODE_REPR_LENGTH=100,
            website_code=html,
            repr_length_compared_by=ReprLengthComparisionBy.HTML_LENGTH
        )

        dom.compute_tree_representation()
        dom.compute_tree_regions_system()

        # Should handle gracefully
        assert dom.tree_representation is not None

    def test_malformed_html_handling(self):
        """Test handling of malformed HTML."""
        html = "<html><body><p>Unclosed paragraph</body></html>"
        dom = DomRepresentation(
            MAX_NODE_REPR_LENGTH=100,
            website_code=html,
            repr_length_compared_by=ReprLengthComparisionBy.HTML_LENGTH
        )

        # Should parse without crashing
        dom.compute_tree_representation()
        assert dom.tree_representation is not None

    def test_regions_of_interest_list_property(self):
        """Test that regions_of_interest_list property works."""
        html = "<html><body><p>Content</p></body></html>"
        dom = DomRepresentation(
            MAX_NODE_REPR_LENGTH=100,
            website_code=html,
            repr_length_compared_by=ReprLengthComparisionBy.HTML_LENGTH
        )

        dom.compute_tree_representation()
        dom.compute_tree_regions_system()

        # Should be able to access regions list
        regions = dom.tree_regions_system.regions_of_interest_list
        assert regions is not None
        assert isinstance(regions, list)


class TestFixMojibake:
    """Tests for the fix_mojibake option (ftfy text repair)."""

    # "cafÃ©" / "Ã¼ber": UTF-8 "café"/"über" mis-decoded as latin-1.
    MOJIBAKE_HTML = (
        "<html><body><p>cafÃ© Ã¼ber</p></body></html>"
    )

    def test_fix_mojibake_on_by_default_repairs_text(self):
        dom = DomRepresentation(
            MAX_NODE_REPR_LENGTH=1000,
            website_code=self.MOJIBAKE_HTML,
            repr_length_compared_by=ReprLengthComparisionBy.TEXT_LENGTH,
        )
        dom.start()
        text = "\n".join(dom.render_system.text_render_roi.values())
        assert "café über" in text      # "café über" repaired
        assert "cafÃ©" not in text      # mojibake gone

    def test_fix_mojibake_off_keeps_raw_text(self):
        dom = DomRepresentation(
            MAX_NODE_REPR_LENGTH=1000,
            website_code=self.MOJIBAKE_HTML,
            repr_length_compared_by=ReprLengthComparisionBy.TEXT_LENGTH,
            fix_mojibake=False,
        )
        dom.start()
        text = "\n".join(dom.render_system.text_render_roi.values())
        assert "cafÃ©" in text          # mojibake preserved

    def test_fix_mojibake_default_matches_previous_behavior(self):
        """Default (fix on) must match a no-mojibake baseline unchanged."""
        html = "<html><body><p>clean text</p></body></html>"
        dom = DomRepresentation(
            MAX_NODE_REPR_LENGTH=1000,
            website_code=html,
            repr_length_compared_by=ReprLengthComparisionBy.TEXT_LENGTH,
        )
        dom.start()
        assert "clean text" in "\n".join(dom.render_system.text_render_roi.values())


class TestLoneSurrogates:
    """DomRepresentation rejects text that lxml would silently truncate."""

    def test_rejected_at_construction(self):
        """A lone surrogate fails fast, before any processing."""
        with pytest.raises(ValueError, match="lone surrogate"):
            DomRepresentation(
                MAX_NODE_REPR_LENGTH=1000,
                website_code="<p>caf\udce9 cr\udce8me</p><p>second paragraph</p>",
                repr_length_compared_by=ReprLengthComparisionBy.HTML_LENGTH,
            )

    def test_escaped_surrogate_references_are_accepted(self):
        """&#xD800; is plain text: html.unescape maps it to U+FFFD, no loss."""
        dom = DomRepresentation(
            MAX_NODE_REPR_LENGTH=1000,
            website_code=(
                "<html><body><p>before &#xD800; after</p>"
                "<p>second paragraph</p></body></html>"
            ),
            repr_length_compared_by=ReprLengthComparisionBy.TEXT_LENGTH,
        )
        dom.start()
        text = "\n".join(dom.render_system.text_render_roi.values())
        assert "after" in text
        assert "second paragraph" in text


class TestSplitKeepsText:
    """Splitting an element into regions keeps the text directly inside it."""

    INTRO_HTML = (
        "<html><body><div>INTRO text. "
        + "".join(
            f"<span>span number {i} xxxxxxxxx</span> TAIL{i} " for i in range(6)
        )
        + "</div></body></html>"
    )

    # Inline elements, comments, <br>, a list and a <pre>: plenty of text
    # nodes directly inside elements that a small limit forces to split.
    MIXED_HTML = (
        "<html><body>"
        "<div>Lead text <a href='#'>link one</a>, middle <!-- c --> after "
        "comment <b>bold <i>nested italic</i> end of bold</b> tail of bold."
        "<p>Paragraph <em>with emphasis</em> and more.</p>"
        "Loose text after the paragraph.<br>Line after br<br>Last line"
        "<ul><li>One <code>x</code> two</li><li>Three</li></ul> after list"
        "</div>"
        "<pre>  indented <span>code</span>\n    more code</pre>"
        "</body></html>"
    )

    @staticmethod
    def _run(html, max_length, mode=ReprLengthComparisionBy.HTML_LENGTH):
        dom = DomRepresentation(
            MAX_NODE_REPR_LENGTH=max_length,
            website_code=html,
            repr_length_compared_by=mode,
            fix_mojibake=False,
        )
        dom.start()
        return dom

    @staticmethod
    def _all_text(dom):
        return "\n".join(dom.render_system.text_render_roi.values())

    def test_parent_text_and_tails_are_kept_in_order(self):
        dom = self._run(self.INTRO_HTML, 100)
        assert len(dom.render_system.html_render_roi) > 1  # it was split
        text = self._all_text(dom)
        html = "\n".join(dom.render_system.html_render_roi.values())
        words = ["INTRO"] + [f"TAIL{i}" for i in range(6)]
        for word in words:
            assert word in text
            assert word in html
        positions = [text.index(word) for word in words]
        assert positions == sorted(positions)

    def test_text_length_mode_keeps_text(self):
        dom = self._run(
            self.INTRO_HTML, 30, mode=ReprLengthComparisionBy.TEXT_LENGTH
        )
        text = self._all_text(dom)
        for word in ["INTRO"] + [f"TAIL{i}" for i in range(6)]:
            assert word in text

    def test_br_separated_lines_are_kept(self):
        html = (
            "<html><body><div>"
            + "<br>".join(f"line {i} with some words" for i in range(600))
            + "</div></body></html>"
        )
        dom = self._run(html, 1000)
        assert len(dom.render_system.html_render_roi) > 1
        text = self._all_text(dom)
        assert all(f"line {i} with some words" in text for i in range(600))

    def test_split_pre_keeps_whitespace(self):
        html = (
            "<html><body><pre>"
            + "".join(f"  File <span>f{i}.py</span>, line {i}\n" for i in range(20))
            + "</pre></body></html>"
        )
        dom = self._run(html, 100)
        units = [
            xpath
            for roi in dom.tree_regions_system.sorted_roi_by_pos_xpath.values()
            for xpath in roi.pos_xpath_list
        ]
        assert any(is_text_node_xpath(xpath) for xpath in units)  # was split
        assert "  File " in self._all_text(dom)

    @pytest.mark.parametrize("mode,max_length", [
        (ReprLengthComparisionBy.HTML_LENGTH, 20),
        (ReprLengthComparisionBy.HTML_LENGTH, 60),
        (ReprLengthComparisionBy.HTML_LENGTH, 200),
        (ReprLengthComparisionBy.TEXT_LENGTH, 10),
        (ReprLengthComparisionBy.TEXT_LENGTH, 40),
    ])
    def test_every_text_line_lands_in_exactly_one_chunk(self, mode, max_length):
        """The chunks hold the document's text: nothing lost, duplicated or
        reordered."""
        dom = self._run(self.MIXED_HTML, max_length, mode=mode)
        chunk_lines = [
            line for line in self._all_text(dom).split("\n") if line
        ]
        document_text = get_element_text(
            dom.tree_representation.root, fix_mojibake=False
        )
        document_lines = [
            line for line in document_text.split("\n") if line
        ]
        assert chunk_lines == document_lines


class TestHtmlUnescape:
    """html_unescape=None (the default) only unescapes escaped documents."""

    @staticmethod
    def _dom(website_code, **kwargs):
        dom = DomRepresentation(
            MAX_NODE_REPR_LENGTH=1000,
            website_code=website_code,
            repr_length_compared_by=ReprLengthComparisionBy.HTML_LENGTH,
            **kwargs,
        )
        dom.start()
        return dom

    @staticmethod
    def _text(dom):
        return "\n".join(dom.render_system.text_render_roi.values())

    def test_default_keeps_quotes_inside_attributes(self):
        dom = self._dom(
            '<html><body><p><a href="https://example.com/x" '
            'title="say &quot;hi&quot;">link</a> after</p></body></html>'
        )
        link = dom.tree_representation.root.find(".//a")
        assert link.get("title") == 'say "hi"'
        assert link.get("href") == "https://example.com/x"

    def test_default_keeps_escaped_markup_as_text(self):
        dom = self._dom(
            "<html><body><p>Use &lt;script&gt; tags carefully.</p>"
            "<p>Second paragraph.</p></body></html>"
        )
        text = self._text(dom)
        assert "Use <script> tags carefully." in text
        assert "Second paragraph." in text

    def test_default_keeps_code_samples(self):
        dom = self._dom(
            "<html><body><pre>if a &lt;b and c&gt; d:</pre></body></html>"
        )
        assert "if a <b and c> d:" in self._text(dom)
        assert dom.tree_representation.root.find(".//pre/b") is None

    def test_default_unescapes_an_escaped_document(self):
        dom = self._dom(
            escape("<html><body><p>Hello</p><p>World</p></body></html>")
        )
        assert "/html/body/p[2]" in dom.tree_representation.pos_xpaths_list
        assert "World" in self._text(dom)

    def test_false_never_unescapes(self):
        escaped = escape("<html><body><p>Hello</p></body></html>")
        dom = self._dom(escaped, html_unescape=False)
        assert dom.website_code == escaped
        assert "<p>Hello</p>" in self._text(dom)  # kept as literal text

    @pytest.mark.parametrize("website_code,expected", [
        ("<p>Use &lt;b&gt; for bold</p>", False),  # real HTML: leave it alone
        ("&lt;p&gt;Hello&lt;/p&gt;", True),         # an escaped document
        ("&lt;!DOCTYPE html&gt;&lt;html&gt;", True),
        ("&LT;P&GT;upper case", True),
        ("Fish &amp; Chips", False),                 # no escaped tag
        ("5 &lt; 6", False),                         # "&lt;" then a space
        ("", False),
    ])
    def test_looks_html_escaped(self, website_code, expected):
        assert looks_html_escaped(website_code) is expected
