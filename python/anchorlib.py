
"""
SSD Anchor generation for MediaPipe palm detection.
Translated from:
  mediapipe/calculators/tflite/ssd_anchors_calculator.cc

Palm detection config (192x192 input, 2016 anchors):
  - strides: [8, 8, 16, 16]  (two layers at each stride, merged per same-stride logic)
  - aspect_ratios: [1.0]
  - interpolated_scale_aspect_ratio: 1.0  -> 2 anchors/cell per layer -> 4 anchors/cell total
  - min_scale: 0.1484375, max_scale: 0.75
  - anchor_offset_x: 0.5, anchor_offset_y: 0.5
  - fixed_anchor_size: True  -> stored w/h are always 1.0
"""

import math
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SsdAnchorsOptions:
    input_size_height: int
    input_size_width: int
    min_scale: float
    max_scale: float
    num_layers: int
    strides: list[int]
    aspect_ratios: list[float]
    anchor_offset_x: float = 0.5
    anchor_offset_y: float = 0.5
    interpolated_scale_aspect_ratio: float = 1.0
    reduce_boxes_in_lowest_layer: bool = False
    fixed_anchor_size: bool = False
    feature_map_height: Optional[list[int]] = None
    feature_map_width: Optional[list[int]] = None


@dataclass
class Anchor:
    x_center: float
    y_center: float
    w: float
    h: float

    def __repr__(self):
        return (f"Anchor(x={self.x_center:.4f}, y={self.y_center:.4f}, "
                f"w={self.w:.4f}, h={self.h:.4f})")


def calculate_scale(min_scale: float, max_scale: float,
                    stride_index: int, num_strides: int) -> float:
    """Linearly interpolate scale between min and max."""
    if num_strides == 1:
        return (min_scale + max_scale) * 0.5
    return min_scale + (max_scale - min_scale) * stride_index / (num_strides - 1)


def generate_anchors(options: SsdAnchorsOptions) -> list[Anchor]:
    """
    Main anchor generation — mirrors SsdAnchorsCalculator::GenerateAnchors().

    Layers sharing the same stride are merged: their aspect ratios and scales
    are accumulated before iterating over the feature map grid, so you get
    multiple anchors per spatial cell.
    """
    anchors: list[Anchor] = []
    num_layers = options.num_layers

    layer_id = 0
    while layer_id < num_layers:
        anchor_heights: list[float] = []
        anchor_widths: list[float] = []
        aspect_ratios: list[float] = []
        scales: list[float] = []

        # Merge all consecutive layers that share the same stride
        last_same_stride_layer = layer_id
        while (last_same_stride_layer < len(options.strides) and
               options.strides[last_same_stride_layer] == options.strides[layer_id]):

            scale = calculate_scale(
                options.min_scale, options.max_scale,
                last_same_stride_layer, len(options.strides)
            )

            if last_same_stride_layer == 0 and options.reduce_boxes_in_lowest_layer:
                # Special predefined anchors for the first layer
                aspect_ratios += [1.0, 2.0, 0.5]
                scales += [0.1, scale, scale]
            else:
                for ar in options.aspect_ratios:
                    aspect_ratios.append(ar)
                    scales.append(scale)

                if options.interpolated_scale_aspect_ratio > 0.0:
                    # Add an extra anchor at the geometric mean of adjacent scales
                    if last_same_stride_layer == len(options.strides) - 1:
                        scale_next = 1.0
                    else:
                        scale_next = calculate_scale(
                            options.min_scale, options.max_scale,
                            last_same_stride_layer + 1, len(options.strides)
                        )
                    scales.append(math.sqrt(scale * scale_next))
                    aspect_ratios.append(options.interpolated_scale_aspect_ratio)

            last_same_stride_layer += 1

        # Compute anchor w/h from scale + aspect ratio
        for i in range(len(aspect_ratios)):
            ratio_sqrt = math.sqrt(aspect_ratios[i])
            anchor_heights.append(scales[i] / ratio_sqrt)
            anchor_widths.append(scales[i] * ratio_sqrt)

        # Determine feature map dimensions for this layer
        if options.feature_map_height is not None:
            feature_map_height = options.feature_map_height[layer_id]
            feature_map_width = options.feature_map_width[layer_id]
        else:
            stride = options.strides[layer_id]
            feature_map_height = math.ceil(options.input_size_height / stride)
            feature_map_width = math.ceil(options.input_size_width / stride)

        # Place one anchor per (cell, anchor_shape) combination
        for y in range(feature_map_height):
            for x in range(feature_map_width):
                for anchor_id in range(len(anchor_heights)):
                    x_center = (x + options.anchor_offset_x) / feature_map_width
                    y_center = (y + options.anchor_offset_y) / feature_map_height

                    if options.fixed_anchor_size:
                        w, h = 1.0, 1.0
                    else:
                        w = anchor_widths[anchor_id]
                        h = anchor_heights[anchor_id]

                    anchors.append(Anchor(x_center, y_center, w, h))

        layer_id = last_same_stride_layer

    return anchors


# ---------------------------------------------------------------------------
# Palm detection config  (192x192, expects 2016 anchors)
#
# Stride layout:
#   stride 8  -> 1 layer  -> 24x24 grid, 2 anchors/cell ->  1152 anchors
#   stride 16 -> 3 layers -> 12x12 grid, 6 anchors/cell ->   864 anchors
#                                                     total: 2016 anchors
#
# Each layer contributes 2 anchors/cell: 1 from aspect_ratio=1.0 at scale_i,
# plus 1 interpolated anchor at sqrt(scale_i * scale_{i+1}) with aspect_ratio=1.0.
# The 3 stride-16 layers are merged by the same-stride loop, giving 6/cell.
# ---------------------------------------------------------------------------
PALM_DETECTION_OPTIONS = SsdAnchorsOptions(
    input_size_height=192,
    input_size_width=192,
    num_layers=4,
    strides=[8, 16, 16, 16],
    min_scale=0.1484375,
    max_scale=0.75,
    aspect_ratios=[1.0],
    anchor_offset_x=0.5,
    anchor_offset_y=0.5,
    interpolated_scale_aspect_ratio=1.0,
    reduce_boxes_in_lowest_layer=False,
    fixed_anchor_size=True,
)


if __name__ == "__main__":
    anchors = generate_anchors(PALM_DETECTION_OPTIONS)

    print(f"Total anchors generated: {len(anchors)}")
    assert len(anchors) == 2016, f"Expected 2016, got {len(anchors)}"
    print("✓ Anchor count matches expected 2016\n")

    # Breakdown
    stride8_cells  = math.ceil(192 / 8)  ** 2   # 24x24 = 576
    stride16_cells = math.ceil(192 / 16) ** 2   # 12x12 = 144
    stride8_anchors_per_cell  = 2   # 1 merged layer  × 2 anchors/cell
    stride16_anchors_per_cell = 6   # 3 merged layers × 2 anchors/cell

    print(f"Stride 8  (24×24):  {stride8_cells} cells × {stride8_anchors_per_cell} anchors/cell"
          f" = {stride8_cells * stride8_anchors_per_cell}")
    print(f"Stride 16 (12×12):  {stride16_cells} cells × {stride16_anchors_per_cell} anchors/cell"
          f" = {stride16_cells * stride16_anchors_per_cell}")
    print(f"Total: {stride8_cells*stride8_anchors_per_cell + stride16_cells*stride16_anchors_per_cell}\n")

    boundary = stride8_cells * stride8_anchors_per_cell  # 1152

    print("First 4 anchors  [stride-8 layer, cell (0,0)]:")
    for a in anchors[:4]:
        print(f"  {a}")

    print("\nLast 4 anchors of stride-8 layer [cell (23,23)]:")
    for a in anchors[boundary - 4: boundary]:
        print(f"  {a}")

    print("\nFirst 6 anchors of stride-16 layer [cell (0,0)]:")
    for a in anchors[boundary: boundary + 6]:
        print(f"  {a}")