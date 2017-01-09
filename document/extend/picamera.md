## prepare for pi camera

hardware:
pi3 model b

os:
ubuntu MATE 16.04

#### config.txt

start_x = 0 >> start = **1** `default disabled camera`
gpu_mem=64 >> gpu_mem=128   `dunno why`

#### python-picamera

picamera is pre-installed in ubuntu MATE
if not：

```
sudo apt-get install python3-picamera
sudo apt install python-picamera


```



test:
python
import picamera
camera = picamera.PiCamera()
camera.capture('image.jpg')

在zkjs888
192.168.43.87 上测试成功；