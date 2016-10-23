# Periskop - Slack Bot Integration Tests


## Writing tests

### RegEx
```
test_name: diskspace
bot_name: roboto
timeout: 60
slack:
  channel: "#stackaton"
  as_user: roberterdin
  text: "!diskspace infra-dev-bei.p.unic24.net /var"
expect:
  regex: true
  attachments:
    text: |
      .*{u'failures': 0, u'skipped': 1, u'ok': 3, u'unreachable': 0, u'changed': 1}.*
```

### Full match
```
test_name: status command
bot_name: roboto
timeout: 300
slack:
  channel: "#stackaton"
  as_user: roberterdin
  text: "!status infra-dev-bei.p.unic24.net"
expect:
  attachments:
    text: |
      ```<http://infra-dev-bei.p.unic24.net|infra-dev-bei.p.unic24.net> | SUCCESS =&gt; {\n    "changed": false, \n    "ping": "pong"\n}```
  text: "@roberterdin: Here is your status for `<http://infra-dev-bei.p.unic24.net>` host(s):"`
```

## Configuration
Most configuration parameters can be defined globally, if desired, and overwritten by the integration tests. 