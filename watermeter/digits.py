#!/usr/bin/env python3

import argparse
from collections import namedtuple
import logging
import math
import sys
import os

import cv2
import numpy as np

from .utils import write_image_if_verbose

BASE_IMAGE_WIDTH = 3280

DIGITS_X = 810
DIGITS_Y = 260
DIGITS_WIDTH = 1110
DIGITS_HEIGHT = 300

NUM_DIGITS = 5
DIGIT_WIDTH = 180
DIGIT_HEIGHT = 280
DIGIT1_X = 0
DIGIT1_Y = 10
DIGIT_DIST = 224

def warp(img):
    # Outer corners of the digits.
    size = (img.shape[1], img.shape[0])
    fromPts = np.float32([[2532, 720], [2121, 1685], [1915, 1590], [2330, 634]])
    toPts = np.float32([[821, 300], [1871, 300], [1871, 540], [821, 540]])
    p = cv2.getPerspectiveTransform(fromPts, toPts)
    return cv2.warpPerspective(img, p, size)

def extract_all_digits(img, scale):
    x = int(DIGITS_X * scale)
    width = int(DIGITS_WIDTH * scale)
    y = int(DIGITS_Y * scale)
    height = int(DIGITS_HEIGHT * scale)
    return img[y:y+height, x:x+width]

def extract_digits(all_digits_img, scale):
    digits = []
    for i in range(NUM_DIGITS):
        x = int((DIGIT1_X + DIGIT_DIST * i) * scale)
        width = int(DIGIT_WIDTH * scale)
        y = int(DIGIT1_Y * scale)
        height = int(DIGIT_HEIGHT * scale)
        digits.append(all_digits_img[y:y+height, x:x+width])
    return digits

def filter_image(img):
    res = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #res = cv2.Canny(res, 80, 250, 5)
    #m = cv2.medianBlur(res, 5)
    #res = cv2.inRange(m, 0, 50)
    return res

def load_templates(path, verbose):
    logger = logging.getLogger()
    templates = []
    for i in range(10):
        filename = os.path.join(path, "digit{}_2.png".format(i))
        img = cv2.imread(filename)
        if img is None:
            filename = os.path.join(path, "digit{}.png".format(i))
            img = cv2.imread(filename)
        if img is None:
            raise RuntimeError("Failed to read image: %s" % filename)
        logger.debug("Image %s: %d x %d", filename, img.shape[1], img.shape[0])
        filtered = filter_image(img)
        write_image_if_verbose("template_digit{}_filtered.png".format(i), filtered, verbose)
        templates.append(filtered)
    return templates

def classify_digit(index, digit, templates, verbose):
    logger = logging.getLogger()
    scores = []
    for i, template in enumerate(templates):
        match = cv2.matchTemplate(digit, template, cv2.TM_SQDIFF)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(match)
        #logger.debug("Index %d: match with digit %d: %f at %r", index, i, min_val, min_loc)
        scores.append((i, min_val))
    scores.sort(key=lambda e: e[1])
    logger.debug("index %d: Sorted scores: %r", index, scores)
    return scores[0][0]

def classify_digits(digits, templates, verbose):
    res = []
    for i, digit in enumerate(digits, start = 1):
        res.append(classify_digit(i, digit, templates, verbose))
    return res

def read_digits(img, template_path="digits", verbose=False):
    scale = img.shape[1] / BASE_IMAGE_WIDTH

    warped_img = warp(img)
    write_image_if_verbose("all_digits_warped.jpg", warped_img, verbose)

    all_digits_img = extract_all_digits(warped_img, scale)
    write_image_if_verbose("all_digits.png", all_digits_img, verbose)

    all_digits_img_filtered = filter_image(all_digits_img)
    write_image_if_verbose("all_digits_filtered.png", all_digits_img_filtered, verbose)

    digits = extract_digits(all_digits_img_filtered, scale)
    for i, digit in enumerate(digits, start = 1):
        write_image_if_verbose("digit{}.png".format(i), digit, verbose)

    templates = load_templates(template_path, verbose)
    return classify_digits(digits, templates, verbose)
