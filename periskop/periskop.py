import os
import time
import re
from logging.config import fileConfig

import yaml
import logging
from slack_adapter import SlackAdapter

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
# logger.setLevel(logging.DEBUG)
# ch = logging.StreamHandler(sys.stdout)
# ch.setLevel(logging.DEBUG)
# logger.addHandler(ch)


class Periskop:
    def __init__(self):
        self.slack = SlackAdapter(_config['slack_token'])
        pass

    def run(self):
        tests = os.listdir(_tests_dir)
        results = {}
        for test_file_name in tests:
            if re.match(_YAML_PATTERN, test_file_name):
                with open(os.path.join(_tests_dir, test_file_name)) as test_file:
                    test = yaml.load(test_file)

                self.validate(results, test)

        self.post_result(results)

    def validate(self, results, test):
        bot = self.slack.get_user_by_name(_config['bot_name']) \
            if 'bot_name' in _config \
            else self.slack.get_user_by_name(test['bot_name'])
        timeout = test['timeout'] if 'timeout' in test else _DEFAULT_TIMEOUT
        if self.slack.sc.rtm_connect():
            self.slack.sc.api_call("chat.postMessage", **test['slack'])
            success = False
            elapsed_time = 0

            while not success and elapsed_time < timeout:
                update = self.slack.sc.rtm_read()
                logger.debug("RTM: " + str(update))
                if len(update) > 0 and 'attachments' in update[0] and update[0]['user'] == bot['id']:
                    # message is from bot

                    given = update[0]['attachments'][0]['text'].replace('\n', '')
                    expected = test['expect']['attachments']['text'].replace('\\n', '').replace('\n', '')

                    if 'regex' in test['expect'] and test['expect']['regex']:
                        if re.match(expected, given):
                            # test successful
                            logger.info(test['test_name'] + ": passed")
                            success = True
                            results[test['test_name']] = "passed"
                            self.slack.send_message(test['test_name'] + ": passed", **test['slack'])
                    else:
                        if expected == given:
                            # test successful
                            logger.info(test['test_name'] + ": passed")
                            success = True
                            results[test['test_name']] = "passed"
                            self.slack.send_message(test['test_name'] + ": passed", **test['slack'])

                        else:
                            # just continue until the timeout for now
                            pass
                elapsed_time += 1
                time.sleep(1)

            # timeout reached
            if not success:
                results[test['test_name']] = "failed"
                self.slack.send_message(test['test_name'] + ": failed. Timeout reached.", **test['slack'])
        else:
            logger.error("Connection Failed, invalid token?")

    def post_result(self, results):
        attachments = []
        for key, value in results.iteritems():
            attachments.append({
                'title': key,
                'text': value,
                'color': ('danger' if value != 'passed' else 'good')
            })
        formatted_result = {
            'title': 'Execution Results',
            'attachments': attachments
        }
        self.slack.send_message("*Test results*", **formatted_result)


# execute tests
Periskop().run()
