#!/usr/bin/env python3

import dbus
import os
import sys
from subprocess import call

def notify(summary, body):
  call(["notify-send", "-a", "obdevicemenu", summary, body])

class DbusProxyIface(object):
  def __init__(self, proxy, iface):
    self.proxy = proxy;
    self.iface = iface;

  def GetProperty(self, property):
    return self.proxy.Get(self.iface, property, dbus_interface=dbus.PROPERTIES_IFACE, byte_arrays=True)

  def SetProperty(self, property, value):
    self.proxy.Set(self.iface, property, value, dbus_interface=dbus.PROPERTIES_IFACE)

  def CallMethod(self, method, *args):
    return self.proxy.get_dbus_method(method, dbus_interface=self.iface)(byte_arrays=True, *args)

bus = dbus.SystemBus()

if len(sys.argv) == 1:
  proxy = DbusProxyIface(bus.get_object("org.freedesktop.UDisks2", "/org/freedesktop/UDisks2"), 'org.freedesktop.DBus.ObjectManager')
  objects = proxy.CallMethod(method="GetManagedObjects")
  mountable_devices = []
  for k,v in objects.items():
    if str(k).find("/block_devices") != -1:
      for k2,v2 in v.items():
        if k2 == "org.freedesktop.UDisks2.Filesystem":
          mountable_devices.append((DbusProxyIface(bus.get_object("org.freedesktop.UDisks2", k), "org.freedesktop.UDisks2.Filesystem"), v2["MountPoints"]))
  mountable_devices.sort(key=lambda k: str(k[0].proxy.object_path))

  print("<openbox_pipe_menu>")
  for d,mountPoints in mountable_devices:
    device = os.path.basename(d.proxy.object_path)
    action = "Mount" if len(mountPoints) == 0 else "Unmount"
    mountPoint = " (mounted at '{}')".format(mountPoints[0].decode('UTF-8').rstrip('\0')) if len(mountPoints)>0 else ""
    print('  <separator label="{}{}" />'.format(device, mountPoint))
    print('  <item label="{}">'.format(action))
    print('    <action name="Execute">')
    print('      <command>obdevicemenu {} {}</command>'.format(device, action))
    print('    </action>')
    print('  </item>')
  print('</openbox_pipe_menu>')
elif len(sys.argv) == 3:
  try:
    mountPoint = DbusProxyIface(bus.get_object("org.freedesktop.UDisks2", "/org/freedesktop/UDisks2/block_devices/{}".format(sys.argv[1])), "org.freedesktop.UDisks2.Filesystem").CallMethod(sys.argv[2], [])
    notify("Success", "Successfully {} {} {}".format("unmounted" if sys.argv[2]=="Unmount" else "mounted", sys.argv[1], "" if sys.argv[2]=="Unmount" else "at {}".format(mountPoint)))
  except Exception as e:
    notify("Error {} {}".format("unmounting" if sys.argv[2]=="Unmount" else "mounting", sys.argv[1]), "Error message: {}".format(e))

