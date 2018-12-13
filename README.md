# slack 2 EC2

* slackからEC2の操作(起動/停止/状態確認/NSGの追加/削除)を行う。
*  $server (status | help | [server name] start | [server name] stop | ipshow | ipadd/ipdell [server name] -FromPort xx -IpRanges xx.xx.xx.xx/xx -Description xxxx
* Slack → APIGateway → Lambda → APIGateway


----
## TestCode
```  
event = {
    'body':'$server Instance stop'
}  
context = {
    'test':'test'
}
event = {  
    "body" : "'body': '&user_id=AAAAAAA&text=%24server+Testweb01+ipadd+-FromPort+443+-IpRanges+101.1.1.5%2F32+-Description+Addtest&trigger_word=%24server'"  
}  
context = {  
    'test':'test'  
}  
lambda_handler(event,context)
```