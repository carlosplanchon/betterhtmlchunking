#!/usr/bin/env python3

import attrs
import html
import logging
from typing import Optional

from attrs_strict import type_validator
from betterhtmlchunking.utils import remove_unwanted_tags
from betterhtmlchunking.tree_representation import DOMTreeRepresentation
from betterhtmlchunking.tree_regions_system import (
    TreeRegionsSystem,
    ReprLengthComparisionBy,
)
from betterhtmlchunking.render_system import RenderSystem
from betterhtmlchunking.logging_config import get_logger

# Module-level logger
logger = get_logger("main")

tag_list_to_filter_out: list[str] = [
    "/head",
    "/select",
    # "/form",
    "/footer",
    "/svg",
    "/defs",
    "/g",
    "/header",
    "/script",
    "/style",
]


@attrs.define()
class DomRepresentation:
    # Input
    MAX_NODE_REPR_LENGTH: int = attrs.field(
        validator=type_validator()
    )
    website_code: str = attrs.field(
        validator=type_validator(), 
        repr=False
    )
    repr_length_compared_by: ReprLengthComparisionBy = attrs.field(
        validator=type_validator()
    )

    # Optional inputs
    tag_list_to_filter_out: Optional[list[str]] = attrs.field(
        validator=type_validator(), 
        default=None
    )
    html_unescape: bool = attrs.field(
        validator=type_validator(), 
        default=True
    )

    # Result
    tree_representation: DOMTreeRepresentation = attrs.field(
        validator=type_validator(), init=False, repr=False
    )
    tree_regions_system: TreeRegionsSystem = attrs.field(
        validator=type_validator(), init=False, repr=False
    )
    render_system: RenderSystem = attrs.field(
        validator=type_validator(), init=False, repr=False
    )

    def __attrs_post_init__(self):
        if self.tag_list_to_filter_out is None:
            self.tag_list_to_filter_out = tag_list_to_filter_out
        if self.html_unescape:
            self.website_code = html.unescape(self.website_code)

    def compute_tree_representation(self):
        self.tree_representation = DOMTreeRepresentation(
            website_code=self.website_code
        )
        self.tree_representation = remove_unwanted_tags(
            tree_representation=self.tree_representation,
            tag_list_to_filter_out=self.tag_list_to_filter_out,
        )
        self.tree_representation.recompute_representation()

    def compute_tree_regions_system(self):
        self.tree_regions_system = TreeRegionsSystem(
            tree_representation=self.tree_representation,
            max_node_repr_length=self.MAX_NODE_REPR_LENGTH,
            repr_length_compared_by=self.repr_length_compared_by,
        )

    def compute_render_system(self):
        self.render_system = RenderSystem(
            tree_regions_system=self.tree_regions_system,
            tree_representation=self.tree_representation,
        )

    def start(self, verbose: bool = False, maximal_verbose: bool = False):
        """Run the full chunking pipeline with optional verbose logging.

        Parameters
        ----------
        verbose:
            Logs high-level pipeline steps (INFO level).
        maximal_verbose:
            Logs detailed DOM, node info, ROIs, and chunk info (DEBUG level).
        """
        logger.info("Starting DOM representation processing")
        logger.info("Step 1/3: Computing tree representation")
        self.compute_tree_representation()

        if maximal_verbose:
            all_nodes = self.tree_representation.tree.all_nodes()
            logger.debug(f"Total nodes in DOM tree: {len(all_nodes)}")
            for node in all_nodes:
                if node.data is not None:
                    logger.debug(
                        f"Node XPath: {node.identifier}, "
                        f"HTML length: {node.data.html_length}, "
                        f"Text length: {node.data.text_length}"
                    )

        logger.info("Step 2/3: Computing tree regions system")
        self.compute_tree_regions_system()

        if maximal_verbose:
            roi_count = len(self.tree_regions_system.sorted_roi_by_pos_xpath)
            logger.debug(f"Total ROIs (chunks): {roi_count}")
            for idx in self.tree_regions_system.sorted_roi_by_pos_xpath:
                roi = self.tree_regions_system.sorted_roi_by_pos_xpath[idx]
                logger.debug(
                    f"ROI {idx}: HTML length {roi.repr_length}, Nodes XPaths: {roi.pos_xpath_list}"
                )

        logger.info("Step 3/3: Computing render")
        self.compute_render_system()

        if maximal_verbose:
            for idx, html_chunk in self.render_system.html_render_roi.items():
                text_chunk = self.render_system.text_render_roi.get(idx, "")
                logger.debug(
                    f"Chunk {idx}: HTML {len(html_chunk)} chars, Text {len(text_chunk)} chars"
                )

        logger.info(
            f"Processing complete: Generated {len(self.render_system.html_render_roi)} chunks"
        )
