# BS 基站设置：

1. 重启自动运行 python (写在ubuntu MATE里的 personal)
2. predefined wifi connect:
	1. xprod (无密码)
	2. QiKU_259F / 5720qcxy
3. 通过优先wifi登录之；
4. 修改`t.cnf`文件中的各项参数；增加工作wifi；
5. 重启生效。在基站中检验结果。
6. 已增加sudo 的NOPASSWD的设置(in visudo)

### Defects （1204日1.0版）

- wifi设置其中通过ui配置的需要输入密码确认；即便是允许了所有用户也不行；
- wifi的设置应为wlan0（nmcli配置），而不是mac地址（GUI配置）
- crontab 重启函数需要增加sudo
- 目前未知原因的系统挂掉，重启可恢复，但尚不清楚原因；（TODO：查/var/log）
