#!/usr/bin/env python3

from betterhtmlchunking.utils import wanted_xpath
from betterhtmlchunking.utils import remove_unwanted_tags
from betterhtmlchunking.tree_representation import DOMTreeRepresentation


class TestWantedXPath:
    """Tests for wanted_xpath function."""

    def test_wanted_xpath_with_allowed_tag(self):
        """Test that allowed tags return True."""
        xpath = "/html/body/div"
        tag_list = ["/head", "/script"]
        assert wanted_xpath(xpath, tag_list) is True

    def test_wanted_xpath_with_filtered_tag(self):
        """Test that filtered tags return False."""
        xpath = "/html/head/title"
        tag_list = ["/head", "/script"]
        assert wanted_xpath(xpath, tag_list) is False

    def test_wanted_xpath_with_multiple_filtered_tags(self):
        """Test filtering with multiple unwanted tags."""
        xpath = "/html/body/script"
        tag_list = ["/head", "/script", "/style"]
        assert wanted_xpath(xpath, tag_list) is False

    def test_wanted_xpath_with_empty_filter_list(self):
        """Test that empty filter list allows all tags."""
        xpath = "/html/body/div"
        tag_list = []
        assert wanted_xpath(xpath, tag_list) is True


class TestRemoveUnwantedTags:
    """Tests for remove_unwanted_tags function."""

    def test_remove_script_tags(self):
        """Test removing script tags from tree."""
        html = "<html><body><div>Content</div><script>alert('test')</script></body></html>"
        tree = DOMTreeRepresentation(website_code=html)

        filtered_tree = remove_unwanted_tags(
            tree_representation=tree,
            tag_list_to_filter_out=["/script"]
        )

        # Check that script tag is removed
        xpath_strings = [
            node.identifier for node in filtered_tree.tree.all_nodes()
        ]
        assert not any("/script" in xpath for xpath in xpath_strings)

    def test_remove_multiple_tag_types(self):
        """Test removing multiple tag types."""
        html = "<html><head><title>Test</title></head><body><div>Content</div></body></html>"
        tree = DOMTreeRepresentation(website_code=html)

        filtered_tree = remove_unwanted_tags(
            tree_representation=tree,
            tag_list_to_filter_out=["/head", "/title"]
        )

        xpath_strings = [
            node.identifier for node in filtered_tree.tree.all_nodes()
        ]
        assert not any("/head" in xpath for xpath in xpath_strings)
        assert not any("/title" in xpath for xpath in xpath_strings)

    def test_remove_unwanted_tags_preserves_wanted_content(self):
        """Test that wanted content is preserved after filtering."""
        html = "<html><body><div>Keep this</div><script>Remove this</script></body></html>"
        tree = DOMTreeRepresentation(website_code=html)

        filtered_tree = remove_unwanted_tags(
            tree_representation=tree,
            tag_list_to_filter_out=["/script"]
        )

        xpath_strings = [node.identifier for node in filtered_tree.tree.all_nodes()]
        assert any("/div" in xpath for xpath in xpath_strings)
