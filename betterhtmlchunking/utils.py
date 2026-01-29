#!/usr/bin/env python3

import treelib

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
    """Remove nodes matching tags in the filter list."""
    logger.debug(f"Filtering unwanted tags: {tag_list_to_filter_out}")

    total_nodes = len(tree_representation.pos_xpaths_list)
    removed_count = 0

    for pos_xpath in tree_representation.pos_xpaths_list:
        if wanted_xpath(
            xpath=pos_xpath,
            tag_list_to_filter_out=tag_list_to_filter_out
                ) is False:
            try:
                tree_representation.delete_node(pos_xpath=pos_xpath)
                removed_count += 1
            except treelib.exceptions.NodeIDAbsentError:
                logger.debug(f"Node already removed: {pos_xpath}")

    logger.info(f"Filtered {removed_count} unwanted nodes out of {total_nodes} total")
    return tree_representation
