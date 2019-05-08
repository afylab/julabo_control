# Copyright []
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
### BEGIN NODE INFO
[info]
name = Julabo LC4 temperature controller
version = 1.0
description =
[startup]
cmdline = %PYTHON% %FILE%
timeout = 20
[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""

import platform
global serial_server_name
serial_server_name = platform.node() + '_serial_server'

from labrad.server import setting
from labrad.devices import DeviceServer,DeviceWrapper
from twisted.internet.defer import inlineCallbacks, returnValue
import labrad.units as units
from labrad.types import Value

TIMEOUT = Value(5,'s')
BAUD    = 4800
PARITY = 'E'
STOP_BITS = 1
BYTESIZE= 7
RTSCTS = True

class JulaboLC4Wrapper(DeviceWrapper):

    @inlineCallbacks
    def connect(self, server, port):
        """Connect to a device."""
        print 'connecting to "%s" on port "%s"...' % (server.name, port),
        self.server = server
        self.ctx = server.context()
        self.port = port
        p = self.packet()
        p.open(port)
        print 'opened on port "%s"' %self.port
        p.baudrate(BAUD)
        p.parity(PARITY)
        p.stopbits(STOP_BITS)
        p.bytesize(BYTESIZE)
        p.rtscts(RTSCTS)
        p.read()  # clear out the read buffer
        p.timeout(TIMEOUT)
        print(" CONNECTED ")
        yield p.send()

    def packet(self):
        """Create a packet in our private context."""
        return self.server.packet(context=self.ctx)

    def shutdown(self):
        """Disconnect from the serial port when we shut down."""
        return self.packet().close().send()

    @inlineCallbacks
    def write(self, code):
        """Write a data value to the temperature controller."""
        yield self.packet().write(code).send()

    @inlineCallbacks
    def read(self):
        p=self.packet()
        p.read_line('\n')
        ans=yield p.send()
        returnValue(ans.read_line)

    @inlineCallbacks
    def query(self, code):
        """ Write, then read. """
        p = self.packet()
        p.write(code+'\r')
        p.read_line('\n')
        ans = yield p.send()
        returnValue(ans.read_line)


class JulaboLC4Server(DeviceServer):
    name = 'julabo_lc4'
    deviceName = 'Julabo LC4'
    deviceWrapper = JulaboLC4Wrapper

    @inlineCallbacks
    def initServer(self):
        print 'loading config info...',
        self.reg = self.client.registry()
        yield self.loadConfigInfo()
        print 'done.'
        print self.serialLinks
        yield DeviceServer.initServer(self)

    @inlineCallbacks
    def loadConfigInfo(self):
        """Load configuration information from the registry."""
        # reg = self.client.registry
        # p = reg.packet()
        # p.cd(['', 'Servers', 'Heat Switch'], True)
        # p.get('Serial Links', '*(ss)', key='links')
        # ans = yield p.send()
        # self.serialLinks = ans['links']
        reg = self.reg
        yield reg.cd(['', 'Servers', 'Julabo LC4', 'Links'], True)
        dirs, keys = yield reg.dir()
        p = reg.packet()
        print " created packet"
        print "printing all the keys",keys
        for k in keys:
            print "k=",k
            p.get(k, key=k)

        ans = yield p.send()
        print "ans=",ans
        self.serialLinks = dict((k, ans[k]) for k in keys)


    @inlineCallbacks
    def findDevices(self):
        """Find available devices from list stored in the registry."""
        devs = []
        # for name, port in self.serialLinks:
        # if name not in self.client.servers:
        # continue
        # server = self.client[name]
        # ports = yield server.list_serial_ports()
        # if port not in ports:
        # continue
        # devName = '%s - %s' % (name, port)
        # devs += [(devName, (server, port))]
        # returnValue(devs)
        for name, (serServer, port) in self.serialLinks.items():
            if serServer not in self.client.servers:
                continue
            server = self.client[serServer]
            print server
            print port
            ports = yield server.list_serial_ports()
            print ports
            if port not in ports:
                continue
            devName = '%s - %s' % (serServer, port)
            devs += [(devName, (server, port))]

       # devs += [(0,(3,4))]
        returnValue(devs)

    @setting(100)
    def connect(self,c,server,port):
        dev=self.selectedDevice(c)
        yield dev.connect(server,port)

    @setting(101,returns='s')
    def ID(self,c):
        dev=self.selectedDevice(c)
        yield dev.write("*IDN?\r")
        ans = yield dev.read()
        returnValue(ans)

    @setting(102,returns='s')
    def get_setpoint(self,c):
        dev=self.selectedDevice(c)
        yield dev.write("in_sp_00\r")
        ans = yield dev.read()
        returnValue(ans[:-1])

    @setting(202, data='v')
    def set_temp(self,c,data):
        dev=self.selectedDevice(c)
        yield dev.write("out_sp_00 %s\r"%data)

    @setting(203,returns='s')
    def get_temp(self,c):
        dev=self.selectedDevice(c)
        yield dev.write('in_pv_00\r')
        ans = yield dev.read()
        returnValue(ans[:-1])

    @setting(204,returns='s')
    def get_heater(self,c):
        dev=self.selectedDevice(c)
        yield dev.write('in_pv_01\r')
        ans = yield dev.read()
        returnValue(ans[:-1])

    @setting(105, data='v')
    def set_Xp(self,c,data):
        dev=self.selectedDevice(c)
        yield dev.write('out_par_00 %s\r'%data)

    @setting(205, returns='s')
    def get_Xp(self,c):
        dev=self.selectedDevice(c)
        yield dev.write('in_par_00\r')
        ans = yield dev.read()
        returnValue(ans[:-1])

    @setting(106, data='v')
    def set_Tn(self,c,data):
        dev=self.selectedDevice(c)
        yield dev.write('out_par_01 %s\r'%data)

    @setting(206, returns='s')
    def get_Tn(self,c):
        dev=self.selectedDevice(c)
        yield dev.write('in_par_01\r')
        ans = yield dev.read()
        returnValue(ans[:-1])

    @setting(107, data='v')
    def set_Tv(self,c,data):
        dev=self.selectedDevice(c)
        yield dev.write('out_par_02 %s\r'%data)

    @setting(207, returns='s')
    def get_Tv(self,c):
        dev=self.selectedDevice(c)
        yield dev.write('in_par_02\r')
        ans = yield dev.read()
        returnValue(ans[:-1])


    @setting(301)
    def start(self,c):
        dev=self.selectedDevice(c)
        yield dev.write("out_mode_05 1\r")

    @setting(302)
    def stop(self,c):
        dev=self.selectedDevice(c)
        yield dev.write("out_mode_05 0\r")

    @setting(303,returns = 's')
    def status(self,c):
        dev=self.selectedDevice(c)
        yield dev.write("status\r")
        ans = yield dev.read()
        returnValue(ans[:-1])


    @setting(9001,v='v')
    def do_nothing(self,c,v):
        pass

    @setting(9002)
    def read(self,c):
        dev=self.selectedDevice(c)
        ret=yield dev.read()
        returnValue(ret)

    @setting(9003)
    def write(self,c,phrase):
        dev=self.selectedDevice(c)
        yield dev.write(phrase)
    @setting(9004)
    def query(self,c,phrase):
        dev=self.selectedDevice(c)
        yield dev.write(phrase)
        ret = yield dev.read()
        returnValue(ret)


__server__ = JulaboLC4Server()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)