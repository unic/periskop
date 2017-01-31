# periskop - Slack Bot Integration Tests
periskop is an integration testing tool for slack bots. An increasing diverse set of use-cases are implemented with chat bots e.g. ChatOps, Service Desk, etc. 
With periskop we can implement and run integration tests using a simple yaml file.

Here's a quick example of the power of periskop:
```
test_name: chatops_diskspace
bot_name: mrrobot
timeout: 60
slack:
  channel: "#periskop-test"
  as_user: periskop-user
  text: "!diskspace mymachine /var"
expect:
  regex: true
  attachments:
    text: |
      .*{u'failures': 0, u'skipped': 1, u'ok': 3, u'unreachable': 0, u'changed': 1}.*
```
This test `chatops_diskspace` executes the command `!diskspace mymachine /var` in the channel `#periskop-test` as user `periskop-user` and checks for the result in an attachment. The result is a string with regular expression matching.

## Getting Started
Install periskop:
```
pip install periskop
```

Check for successfull installation.
```
periskop --help
```

Create a config file `config.yml` with the necessary information to run tests:
```
slack_token: abcd-efgh-...-...
as_user: myusername
bot_name: mybotname
channel: "#periskop"
```
Make sure that the slack token is a valid API Tester token. We need this kind of token, because bots can't talk to other bots :).

Create your first test `firsttest.yml`:
```
test_name: chatops_diskspace
bot_name: mrrobot
timeout: 60
slack:
  text: "!diskspace mymachine /var"
expect:
  regex: true
  attachments:
    text: |
      .*{u'failures': 0, u'skipped': 1, u'ok': 3, u'unreachable': 0, u'changed': 1}.*
```

List all tests:
```
periskop list
```

Run the test:
```
periskop run firsttest
```

## Test Implementation

### Slack Input
In the examples above we specified the following simple slack command:
```
slack:
  text: "!diskspace mymachine /var"
```
We can not only specify text but use the full set of arguments defined here: [Slack PostMessage API](https://api.slack.com/methods/chat.postMessage#arguments)

### Test Condition
We can test either for a full text match or for regex. The test allows for specification of the complete [message event type](https://api.slack.com/events/message). 
Instead of checking for the attachment you may as well check for the text:
```
expect:
  regex: true
  text: |
    .*ok.*
```

#### RegEx
```
test_name: chatops_diskspace
bot_name: mrrobot
timeout: 60
slack:
  channel: "#periskop"
  as_user: periskop-user
  text: "!diskspace mymachine /var"
expect:
  regex: true
  attachments:
    text: |
      .*{u'failures': 0, u'skipped': 1, u'ok': 3, u'unreachable': 0, u'changed': 1}.*
```

#### Full match
```
test_name: status command
bot_name: mrrobot
timeout: 300
slack:
  channel: "#periskop"
  as_user: periskop-user
  text: "!status mymachine"
expect:
  attachments:
    text: |
      ```<http://mymachine> | SUCCESS =&gt; {\n    "changed": false, \n    "ping": "pong"\n}```
  text: "@mrrobot: Here is your status for `<http://mymachine>` host(s):"`
```


## Setup Development Environment
```
git clone https://github.com/unic/periskop.git
python setup.py develop
```

### PyPi
If you want to update the PyPi package, make sure you have a valid `~/.pypirc` configuration:
```
[distutils]
index-servers =
  pypi
  pypitest

[pypi]
repository=https://pypi.python.org/pypi
username=your_username
password=your_password

[pypitest]
repository=https://testpypi.python.org/pypi
username=your_username
password=your_password
```

Then execute
```
pip install pypandoc
brew install pandoc
python setup.py register -r pypi
```