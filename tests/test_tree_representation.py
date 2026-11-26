#!/usr/bin/env python3

from betterhtmlchunking.tree_representation import DOMTreeRepresentation
from betterhtmlchunking.tree_representation import get_xpath_depth
from betterhtmlchunking.tree_representation import (
    render_element_html,
    get_element_text,
    is_text_node_xpath,
)

import lxml.html
import pytest


def _element(html: str, tag: str):
    """Parse *html* and return the first element matching *tag* (lxml)."""
    root = lxml.html.document_fromstring(html)
    return root if root.tag == tag else root.find(".//" + tag)


class TestGetXPathDepth:
    """Tests for get_xpath_depth function."""

    def test_root_depth(self):
        """Test depth of root element."""
        assert get_xpath_depth("/html") == 1

    def test_nested_depth(self):
        """Test depth of nested elements."""
        assert get_xpath_depth("/html/body") == 2
        assert get_xpath_depth("/html/body/div") == 3
        assert get_xpath_depth("/html/body/div/p") == 4

    def test_indexed_elements(self):
        """Test depth with indexed elements."""
        assert get_xpath_depth("/html/body/div[1]") == 3
        assert get_xpath_depth("/html/body/div[1]/p[2]") == 4


class TestDOMTreeRepresentation:
    """Tests for DOMTreeRepresentation class."""

    def test_simple_html_parsing(self):
        """Test parsing simple HTML."""
        html = "<html><body><div>Hello World</div></body></html>"
        tree = DOMTreeRepresentation(website_code=html)

        assert tree.tree is not None
        assert len(tree.pos_xpaths_list) > 0

    def test_tree_has_html_root(self):
        """Test that tree has html as root."""
        html = "<html><body><p>Test</p></body></html>"
        tree = DOMTreeRepresentation(website_code=html)

        # Check that /html is in the tree
        assert any("/html" in xpath for xpath in tree.pos_xpaths_list)

    def test_nested_structure(self):
        """Test parsing nested HTML structure."""
        html = """
        <html>
            <body>
                <div>
                    <p>Paragraph 1</p>
                    <p>Paragraph 2</p>
                </div>
            </body>
        </html>
        """
        tree = DOMTreeRepresentation(website_code=html)

        # Check for expected tags
        xpaths = tree.pos_xpaths_list
        assert any("/body" in xpath for xpath in xpaths)
        assert any("/div" in xpath for xpath in xpaths)
        assert any("/p" in xpath for xpath in xpaths)

    def test_get_children_tag_list(self):
        """Test getting children tags of a node."""
        html = "<html><body><div>A</div><div>B</div></body></html>"
        tree = DOMTreeRepresentation(website_code=html)

        body_xpath = [x for x in tree.pos_xpaths_list if x.endswith("/body")][0]
        children = tree.get_children_tag_list(xpath=body_xpath)

        assert len(children) >= 2
        assert all("/div" in child for child in children)

    def test_delete_node(self):
        """Test deleting a node from tree."""
        html = "<html><body><div>Keep</div><script>Remove</script></body></html>"
        tree = DOMTreeRepresentation(website_code=html)

        # Find script tag
        script_xpath = [x for x in tree.pos_xpaths_list if "/script" in x]
        if script_xpath:
            tree.delete_node(pos_xpath=script_xpath[0])

            # Script should be removed
            assert not any("/script" in x for x in tree.pos_xpaths_list)

    def test_text_length_attribute(self):
        """Test that nodes have text_length attribute."""
        html = "<html><body><p>Some text content here</p></body></html>"
        tree = DOMTreeRepresentation(website_code=html)

        p_xpath = [x for x in tree.pos_xpaths_list if "/p" in x][0]
        node = tree.tree.get_node(p_xpath)

        assert hasattr(node.data, 'text_length')
        assert node.data.text_length > 0

    def test_html_length_attribute(self):
        """Test that nodes have html_length attribute."""
        html = "<html><body><div>Content</div></body></html>"
        tree = DOMTreeRepresentation(website_code=html)

        div_xpath = [x for x in tree.pos_xpaths_list if "/div" in x][0]
        node = tree.tree.get_node(div_xpath)

        assert hasattr(node.data, 'html_length')
        assert node.data.html_length > 0

    def test_recompute_representation(self):
        """Test recomputing representation after modifications."""
        html = "<html><body><div>Content</div><script>Remove</script></body></html>"
        tree = DOMTreeRepresentation(website_code=html)

        # Delete a node
        script_xpath = [x for x in tree.pos_xpaths_list if "/script" in x]
        if script_xpath:
            tree.delete_node(pos_xpath=script_xpath[0])

        # Recompute
        tree.recompute_representation()

        # Check that representation is updated
        assert tree.pos_xpaths_list is not None

    def test_empty_html(self):
        """Test parsing empty HTML."""
        html = "<html></html>"
        tree = DOMTreeRepresentation(website_code=html)

        assert tree.tree is not None
        assert len(tree.pos_xpaths_list) >= 1

    def test_self_closing_tags(self):
        """Test parsing self-closing tags."""
        html = "<html><body><img src='test.jpg'/><br/></body></html>"
        tree = DOMTreeRepresentation(website_code=html)

        xpaths = tree.pos_xpaths_list
        # Should handle self-closing tags
        assert any("/body" in xpath for xpath in xpaths)

    def test_multiple_same_tags(self):
        """Test parsing multiple tags of same type."""
        html = "<html><body><p>1</p><p>2</p><p>3</p></body></html>"
        tree = DOMTreeRepresentation(website_code=html)

        p_xpaths = [x for x in tree.pos_xpaths_list if "/p" in x]
        assert len(p_xpaths) == 3

    def test_deeply_nested_structure(self):
        """Test parsing deeply nested structure."""
        html = """
        <html>
            <body>
                <div>
                    <section>
                        <article>
                            <p>Deep content</p>
                        </article>
                    </section>
                </div>
            </body>
        </html>
        """
        tree = DOMTreeRepresentation(website_code=html)

        # Check depth
        p_xpath = [x for x in tree.pos_xpaths_list if "/p" in x][0]
        depth = get_xpath_depth(p_xpath)
        assert depth >= 5


class TestRenderElementHtml:
    """render_element_html: non-pretty HTML5 serialisation backing A''."""

    def test_compact_no_indentation(self):
        """Nested markup renders compactly (no bs4-style prettify inflation)."""
        html = "<html><body><div><p>Hi</p></div></body></html>"
        assert render_element_html(_element(html, "div")) == "<div><p>Hi</p></div>"

    def test_no_added_newlines(self):
        """Output carries no added indentation newlines (real markup size)."""
        html = "<html><body><ul><li>a</li><li>b</li></ul></body></html>"
        out = render_element_html(_element(html, "ul"))
        assert out == "<ul><li>a</li><li>b</li></ul>"
        assert "\n" not in out

    def test_attribute_source_order_preserved(self):
        """Attributes keep document order (bs4.prettify alphabetised them)."""
        html = "<html><body><a href='u' class='c' id='i'>t</a></body></html>"
        assert (
            render_element_html(_element(html, "a"))
            == '<a href="u" class="c" id="i">t</a>'
        )

    def test_void_elements_html5(self):
        """Void elements use HTML5 form (no XML self-closing slash)."""
        html = "<html><body><div><img src='x.jpg'><br></div></body></html>"
        assert (
            render_element_html(_element(html, "div"))
            == '<div><img src="x.jpg"><br></div>'
        )

    def test_empty_element_is_valid_html5(self):
        """Empty non-void elements render as <tag></tag>, never <tag/>."""
        html = "<html><body><div></div></body></html>"
        assert render_element_html(_element(html, "div")) == "<div></div>"

    def test_entities_escaped(self):
        """Special characters stay escaped in the markup."""
        html = "<html><body><p>a &amp; b &lt; c</p></body></html>"
        assert render_element_html(_element(html, "p")) == "<p>a &amp; b &lt; c</p>"

    def test_non_ascii_preserved(self):
        """Non-ASCII text is kept as unicode, not numeric entities."""
        html = "<html><body><p>café über</p></body></html>"
        assert render_element_html(_element(html, "p")) == "<p>café über</p>"

    def test_tail_text_excluded(self):
        """with_tail=False: trailing text (belongs to the parent) is excluded."""
        html = "<html><body><p>foo <b>bar</b> baz</p></body></html>"
        assert render_element_html(_element(html, "b")) == "<b>bar</b>"


class TestGetElementText:
    """get_element_text: parsel-native text extraction."""

    def test_block_elements_joined_with_newline(self):
        html = "<html><body><div><p>A</p><p>B</p></div></body></html>"
        assert get_element_text(_element(html, "div")) == "A\nB"

    def test_entities_decoded_in_text(self):
        html = "<html><body><p>a &amp; b</p></body></html>"
        assert get_element_text(_element(html, "p")) == "a & b"


class TestHtmlLengthCoherence:
    """A'' contract: the size metric equals the delivered markup."""

    def test_node_html_length_equals_rendered_length(self):
        """Every node's html_length == len(render_element_html(its element))."""
        html = """
        <html><body>
            <section><h1>Title</h1><p>One</p><p>Two</p></section>
            <div><ul><li>x</li><li>y</li></ul></div>
        </body></html>
        """
        tree = DOMTreeRepresentation(website_code=html)
        assert len(tree.pos_xpaths_list) > 0
        for xpath in tree.pos_xpaths_list:
            node = tree.tree.get_node(xpath)
            expected = len(render_element_html(node.data.lxml_elem))
            assert node.data.html_length == expected

    def test_text_length_equals_extracted_text_length(self):
        """Every node's text_length == len(get_element_text(its element))."""
        html = "<html><body><div><p>Hello</p><p>World</p></div></body></html>"
        tree = DOMTreeRepresentation(website_code=html)
        for xpath in tree.pos_xpaths_list:
            node = tree.tree.get_node(xpath)
            expected = len(get_element_text(node.data.lxml_elem))
            assert node.data.text_length == expected


class TestPositionalXpath:
    """Positional xpaths generated via lxml getpath()."""

    def test_siblings_get_indices(self):
        html = "<html><body><p>1</p><p>2</p><p>3</p></body></html>"
        tree = DOMTreeRepresentation(website_code=html)
        xpaths = tree.pos_xpaths_list
        assert "/html/body/p[1]" in xpaths
        assert "/html/body/p[2]" in xpaths
        assert "/html/body/p[3]" in xpaths

    def test_unique_elements_have_no_index(self):
        html = "<html><body><div>only</div></body></html>"
        tree = DOMTreeRepresentation(website_code=html)
        assert "/html/body/div" in tree.pos_xpaths_list
        assert "/html/body" in tree.pos_xpaths_list


class TestConstructorFiltering:
    """DOMTreeRepresentation prunes unwanted tags in one pass at build time."""

    def test_tag_list_filters_at_construction(self):
        html = (
            "<html><head><title>T</title></head>"
            "<body><div>keep</div><script>x</script></body></html>"
        )
        tree = DOMTreeRepresentation(
            website_code=html,
            tag_list_to_filter_out=["/head", "/script"],
        )
        xpaths = tree.pos_xpaths_list
        assert not any("/head" in x for x in xpaths)
        assert not any("/script" in x for x in xpaths)
        assert any("/div" in x for x in xpaths)

    def test_no_filter_list_keeps_everything(self):
        """Default (None) filters nothing, so direct callers get the full tree."""
        html = "<html><head><title>T</title></head><body><div>x</div></body></html>"
        tree = DOMTreeRepresentation(website_code=html)
        assert any("/head" in x for x in tree.pos_xpaths_list)


class TestLoneSurrogates:
    """Lone surrogates are rejected: lxml would drop everything after them."""

    # What b"<p>caf\xe9 cr\xe8me</p>..." becomes with errors="surrogateescape".
    SURROGATE_HTML = "<p>caf\udce9 cr\udce8me</p><p>second paragraph</p>"

    def test_lone_surrogate_is_rejected(self):
        with pytest.raises(ValueError) as excinfo:
            DOMTreeRepresentation(website_code=self.SURROGATE_HTML)
        message = str(excinfo.value)
        assert "website_code" in message
        assert "lone surrogate (U+DCE9) at index 6" in message

    def test_astral_characters_are_accepted(self):
        """Characters outside the BMP (e.g. emoji) are not surrogates in a str."""
        tree = DOMTreeRepresentation(
            website_code="<html><body><p>hi \U0001F600 there</p></body></html>"
        )
        assert "\U0001F600" in render_element_html(tree.root)


class TestContentUnits:
    """Text directly inside an element is exposed as text-node units."""

    HTML = (
        "<html><body><p>Intro <b>bold</b> middle <!-- note --> after comment"
        "<i>it</i>   </p></body></html>"
    )

    def test_units_interleave_elements_and_text(self):
        tree = DOMTreeRepresentation(website_code=self.HTML)
        assert tree.get_content_units("/html/body/p") == [
            "/html/body/p/text()[1]",   # "Intro "
            "/html/body/p/b",
            "/html/body/p/text()[2]",   # " middle " (tail of <b>)
            "/html/body/p/text()[3]",   # " after comment" (tail of the comment)
            "/html/body/p/i",           # its blank tail is not a unit
        ]

    def test_text_unit_ids_are_valid_xpath(self):
        tree = DOMTreeRepresentation(website_code=self.HTML)
        roottree = tree.root.getroottree()
        for unit in tree.get_content_units("/html/body/p"):
            if is_text_node_xpath(unit):
                (node,) = roottree.xpath(unit)
                assert node == tree.text_nodes_metadata[unit].text_node

    def test_text_unit_html_and_text(self):
        html = "<html><body><pre>  File <b>x</b>, a &lt; b  </pre></body></html>"
        tree = DOMTreeRepresentation(website_code=html)
        first, last = tree.get_content_units("/html/body/pre")[::2]
        first = tree.text_nodes_metadata[first]
        last = tree.text_nodes_metadata[last]
        assert first.text == "  File "          # whitespace kept inside <pre>
        assert last.html == ", a &lt; b  "     # escaped exactly like lxml does
        assert last.html_length == len(last.html)

    def test_control_characters_do_not_break_rendering(self):
        """lxml keeps control characters when parsing; rendering must too."""
        tree = DOMTreeRepresentation(
            website_code="<html><body><p>a\x0cb <b>x</b> c</p></body></html>"
        )
        unit = tree.get_content_units("/html/body/p")[0]
        assert tree.text_nodes_metadata[unit].html == "a\x0cb "


class TestRemovalKeepsTails:
    """Removing an element keeps the text that follows it (its tail)."""

    def test_filter_keeps_tails(self):
        html = (
            "<html><body><p>Hello <script>x()</script> world, "
            "<svg><g/></svg> icon text.</p></body></html>"
        )
        tree = DOMTreeRepresentation(
            website_code=html, tag_list_to_filter_out=["/script", "/svg"]
        )
        text = get_element_text(tree.root)
        assert "world," in text
        assert "icon text." in text
        assert "x()" not in text

    def test_delete_node_keeps_tail(self):
        html = "<html><body><p>a <b>bold</b> tail</p></body></html>"
        tree = DOMTreeRepresentation(website_code=html)
        tree.delete_node("/html/body/p/b")
        text = get_element_text(tree.root)
        assert "tail" in text
        assert "bold" not in text


class TestWholeStepMatching:
    """Filters and deletions never catch a tag whose name merely starts alike."""

    def test_filter_b_keeps_body(self):
        html = "<html><body><p>a <b>bold</b> word</p></body></html>"
        tree = DOMTreeRepresentation(website_code=html, tag_list_to_filter_out=["/b"])
        text = get_element_text(tree.root)
        assert "word" in text          # <body> survives
        assert "bold" not in text      # <b> is gone
        assert "/html/body/p" in tree.pos_xpaths_list

    def test_default_filter_keeps_custom_elements(self):
        from betterhtmlchunking.main import tag_list_to_filter_out
        html = (
            "<html><body><p>Nice <g-emoji alias='tada'>🎉</g-emoji>!</p>"
            "<svg><g><path/></g></svg></body></html>"
        )
        tree = DOMTreeRepresentation(
            website_code=html, tag_list_to_filter_out=tag_list_to_filter_out
        )
        assert "/html/body/p/g-emoji" in tree.pos_xpaths_list
        assert not any("svg" in xpath for xpath in tree.pos_xpaths_list)

    def test_filter_with_index_and_with_several_steps(self):
        html = (
            "<html><body><div>one</div><div>two</div>"
            "<aside>side</aside><main><aside>inner</aside></main></body></html>"
        )
        tree = DOMTreeRepresentation(
            website_code=html, tag_list_to_filter_out=["/div[2]", "/body/aside"]
        )
        text = get_element_text(tree.root)
        assert "one" in text and "inner" in text
        assert "two" not in text and "side" not in text

    def test_delete_node_keeps_similarly_named_siblings(self):
        from betterhtmlchunking.render_system import RenderSystem
        from betterhtmlchunking.tree_regions_system import TreeRegionsSystem
        html = (
            "<html><body><p>uno</p><pre>code <b>x</b></pre>"
            "<blockquote>cita</blockquote></body></html>"
        )
        tree = DOMTreeRepresentation(website_code=html)
        tree.delete_node("/html/body/p")
        assert "/html/body/p" not in tree.xpaths_metadata
        assert "/html/body/pre" in tree.xpaths_metadata
        assert "/html/body/pre/b" in tree.xpaths_metadata
        # Rendering used to fail with KeyError: '/html/body/pre'.
        regions = TreeRegionsSystem(tree_representation=tree, max_node_repr_length=10)
        render = RenderSystem(tree_regions_system=regions, tree_representation=tree)
        assert "code" in "\n".join(render.text_render_roi.values())
