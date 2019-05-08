import os, time

#trying to start everything from python
os.system("start labrad")
time.sleep(5)
os.system("start python ./servers/serial_server.py")
time.sleep(2)
os.system("start python ./servers/julabo_lc4.py")
time.sleep(2)

os.system("python main.py")
