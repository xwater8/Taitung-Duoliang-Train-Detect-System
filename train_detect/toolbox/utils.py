# -*- coding: utf-8 -*-
"""
Utility functions
"""
import os
import cv2


def show_img(win_name, img, width=1280, height=720):
    """
    Display image in a window with specified size
    Args:
        win_name(str): Window name
        img(np.ndarray): OpenCV image to display
        width(int): Window width
        height(int): Window height
    """
    cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win_name, width, height)
    cv2.imshow(win_name, img)


def get_fileMainName(file_path):
    """
    Get main name of file (without extension)
    Args:
        file_path(str): File path. Ex: /home/user/test_123.jpg
    Return:
        fileMainName(str): Main file name. Ex: test_123
    """
    fileName = os.path.basename(file_path)
    fileMainName = os.path.splitext(fileName)[0]
    return fileMainName
