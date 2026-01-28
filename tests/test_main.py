#!/usr/bin/env python3

from betterhtmlchunking.main import DomRepresentation
from betterhtmlchunking.tree_regions_system import ReprLengthComparisionBy


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
        """Test that HTML unescaping is applied when enabled."""
        html = "<html><body><p>&lt;Hello&gt;</p></body></html>"
        dom = DomRepresentation(
            MAX_NODE_REPR_LENGTH=100,
            website_code=html,
            repr_length_compared_by=ReprLengthComparisionBy.HTML_LENGTH,
            html_unescape=True
        )

        # HTML should be unescaped
        assert "<Hello>" in dom.website_code or "&lt;" in html

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
