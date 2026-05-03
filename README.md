# USB RGB Light Control on Linux

A beginner-friendly reverse engineering guide for USB RGB lights with Windows-only control apps.

This guide started with a light sold as **DX Light**, but the method can apply to many similar USB RGB lights.

It is useful for lights that:

- connect over USB
- appear as HID devices
- receive small binary control messages
- use a vendor-defined/custom protocol
- have a Windows app that sends color commands

The exact packet format may be different for other lights, but the general process is similar.

---

## Quick summary

Many USB RGB lights are controlled by small binary messages.

The official Windows app may send commands like:

```text
set color to red
set color to blue
set color to purple
```

But over USB, those commands are usually sent as raw binary HID reports.

This guide explains how to:

1. Find the USB device on Linux.
2. Find the correct HID interface.
3. Check whether the device uses raw HID reports.
4. Capture packets from the official app, if needed.
5. Understand the packet format.
6. Recreate those packets on Linux.

Result:

- RGB control from a Linux CLI tool
- optional RGB control from a small Linux GUI picker

---

## Important note about Windows

You do **not** need to dual-boot.

For the packet capture step, you only need temporary access to Windows. That can be:

- a Windows laptop
- a friend’s Windows computer
- a separate Windows PC
- a Windows virtual machine with USB passthrough

You only need Windows long enough to run the official app, change a few colors, and capture the USB packets.

After that, everything can be done on Linux.

If your light uses the same packet format as the example device, you may not need Windows at all.

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

<details>
<summary><strong>Beginner vocabulary</strong></summary>

## USB

USB is the standard way devices connect to your computer.

Your RGB light connects over USB.

---

## HID

HID means **Human Interface Device**.

Keyboards and mice use HID, but many RGB devices also use HID because it is simple and works on many systems.

---

## Interface

One USB device can expose multiple logical parts.

For example, one USB RGB light may appear as:

- a keyboard-like interface
- a vendor control interface
- another custom HID interface

The keyboard-like interface is usually not the one we want.

The vendor-defined or custom interface is usually the one used for RGB control.

---

## hidraw

On Linux, raw HID devices appear as files like:

```bash
/dev/hidraw0
/dev/hidraw1
/dev/hidraw2
```

These files let programs send raw HID messages directly to USB devices.

---

## Report descriptor

A report descriptor is metadata that describes what kind of HID messages a HID device expects.

You usually do not need to fully understand it, but it helps confirm things like report size and whether an interface is vendor-defined.

---

## Packet / report

A packet, also called a report, is one message sent to the device.

In the example device, each useful report is 64 bytes long.

Other lights may use a different size.

---

## Vendor-defined

Vendor-defined means the manufacturer made their own custom message format.

It is not a standard keyboard, mouse, or lighting protocol.

---

## Checksum

A checksum is a small value used to verify that a packet is valid.

Some lights use a checksum.

Some do not.

For the example device, the checksum is calculated by adding the first 15 bytes of the packet and keeping only the lowest 8 bits.

</details>

---

<details>
<summary><strong>Linux-only method</strong></summary>

Use this method if:

- you do not have Windows
- you do not want to use Windows
- you want to check whether your light matches the known example format
- you want to inspect the device from Linux first

This works directly only if your light uses the same or a very similar packet format as the example device.

If it does not, you may need to use the capture method later.

---

## Step 1) Connect the light

Plug the USB RGB light into your Linux computer.

Then run:

```bash
lsusb
```

You should see a list of USB devices.

For the example DX Light device, the output looks similar to:

```text
Bus 001 Device 010: ID 1a86:fe07 QinHeng Electronics USBHID
```

The important part is the USB ID:

```text
Vendor ID:  1a86
Product ID: fe07
```

Your light may show a different ID.

That is normal.

Write down your device’s USB ID, because you may need it later.

The format is:

```text
vendor_id:product_id
```

For example:

```text
1a86:fe07
```

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

These are raw HID devices.

Your light may be one of them.

---

## Step 3) Find which hidraw device belongs to your light

Run:

```bash
for d in /sys/class/hidraw/hidraw*/device/uevent; do
  echo "---- $d"
  grep -E "HID_NAME|HID_ID|HID_UNIQ|HID_PHYS" "$d"
done
```

Look for entries that match your USB light.

For the example device, useful clues were:

```text
1A86
FE07
QinHeng
USBHID
```

For your device, the names and IDs may be different.

You are looking for the hidraw entry that matches the vendor ID and product ID you saw in `lsusb`.

---

## Step 4) Find the correct HID interface

Many USB devices expose more than one HID interface.

Not every interface controls the RGB light.

There may be:

- one keyboard-like interface
- one vendor-defined control interface
- one media-key interface
- one custom lighting interface

The vendor-defined or custom interface is usually the one we want.

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

You are looking for the interface that looks vendor-defined or custom rather than keyboard-like.

---

## Step 5) Read HID descriptors

Install `usbhid-dump` if needed.

On Debian, Ubuntu, or Linux Mint:

```bash
sudo apt install usbhid-dump
```

Then run:

```bash
sudo usbhid-dump -d VENDOR_ID:PRODUCT_ID -e descriptor
```

Replace `VENDOR_ID:PRODUCT_ID` with your device ID.

For the example device:

```bash
sudo usbhid-dump -d 1a86:fe07 -e descriptor
```

This is a sanity check.

It helps confirm that the device exposes HID interfaces and shows what kind of HID reports the device expects.

For the example device, the useful report is 64 bytes long.

Other devices may use a different report length.

---

## Step 6) Try the known example packet format

The example device uses this 16-byte header:

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

The full HID report for the example device is 64 bytes long:

```text
16 useful bytes + 48 zero bytes
```

The checksum is calculated like this:

```text
YY = sum(first_15_bytes) & 0xFF
```

You usually do not need to calculate the checksum yourself.

The provided Linux tool does it automatically.

Important:

This exact packet format is known to work for the example DX Light-style device.

Other USB RGB lights may use a different format.

If this does not work, your light may still be controllable, but you will need to capture and study its own packets.

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

Note:

The included `dxlight` tool is written for the known example packet format.

If your light uses a different protocol, you may need to modify the tool.

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

Note:

The GUI also uses the known example packet format.

If your light uses a different protocol, the GUI may need changes.

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
sudo nano /etc/udev/rules.d/99-usb-rgb-light.rules
```

Add a rule using your device’s vendor ID and product ID.

For the example device:

```text
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="fe07", MODE="0666"
```

For another device, replace the IDs:

```text
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="VENDOR_ID", ATTRS{idProduct}=="PRODUCT_ID", MODE="0666"
```

For example, if your device ID is `abcd:1234`, use:

```text
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="abcd", ATTRS{idProduct}=="1234", MODE="0666"
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

</details>

---

<details>
<summary><strong>Windows capture method</strong></summary>

Use this method if:

- the Linux-only method does not work
- your light behaves differently
- your light has a different packet format
- you want to reverse engineer the protocol yourself
- you want to verify the messages sent by the official app

You do **not** need to dual-boot.

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

Choose the USBPcap interface that contains your USB RGB light.

Start capturing.

Then open the official app for your light and change some colors.

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

These are often the packets sent from the app to the light.

Depending on the device, the traffic may use a different transfer type or endpoint.

But for many HID-based lights, this filter is a good starting point.

---

## Step 4) Copy only the HID payload

This is very important.

Copy only the HID payload bytes:

```text
usbhid.data
```

The payload may be 64 bytes, but other devices may use a different size.

Do **not** copy the full USB frame.

The full USB frame contains extra USB metadata, which is not part of the actual message sent to the light.

---

## Step 5) Compare captured packets

Capture packets for simple colors first.

For example:

```text
red
green
blue
white
black/off
```

Then compare the packets.

Look for bytes that change in a familiar way.

For example, RGB values often appear as:

```text
ff 00 00
```

for red,

```text
00 ff 00
```

for green,

```text
00 00 ff
```

for blue,

and:

```text
ff ff ff
```

for white.

The bytes may also appear in a different order, such as:

```text
RR GG BB
```

or:

```text
BB GG RR
```

or with brightness/effect bytes nearby.

</details>

---

<details>
<summary><strong>Example packet format</strong></summary>

The example device used while writing this guide has this packet structure:

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

Example first 16 bytes:

```text
52 42 10 41 86 01 00 ff 00 3f 40 00 00 00 fe e8
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

## Full example report

The final report for the example device must be 64 bytes long.

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

This is only the example format.

Other lights may use different headers, different RGB byte positions, different checksums, or no checksum at all.

</details>

---

<details>
<summary><strong>Troubleshooting</strong></summary>

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

Many USB devices expose more than one HID interface.

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
- your device uses a different packet format
- the light is not HID-based
- the report length is different

First try:

```bash
sudo ./dxlight 255 0 0
```

If that works, it was a permissions problem.

If it still does not work, check that you are sending to the correct hidraw interface.

If the device is not the example model, you may need to capture its own packets from the official app.

---

## Permission denied

For quick testing:

```bash
sudo ./dxlight 255 0 0
```

For permanent access, create a udev rule using your device’s vendor ID and product ID.

---

## My device has a different vendor/product ID

That is normal.

The example device used this ID:

```text
1a86:fe07
```

Your device may use something else.

If your device has a different ID, it may still work the same way, but the code or udev rule may need changes.

If the packet format is different, you will need to capture packets from the official app and compare them.

---

## Wireshark shows too much data

Make sure you start with this filter:

```text
usb.transfer_type == 0x01 && usb.endpoint_address.direction == 0
```

Also make sure you copy only:

```text
usbhid.data
```

Do not copy the full USB frame.

---

## I cannot find `usbhid.data`

Depending on the device or Wireshark version, the field may appear differently.

Look for the HID report payload inside the USB packet.

You want the actual bytes sent to the device, not the whole USB packet.

The useful payload is usually much shorter than the full captured frame.

</details>

---

<details>
<summary><strong>Files in this repo</strong></summary>

```text
list_dxlights.py   Windows helper: lists interfaces for the example device
dxlights.py        Windows sender using hidapi for the example device
dxlight            Linux CLI sender for the known example packet format
dxlight-picker     Linux Tkinter GUI sender for the known example packet format
```

If you adapt this project for another light, you may want to rename these files or update the code comments to match your device.

</details>

---

<details>
<summary><strong>Final notes</strong></summary>

The general process is:

```text
1. Plug in the light.
2. Find the USB device ID.
3. Find the correct hidraw interface.
4. Check the HID descriptor.
5. Try the known packet format if your device is similar.
6. If needed, capture packets from the official app.
7. Recreate those packets on Linux.
8. Fix permissions with a udev rule.
```

The Windows capture step is optional if the known packet format already works.

You only need it if:

- the known packet format does not work
- your device is a different variant
- you want to verify the protocol yourself
- you want to adapt this guide to another USB RGB light

You do not need dual-boot.

A Windows laptop, a friend’s Windows computer, a separate Windows PC, or a Windows VM with USB passthrough is enough for the capture step.

This guide started with one DX Light-style USB RGB light, but the method can apply to many similar HID-based RGB lights.

</details>
