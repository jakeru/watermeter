#!/usr/bin/env python3

import argparse
import json
import logging
import sys

# Requires OpenCV
import cv2

from watermeter import digits
from watermeter import gauges

def trust_last_main_digit(gauge_digits):
    return gauge_digits[0] < 9

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Read value of a watermeter")
    parser.add_argument("--verbose", help="Verbose mode", action="store_true")
    parser.add_argument("--memory", help="File to use to remember last reading")
    parser.add_argument("--template_path", help="Path to templates (digitN.png)", default="digits")
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

    main_digits = digits.read_digits(img, template_path=args.template_path, verbose=args.verbose)
    main_digits_str = "".join(map(str, main_digits))
    logger.debug("Digits: %s", main_digits_str)

    gauge_digits = gauges.read_gauges(img, verbose=args.verbose)
    gauge_digits_str = "".join(map(str, gauge_digits))
    logger.debug("Gauges: %s", gauge_digits_str)

    memory = {}
    if args.memory:
        try:
            with open(args.memory, "r") as memory_file:
                memory = json.load(memory_file)
        except FileNotFoundError:
            logger.warn("Memory file not found")
        except json.decoder.JSONDecodeError:
            logger.warn("Failed to parse memory file")

    if not trust_last_main_digit(gauge_digits) and 'digits' in memory:
        main_digits_str = memory.get('digits')
        logger.debug("Using value stored in memory for digits: %s", main_digits_str)

    if args.memory:
        memory['digits'] = main_digits_str
        with open(args.memory, "w") as memory_file:
            json.dump(memory, memory_file)

    print(str(int(main_digits_str)) + gauge_digits_str)
