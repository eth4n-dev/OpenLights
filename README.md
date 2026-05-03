# DX Light on Linux (Beginner-Friendly Guide)

This project shows how to control a USB RGB light, marketed as **DX Light**, on Linux.

The official control app is Windows-only, but the light itself is just a USB HID device. That means the Windows app sends small binary messages to the light, such as “set red”, “set blue”, or “set purple”.

This guide explains how to find the correct USB interface, understand the message format, and control the light from Linux.

It also explains what to do if you do not have Windows or dual-boot.

---

## Quick summary

Your light is a USB device.

The Windows app sends small 64-byte HID messages to it.

This repo explains how we:

1. Found which USB connection is the real control channel.
2. Captured messages sent by the Windows app.
3. Learned the message format.
4. Recreated those messages on Linux.

Result:

- RGB control from a Linux CLI tool
- RGB control from a small Linux GUI picker

---

## Important note about Windows

You do **not** need to dual-boot.

For the packet capture step, you only need temporary access to Windows. That can be:

- a Windows laptop
- a friend’s Windows computer
- a separate Windows PC
- a Windows virtual machine with USB passthrough

You only need Windows long enough to run the official DX Light app, change a few colors, and capture the USB packets.

After that, everything can be done on Linux.

If you do not have access to Windows at all, that is also okay. Since the packet format is already known for this device, you can try the Linux-only method first.

---

## What terminal are these commands for?

The commands in this guide are written for a normal Linux shell.

They should work in:

- Bash
- Zsh
- most standard Linux terminals

Examples of terminal apps where these commands should work:

- GNOME Terminal
- KDE Konsole
- Linux Mint Terminal
- Ubuntu Terminal
- Alacritty
- Kitty

Some commands start with `sudo`.

That means the command needs administrator/root permission.

---

## Glossary

### USB

USB is the standard way devices connect to your computer.

Your DX Light connects over USB.

---

### HID

HID means **Human Interface Device**.

Keyboards and mice use HID, but many RGB devices also use HID because it is simple and works on many systems.

---

### Interface

One USB device can expose multiple logical parts.

For example, one DX Light device may appear as:

- a keyboard-like interface
- a vendor control interface

The keyboard-like interface is usually not the one we want.

The vendor control interface is usually the one used for RGB control.

---

### hidraw

On Linux, raw HID devices appear as files like:

```bash
/dev/hidraw0
/dev/hidraw1
/dev/hidraw2
```

These files let programs send raw HID messages directly to USB devices.

---

### Report descriptor

A report descriptor is metadata that describes what kind of HID messages a device expects.

You usually do not need to fully understand it, but it helps confirm that the device uses 64-byte HID reports.

---

### Packet / report

A packet, also called a report, is one message sent to the device.

For this DX Light, each useful report is 64 bytes long.

---

### Vendor-defined

Vendor-defined means the manufacturer made their own custom message format.

It is not a standard keyboard, mouse, or lighting protocol.

---

### Checksum

A checksum is a small value used to verify that a packet is valid.

For this light, the checksum is calculated by adding the first 15 bytes of the packet and keeping only the lowest 8 bits.

---

# Linux-only method

Use this method if:

- you do not have Windows
- you do not want to use Windows
- you just want to control the light from Linux

This works because the packet format for this device is already known.

---

## Step 1) Connect the light

Plug the DX Light into your Linux computer.

Then run:

```bash
lsusb
```

You should see something similar to:

```text
Bus 001 Device 010: ID 1a86:fe07 QinHeng Electronics USBHID
```

The important IDs are:

```text
Vendor ID:  1a86
Product ID: fe07
```

If you do not see `1a86:fe07`, your device may be different, or it may not have been detected correctly.

Try unplugging and reconnecting the light.

---

## Step 2) List hidraw devices

Run:

```bash
ls /dev/hidraw*
```

You may see something like:

```text
/dev/hidraw0
/dev/hidraw1
/dev/hidraw2
/dev/hidraw3
```

The exact numbers will be different depending on your system.

---

## Step 3) Find which hidraw device belongs to the DX Light

Run:

```bash
for d in /sys/class/hidraw/hidraw*/device/uevent; do
  echo "---- $d"
  grep -E "HID_NAME|HID_ID|HID_UNIQ|HID_PHYS" "$d"
done
```

Look for entries that mention the DX Light’s USB IDs:

```text
1A86
FE07
QinHeng
USBHID
```

This helps you find which `/dev/hidrawX` devices belong to the light.

---

## Step 4) Find the correct HID interface

The DX Light can expose more than one HID interface.

Not every interface controls the RGB light.

There may be:

- one keyboard-like interface
- one vendor-defined control interface

The vendor-defined interface is usually the one we want.

To inspect likely candidates, run:

```bash
for d in /sys/class/hidraw/hidrawN /sys/class/hidraw/hidrawM; do
  echo "==== $d ===="
  readlink -f "$d/device"
  cat "$d/device/uevent"
done
```

Replace `hidrawN` and `hidrawM` with the real hidraw names you found.

For example:

```bash
for d in /sys/class/hidraw/hidraw3 /sys/class/hidraw/hidraw4; do
  echo "==== $d ===="
  readlink -f "$d/device"
  cat "$d/device/uevent"
done
```

You are looking for the interface that looks vendor-defined rather than keyboard-like.

---

## Step 5) Read HID descriptors

Install `usbhid-dump` if needed.

On Debian, Ubuntu, or Linux Mint:

```bash
sudo apt install usbhid-dump
```

Then run:

```bash
sudo usbhid-dump -d 1a86:fe07 -e descriptor
```

This is a sanity check.

It helps confirm that the device exposes HID interfaces and uses HID reports.

For this project, the important part is that the useful report is 64 bytes long.

---

## Step 6) Understand the known packet format

The useful part of the packet is 16 bytes long:

```text
52 42 10 XX 86 01 RR GG BB 3F 40 00 00 00 FE YY
```

Where:

```text
XX = sequence byte
RR = red value
GG = green value
BB = blue value
YY = checksum
```

The RGB values go from `0` to `255`.

For example:

```text
255 0 0
```

means full red.

```text
0 255 0
```

means full green.

```text
0 0 255
```

means full blue.

The full HID report must be 64 bytes long:

```text
16 useful bytes + 48 zero bytes
```

The checksum is calculated like this:

```text
YY = sum(first_15_bytes) & 0xFF
```

You usually do not need to calculate the checksum yourself.

The provided Linux tool does it automatically.

---

## Step 7) Use the Linux CLI tool

To set the light to red:

```bash
./dxlight 255 0 0
```

To set it to green:

```bash
./dxlight 0 255 0
```

To set it to blue:

```bash
./dxlight 0 0 255
```

To set it to white:

```bash
./dxlight 255 255 255
```

To set a custom purple color:

```bash
./dxlight 128 64 255
```

The format is:

```bash
./dxlight RED GREEN BLUE
```

Each value must be between `0` and `255`.

You can also provide a custom sequence byte:

```bash
./dxlight 128 64 255 0x55
```

Most users do not need to do that.

---

## Step 8) Use the Linux GUI picker

Run:

```bash
./dxlight-picker
```

The GUI includes:

- hue bar
- saturation/brightness square
- RGB input fields
- live preview
- direct sending to the light

---

## Step 9) Fix permission errors

If you get an error like:

```text
Permission denied: /dev/hidrawX
```

your user does not have permission to write to the hidraw device.

For quick testing, run the CLI with `sudo`:

```bash
sudo ./dxlight 255 0 0
```

If that works, the problem is permissions.

For a permanent fix, create a udev rule.

Open a new rule file:

```bash
sudo nano /etc/udev/rules.d/99-dxlight.rules
```

Add this line:

```text
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="fe07", MODE="0666"
```

Save the file.

Then reload the udev rules:

```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Unplug and reconnect the light.

Now try again without `sudo`:

```bash
./dxlight 255 0 0
```

---

# Windows capture method

This method is useful if:

- the Linux-only method does not work
- your device behaves differently
- your device has a different packet format
- you want to reverse engineer the protocol yourself
- you want to verify the messages sent by the official app

Again, you do **not** need to dual-boot.

You only need temporary access to Windows.

That can be:

- a Windows laptop
- a friend’s Windows computer
- a separate Windows PC
- a Windows virtual machine with USB passthrough

The goal is only to capture a few packets from the official app.

After that, you can return to Linux.

---

## Step 1) Install capture tools on Windows

Install:

- Wireshark
- USBPcap

USBPcap is usually offered during Wireshark installation on Windows.

---

## Step 2) Start capturing USB traffic

Open Wireshark.

Choose the USBPcap interface that contains the DX Light.

Start capturing.

Then open the official DX Light app and change some colors.

Good colors to test:

```text
red
green
blue
white
purple
```

Changing simple colors makes it easier to understand which bytes represent RGB values.

---

## Step 3) Filter outgoing HID packets

In Wireshark, use this filter:

```text
usb.transfer_type == 0x01 && usb.endpoint_address.direction == 0
```

This shows outgoing interrupt transfers.

These are likely the packets sent from the app to the light.

---

## Step 4) Copy only the HID payload

This is very important.

Copy only the HID payload bytes:

```text
usbhid.data
```

The payload should be 64 bytes.

Do **not** copy the full USB frame.

The full USB frame contains extra USB metadata, which is not part of the actual message sent to the light.

---

## Step 5) Compare captured packets

Example first 16 bytes:

```text
52 42 10 41 86 01 00 ff 00 3f 40 00 00 00 fe e8
```

Known structure:

```text
52 42 10 XX 86 01 RR GG BB 3F 40 00 00 00 FE YY
```

Where:

```text
XX = sequence byte
RR = red value
GG = green value
BB = blue value
YY = checksum
```

In this example:

```text
RR GG BB = 00 ff 00
```

That means:

```text
red   = 0
green = 255
blue  = 0
```

So this packet sets the light to green.

---

# Packet format

The useful 16-byte header looks like this:

```text
52 42 10 XX 86 01 RR GG BB 3F 40 00 00 00 FE YY
```

The final report must be 64 bytes long.

That means the 16-byte header is followed by 48 zero bytes.

Example layout:

```text
52 42 10 XX 86 01 RR GG BB 3F 40 00 00 00 FE YY
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
```

Checksum rule:

```text
YY = sum(first_15_bytes) & 0xFF
```

Example first 15 bytes:

```text
52 42 10 41 86 01 00 ff 00 3f 40 00 00 00 fe
```

Checksum:

```text
e8
```

So the first 16 bytes become:

```text
52 42 10 41 86 01 00 ff 00 3f 40 00 00 00 fe e8
```

---

# Troubleshooting

## `lsusb` does not show the device

Try unplugging and reconnecting the light.

Then run:

```bash
lsusb
```

Also try:

- a different USB port
- a different USB cable
- avoiding USB hubs

---

## I see multiple `/dev/hidrawX` devices

That is normal.

The DX Light may expose more than one HID interface.

Use this command to inspect them:

```bash
for d in /sys/class/hidraw/hidraw*/device/uevent; do
  echo "---- $d"
  grep -E "HID_NAME|HID_ID|HID_UNIQ|HID_PHYS" "$d"
done
```

---

## The command runs, but the light does not change

Possible causes:

- wrong `/dev/hidrawX` device
- wrong HID interface
- missing permissions
- another program is controlling the light
- your device uses a slightly different packet format

First try:

```bash
sudo ./dxlight 255 0 0
```

If that works, it was a permissions problem.

If it still does not work, check that you are sending to the correct hidraw interface.

---

## Permission denied

For quick testing:

```bash
sudo ./dxlight 255 0 0
```

For permanent access, create the udev rule from the permissions section.

---

## My device has a different vendor/product ID

This guide is written for this device:

```text
1a86:fe07
```

If your device has a different ID, it may still be similar, but the code may need changes.

You may need to capture packets from the official app and compare them.

---

## Wireshark shows too much data

Make sure you are using this filter:

```text
usb.transfer_type == 0x01 && usb.endpoint_address.direction == 0
```

Also make sure you copy only:

```text
usbhid.data
```

Do not copy the full USB frame.

---

# Files in this repo

```text
list_dxlights.py   Windows helper: lists interfaces for this device
dxlights.py        Windows sender using hidapi and the MI_00 interface
dxlight            Linux CLI sender
dxlight-picker     Linux Tkinter GUI sender
```

---

# Final notes

The easiest path is:

```text
1. Plug in the light.
2. Find the correct hidraw device.
3. Run the Linux dxlight tool.
4. Fix permissions if needed.
```

The Windows capture step is optional.

You only need it if:

- the known packet format does not work
- your device is a different variant
- you want to verify the protocol yourself

You do not need dual-boot.

A Windows laptop, a friend’s Windows computer, a separate Windows PC, or a Windows VM with USB passthrough is enough for the capture step.
