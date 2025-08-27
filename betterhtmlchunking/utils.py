#!/usr/bin/env python3

import treelib

from betterhtmlchunking.tree_representation import DOMTreeRepresentation


def wanted_xpath(
    xpath: str,
    tag_list_to_filter_out: list[str]
        ) -> bool:
    """Check if a node should be kept based on its XPath.

    The previous implementation relied on simple substring matching which
    meant that filtering out ``"/head"`` would also remove nodes such as
    ``"/header"``.  To avoid these partial matches we compare XPath segments
    against the unwanted tags, ignoring positional indices and case.

    Parameters
    ----------
    xpath:
        The XPath of the node to evaluate.
    tag_list_to_filter_out:
        Tags or paths to exclude.  Each entry may contain multiple segments
        (e.g. ``"/html/head"``).
    """

    def _split(xpath_to_split: str) -> list[str]:
        """Return a list of lowercase tag names without positional indices."""
        return [
            segment.split("[")[0].lower()
            for segment in xpath_to_split.strip("/").split("/")
            if segment
        ]

    xpath_segments = _split(xpath)

    for tag in tag_list_to_filter_out:
        tag_segments = _split(tag)
        tag_len = len(tag_segments)
        # Slide over the xpath segments to look for an exact sequence match
        for i in range(len(xpath_segments) - tag_len + 1):
            if xpath_segments[i : i + tag_len] == tag_segments:
                return False

    return True


def remove_unwanted_tags(
    tree_representation: DOMTreeRepresentation,
    tag_list_to_filter_out: list[str]
        ):
    for pos_xpath in tree_representation.pos_xpaths_list:
        if wanted_xpath(
            xpath=pos_xpath,
            tag_list_to_filter_out=tag_list_to_filter_out
                ) is False:
            try:
                tree_representation.delete_node(pos_xpath=pos_xpath)
            except treelib.exceptions.NodeIDAbsentError:
                ...
    return tree_representation
