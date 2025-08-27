import betterhtmlchunking.tree_representation as tr
from betterhtmlchunking.tree_regions_system import TreeRegionsSystem


def test_root_selection_without_html_tag():
    html = "<div><p>Hello World</p></div>"
    dom_tree = tr.DOMTreeRepresentation(website_code=html)

    trs = TreeRegionsSystem(
        tree_representation=dom_tree,
        max_node_repr_length=200,
    )

    assert trs.sorted_roi_by_pos_xpath, "ROI list should not be empty"

    first_pos_xpath = dom_tree.pos_xpaths_list[0]
    first_roi = trs.sorted_roi_by_pos_xpath[0]

    assert first_roi.pos_xpath_list[0] == first_pos_xpath
