#!/usr/bin/env python3

import attrs
from attrs_strict import type_validator

import parsel_text
from parsel import Selector

import lxml.html
import lxml.etree

import treelib

import functools

from typing import Any, Optional

from betterhtmlchunking.logging_config import get_logger

# Module logger
logger = get_logger("tree_representation")


def get_parent_xpath(xpath: str) -> str:
    if xpath.count("/") == 1:
        return "root"
    return "/".join(xpath.split("/")[:-1])


def get_xpath_depth(xpath: str) -> int:
    xpath: str = xpath.rstrip("/")
    return xpath.count("/")


def wanted_xpath(
    xpath: str,
    tag_list_to_filter_out: list[str]
        ) -> bool:
    """Check if an xpath should be kept based on the filter list."""
    # Kept unless any of the unwanted tags appears in the xpath.
    return not any(tag in xpath for tag in tag_list_to_filter_out)


def get_children_tags(node):
    # Extract the tag names from the children of the given node
    return [child.tag for child in node]


def render_element_html(element) -> str:
    """Serialise an lxml element to HTML markup.

    Non-pretty HTML5 serialisation (no added indentation), so the length of
    the result reflects the real markup size. This same function backs both
    the ``html_length`` metric and the rendered chunk output, which keeps the
    size metric equal to what callers actually receive. ``with_tail=False``
    keeps the element's trailing text (which belongs to the parent) out of
    the element's own HTML.
    """
    return lxml.html.tostring(
        element,
        pretty_print=False,
        encoding="unicode",
        with_tail=False,
    )


def get_element_text(element, fix_mojibake: bool = True) -> str:
    """Extract normalised text from an lxml element (parsel-native).

    ``fix_mojibake`` (default True) runs the text through ``ftfy`` to repair
    mis-encoded characters. Disabling it skips ftfy and is noticeably faster
    in TEXT_LENGTH mode, at the cost of not fixing mojibake.
    """
    return parsel_text.get_xpath_text(
        Selector(root=element), ".", fix_mojibake=fix_mojibake
    )


@attrs.define(on_setattr=attrs.setters.NO_OP)
class NodeMetadata:
    idx: int = attrs.field(
        validator=type_validator(),
        init=False
    )
    lxml_elem: Any = attrs.field(
        validator=type_validator(),
        init=False
    )
    extra_metadata: Any = attrs.field(
        validator=type_validator(),
        default=None
    )
    fix_mojibake: bool = attrs.field(
        validator=type_validator(),
        default=True
    )

    # Lazy, cached size metrics: computed on first access (and only for the
    # nodes the chunker/renderer actually touch), not eagerly for every node.
    @functools.cached_property
    def text_length(self) -> int:
        return len(
            get_element_text(self.lxml_elem, fix_mojibake=self.fix_mojibake)
        )

    @functools.cached_property
    def html_length(self) -> int:
        return len(render_element_html(self.lxml_elem))


@attrs.define(on_setattr=attrs.setters.NO_OP)
class DOMTreeRepresentation:
    website_code: str = attrs.field(
        validator=type_validator()
    )
    fix_mojibake: bool = attrs.field(
        validator=type_validator(),
        default=True
    )
    tag_list_to_filter_out: Optional[list[str]] = attrs.field(
        validator=type_validator(),
        default=None
    )
    root: Any = attrs.field(
        validator=type_validator(),
        init=False
    )

    tree: treelib.Tree = attrs.field(
        validator=type_validator(),
        init=False
    )

    xpaths_metadata: dict[str, NodeMetadata] = attrs.field(
        validator=type_validator(),
        init=False
    )

    pos_xpaths_list: list[str] = attrs.field(
        validator=type_validator(),
        init=False
    )
    pos_sorted_xpaths: list[str] = attrs.field(
        validator=type_validator(),
        init=False
    )

    def __attrs_post_init__(self):
        self.start()

    def parse_html(self):
        """Parse HTML content into an lxml element tree."""
        logger.debug("Parsing HTML with lxml.html")
        try:
            self.root = lxml.html.document_fromstring(self.website_code)
        except lxml.etree.ParserError:
            # Empty / whitespace-only input: fall back to an empty document.
            self.root = lxml.html.document_fromstring("<html></html>")
        logger.debug("HTML parsing complete")

    def filter_unwanted_tags(self):
        """Prune unwanted elements directly on the lxml tree.

        Done before building the treelib tree so the structure is computed
        only once (instead of building it for every node and then rebuilding
        after node-by-node deletion).
        """
        if not self.tag_list_to_filter_out:
            return

        roottree = self.root.getroottree()
        to_remove = [
            element for element in self.root.iter()
            if isinstance(element.tag, str)
            and not wanted_xpath(
                roottree.getpath(element), self.tag_list_to_filter_out
            )
        ]

        for element in to_remove:
            parent = element.getparent()
            if parent is not None:
                parent.remove(element)

        logger.info(f"Filtered {len(to_remove)} unwanted elements")

    def compute_xpaths_data(self):
        """Compute per-element metadata (xpath + element reference).

        Text/HTML lengths are intentionally NOT computed here: they are lazy
        cached properties on ``NodeMetadata``, so only the nodes the chunker
        and renderer actually touch pay the serialisation cost.
        """
        logger.debug("Computing xpaths and metadata for all elements")

        roottree = self.root.getroottree()
        elements = [
            element for element in self.root.iter()
            if isinstance(element.tag, str)
        ]

        logger.info(f"Found {len(elements)} HTML elements to process")

        self.xpaths_metadata: dict[str, Any] = {}

        for element in elements:
            pos_xpath: str = roottree.getpath(element)

            node_metadata = NodeMetadata()
            node_metadata.lxml_elem = element
            node_metadata.fix_mojibake = self.fix_mojibake

            self.xpaths_metadata[pos_xpath] = node_metadata

        logger.debug(f"Computed metadata for {len(self.xpaths_metadata)} xpaths")

    def make_tree_representation(self):
        """Build the tree representation from xpath metadata."""
        logger.debug("Building tree representation")

        # Initialize the tree.
        self.tree = treelib.Tree()

        # Add the root node:
        self.tree.create_node(
            tag="root",
            identifier="root"
        )

        i = 0
        # Add nodes to the tree:

        for pos_xpath, node_metadata in self.xpaths_metadata.items():
            parent_xpath: str = get_parent_xpath(xpath=pos_xpath)

            node_metadata.idx = i

            self.tree.create_node(
                tag=pos_xpath,
                identifier=pos_xpath,
                parent=parent_xpath,
                data=node_metadata
            )

            i += 1

    def define_pos_xpaths_list(self):
        self.pos_xpaths_list: list[str] = list(
            self.xpaths_metadata.keys()
        )

    def sort_pos_xpaths(self):
        self.pos_sorted_xpaths: list[str] = sorted(
            self.pos_xpaths_list,
            key=get_xpath_depth,
            reverse=True
        )

    def get_children_tag_list(self, xpath: str) -> list[str]:
        children_tags: list[str] = get_children_tags(
            self.tree.children(xpath)
        )
        return children_tags

    def delete_node(self, pos_xpath: str) -> None:
        """Delete a node from the tree and all associated metadata."""
        logger.debug(f"Deleting node: {pos_xpath}")

        # Delete on treelib.Tree:
        self.tree.remove_node(pos_xpath)

        # Delete on the lxml tree (removes the element and its subtree):
        element = self.xpaths_metadata[pos_xpath].lxml_elem
        parent = element.getparent()
        if parent is not None:
            parent.remove(element)

        keys_to_remove: list[str] = [
            xpath for xpath in self.pos_xpaths_list
            if xpath.startswith(pos_xpath)
        ]

        logger.debug(f"Removing {len(keys_to_remove)} child nodes")

        # Delete on metadata all which start with pos_xpath:
        for xpath in keys_to_remove:
            del self.xpaths_metadata[xpath]

        self.define_pos_xpaths_list()
        self.sort_pos_xpaths()

        # After operating with node deletion
        # you need to recompute the representation.

    def recompute_representation(self):
        self.compute_xpaths_data()
        self.make_tree_representation()
        self.define_pos_xpaths_list()
        self.sort_pos_xpaths()

    def start(self):
        self.parse_html()
        self.filter_unwanted_tags()
        self.recompute_representation()
