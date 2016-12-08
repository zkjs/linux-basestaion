# basestation ble scanner

[参考地址](http://www.orangenarwhals.com/2014/06/bluetooth-low-energy-4-0-on-ubuntu-13-10-advertisements-sending-and-receiving/)

### 程序设计：

- 初始化

初始化mqtt client；连接本地网关服务器；注册自己的基站编号为alias；

- 注册监听事件；

开启扫描，关闭扫描，

- 开启下列循环：

	1. 扫描ble数据广播包；
	2. 组装数据：为：基站号：手环号：RSSI：手环状态；
	3. 判断是否报警包；
	4. 发送至网关服务器；（同安卓基站的逻辑）

在循环中可以通过远程发送命令消息来跳出循环。

### 环境和依赖：

对Raspberry Pi 3基站来说，安装[blueZ](http://www.bluez.org/download/)，libbluetooth-dev：

	sudo apt-get install libbluetooth-dev

安装bluepy
```shell
#python-pip if neccesssary↓
sudo apt-get install python-pip libglib2.0-dev
sudo pip install bluepy
```
安装mqtt client和paho-mqtt
```shell
sudo apt install mosquitto-clients
sudo pip install paho-mqtt #--trusted-host http://pypi.douban.com/
```
