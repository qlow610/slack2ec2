# slack 2 EC2

* slackからEC2の操作(起動/停止/状態確認)を行う。
*  $server (status | help | [server name] start | [server name] stop)
* Slack → APIGateway → Lambda → APIGateway → Slack