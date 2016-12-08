# hbm-specs: bracelet and base station (type 1) 
V0.2

本文提供方案1的手环、基站设计的一些基本需求；

## 目的和概述

方案1(type 1)的设计基于约定以下目的：

- 手环能够满足定位，告警，一次性腕带能满足离体状态的监控需求。
- 手环的广播需要：定位、呼救、离体，三种特征传递以及表达格式。让手环1，手环2均能满足基站1和基站2的监控。
- 手环定位的频率、呼救广播包频率和次数、离体状态复位的频率、条件和方式的约定。
- 手环和基站的上下行命令方式；

## 手环规格(#TODO)

- 传感器，耗电，充电方案；
- 交互界面，包括按键人机设计和按键功能；
- 一次性表带安装方式和离体检测设计；

## 手环-基站通信协议

- 其一为广播协议，约定定位、呼救、离体，三种特征，其它信息包括：电量，其他测量结果； 广播协议主要是约定在以下方式： 

 1. manufacture id: 目前为00ff（65280）需进一步协商（#TODO）； 
 2. manufactureSpecificData：目前以12开头； data的二进制位和含义表达如下（-为便于阅读的分隔符）： `B1-B2-B3-B4-B5-B6-B7-B8.... `
 3. B1：长度2，版本号：目前为0x12 
 4. B2：长度2，手环状态位：0x13=正常定位包；0x66=告警；0x68=离体；其他，可包含手环规格； 
 5. B3-B4-B5-B6：手环编号段；0x0000 0000-0xffff ffff 
 6. B7：长度2，电量，格式待定0x00～0xff，按手环原有设置； 
 7. B8及以后：其他信息；

- 其二为链接协议。按手环设计来提供基站主动链接手环后进行的行为；该协议可通过基站自动连接，也可以通过配置管理工具来连接。其安全性和其他设置也应予以规定。 待定，遵循手环规格；(#TODO)

## 基站-服务器通信协议

- 基站应可在部署现场设置：本地服务器地址；基站编号；WLAN设置； 
- 基站使用mqtt client与本地服务器实时数据通讯；保留使用其他互联网标准协议进行其他通讯； 
- mqtt client连接至本地服务器，并注册自己基站编号为clientID； 
- mqtt client可使用eclipse的paho项目下的[java](https://eclipse.org/paho/clients/java/)或[android client](https://eclipse.org/paho/clients/android/)；

- 上行报文1；扫描广播的结果； 上行报文应有以下规则：

 1. 扫描到定位+离体包信息时，不超过t1(t1=5-20)秒发送一次，批量发送所有收到定位包；分别至`position`和`common`；
 2. 扫描不到手环时，应每t2（t2=30）秒发送一次基站状态包至`common`; 其中`status`为0时为正常。其他值为异常。异常原因按照调试中发现的问题，另外更新。
 3. 告警包信息，立即发送至`nursecall`频道；

定位和离体信息格式：topic: `position`

	JSON: [{"bsid": $basestation_id, "rssi": $rssi, "data": $data.toString, "bcid": $bracelet_id, "timestamp": $epoch_timestamp}...]
	Byte: $basestation_id(6) $rssi(2) $data_from_lescan
	
告警信息格式：topic: `nursecall`

	JSON: {"bsid": $basestation_id, "rssi": $rssi, "nursecall": True, "data": $data.toString, "bcid": $bracelet_id, "timestamp": $epoch_timestamp}
	Byte: $basestation_id(6) $rssi(2) $data_from_lescan
	
基站状态包：topic: `common`

	JSON: {"bsid": $basestation_id, "status": $status, "timestamp": $epoch_timestamp}
	Byte: $basestation_id(6) $status(2)


- 下行报文：服务器下行返回的指令，分为以下几种；
  
  1. `nursecall` 的回复指令；
  2. 其它指令；(#TODO)

一般格式：`alias` 方式或topic: `command`，需根据`bsid`过滤

	JSON: {"bsid": $basestation_id, "type": $commandtype, "content": $content}
	(nursecall_reply): {"bsid": $basestation_id, "type": "nursecall_reply", "content": "..."} 
	
	
- 上行报文2：链接后获取手环数据的上发报文，按手环硬件制造商需求设定(#TODO)；

