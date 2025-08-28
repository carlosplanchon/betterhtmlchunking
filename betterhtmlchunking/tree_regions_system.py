#!/usr/bin/env python3

import attrs

from attrs_strict import type_validator

import queue
import warnings

import treelib

from betterhtmlchunking.tree_representation import\
    DOMTreeRepresentation
from betterhtmlchunking.tree_representation import\
    get_xpath_depth

from enum import StrEnum

from typing import Iterator
from typing import Any
from typing import Optional

# import prettyprinter


#################################
#                               #
#   --- TreeRegionsSystem ---   #
#                               #
#################################

class ROIParsingState(StrEnum):
    SEEK_END: str = "seek_end"
    REGION_READY: str = "region_ready"
    EOF: str = "EOF"


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

    PARSING_STATE: ROIParsingState = attrs.field(
        validator=type_validator(),
        default=ROIParsingState.SEEK_END
    )
    children_tags_iter: Iterator[str] = attrs.field(
        validator=type_validator(),
        init=False
    )
    actual_region_of_interest: Any = attrs.field(
        validator=type_validator(),
        init=False
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
        # print(f"> ROIMaker: Node XPATH: {self.node_xpath}")

        self.regions_of_interest_list: list[RegionOfInterest] = []
        self.children_to_enqueue: list[str] = []
        self.actual_region_of_interest = RegionOfInterest()

        # Explore for ROIs on children.
        self.children_tags_iter = iter(self.children_tags)

        self.actual_region_of_interest.node_is_roi = False

        self.step()
        while self.PARSING_STATE != ROIParsingState.EOF:
            self.step()

        # If no region was finalized but some nodes were gathered, ensure
        # this collected region is not lost.
        if (
            len(self.regions_of_interest_list) == 0
            and self.actual_region_of_interest.pos_xpath_list != []
        ):
            self.regions_of_interest_list.append(self.actual_region_of_interest)

        node_is_roi: bool = False
        node_repr_length: Optional[int] = None
        if len(self.children_tags) == 0:
            node_is_roi = True
            node = self.tree_representation.tree.get_node(
                nid=self.node_xpath
            )
            node_repr_length = self.get_node_repr_length(node=node)
            if node_repr_length > self.max_node_repr_length:
                warnings.warn(
                    (
                        f"Leaf node '{self.node_xpath}' has length "
                        f"{node_repr_length} which exceeds the maximum "
                        f"allowed ({self.max_node_repr_length}). "
                        "Consider splitting the text or increasing the limit."
                    )
                )
        elif len(self.regions_of_interest_list) == 1:
            roi = self.regions_of_interest_list[0]
            if len(roi.pos_xpath_list) == len(self.children_tags):
                node_is_roi = True

        # Node itself is ROI.
        if node_is_roi is True:
            # print(f"> Node itself is ROI: {self.node_xpath}")
            if node_repr_length is None:
                node: treelib.Node = self.tree_representation.tree.get_node(
                    nid=self.node_xpath
                )
                node_repr_length = self.get_node_repr_length(node=node)

            # prettyprinter.cpprint(node_repr_length)

            # if node_repr_length > self.max_node_repr_length:
            self.actual_region_of_interest.repr_length =\
                node_repr_length
            self.actual_region_of_interest.pos_xpath_list.append(
                self.node_xpath
            )
            self.actual_region_of_interest.node_is_roi = True

            self.regions_of_interest_list = []

            self.regions_of_interest_list.append(
                self.actual_region_of_interest
            )

        return None

    def get_node_repr_length(self, node: treelib.Node) -> int:
        match self.repr_length_compared_by:
            case ReprLengthComparisionBy.TEXT_LENGTH:
                node_repr_length: int = node.data.text_length
            case ReprLengthComparisionBy.HTML_LENGTH:
                node_repr_length: int = node.data.html_length

        return node_repr_length

    # Based on XMLStreamer.
    def step(self):
        match self.PARSING_STATE:
            case ROIParsingState.SEEK_END:
                # print("> SEEK END:")
                try:
                    children_tag: str = next(self.children_tags_iter)
                    # print(f"children_tag: {children_tag}")
                    node: treelib.Node =\
                        self.tree_representation.tree.get_node(
                            nid=children_tag
                        )

                    node_repr_length: int = self.get_node_repr_length(
                        node=node
                    )
                    # print(f"node_repr_length: {node_repr_length}")

                    if node_repr_length >= self.max_node_repr_length:
                        self.PARSING_STATE = ROIParsingState.REGION_READY
                        self.children_to_enqueue.append(children_tag)
                    else:
                        proposed_repr_length: int = node_repr_length +\
                            self.actual_region_of_interest.repr_length

                        # print(f"proposed_repr_length: {proposed_repr_length}")

                        self.actual_region_of_interest.pos_xpath_list.append(
                            node.identifier
                        )
                        self.actual_region_of_interest.repr_length =\
                            proposed_repr_length

                        if proposed_repr_length >= self.max_node_repr_length:
                            self.PARSING_STATE = ROIParsingState.REGION_READY

                except StopIteration:
                    self.PARSING_STATE = ROIParsingState.EOF
                    # print("StopIteration.")
                    # prettyprinter.cpprint(self.actual_region_of_interest)
                    if self.actual_region_of_interest.repr_length > 0 and\
                            len(self.regions_of_interest_list) > 0:
                        # print("Hanging xpaths.")
                        self.regions_of_interest_list[-1].repr_length +=\
                            self.actual_region_of_interest.repr_length
                        self.regions_of_interest_list[-1].pos_xpath_list +=\
                            self.actual_region_of_interest.pos_xpath_list
                        self.actual_region_of_interest = RegionOfInterest()

            case ROIParsingState.REGION_READY:
                # print("> REGION READY:")
                self.regions_of_interest_list.append(
                    self.actual_region_of_interest
                )

                self.PARSING_STATE = ROIParsingState.SEEK_END
                self.actual_region_of_interest = RegionOfInterest()


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

    def print_tree_node_states(self):
        print("--- PRINT TREE NODE STATES ---")
        for pos_xpath in self.tree_representation.pos_xpaths_list:
            pad: str = get_xpath_depth(xpath=pos_xpath) * " " * 4
            node = self.tree_representation.tree.get_node(pos_xpath)
            print(f"{pad}|")
            print(f"{pad}| {pos_xpath}")
            print(f"{pad}| Text length: {node.data.text_length}")
            print(f"{pad}| HTML length: {node.data.html_length}")

    def get_node_repr_length(self, node: treelib.Node) -> int:
        match self.repr_length_compared_by:
            case ReprLengthComparisionBy.TEXT_LENGTH:
                node_repr_length: int = node.data.text_length
            case ReprLengthComparisionBy.HTML_LENGTH:
                node_repr_length: int = node.data.html_length

        return node_repr_length

    def start(self):
        self.regions_of_interest_list: list[RegionOfInterest] = []

        subtrees_queue = queue.Queue()

        if self.root_xpath is not None:
            root_xpath = self.root_xpath
        elif "/html" in self.tree_representation.pos_xpaths_list:
            root_xpath = "/html"
        elif self.tree_representation.pos_xpaths_list:
            root_xpath = self.tree_representation.pos_xpaths_list[0]
        else:
            self.sorted_roi_by_pos_xpath = {}
            return

        subtrees_queue.put(root_xpath)

        while subtrees_queue.empty() is False:
            # print("#" * 100)
            node_xpath: str = subtrees_queue.get()
            # print("--- NODE XPATH ---")
            # print(node_xpath)

            node: treelib.Node = self.tree_representation.tree.get_node(
                node_xpath
            )
            # print(node.data.text_length)

            children_tags: list[str] =\
                self.tree_representation.get_children_tag_list(
                    xpath=node_xpath
                )

            region_of_interest_maker = ROIMaker(
                node_xpath=node_xpath,
                children_tags=children_tags,
                tree_representation=self.tree_representation,
                max_node_repr_length=self.max_node_repr_length,
                repr_length_compared_by=self.repr_length_compared_by
            )

            # print("--- REGIONS OF INTEREST LIST ---")
            # prettyprinter.cpprint(region_of_interest_maker.regions_of_interest_list)

            for roi in region_of_interest_maker.regions_of_interest_list:
                # If we are based on text_length,
                # tags like img (text_length == 0) are ignored.
                # For that reason we base ROI on pos_xpath_list.
                # if roi.text_length > 0:
                if roi.pos_xpath_list != []:
                    self.regions_of_interest_list.append(roi)

            # print("--- CHILDREN TO ENQUEUE ---")
            # prettyprinter.cpprint(region_of_interest_maker.children_to_enqueue)

            """
            Try to make ROIs under.
            If ROI occupy all children, ROI contains node itself.

            Those elements who are not ROI, are put into queue.
            Elements who are ROI, are put into a separate dict.
            """

            for child_tag in region_of_interest_maker.children_to_enqueue:
                subtrees_queue.put(child_tag)

            """
            for child_tag in children_tags:
                subtrees_queue.put(child_tag)
            """

        sorted_regions: list[RegionOfInterest] =\
            order_regions_of_interest_by_pos_xpath(
                region_of_interest_list=\
                self.regions_of_interest_list,
                pos_xpaths_list=\
                self.tree_representation.pos_xpaths_list
            )

        # This happen when there are no nodes to detect as RegionOfInterest
        # or when max_node_repr_length is greater than total repr_length in
        # the document.
        if sorted_regions == [] and\
                len(self.tree_representation.pos_xpaths_list) > 0:
            node_xpath: str = self.tree_representation.pos_xpaths_list[0]

            node: treelib.Node = self.tree_representation.tree.get_node(
                node_xpath
            )

            node_repr_length: int = self.get_node_repr_length(
                node=node
            )
            # print(node_repr_length)

            roi = RegionOfInterest()
            roi.pos_xpath_list = [node_xpath]
            roi.repr_length = node_repr_length
            roi.node_is_roi = True

            sorted_regions = [roi]

        self.sorted_roi_by_pos_xpath = dict(enumerate(sorted_regions))
