#!/usr/bin/env python3

from betterhtmlchunking.tree_representation import DOMTreeRepresentation
from betterhtmlchunking.logging_config import get_logger

# Module logger
logger = get_logger("utils")


def wanted_xpath(
    xpath: str,
    tag_list_to_filter_out: list[str]
        ) -> bool:
    """Check if an xpath should be kept based on filter list."""
    # Check if any of the unwanted tags are present in the given XPath
    return not any(tag in xpath for tag in tag_list_to_filter_out)


def remove_unwanted_tags(
    tree_representation: DOMTreeRepresentation,
    tag_list_to_filter_out: list[str]
        ):
    """Remove nodes matching tags in the filter list.

    Single pass: every unwanted element is detached from the lxml tree in one
    go, then the representation is recomputed once. This avoids deleting node
    by node and re-sorting the entire xpath list on each removal (O(K*N log N)).
    """
    logger.debug(f"Filtering unwanted tags: {tag_list_to_filter_out}")

    total_nodes = len(tree_representation.pos_xpaths_list)
    removed_count = 0

    for pos_xpath in tree_representation.pos_xpaths_list:
        if wanted_xpath(
            xpath=pos_xpath,
            tag_list_to_filter_out=tag_list_to_filter_out
                ) is False:
            element = tree_representation.xpaths_metadata[pos_xpath].lxml_elem
            parent = element.getparent()
            if parent is not None:
                parent.remove(element)
                removed_count += 1

    # Rebuild the tree/xpaths once from the pruned lxml tree.
    tree_representation.recompute_representation()

    logger.info(f"Filtered {removed_count} unwanted nodes out of {total_nodes} total")
    return tree_representation
