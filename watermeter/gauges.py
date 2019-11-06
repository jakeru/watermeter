#!/usr/bin/env python3

# Read all 4 gauges from a watermeter.

from collections import namedtuple
import logging
import math
import os

# Requires OpenCV
import cv2
import numpy as np

from .utils import write_image_if_verbose

Gauge = namedtuple('Gauge', "scale, p0, p3, p5, p8")

BASE_IMAGE_WIDTH = 3280

GAUGES = (
    Gauge(0.1, (1496, 2126), (1007, 2239), (951, 1880), (1429, 1775)),
    Gauge(0.01, (1027, 1603), (531, 1705), (476, 1355), (967, 1264)),
    Gauge(0.001, (1074, 920), (598, 1002), (534, 672), (1007, 593)),
    Gauge(0.0001, (1604, 454), (1156, 531), (1088, 207), (1540, 134)),
)

# Radius of a gauge.
RADIUS = 256

# Radius of center of the gauge.
CENTER_RADIUS = 140

def value_pos(value):
    angle = value / 10.0 * 2 * math.pi
    return np.float32([math.sin(angle), -math.cos(angle)])

def warp_gauge(img, gauge, image_scale):
    center = np.float32([RADIUS, RADIUS])
    fromPoints = np.float32([gauge.p0, gauge.p3, gauge.p5, gauge.p8]) * image_scale
    toPoints = center + RADIUS * np.float32([value_pos(0), value_pos(3), value_pos(5), value_pos(8)])
    p = cv2.getPerspectiveTransform(fromPoints, toPoints)
    return cv2.warpPerspective(img, p, (RADIUS * 2, RADIUS * 2))

def mask_out_center(img, image_scale):
    c = int(img.shape[1] / 2)
    radius = int(CENTER_RADIUS * image_scale)
    color = (0, )
    cv2.circle(img, (c, c), radius, color, -1)

def average_value_from_mask(mask, gauge):
    logger = logging.getLogger()
    mask_indices = np.transpose(np.nonzero(mask))
    c = mask.shape[1] / 2
    vx_sum = 0.0
    vy_sum = 0.0
    for y, x in mask_indices:
        vx = x - c
        vy = -y + c
        angle = math.atan2(vy, vx)
        vx_sum += math.cos(angle)
        vy_sum += math.sin(angle)
    cw_angle = math.atan2(vx_sum, vy_sum)
    if cw_angle < 0:
        cw_angle = 2 * math.pi + cw_angle
    value = cw_angle / 2 / math.pi * 10
    logger.debug("Gauge %f: value: %f", gauge.scale, value)
    return value

def read_gauge(img, gauge, image_scale, verbose):
    needle_min = np.array([170, 150, 80])
    needle_max = np.array([185, 255, 255])
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, needle_min, needle_max)
    write_image_if_verbose("gauge_{}_mask.jpg".format(gauge.scale), mask, verbose)
    res = cv2.bitwise_and(img, img, mask=mask)
    write_image_if_verbose("gauge_{}_masked.jpg".format(gauge.scale), res, verbose)
    mask_out_center(mask, image_scale)
    write_image_if_verbose("gauge_{}_masked_no_center.jpg".format(gauge.scale), mask, verbose)
    return average_value_from_mask(mask, gauge)

def integral_part(msv, lsv):
    tolerance = 0.25
    fract, integral = math.modf(msv)
    if fract < tolerance and lsv >= 5:
        return int(integral - 1) if integral > 0 else 9
    elif fract > 1 - tolerance and lsv < 5:
        return int(integral + 1) if integral < 9 else 0
    return int(integral)

def read_gauges(img, verbose = False):
    image_scale = img.shape[1] / BASE_IMAGE_WIDTH

    # Extract gauges from the image
    values = []
    gauge_images = []

    for gauge in GAUGES:
        gauge_img = warp_gauge(img, gauge, image_scale)
        gauge_images.append(gauge_img)
        write_image_if_verbose("gauge_warped_{}.jpg".format(gauge.scale), gauge_img, verbose)

    # Read the gauges.
    for i, gauge in enumerate(GAUGES):
        values.append(read_gauge(gauge_images[i], gauge, image_scale, verbose))

    # Interpret the results.
    # Adjust gauges as needed.
    digits_reversed = []
    digits_reversed.append(int(values[-1]))
    for i in range(len(values) - 1):
        digits_reversed.append(integral_part(values[len(values) - i - 2], digits_reversed[i]))
    digits = list(reversed(digits_reversed))

    # Draw an output image with all the results.
    res_img = np.zeros((RADIUS * 2, len(values) * RADIUS * 2, 3), np.uint8)
    for i in range(len(values)):
        img = gauge_images[i]
        for v in range(0,10):
            pos = tuple(map(int, (RADIUS + RADIUS * value_pos(v))))
            cv2.line(img, (RADIUS, RADIUS), pos, (255, 0, 0), 1)
        pos = tuple(map(int, (RADIUS + RADIUS * value_pos(values[i]))))
        cv2.line(img, (RADIUS, RADIUS), pos, (0, 255, 0), 2)
        x = i * RADIUS * 2
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(img, "%.4f" % GAUGES[i].scale, (10, 30), font, 1, (255,0,0), 2, cv2.LINE_AA)
        cv2.putText(img, "%.3f" % values[i], (10, 60), font, 1, (255,0,0), 2, cv2.LINE_AA)
        cv2.putText(img, "%d" % digits[i], (10, 90), font, 1, (0,255,0), 2, cv2.LINE_AA)
        res_img[0:img.shape[0], x:x+img.shape[1]] = img
    write_image_if_verbose("all_gauges.jpg", res_img, verbose)
    return digits
