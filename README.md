Graphical User Interface for iperf3
===================================

This is a python 2.7 program to give a graphical front end to iperf3

This is version 1.0 so it may be buggy!
**NOTE: This is a python 2.7 program**
If you want to use it with python 3.xx some work will need to be done.

Tested on Ubuntu 14.04, and Windows 10, **no guarantees** on anything else!

## Introduction
This program has the following features:
* enter your own server ip/fqdm
* presets for public iperf3 servers
* ports configurable (and presets)
* several (not all) options graphically configurable
* large gauge display
* works on windows or linux
* shows ping values
* gives download and upload speeds

![screenshot](https://github.com/NickWaterton/iperf3-GUI/blob/master/Screenshot%202018-04-24%2018.19.46.png "Screenshot")

## Pre-Requisites
You need iperf3 installed. It can be downloaded from here: https://iperf.fr/iperf-download.php

## Dependencies
The program will optionally use pyping if you have it installed, otherwise it uses plain old ping.

See:https://pypi.org/project/pyping/
install with `pip install pyping`

## Install
First you need python 2.7 installed. **This program will not work with Python 3.x without some work**

now clone the repository from GitHub (obviously you need `git` installed)
```bash
git clone https://github.com/NickWaterton/iperf3-GUI.git
cd iperf3-GUI
```
You should now have the program `iperf.py` - make sure the file is executable

No need to install anything, you can just run the program as is.

run `./iperf.py -h` (or `python ./iperf.py -h` if you are on windows)

```
usage: iperf.py [-h] [-I IPERF_EXEC] [-ip IP_ADDRESS] [-p PORT] [-r RANGE]
                [-R] [-m {OFF,Track,Peak}] [-D] [-V] [-v]

Iperf3 GUI Network Speed Tester

optional arguments:
  -h, --help            show this help message and exit
  -I IPERF_EXEC, --iperf_exec IPERF_EXEC
                        location and name of iperf3 executable
                        (default=iperf3)
  -ip IP_ADDRESS, --ip_address IP_ADDRESS
                        default server address (default=192.168.100.119)
  -p PORT, --port PORT  server port (default=5201)
  -r RANGE, --range RANGE
                        range to start with in Mbps (default=10)
  -R, --reset_range     Do NOT Reset range to Default for Upload test
  -m {OFF,Track,Peak}, --max_mode {OFF,Track,Peak}
                        Show Peak Mode (default = Peak)
  -D, --debug           debug mode
  -V, --verbose         print everything
  -v, --version         show program's version number and exit
```

## Quick Start
You need to know the pathname of your iperf3 executable, the default is `iperf3`, but you can use the `-I` option to specify the pathname
for example on my Windows system I use
```bash
python .\iperf.py -I D:\utils\iperf3.exe
```
Because my `iperf3.exe` is in my `D:/utils directory`.
Using Linux, the default usually works just fine (if iperf3 was installed using `apt-get` or is otherwise in your `PATH`, so you would use:
```bash
.\iperf.py
```

You may need to be Administrator to use ping - it works fine for me as none-Administrator, but read the pyping page (if you are using it).

To test on your local network, you will need another computer running another copy of iperf3 as as server:
```bash
.\iperf3 -s
```
You can then test your local network/wifi speeds against the new server you just started using it's ip address.

That's it!