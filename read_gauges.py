#!/usr/bin/env python3

import argparse
import logging
import sys

# Requires OpenCV
import cv2

from watermeter import gauges

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Read gauges from water meter image")
    parser.add_argument("--verbose", help="Verbose mode", action="store_true")
    parser.add_argument("input", help="Filename of input image")
    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    log_format = '%(asctime)-15s %(levelname)-7s %(name)s %(message)s'
    logging.basicConfig(format=log_format, level=log_level)
    logger = logging.getLogger()

    # Open the input image.
    img = cv2.imread(args.input)
    if img is None:
        logger.error("Could not open image for reading: %s", args.input)
        sys.exit(1)
    digits = gauges.read_gauges(img, verbose=args.verbose)
    result = "".join(map(str, digits))
    print(result)
