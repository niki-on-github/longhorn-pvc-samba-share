import warnings
import traceback
import tempfile
import json
import logging
import os
import sys
import time
import yaml


def setup_logging():
    logging.basicConfig(
        level=os.getenv('LOG_LEVEL', "INFO"),
        format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(stream=sys.stdout)
        ]
    )


if __name__ == "__main__":
    setup_logging()
    print("Hello World")
