# base station data interface specs

## 1 BLE扫描数据
扫描的数据面向2个手环2个版本：
基础数据包括：手环`mac`地址；

- version bj:
manufacture data example:
`0x00ff12138200000000`
释义：
00-01位`00ff` 固定包头
02位`12` 版本号
03位`13` 状态/命令位；`13`为定位，`66`为告警，`68`为离体
04-07位，手环编号；即将废止

- version dg:
manufacture data example:
`0x00ffxx208000000000`
释义：
00-01位：`00ff`固定的包偷
02位：`10`=步行,`11`=慢跑, `12`=快跑, `13`=无活动, `14` =没有穿戴`20`=轻度睡眠`21`=深度睡眠
03位：`80`=按键


## 2 Socket上报数据
扫描数据重新封装以后有两种格式：BINARY和JSON，分别通过Socket raw协议和MQTT协议发送。

- version 1:
自有json格式；MQTT发送序列化字串；

- version 2：
兼容对方json格式；Socket发送序列化字串；


	{"Command": 2003, "APMac":"~", “DevMac": "-", "Power": 0.0, "Temperature": 0.0, "APAddress":"ip", "APPort":0}

其中：`Command` 对应手环命令，但缺乏`RSSI`字段，应予协调和增加；
 `2001`=报警，`2002`=强拆/离体，`2003`=分配，`2004`=正常/心跳/定位

- version 3：
对方规定的BINARY格式；Socket发送；


	fefe-01-010000000000-f0000001-010000000000-010101-010001000100-f7

