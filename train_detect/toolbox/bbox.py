# -*- coding: utf-8 -*-
"""
BBox class and drawing utilities
"""
import cv2
from functools import total_ordering


def draw_text(img, bbox, font_scale=0.5, color=(0, 0, 255), thickness=2, bbox_y_offset=10):
    """
    Draw text on image
    Args:
        img(np.ndarray): Image to draw on
        bbox(BBox): BBox object with coordinates and class info
        font_scale(float): Text size
        color(tuple): Text color
        thickness(float): Text thickness
        bbox_y_offset: Text position relative to ymin
    """
    font_type = cv2.FONT_HERSHEY_SIMPLEX
    draw_str = "{}:{:.2f}".format(bbox.clsName, bbox.score)
    cv2.putText(img, draw_str, (bbox.xmin, bbox.ymin - bbox_y_offset), font_type, font_scale, color, thickness)


def draw_bbox(img, bbox, color=(0, 0, 255), thickness=3, font_scale=0.5):
    """Draw bounding box on image"""
    cv2.rectangle(img, (bbox.xmin, bbox.ymin), (bbox.xmax, bbox.ymax), color, thickness)
    draw_text(img, bbox, font_scale, color)


def draw_bboxes(img, bboxes, color=(0, 0, 255), thickness=3, font_scale=0.5):
    """Draw multiple bounding boxes on image"""
    for bbox in bboxes:
        draw_bbox(img, bbox, color, thickness, font_scale)


@total_ordering
class BBox:
    """Bounding box class"""
    def __init__(self, xmin, ymin, xmax, ymax, score, clsName):
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax
        self.clsName = clsName
        self.score = score

    @property
    def pt1(self):
        return (self.xmin, self.ymin)

    @property
    def pt2(self):
        return (self.xmax, self.ymax)

    @property
    def width(self):
        return abs(self.xmax - self.xmin)

    @property
    def height(self):
        return abs(self.ymax - self.ymin)

    @property
    def area(self):
        return self.width * self.height

    def __eq__(self, other):
        if other is None:
            return False
        if self.xmin != other.xmin or self.xmax != other.xmax:
            return False
        if self.ymin != other.ymin or self.ymax != other.ymax:
            return False
        if self.clsName != other.clsName:
            return False
        if self.score != other.score:
            return False
        return True

    def __lt__(self, other):
        return self.score < other.score
