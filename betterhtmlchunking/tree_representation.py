#!/usr/bin/env python3

import attrs
from attrs_strict import type_validator

import parsel_text
from parsel import Selector

import lxml.html
import lxml.etree

import treelib

from typing import Any

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


def get_element_text(element) -> str:
    """Extract normalised text from an lxml element (parsel-native)."""
    return parsel_text.get_xpath_text(Selector(root=element), ".")


@attrs.define()
class NodeMetadata:
    idx: int = attrs.field(
        validator=type_validator(),
        init=False
    )
    text_length: int = attrs.field(
        validator=type_validator(),
        init=False
    )
    html_length: int = attrs.field(
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


@attrs.define()
class DOMTreeRepresentation:
    website_code: str = attrs.field(
        validator=type_validator()
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

    def compute_xpaths_data(self):
        """Compute metadata for all elements in the HTML."""
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

            child_text: str = get_element_text(element)
            text_length: int = len(child_text)

            child_html: str = render_element_html(element)
            html_length: int = len(child_html)

            node_metadata = NodeMetadata()
            node_metadata.text_length = text_length
            node_metadata.html_length = html_length
            node_metadata.lxml_elem = element

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
        self.recompute_representation()
