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

> 在循环中可以通过远程发送命令消息来跳出循环。暂时没做

- 根据广播服务来热切换mqtt 服务器
- 自我更新
需要在监听的mqtt的指令频道发送update命令
```shell
update -i10.8.47.5 -p8000 -m%s -fupgrade.tar -v1.0 -r10
```
- -i:IP
- -p:端口
- -m:文件md5值
- -f:tar文件，目前仅支持tar文件部署
- -v:version版本号，基站会和本地t.cnf的文件内的版本号对比，比当前版本新才会执行更新
- -r:随机睡眠时间，缺省为600s

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
安装zeroconf
```shell
sudo pip install zeroconf
```
