#!/usr/bin/env python3

import attrs
from attrs_strict import type_validator

import parsel_text
from parsel import Selector

import lxml.html
import lxml.etree

import treelib

import functools
import html

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


# XPath step of the k-th text node child of an element, as in
# "/html/body/p/text()[2]". Text nodes are not elements, so they have no entry
# in ``xpaths_metadata``; they are kept in ``text_nodes_metadata`` instead.
TEXT_NODE_STEP = "/text()["


def is_text_node_xpath(xpath: str) -> bool:
    return TEXT_NODE_STEP in xpath


def split_text_node_xpath(xpath: str) -> tuple[str, int]:
    """Split "/html/body/p/text()[2]" into ("/html/body/p", 2)."""
    parent_xpath, _, index = xpath.rpartition(TEXT_NODE_STEP)
    return parent_xpath, int(index[:-1])


def render_text_node_html(text_node: str) -> str:
    """Serialise a text node as HTML, byte-identical to lxml's own output.

    lxml only escapes ``&``, ``<`` and ``>`` in text content. Assigning the
    text to a temporary element and serialising it would not work: lxml
    refuses control characters on assignment, although its parser keeps them.
    """
    return html.escape(text_node, quote=False)


def get_text_node_text(text_node, fix_mojibake: bool = True) -> str:
    """Normalised text of one lxml text node, following parsel_text's rules.

    The lxml node itself is the Selector root on purpose: it is a "smart
    string" that knows its parent, so parsel_text can apply the <pre> and
    <script> rules. Through ``Selector.xpath("text()")`` parsel would return
    a plain str instead, and that context would be lost.
    """
    return parsel_text.get_selector_text(
        Selector(root=text_node), fix_mojibake=fix_mojibake
    )


def get_last_element(element):
    """Last element of ``element``'s subtree in document order."""
    while True:
        for child in reversed(element):
            if isinstance(child.tag, str):
                element = child
                break
        else:
            return element


def reject_lone_surrogates(instance, attribute, value: str) -> None:
    """attrs validator: refuse text that lxml would silently truncate.

    lxml stops parsing at the first lone surrogate (U+D800 to U+DFFF) and
    drops the rest of the document without raising. These code points usually
    come from bytes decoded with ``errors="surrogateescape"``, which is how
    ``sys.stdin`` decodes by default since Python 3.15 (PEP 686). Encoding to
    UTF-8 fails exactly on them, and is much faster than a regex scan.
    """
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError(
            f"{attribute.name} contains a lone surrogate "
            f"(U+{ord(value[exc.start]):04X}) at index {exc.start}; lxml "
            "would silently drop everything after it. This usually means the "
            'bytes were decoded with errors="surrogateescape": decode them '
            "with the document's real encoding instead."
        ) from None


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
class TextNodeMetadata:
    """A non-blank text node directly inside an element.

    It is the element's own ``.text`` or the ``.tail`` of one of its children.
    When an element is split into regions, each such node is a content unit
    of its own (next to the element children), addressed by its standard
    XPath ``<element xpath>/text()[k]``, so no text is left out of the chunks.
    """
    # The lxml "smart string": it knows its parent element.
    text_node: Any = attrs.field(
        validator=type_validator()
    )
    # Last element that starts before this text node in document order. It
    # places regions that begin with a text node when they are sorted.
    preceding_xpath: str = attrs.field(
        validator=type_validator()
    )
    fix_mojibake: bool = attrs.field(
        validator=type_validator(),
        default=True
    )

    @functools.cached_property
    def html(self) -> str:
        return render_text_node_html(self.text_node)

    @functools.cached_property
    def text(self) -> str:
        return get_text_node_text(self.text_node, fix_mojibake=self.fix_mojibake)

    @property
    def html_length(self) -> int:
        return len(self.html)

    @property
    def text_length(self) -> int:
        return len(self.text)


@attrs.define(on_setattr=attrs.setters.NO_OP)
class DOMTreeRepresentation:
    website_code: str = attrs.field(
        validator=[type_validator(), reject_lone_surrogates]
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
    # Filled lazily by get_content_units(), only for the elements the
    # chunker splits.
    text_nodes_metadata: dict[str, TextNodeMetadata] = attrs.field(
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
        after node-by-node deletion). ``drop_tree()`` keeps each removed
        element's tail (the text after it, which belongs to the parent);
        ``parent.remove()`` would drop that text together with the element.
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
            if element.getparent() is not None:
                element.drop_tree()

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
        self.text_nodes_metadata: dict[str, TextNodeMetadata] = {}

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

    def get_content_units(self, xpath: str) -> list[str]:
        """Contents of an element as chunkable units, in document order.

        Element children are listed by their positional xpath, and non-blank
        text nodes (the element's ``.text`` and each child's ``.tail``) by
        their text-node XPath ``<xpath>/text()[k]``, registering them in
        ``text_nodes_metadata``. Whitespace-only text nodes carry no content
        and are skipped.
        """
        element = self.xpaths_metadata[xpath].lxml_elem
        roottree = element.getroottree()
        # One entry per non-empty .text/.tail, in document order.
        text_nodes = iter(element.xpath("text()"))
        units: list[str] = []
        position = 0

        def add_text_node(after) -> None:
            nonlocal position
            text_node = next(text_nodes)
            position += 1
            if not text_node.strip():
                return
            text_xpath = f"{xpath}{TEXT_NODE_STEP}{position}]"
            if text_xpath not in self.text_nodes_metadata:
                preceding = (
                    xpath if after is None
                    else roottree.getpath(get_last_element(after))
                )
                self.text_nodes_metadata[text_xpath] = TextNodeMetadata(
                    text_node=text_node,
                    preceding_xpath=preceding,
                    fix_mojibake=self.fix_mojibake,
                )
            units.append(text_xpath)

        if element.text:
            add_text_node(after=None)
        # Last element child seen so far: the tail of a comment follows it.
        last_child = None
        for child in element:
            if isinstance(child.tag, str):
                units.append(roottree.getpath(child))
                last_child = child
            if child.tail:
                add_text_node(after=last_child)
        return units

    def delete_node(self, pos_xpath: str) -> None:
        """Delete a node from the tree and all associated metadata."""
        logger.debug(f"Deleting node: {pos_xpath}")

        # Delete on treelib.Tree:
        self.tree.remove_node(pos_xpath)

        # Delete on the lxml tree (removes the element and its subtree, but
        # keeps its tail, which belongs to the parent):
        element = self.xpaths_metadata[pos_xpath].lxml_elem
        if element.getparent() is not None:
            element.drop_tree()
        # Text node positions inside the parent may have shifted.
        self.text_nodes_metadata = {}

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
