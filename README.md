#### SDN-QoS-RYU-APP-2
>It is a application for QoS routing in software defined network
### required 
* PuLP  —— [A Linear Programming Toolkit for Python ](http://www.optimization-online.org/DB_FILE/2011/09/3178.pdf)
* Ryu ——[SDN controller write in python](https://github.com/osrg/ryu)
* mininet——[Emulator for rapid prototyping of Software Defined Networks](https://github.com/mininet/mininet)
* openvSwitch——[Production Quality, Multilayer Open Virtual Switch](https://www.openvswitch.org/)


create a application for SDN QoS routing, use the traditional method (shortest path or ECMP) for primary routing, when congestion happened, it can reallocate resource use MILP method.

### usage
* `cd ryu/app/`
* `mkdir sdn_routing`
* copy all the file to the directary.
* create a topology  `python mntopo2.py`
* start the application. `ryu-manage shorest_forwarding.py --observe-links`
* use mininet to test the idea.
### others
* any question, email: yuan_bupt@163.com
