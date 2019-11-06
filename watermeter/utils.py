#!/usr/bin/env python3
import logging
import os

import cv2

# Directory to store images when in --verbose mode.
OUTPUT_DIRECTORY = "out"

def write_image_if_verbose(name, img, verbose):
    log = logging.getLogger()
    if not verbose:
        return
    try:
        os.mkdir(OUTPUT_DIRECTORY)
    except FileExistsError:
        pass
    output_file = os.path.join(OUTPUT_DIRECTORY, name)
    res = cv2.imwrite(output_file, img)
    if res:
        log.debug("Wrote image {}".format(output_file))
    else:
        log.warning("Failed to write image {}".format(output_file))
