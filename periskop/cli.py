#!/usr/bin/env python
#
# Copyright 2017 Unic AG
#

import click
import sys
import os
import yaml
import re
import time
import logging
from slackclient import SlackClient


levels = [logging.ERROR, logging.INFO, logging.DEBUG]
logger = logging.getLogger('periskop')
logger.addHandler(logging.StreamHandler())

_YAML_PATTERN = r'test_.+\.yaml'
_DEFAULT_TIMEOUT = 30

_tests = {}
_results = {}

def _get_channel_by_name(slack, name):
    response = slack.api_call("channels.list")
    for channel in response['channels']:
        if channel['name'] == name:
            return channel


def _get_user_by_name(slack, name):
    response = slack.api_call("users.list")
    for user in response['members']:
        if user['name'] == name:
            return user


def _validate(test):
    slack = SlackClient(_config['slack_token'])

    bot = _get_user_by_name(slack, _config['username']) \
        if 'bot_name' not in test \
        else _get_user_by_name(slack, test['bot_name'])

    # figure out which values to pass
    test['slack']['channel'] = test['slack'].get('channel', _config['channel'])
    test['slack']['as_user'] = test['slack'].get('as_user', _config['as_user'])

    timeout = test.get('timeout', _DEFAULT_TIMEOUT)

    if slack.rtm_connect():
        slack.api_call("chat.postMessage", **test['slack'])
        success = False
        elapsed_time = 0

        click.echo('Running {0}...'.format(test['test_name']))
        with click.progressbar(length=timeout, label=' ') as bar:
            while not success and elapsed_time < timeout:
                elapsed_time += 1
                bar.update(1)
                update = slack.rtm_read()
                logger.debug("RTM: " + str(update))
                if len(update) > 0 and 'user' in update[0] and update[0]['user'] == bot['id']:
                    # message is from bot

                    if 'attachements' in test['expect']:
                        expected = test['expect']['attachments']['text'].replace('\\n', '').replace('\n', '')
                        given = update[0]['attachments'][0]['fallback'].replace('\n', '')
                    elif 'text' in test['expect']:
                        expected = test['expect']['text'].replace('\\n', '').replace('\n', '')
                        given = update[0]['text'].replace('\n', '')

                    if 'regex' not in test['expect'] or not test['expect']['regex']:
                        # wrap proved string
                        expected = r"^" + expected + r"$"
                    if re.match(expected, given):
                        # test successful
                        success = True
                        bar.update(timeout)

                time.sleep(1)

            if success:
                _results[test['test_name']] = "passed"
                _report_test(test, True, slack)
            else:
                # timeout reached
                _results[test['test_name']] = "failed"
                _report_test(test, False, slack)

    else:
        logger.error("Connection Failed, invalid token?")


def _report_test(test, passed, slack):

    # overwrite globals with test specifics
    merged = _config.copy()
    merged.update(test['slack'])
    merged.pop('text', None)
    merged['as_user'] = 'false'

    if passed:
        logger.info(test['test_name'] + ": passed")
        click.secho("passed", fg='green')
        slack.api_call("chat.postMessage",
                       text=test['test_name'] + ": passed. ",
                       **merged)
    else:
        logger.info(test['test_name'] + ": failed")
        click.secho("failed", fg='red')
        slack.api_call("chat.postMessage",
                       text=test['test_name'] + ": failed. ",
                       **merged)


def _post_result():
    slack = SlackClient(_config['slack_token'])
    attachments = []
    for key, value in _results.iteritems():
        attachments.append({
            'title': key,
            'text': value,
            'color': ('danger' if value != 'passed' else 'good')
        })
    formatted_result = _config.copy()
    formatted_result.update({
        'title': 'Execution Results',
        'attachments': attachments,
        'as_user': "false"
    })
    slack.api_call("chat.postMessage",
                   text="*Test results*",
                   **formatted_result)


def run_all():
    for test in _tests.values():
        _validate(test)

    _post_result()


@click.group()
@click.option('--tests-directory', '-d',
              default=os.getcwd(),
              help='The directory containing the test files. [default: current working directory]')
@click.option('-v', '--verbose', count=True)
def main(tests_directory, verbose):
    """Integration testing for ChatOps via Slack

    \b
    Options are prioritised in the following order: \b
    1) test specific arguments
    2) cli arguments
    3) config file in current working directory
    4) global config file in "/etc/periskop/"

    """
    # Configuration
    logger.setLevel(levels[verbose])
    global _config
    _cwd = os.getcwd()
    _config_file_name = "config.yaml"
    _abs_file_path = os.path.join(_cwd, _config_file_name)
    if not os.path.isfile(_abs_file_path):
        if os.path.isfile('/etc/periskop/config.yaml'):
            _abs_file_path = '/etc/periskop/config.yaml'
        else:
            print('No config found, in "{0}" or "/etc/periskop/config.yaml"'.format(_abs_file_path))
            sys.exit(1)

    with open(_abs_file_path) as _config_file:
        _config = yaml.load(_config_file)

    global _tests_dir
    _tests_dir = tests_directory

    tests_files = os.listdir(_tests_dir)
    for test_file_name in tests_files:
        if re.match(_YAML_PATTERN, test_file_name):
            with open(os.path.join(_tests_dir, test_file_name)) as test_file:
                test = yaml.load(test_file)
                _tests[test['test_name']] = test


@main.command()
@click.option('--all', is_flag=True)
@click.option('--slack-token', '-t',
              hide_input=True, help='Slack token (default hidden)')
@click.option('--bot-name', '-b',
              help='The name of the bot to post test results from.')
@click.option('--as-user', '-u',
              help='The name of the user to send test commands.')
@click.option('--channel', '-c',
              help='Channel to run tests in.')
@click.argument('name', default='')
def run(all, slack_token, as_user, bot_name, channel, name):
    """Execute Tests"""
    # write all values into _config so it is accessible
    # global conf can then be overwritten by specific test configs
    global _config
    _config['slack_token'] = slack_token if slack_token else _config['slack_token']
    _config['as_user'] = as_user if as_user else _config['as_user']
    _config['username'] = bot_name if bot_name else _config['bot_name']
    _config['channel'] = channel if channel else _config['channel']

    if all:
        click.echo('Running all tests... ')
        run_all()
    else:
        _validate(_tests[name])

    # exit with according code
    exit(1) if 'failed' in _results.values() else exit(0)


@main.command('list', help='List all available tests')
def list_tests():
    click.echo('+----------------------------+')
    click.echo('| Periskop Integration Tests |')
    click.echo('+----------------------------+')
    for test in _tests.keys():
        click.echo(test)


if __name__ == "__main__":
    main()
