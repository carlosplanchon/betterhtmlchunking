#!/usr/bin/env python3

import attrs

from attrs_strict import type_validator

import parsel_text

from betterhtmlchunking.tree_representation import\
    DOMTreeRepresentation

from betterhtmlchunking.tree_regions_system import\
    TreeRegionsSystem

from betterhtmlchunking.logging_config import get_logger

# Module logger
logger = get_logger("render_system")


RegionOfInterestRenderT = dict[int, str]


@attrs.define()
class RenderSystem:
    tree_regions_system: TreeRegionsSystem = attrs.field(
        validator=type_validator()
    )
    tree_representation: DOMTreeRepresentation = attrs.field(
        validator=type_validator()
    )

    html_render_with_pos_xpath: dict[int, RegionOfInterestRenderT] =\
        attrs.field(
            validator=type_validator(),
            init=False
        )
    text_render_with_pos_xpath: dict[int, RegionOfInterestRenderT] =\
        attrs.field(
            validator=type_validator(),
            init=False
        )

    # Render of the regions of interest, each one of them full:
    html_render_roi: dict[int, str] = attrs.field(
        validator=type_validator(),
        init=False
    )
    text_render_roi: dict[int, str] = attrs.field(
        validator=type_validator(),
        init=False
    )

    def get_roi_text_render_with_pos_xpath(self, roi_idx: int) -> str:
        return "\n".join(
            self.text_render_with_pos_xpath[roi_idx].values()
        )

    def get_roi_html_render_with_pos_xpath(self, roi_idx: int) -> str:
        return "\n".join(
            self.html_render_with_pos_xpath[roi_idx].values()
        )

    def render(self) -> None:
        """Render HTML and text output for all regions of interest."""
        logger.debug("Starting render process")

        self.html_render_with_pos_xpath: dict[
            int, RegionOfInterestRenderT] = {}
        self.text_render_with_pos_xpath: dict[
            int, RegionOfInterestRenderT] = {}

        self.html_render_roi: dict[int, str] = {}
        self.text_render_roi: dict[int, str] = {}

        total_rois = len(self.tree_regions_system.sorted_roi_by_pos_xpath)
        logger.info(f"Rendering {total_rois} regions of interest")

        region_of_interest_idx: int = 0

        for roi_idx, roi in\
                self.tree_regions_system.sorted_roi_by_pos_xpath.items():
            logger.debug(f"Rendering ROI {roi_idx} with {len(roi.pos_xpath_list)} xpaths")

            self.html_render_with_pos_xpath[roi_idx] = {}
            self.text_render_with_pos_xpath[roi_idx] = {}

            for pos_xpath in roi.pos_xpath_list:
                logger.debug(f"Processing xpath: {pos_xpath}")

                # HTML render:
                prettified_pos_xpath_html: str =\
                    self.tree_regions_system.tree_representation.xpaths_metadata[
                        pos_xpath].bs4_elem.prettify(
                            formatter="minimal"
                        )

                # Text render:
                pos_xpath_text: str =\
                    parsel_text.get_bs4_soup_text(
                        bs4_soup=self.tree_regions_system.tree_representation.xpaths_metadata[
                            pos_xpath
                        ].bs4_elem
                    )

                self.html_render_with_pos_xpath[
                    roi_idx][pos_xpath] = prettified_pos_xpath_html
                self.text_render_with_pos_xpath[
                    roi_idx][pos_xpath] = pos_xpath_text

                region_of_interest_idx += 1

            self.html_render_roi[roi_idx] =\
                self.get_roi_html_render_with_pos_xpath(
                    roi_idx=roi_idx
                )
            self.text_render_roi[roi_idx] =\
                self.get_roi_text_render_with_pos_xpath(
                    roi_idx=roi_idx
                )

            logger.debug(
                f"ROI {roi_idx} rendered: "
                f"{len(self.html_render_roi[roi_idx])} chars HTML, "
                f"{len(self.text_render_roi[roi_idx])} chars text"
            )

        logger.info(f"Render complete: {total_rois} chunks generated")

    def __attrs_post_init__(self):
        self.render()
