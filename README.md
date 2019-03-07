Remote Firewall (iptables) management

This document will serve as a guide to manage iptables remotely using a simple python program.

Features:
 - Only whitelisted IPs will be allowed to make changes.
 - Basic authentication is used, so every request requires username and password to authenticate.
 - Send arguments of iptables as json data.

Install flask and other libraries using `pip`.
Run the program using `python remote_firewall.py`

Example, to add a rule that blocks an IP:-

curl -H "Content-Type: application/json" -XPOST --user test_user:test_password -d '{"chain":"input", "src":"<ip>", "target":"drop"}' http://172.16.1.235:5000/

Valid Parameters & their possible values.

Parameters | Iptables option | Example values
-----------|-----------------|----------------
chain      |     -A/-D       | input, output, prerouting, postrouting, forward
target     |      -j         | accept, drop, reject, masquerade, snat, dnat, etc.
in_iface   |      -i         | <private_interface>(eth0, ens33)
out_iface  |      -o         | <public_interface>(eth0, ens33)
dport      | --dport         | <port>(80)
to_destination | --to        | <ip:port>(192.168.10.10:80)
table      |    -t           | nat, filter, security, mangle, raw
protocol   |    -p           | tcp, udp
src        |    -s           | <source_IP>
dst        |    -d           | <destination_IP>
to_source  |    --to         | <ip>

Types of requests:-
POST : To add rule
DELETE: To delete a rule(same json data as used to add)
GET: To list iptables rules
More Examples

Calls    |    Result
---------|-------------
POST -d '{"iface":"eth0:1", "ip":"172.16.1.230"}' http://172.16.1.235:5000/add_ip | Add an IP to interface eth0:1.
POST -d '{"dst":"172.16.1.230", "to_destination":"192.16.1.10"}' http://172.16.1.235:5000/dnat | 1:1 NAT. All traffic from 172.16.1.230 is forwarded to 192.16.1.10
POST -d '{"src":"192.16.1.10", "to_source":"172.16.1.230"}' http://172.16.1.235:5000/snat | Changes source IP of the traffic from 192.16.1.10 to 172.16.1.230. Allows the machines in internal network to connect public network.
POST -d '{"dst":"192.16.1.10", "to_source":"172.16.1.230"}' http://172.16.1.235:5000/snat | Changes source IP of all the packets flowing to 192.168.1.10
DELETE -d '{"iface":"eth0:1"}' http://172.16.1.235:5000/remove_ip | Deletes the IP alias bound to the interface
POST -d '{"chain":"input", "src":"192.168.10.10", "target":"drop"}' http://172.16.1.235:5000/ | Blocking all the incoming packets from 192.168.10.10 . Translates to command:- iptables -A INPUT -s 192.168.10.10 -j DROP 
POST -d '{"chain":"input", "src":"192.168.10.10", "target":"drop", "in_iface":"eth0"}' http://172.16.1.235:5000/ | Blocking all the incoming packets from 192.168.10.10 on the interface eth0. Translates to command:- iptables -A INPUT -s 192.168.10.10 -i eth0 -j DROP
DELETE -d '{"chain":"input", "src":"192.168.10.10", "target":"drop", "in_iface":"eth0"}' http://172.16.1.235:5000/ | Delete above rule. Translates to command:- iptables -D INPUT -s 192.168.10.10 -i eth0 -j DROP
POST -d '{"chain":"input", "src":"192.168.10.10", “target”:”accept”}’ http://172.16.1.235:5000/ | Allow incoming packets from 192.168.10.10. Translates to command:- iptables -A INPUT -s 192.168.10.10 -j ACCEPT
POST -d '{"chain":"postrouting", "-s":"192.168.1.0/24", "out_iface":"eth0", "target":"masquerade", "to_source":"172.16.1.235"}' http://172.16.1.235:5000/ | Allow internal traffic out through gateway. Alters the IPs of outgoing packets with its own. Translates to command:- iptables -A POSTROUTING -s 192.168.10.0/24 -j SNAT --to-source 172.16.1.235
POST -d '{"chain":"prerouting","table":"nat", "dport":"81", "target":"dnat", "protocol":"tcp", "to_destination":"192.168.10.3:80"}' http://172.16.1.235:5000/ | Enable port forwarding. Forward all the traffic coming to port 81 to 192.168.10.3:80. Translates to command:- iptables -t nat -A PREROUTING -p tcp --dport 81 -j DNAT --to 192.168.10.3:80 
POST -d '{"chain":"postrouting","table":"nat", "dst":"192.168.1.0/24", "target":"masquerade", "out_iface":"eth1"}' http://172.16.1.235:5000/ | NAT public IPs to private for packets flowing to internal network. This will alter the IPs of all the packets flowing to internal network(192.168.1.0/24). eth1 should be private interface. Translates to command:- iptables -t nat -A POSTROUTING -d 192.168.1.0/24 -o eth1 -j MASQUERADE
POST -d '{"chain":"prerouting","table":"nat", "dst":"172.25.10.10", "target":"dnat", "protocol":"tcp", "to_destination":"192.168.10.3"}' http://172.16.1.235:5000/ | Forwards all the traffic intended for 172.25.10.10 to 192.168.10.3. Will forward traffic to same port(i.e. Port 80 to 80, 81 to 81..). Translates to:- iptables -t nat -A PREROUTING -p tcp -d 172.25.10.10 -j DNAT --to 192.168.10.3  
POST -d '{"chain":"prerouting","table":"nat", "dst":"172.25.10.10", "target":"dnat", "protocol":"tcp", "to_destination":"192.168.10.3:445"}' http://172.16.1.235:5000/ | Forwards traffic of all ports of 172.25.10.10 to port 445 of 192.168.10.3. Translates to:- iptables -t nat -A PREROUTING -p tcp -d 172.25.10.10 -j DNAT --to 192.168.10.3:445
POST -d '{"chain":"prerouting","table":"nat", "dst":"172.25.10.10" "dport":"80:90", "target":"dnat", "protocol":"tcp", "to_destination":"192.168.10.3:80-90"}' http://172.16.1.235:5000/ | Forwards traffic of ports 80-90 172.25.10.10 to port 80-90 of 192.168.10.3. Translates to:- iptables -t nat -A PREROUTING -p tcp -d 172.25.10.10 --dport 80:90 -j DNAT --to 192.168.10.3:80-90
GET http://172.16.1.235:5000/list | Lists iptables rules. Translates to:- iptables -L
GET http://172.16.1.235:5000/list?table=nat | Lists iptables rules for nat table. Specify table name to list rules for tables other than filter. Translates to:- iptables -L -t nat 


Example call

Enable port forwarding for public traffic to access internal network
curl -H "Content-Type: application/json" -XPOST --user <username>:<password> -d '{"chain":"prerouting","table":"nat", "dport":"<destination port>", "dst":"<destination>", "target":"dnat", "to_destination":"<ip>:<port>", "protocol":"tcp"}' http://172.16.1.235:5000/

-H "Content-Type: application/json" -- required for submitting json data
--user test_user:test_password -- every call requires username & password to authenticate


Route calls:-

Calls    |    Result
---------|-------------
GET http://172.16.1.235:5000/route | Lists routing table. Translates to command:- ip route
POST http://172.16.1.235:5000/route -d '{"net":"192.168.1.0", "netmask":"255.255.255.0", "gw":"192.168.1.1"}' | Add a route to 192.168.1.0/24 via 192.168.1.1. Translates to command:- route add -net 192.168.1.0 netmask 255.255.255.0 gw 192.168.1.1. 
POST http://172.16.1.235:5000/route -d '{"net":"192.168.1.0", "netmask":"255.255.255.0", "dev":"eth3"}' | Add a route to 192.168.1.0/24 via eth3 interface. Translates to command:- route add -net 192.168.1.0 netmask 255.255.255.0 dev eth3.
POST http://172.16.1.235:5000/route -d '{"gw":"172.16.1.1"}' | Add a default route via 172.16.1.1. Translates to command:- route add default gw 172.16.1.1.
DELETE http://172.16.1.235:5000/route -d '{"net":"192.168.1.0", "netmask":"255.255.255.0", "gw":"192.168.1.1"}' | Delete the route to 192.168.1.0/24 via 192.168.1.1. Translates to command:- route del -net 192.168.1.0 netmask 255.255.255.0 gw 192.168.1.1. 
