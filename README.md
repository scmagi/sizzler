Sizzler: VPN over WebSocket
===========================

Sizzler is a Linux tool, which sets up a virtual network interface on a
computer, and transmit the data sent/received from it to another computer
running the same program.

The transmission utilizes WebSocket, a common technology used in modern
websites. Therefore all other technologies for optimizing WebSocket connections
apply also for Sizzler: firewalls allowing WebSockets will also allow Sizzler
connections; reverse proxies for accelerating accesses may also work.

The network interface set up by Sizzler behaves like a normal network
interface. Since transmitted are IP packets, not only TCP but also UDP and ICMP
are supported.

Sizzler is MIT licensed.

# Install

Use PyPI to install:

    sudo pip3 install sizzler

# Usage

`sizzler` can be run in command line:

* `sizzler -h` for help
* `sudo sizzler -c CONFIG_FILE`, supply a config file in [YAML format][YAML]
  and start the program in client mode. **Sizzler requires root priviledge!**
  But it will drop that right after virtual network interface is set up and
  run.
* `sudo sizzler -s CONFIG_FILE`, just like above, but in server mode.
* `sizzler -e` will print an example config file to standard output.

[YAML]: https://en.wikipedia.org/wiki/YAML
