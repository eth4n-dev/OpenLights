# DX Light Reverse Engineering on Linux

This repository documents a repeatable process for reverse engineering a USB-connected RGB light marketed as a **DX Light**, then controlling it from Linux without vendor software.

## 1) Identify the device on Linux

~~~bash
lsusb
ls /dev/hidraw*
~~~

Typical output includes:

~~~text
Bus 001 Device 010: ID 1a86:fe07 QinHeng Electronics USBHID
~~~

- Vendor ID: `1a86`
- Product ID: `fe07`

## 2) Map hidraw nodes to interfaces

~~~bash
for d in /sys/class/hidraw/hidraw*/device/uevent; do
  echo "---- $d"
  grep -E "HID_NAME|HID_ID|HID_UNIQ|HID_PHYS" "$d"
done
~~~

~~~bash
for d in /sys/class/hidraw/hidrawN /sys/class/hidraw/hidrawM; do
  echo "==== $d ===="
  readlink -f "$d/device"
  cat "$d/device/uevent"
done
~~~

## 3) Confirm HID report descriptor

~~~bash
sudo usbhid-dump -d 1a86:fe07 -e descriptor
~~~

## 4) Capture packets on Windows

Use Wireshark + USBPcap and filter:

~~~text
usb.transfer_type == 0x01 && usb.endpoint_address.direction == 0
~~~

Extract only HID payload bytes (`usbhid.data`, 64 bytes).

## 5) Packet format

Example first 16 bytes:

~~~text
52 42 10 41 86 01 00 ff 00 3f 40 00 00 00 fe e8
~~~

Derived structure:

~~~text
52 42 10 XX 86 01 RR GG BB 3F 40 00 00 00 FE YY
~~~

Checksum:

~~~text
YY = sum(first_15_bytes) & 0xFF
~~~

## 6) Linux usage

~~~bash
./dxlight 255 0 0
./dxlight 0 255 0
./dxlight 0 0 255
./dxlight 128 64 255 0x55
~~~

## 7) GUI

~~~bash
./dxlight-picker
~~~

## Files

- `list_dxlights.py`
- `dxlights.py`
- `dxlight`
- `dxlight-picker`
