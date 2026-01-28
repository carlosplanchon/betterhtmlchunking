#!/usr/bin/env python3

from betterhtmlchunking.tree_regions_system import ROIMaker
from betterhtmlchunking.tree_regions_system import RegionOfInterest
from betterhtmlchunking.tree_regions_system import TreeRegionsSystem
from betterhtmlchunking.tree_regions_system import ReprLengthComparisionBy
from betterhtmlchunking.tree_regions_system import\
    order_regions_of_interest_by_pos_xpath

from betterhtmlchunking.tree_representation import DOMTreeRepresentation


class TestRegionOfInterest:
    """Tests for RegionOfInterest class."""

    def test_roi_initialization(self):
        """Test that ROI initializes with default values."""
        roi = RegionOfInterest()
        assert roi.pos_xpath_list == []
        assert roi.repr_length == 0
        assert roi.node_is_roi is False

    def test_roi_can_store_xpaths(self):
        """Test that ROI can store xpath list."""
        roi = RegionOfInterest()
        roi.pos_xpath_list = ["/html/body/div[1]", "/html/body/div[2]"]
        roi.repr_length = 100
        assert len(roi.pos_xpath_list) == 2
        assert roi.repr_length == 100


class TestROIMaker:
    """Tests for ROIMaker class."""

    def test_roi_maker_with_empty_children(self):
        """Test ROIMaker with node that has no children."""
        html = "<html><body><div>Simple text</div></body></html>"
        tree = DOMTreeRepresentation(website_code=html)

        # Get the div node which has no children tags
        div_xpath = [x for x in tree.pos_xpaths_list if "/div" in x][0]

        roi_maker = ROIMaker(
            node_xpath=div_xpath,
            children_tags=[],
            tree_representation=tree,
            max_node_repr_length=100,
            repr_length_compared_by=ReprLengthComparisionBy.HTML_LENGTH
        )

        # Node with no children should be treated as ROI itself
        assert len(roi_maker.regions_of_interest_list) == 1
        assert roi_maker.regions_of_interest_list[0].node_is_roi is True


# ... --- TEXT LENGHT TESTING --- (is text length right?) --- ###

    def test_roi_maker_groups_small_children(self):
        """Test that ROIMaker groups small children together."""
        html = "<html><body><p>A</p><p>B</p><p>C</p></body></html>"
        tree = DOMTreeRepresentation(website_code=html)

        body_xpath = [x for x in tree.pos_xpaths_list if x.endswith("/body")][0]
        children = tree.get_children_tag_list(xpath=body_xpath)

        roi_maker = ROIMaker(
            node_xpath=body_xpath,
            children_tags=children,
            tree_representation=tree,
            max_node_repr_length=1000,  # Large enough to group all
            repr_length_compared_by=ReprLengthComparisionBy.HTML_LENGTH
        )

        # When all children fit in one region, parent node becomes the ROI
        assert len(roi_maker.regions_of_interest_list) == 1
        assert roi_maker.regions_of_interest_list[0].node_is_roi is True
        assert roi_maker.regions_of_interest_list[0].pos_xpath_list[0] == body_xpath

    def test_roi_maker_splits_large_children(self):
        """Test that ROIMaker splits when children exceed max length."""
        html = "<html><body><p>" + "A" * 100 + "</p><p>" + "B" * 100 + "</p></body></html>"
        tree = DOMTreeRepresentation(website_code=html)

        body_xpath = [x for x in tree.pos_xpaths_list if x.endswith("/body")][0]
        children = tree.get_children_tag_list(xpath=body_xpath)

        roi_maker = ROIMaker(
            node_xpath=body_xpath,
            children_tags=children,
            tree_representation=tree,
            max_node_repr_length=50,  # Small enough to split
            repr_length_compared_by=ReprLengthComparisionBy.HTML_LENGTH
        )

        # Should enqueue large children for deeper processing
        assert len(roi_maker.children_to_enqueue) >= 1

    def test_roi_maker_text_length_mode(self):
        """Test ROIMaker using text length comparison."""
        html = "<html><body><p>Short text</p></body></html>"
        tree = DOMTreeRepresentation(website_code=html)

        body_xpath = [x for x in tree.pos_xpaths_list if x.endswith("/body")][0]
        children = tree.get_children_tag_list(xpath=body_xpath)

        roi_maker = ROIMaker(
            node_xpath=body_xpath,
            children_tags=children,
            tree_representation=tree,
            max_node_repr_length=100,
            repr_length_compared_by=ReprLengthComparisionBy.TEXT_LENGTH
        )

        assert len(roi_maker.regions_of_interest_list) >= 1


class TestTreeRegionsSystem:
    """Tests for TreeRegionsSystem class."""

    def test_tree_regions_system_simple_html(self):
        """Test TreeRegionsSystem with simple HTML."""
        html = "<html><body><div>Content</div></body></html>"
        tree = DOMTreeRepresentation(website_code=html)

        regions = TreeRegionsSystem(
            tree_representation=tree,
            max_node_repr_length=100,
            repr_length_compared_by=ReprLengthComparisionBy.HTML_LENGTH
        )

        assert regions.regions_of_interest_list is not None
        assert len(regions.regions_of_interest_list) >= 1

    def test_tree_regions_system_with_custom_root(self):
        """Test TreeRegionsSystem with custom root xpath."""
        html = "<html><body><div><p>Paragraph</p></div></body></html>"
        tree = DOMTreeRepresentation(website_code=html)

        body_xpath = [x for x in tree.pos_xpaths_list if x.endswith("/body")][0]

        regions = TreeRegionsSystem(
            tree_representation=tree,
            max_node_repr_length=100,
            root_xpath=body_xpath,
            repr_length_compared_by=ReprLengthComparisionBy.HTML_LENGTH
        )

        assert len(regions.regions_of_interest_list) >= 1

    def test_tree_regions_system_multiple_sections(self):
        """Test TreeRegionsSystem with multiple content sections."""
        html = """
        <html>
            <body>
                <section><p>Section 1 with content</p></section>
                <section><p>Section 2 with content</p></section>
                <section><p>Section 3 with content</p></section>
            </body>
        </html>
        """
        tree = DOMTreeRepresentation(website_code=html)

        regions = TreeRegionsSystem(
            tree_representation=tree,
            max_node_repr_length=50,
            repr_length_compared_by=ReprLengthComparisionBy.HTML_LENGTH
        )

        assert len(regions.regions_of_interest_list) >= 1

    def test_tree_regions_system_text_length_mode(self):
        """Test TreeRegionsSystem using text length comparison."""
        html = "<html><body><p>Text content here</p></body></html>"
        tree = DOMTreeRepresentation(website_code=html)

        regions = TreeRegionsSystem(
            tree_representation=tree,
            max_node_repr_length=100,
            repr_length_compared_by=ReprLengthComparisionBy.TEXT_LENGTH
        )

        assert regions.regions_of_interest_list is not None

    def test_tree_regions_system_empty_tree(self):
        """Test TreeRegionsSystem with empty tree."""
        html = "<html></html>"
        tree = DOMTreeRepresentation(website_code=html)

        regions = TreeRegionsSystem(
            tree_representation=tree,
            max_node_repr_length=100,
            repr_length_compared_by=ReprLengthComparisionBy.HTML_LENGTH
        )

        # Should handle empty tree gracefully
        assert regions.sorted_roi_by_pos_xpath is not None

    def test_tree_regions_system_very_small_max_length(self):
        """Test TreeRegionsSystem with very small max_node_repr_length."""
        html = "<html><body><p>Content</p></body></html>"
        tree = DOMTreeRepresentation(website_code=html)

        regions = TreeRegionsSystem(
            tree_representation=tree,
            max_node_repr_length=10,
            repr_length_compared_by=ReprLengthComparisionBy.HTML_LENGTH
        )

        # Should still create at least one region
        assert len(regions.regions_of_interest_list) >= 1

    def test_tree_regions_system_very_large_max_length(self):
        """Test TreeRegionsSystem with very large max_node_repr_length."""
        html = "<html><body><p>Content 1</p><p>Content 2</p></body></html>"
        tree = DOMTreeRepresentation(website_code=html)

        regions = TreeRegionsSystem(
            tree_representation=tree,
            max_node_repr_length=100000,
            repr_length_compared_by=ReprLengthComparisionBy.HTML_LENGTH
        )

        # Should group everything into one or few regions
        assert len(regions.regions_of_interest_list) >= 1


class TestOrderRegionsOfInterestByPosXpath:
    """Tests for order_regions_of_interest_by_pos_xpath function."""

    def test_order_regions_by_xpath(self):
        """Test ordering regions by their first xpath."""
        roi1 = RegionOfInterest()
        roi1.pos_xpath_list = ["/html/body/div[2]"]

        roi2 = RegionOfInterest()
        roi2.pos_xpath_list = ["/html/body/div[1]"]

        roi3 = RegionOfInterest()
        roi3.pos_xpath_list = ["/html/body/div[3]"]

        pos_xpaths_list = ["/html/body/div[1]", "/html/body/div[2]", "/html/body/div[3]"]

        sorted_regions = order_regions_of_interest_by_pos_xpath(
            region_of_interest_list=[roi1, roi2, roi3],
            pos_xpaths_list=pos_xpaths_list
        )

        assert sorted_regions[0].pos_xpath_list[0] == "/html/body/div[1]"
        assert sorted_regions[1].pos_xpath_list[0] == "/html/body/div[2]"
        assert sorted_regions[2].pos_xpath_list[0] == "/html/body/div[3]"

    def test_order_regions_with_missing_xpath(self):
        """Test ordering when a region's xpath is not in pos_xpaths_list."""
        roi1 = RegionOfInterest()
        roi1.pos_xpath_list = ["/html/body/div[1]"]

        roi2 = RegionOfInterest()
        roi2.pos_xpath_list = ["/html/body/missing"]

        pos_xpaths_list = ["/html/body/div[1]", "/html/body/div[2]"]

        sorted_regions = order_regions_of_interest_by_pos_xpath(
            region_of_interest_list=[roi2, roi1],
            pos_xpaths_list=pos_xpaths_list
        )

        # Known xpath should come first
        assert sorted_regions[0].pos_xpath_list[0] == "/html/body/div[1]"
