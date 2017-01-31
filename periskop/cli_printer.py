#
# Copyright 2017 Unic AG
#

import os
import time
from logging.config import fileConfig

import yaml
import logging
from slackclient import SlackClient

# Configuration
_script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in
_config_file_name = "config.yaml"
_abs_file_path = os.path.join(_script_dir, '..', _config_file_name)
with open(_abs_file_path) as _config_file:
    _config = yaml.load(_config_file)

_tests_dir = os.path.join(os.path.dirname(__file__), '..', 'tests')
_YAML_PATTERN = r'.+\.yaml'
_DEFAULT_TIMEOUT = 30

fileConfig('../logging_config.ini')
logger = logging.getLogger('periskop')


class CliPrinter:
    """
    Used for testing purposes. The whole slack traffic is output to the CLI
    """
    def __init__(self):
        self.slack = SlackClient(_config['slack_token'])
        pass

    def run(self):
        if self.slack.rtm_connect():
            while True:
                update = self.slack.rtm_read()
                logger.debug("RTM: " + str(update))
                time.sleep(1)

# execute tests
CliPrinter().run()