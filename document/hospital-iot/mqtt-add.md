## 暂时可用的mqtt server：

47.88.15.107 无需验证；

- DEmo页地址：https://eclipse.org/paho/clients/android/
- 配置程序详见: https://github.com/eclipse/paho.mqtt.android

## 链接代码和配置语句例子：

	import org.eclipse.paho.android.service.MqttAndroidClient;
	...//其它依赖
	String serverUri       = "tcp://47.88.15.107:1883";
	MqttAndroidClient sampleClient = new MqttAndroidClient(this.getApplicationContext(), serverUri, clientId);

发送消息：

	MqttMessage msg = new MqttMessage();
                        msg.setQos(1);
                        msg.setPayload(result.getScanRecord().getManufacturerSpecificData().valueAt(0));

                        sampleClient.publish("test", msg);

订阅频道：

	sampleClient.subscribe("test", 0, new IMqttMessageListener() {
                @Override
                public void messageArrived(String topic, MqttMessage message) throws Exception {
                    // message Arrived!
                    System.out.println("Message: " + topic + " : " + new String(message.getPayload()));
                }
            });
            
使用其它脚本调试：
如：https://github.com/eclipse/paho.mqtt.python
 https://github.com/eclipse/paho.mqtt.javascript
 https://github.com/eclipse/paho.mqtt.java
 