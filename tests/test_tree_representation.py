#!/usr/bin/env python3

from betterhtmlchunking.tree_representation import DOMTreeRepresentation
from betterhtmlchunking.tree_representation import get_xpath_depth


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
