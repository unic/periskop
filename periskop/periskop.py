import os
import time
import re
import yaml
import slack_adapter
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


# sc = SlackClient(_config['slack_token'])

class Periskop:
    def __init__(self):
        self.slack = slack_adapter.SlackAdapter(_config['slack_token'])
        pass

    def run(self):
        tests = os.listdir(_tests_dir)
        results = {}
        for test_file_name in tests:
            if re.match(_YAML_PATTERN, test_file_name):
                with open(os.path.join(_tests_dir, test_file_name)) as test_file:
                    test = yaml.load(test_file)

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
                        print update
                        if len(update) > 0 and 'attachments' in update[0] and update[0]['user'] == bot['id']:
                            # message is from bot

                            given = update[0]['attachments'][0]['text'].replace('\n', '')
                            expected = test['expect']['attachments']['text'].replace('\\n', '').replace('\n', '')

                            print "given \ expected"
                            print given
                            print expected
                            if 'regex' in test['expect'] and test['expect']['regex']:
                                if re.match(expected, given):
                                    # test successful
                                    print test['test_name'] + ": passed"
                                    success = True
                                    results[test['test_name']] = "passed"
                                    self.slack.send_message(test['test_name'] + ": passed", **test['slack'])
                            else:
                                if expected == given:
                                    # test successful
                                    print test['test_name'] + ": passed"
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
                    print "Connection Failed, invalid token?"

        # all tests ran

        #
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
