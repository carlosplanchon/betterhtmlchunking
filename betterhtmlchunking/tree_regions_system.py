#!/usr/bin/env python3

import attrs

from attrs_strict import type_validator

import queue

import treelib

from betterhtmlchunking.tree_representation import\
    DOMTreeRepresentation
from betterhtmlchunking.tree_representation import\
    get_xpath_depth
from betterhtmlchunking.logging_config import get_logger

from enum import StrEnum

from typing import Optional

# Module logger
logger = get_logger("tree_regions_system")


#################################
#                               #
#   --- TreeRegionsSystem ---   #
#                               #
#################################

@attrs.define()
class RegionOfInterest:
    pos_xpath_list: list[str] = attrs.field(
        validator=type_validator(),
        init=False
    )
    repr_length: int = attrs.field(
        validator=type_validator(),
        init=False
    )
    node_is_roi: bool = attrs.field(
        validator=type_validator(),
        init=False
    )

    def __attrs_post_init__(self):
        self.pos_xpath_list: list[str] = []
        self.repr_length: int = 0
        self.node_is_roi: bool = False


class ReprLengthComparisionBy(StrEnum):
    TEXT_LENGTH: str = "text_length"
    HTML_LENGTH: str = "html_length"


@attrs.define()
class ROIMaker:
    node_xpath: str = attrs.field(
        validator=type_validator()
    )
    children_tags: list[str] = attrs.field(
        validator=type_validator()
    )
    tree_representation: DOMTreeRepresentation = attrs.field(
        validator=type_validator()
    )
    max_node_repr_length: int = attrs.field(
        validator=type_validator()
    )
    repr_length_compared_by: ReprLengthComparisionBy = attrs.field(
        validator=type_validator(),
    )

    regions_of_interest_list: list[RegionOfInterest] = attrs.field(
        validator=type_validator(),
        init=False
    )
    children_to_enqueue: list[str] = attrs.field(
        validator=type_validator(),
        init=False
    )

    def __attrs_post_init__(self) -> None:
        self.regions_of_interest_list: list[RegionOfInterest] = []
        self.children_to_enqueue: list[str] = []

        # Process children and group them into regions
        self._process_children()

        # Check if the node itself should be an ROI
        self._check_node_as_roi()

    def get_node_repr_length(self, node: treelib.Node) -> int:
        """Get the representation length of a node based on comparison mode."""
        match self.repr_length_compared_by:
            case ReprLengthComparisionBy.TEXT_LENGTH:
                return node.data.text_length
            case ReprLengthComparisionBy.HTML_LENGTH:
                return node.data.html_length

    def _process_children(self) -> None:
        """Group children into regions that don't exceed max_node_repr_length."""
        if not self.children_tags:
            return

        current_region = RegionOfInterest()

        for child_xpath in self.children_tags:
            node = self.tree_representation.tree.get_node(nid=child_xpath)
            node_length = self.get_node_repr_length(node=node)

            # If node itself is too large, needs separate processing
            if node_length >= self.max_node_repr_length:
                # Close current region if it has content
                if current_region.pos_xpath_list:
                    self.regions_of_interest_list.append(current_region)
                    current_region = RegionOfInterest()
                # Mark child for deeper processing
                self.children_to_enqueue.append(child_xpath)
                continue

            # Check if adding this node would exceed the limit
            proposed_length = current_region.repr_length + node_length

            if proposed_length >= self.max_node_repr_length:
                # Close current region
                if current_region.pos_xpath_list:
                    self.regions_of_interest_list.append(current_region)
                    current_region = RegionOfInterest()

            # Add node to current region
            current_region.pos_xpath_list.append(child_xpath)
            current_region.repr_length += node_length

        # Handle remaining content in current region
        if current_region.pos_xpath_list:
            if self.regions_of_interest_list:
                # Merge with last region
                self.regions_of_interest_list[-1].pos_xpath_list += current_region.pos_xpath_list
                self.regions_of_interest_list[-1].repr_length += current_region.repr_length
            else:
                # First and only region
                self.regions_of_interest_list.append(current_region)

    def _check_node_as_roi(self) -> None:
        """Check if the node itself should be treated as a single ROI."""
        node_is_roi = False

        # Node is ROI if it has no children
        if not self.children_tags:
            node_is_roi = True
        # Node is ROI if all children fit in a single region
        elif len(self.regions_of_interest_list) == 1:
            roi = self.regions_of_interest_list[0]
            if len(roi.pos_xpath_list) == len(self.children_tags):
                node_is_roi = True

        if node_is_roi:
            node = self.tree_representation.tree.get_node(nid=self.node_xpath)
            node_repr_length = self.get_node_repr_length(node=node)

            # Create a single ROI for the entire node
            single_roi = RegionOfInterest()
            single_roi.repr_length = node_repr_length
            single_roi.pos_xpath_list.append(self.node_xpath)
            single_roi.node_is_roi = True

            self.regions_of_interest_list = [single_roi]


def order_regions_of_interest_by_pos_xpath(
    region_of_interest_list: list[RegionOfInterest],
    pos_xpaths_list: list[str]
        ) -> list[RegionOfInterest]:
    # Create a mapping of xpath to its index in pos_xpaths_list
    xpath_order = {
        xpath: index for index, xpath in enumerate(pos_xpaths_list)
    }

    # Sort the region_of_interest_list
    # based on the first pos_xpath_list entry for each region.
    sorted_regions = sorted(
        region_of_interest_list,
        key=lambda region: xpath_order.get(
            region.pos_xpath_list[0],
            float("inf")
        )
    )

    return sorted_regions


@attrs.define()
class TreeRegionsSystem:
    tree_representation: DOMTreeRepresentation = attrs.field(
        validator=type_validator()
    )
    max_node_repr_length: int = attrs.field(
        validator=type_validator()
    )
    root_xpath: Optional[str] = attrs.field(
        validator=type_validator(),
        default=None
    )
    regions_of_interest_list: list[RegionOfInterest] = attrs.field(
        validator=type_validator(),
        init=False
    )
    sorted_roi_by_pos_xpath: dict[int, RegionOfInterest] = attrs.field(
        validator=type_validator(),
        init=False
    )
    repr_length_compared_by: ReprLengthComparisionBy = attrs.field(
        validator=type_validator(),
        default=ReprLengthComparisionBy.HTML_LENGTH
    )

    def __attrs_post_init__(self):
        self.start()

    def log_tree_node_states(self):
        """Log detailed information about all tree nodes (DEBUG level)."""
        logger.debug("--- TREE NODE STATES ---")
        for pos_xpath in self.tree_representation.pos_xpaths_list:
            pad: str = get_xpath_depth(xpath=pos_xpath) * " " * 4
            node = self.tree_representation.tree.get_node(pos_xpath)
            logger.debug(f"{pad}|")
            logger.debug(f"{pad}| {pos_xpath}")
            logger.debug(f"{pad}| Text length: {node.data.text_length}")
            logger.debug(f"{pad}| HTML length: {node.data.html_length}")

    def get_node_repr_length(self, node: treelib.Node) -> int:
        match self.repr_length_compared_by:
            case ReprLengthComparisionBy.TEXT_LENGTH:
                node_repr_length: int = node.data.text_length
            case ReprLengthComparisionBy.HTML_LENGTH:
                node_repr_length: int = node.data.html_length

        return node_repr_length

    def start(self):
        """Process the DOM tree and identify regions of interest."""
        logger.debug("Starting tree regions system processing")
        self.regions_of_interest_list: list[RegionOfInterest] = []

        subtrees_queue = queue.Queue()

        if self.root_xpath is not None:
            root_xpath = self.root_xpath
        elif "/html" in self.tree_representation.pos_xpaths_list:
            root_xpath = "/html"
        elif self.tree_representation.pos_xpaths_list:
            root_xpath = self.tree_representation.pos_xpaths_list[0]
        else:
            logger.warning("No nodes found in tree representation")
            self.sorted_roi_by_pos_xpath = {}
            return

        logger.debug(f"Starting from root xpath: {root_xpath}")
        subtrees_queue.put(root_xpath)

        nodes_processed = 0
        while subtrees_queue.empty() is False:
            node_xpath: str = subtrees_queue.get()
            nodes_processed += 1
            logger.debug(f"Processing node [{nodes_processed}]: {node_xpath}")

            node: treelib.Node = self.tree_representation.tree.get_node(
                node_xpath
            )

            children_tags: list[str] =\
                self.tree_representation.get_children_tag_list(
                    xpath=node_xpath
                )
            logger.debug(f"Node has {len(children_tags)} children")

            region_of_interest_maker = ROIMaker(
                node_xpath=node_xpath,
                children_tags=children_tags,
                tree_representation=self.tree_representation,
                max_node_repr_length=self.max_node_repr_length,
                repr_length_compared_by=self.repr_length_compared_by
            )

            logger.debug(
                f"ROIMaker created {len(region_of_interest_maker.regions_of_interest_list)} ROIs "
                f"and {len(region_of_interest_maker.children_to_enqueue)} children to enqueue"
            )

            for roi in region_of_interest_maker.regions_of_interest_list:
                # If we are based on text_length,
                # tags like img (text_length == 0) are ignored.
                # For that reason we base ROI on pos_xpath_list.
                if roi.pos_xpath_list != []:
                    self.regions_of_interest_list.append(roi)

            # Enqueue children that need deeper processing
            for child_tag in region_of_interest_maker.children_to_enqueue:
                subtrees_queue.put(child_tag)

        logger.debug(f"Processed {nodes_processed} nodes total")
        logger.info(f"Found {len(self.regions_of_interest_list)} regions of interest")

        sorted_regions: list[RegionOfInterest] =\
            order_regions_of_interest_by_pos_xpath(
                region_of_interest_list=\
                self.regions_of_interest_list,
                pos_xpaths_list=\
                self.tree_representation.pos_xpaths_list
            )

        # This happens when there are no nodes to detect as RegionOfInterest
        # or when max_node_repr_length is greater than total repr_length in
        # the document.
        if sorted_regions == [] and\
                len(self.tree_representation.pos_xpaths_list) > 0:
            logger.info(
                "No ROIs found with current settings, using entire document as single ROI"
            )
            node_xpath: str = self.tree_representation.pos_xpaths_list[0]

            node: treelib.Node = self.tree_representation.tree.get_node(
                node_xpath
            )

            node_repr_length: int = self.get_node_repr_length(
                node=node
            )

            roi = RegionOfInterest()
            roi.pos_xpath_list = [node_xpath]
            roi.repr_length = node_repr_length
            roi.node_is_roi = True

            sorted_regions = [roi]

        self.sorted_roi_by_pos_xpath = dict(enumerate(sorted_regions))
        logger.info(f"Created {len(self.sorted_roi_by_pos_xpath)} final sorted chunks")
