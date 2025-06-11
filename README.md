# Telegram-Bot-Swarm
## Concept Development
想要操作 Swarm 必須依靠電腦才能使用，然而當我們不在電腦旁邊並且發生突發狀況時，就無法進行緊急處理。

因此藉由 Telegram Bot 在手機上操作 Swarm 以達到 Anywhere, anytime 的功用。

## Structure & Function
![Blank diagram](https://github.com/user-attachments/assets/14af925c-7a40-458e-a007-a916e35fb121)
本專題以 Python 作為串接 Telegram Bot 的媒介，接收來自 Telegram 定義的指令。

Swarm 中則包含多個節點，其中 Manager 節點跑 Prometheus 以收集與查詢監控資料，而每個節點都有跑 cAdvisor 與 Node_Exporter 以提供 Prometheus 相關節點與容器的監控資料。

## Prerequisite
* Docker Swarm Node x3
  * Manager - LSA
  * Worker - LSAT2
  * Worker - LSAT3
* Python3

## Installation
**In Manager Node**

`git clone https://github.com/Genly49/telegram-bot-swarm.git`

`pip install python-telegram-bot requests docker python-dotenv matplotlib pandas ace-tools-open`

`cd swarm`

`docker stack deploy --compose-file stack.yml mymonitor`

## Demo
本專題共提供四種功能，分別是：
* /node
  用於查看特定節點的各種資源使用量，節點名稱可用 /ls node 查詢。
  指令：`/node <參數> <節點名稱>`
  參數：cpu - CPU / ram - 記憶體 / disk - 儲存空間 / rx - 下載速度 / tx - 上傳速度 / load - 系統負載
  範例結果：

* /con
  用於查看某個節點特定容器的各種資源使用量，節點名稱一樣可用 /ls node 查詢。
  為了能查看節點上監控容器的資源使用量，而且用 stack 建立的容器名稱又臭又長，因此可輸入 compose file 內建的標籤，當前的標籤包含：`prometheus`、`cadvisor` 和 `node_exporter`。
  指令：`/node <參數> <節點 | 標籤名稱> <true | false 使用標籤>`
  參數：cpu - CPU / ram - 記憶體 / rx - 下載速度 / tx - 上傳速度
  範例結果：

* /ls
  用於查看 Swarm 內所有節點、節點內所有容器或服務。
  指令：`/node <參數> <節點名稱>`
  參數：node - 節點 / con - 容器（需要節點名稱參數） / ser - 服務
  範例結果：

* /modify
  操控 Swarm 內的容器或服務，包含建立、暫停、刪除等。
  指令：`/modify <con | ser> <create | start | run | pause | resume | restart | remove> <名稱> <image> <port> <replicas>`
  服務只有 `create`、`restart` 和 `remove`，並且可輸入 `replicas` 參數，若不輸入則預設值為 1
  範例結果：

## Improvement
* 文字回傳結果格式優化
* 指令進一步分隔，例如容器與服務分開
* 映像檔抓取特定版本並使用
* 容器或服務建立時包含標籤
* 資源使用警報

## Job Assignment
梁灝 - 指令內容開發
黃士瀚 - Telegram Bot 串接

## References
https://docs.docker.com/get-started/
https://prometheus.io/docs/introduction/overview/
cAdvisorhttps://github.com/google/cadvisor.git
https://github.com/prometheus/node_exporter.git
https://github.com/880831ian/Prometheus-Grafana-Docker
[學長們的專題](https://github.com/NCNU-OpenSource/K8s-Telegram-Bot.git)
