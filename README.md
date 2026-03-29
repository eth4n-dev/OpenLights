# DX Light on Linux (Beginner-Friendly Guide)

This project shows how to control a USB RGB light (marketed as **DX Light**) on Linux, even though the official app is Windows-only.

If you are new to reverse engineering, this README is written for you.

---

## Quick summary (what is happening?)

Your light is a USB device. The Windows app sends small binary messages to it ("set red", "set blue", etc.).

This repo explains how we:

1. Found which USB connection is the real control channel.
2. Captured messages sent by the Windows app.
3. Learned the message format.
4. Recreated those messages on Linux.

Result: full RGB control from Linux CLI and a small Linux GUI picker.

---

## Glossary (plain English)

- **USB**: standard way devices connect to your computer.
- **HID**: *Human Interface Device* protocol. Keyboards/mice use it, but many RGB devices also use it.
- **Interface**: one USB device can expose multiple logical channels (for example: keyboard channel + vendor control channel).
- **hidraw** (Linux): raw device files like `/dev/hidraw9` that let software send/receive raw HID data directly.
- **Report descriptor**: metadata that describes what kind of HID messages a device expects.
- **Packet / Report**: one message sent to the device (in this case 64 bytes).
- **Vendor-defined**: custom format made by the manufacturer, not a standard keyboard/mouse format.
- **Checksum**: a small value used to verify packet integrity.

---

## Before you start

- Hardware: DX Light connected via USB.
- Linux tools: `lsusb`, `usbhid-dump`.
- Windows tools (for capture step): Wireshark + USBPcap.

---

## Step 1) Confirm the device exists on Linux

Run:

```bash
lsusb
ls /dev/hidraw*
```

You should see something like:

```text
Bus 001 Device 010: ID 1a86:fe07 QinHeng Electronics USBHID
```

Important IDs:

- Vendor ID: `1a86`
- Product ID: `fe07`

---

## Step 2) Find which HID interface actually controls color

A single USB device can expose multiple HID interfaces. Not all are for RGB control.

Check every hidraw entry:

```bash
for d in /sys/class/hidraw/hidraw*/device/uevent; do
  echo "---- $d"
  grep -E "HID_NAME|HID_ID|HID_UNIQ|HID_PHYS" "$d"
done
```

Then inspect likely candidates in detail:

```bash
for d in /sys/class/hidraw/hidrawN /sys/class/hidraw/hidrawM; do
  echo "==== $d ===="
  readlink -f "$d/device"
  cat "$d/device/uevent"
done
```

Replace `hidrawN/hidrawM` with your real candidates.

What you are looking for:

- one keyboard-like interface (not the one we want)
- one vendor-defined interface (usually the control one)

---

## Step 3) Read HID descriptors (sanity check)

```bash
sudo usbhid-dump -d 1a86:fe07 -e descriptor
```

Why this matters: it confirms which interface uses vendor-defined 64-byte reports.

---

## Step 4) Capture real packets from Windows app

Use Wireshark + USBPcap while changing colors in the official Windows software.

Filter:

```text
usb.transfer_type == 0x01 && usb.endpoint_address.direction == 0
```

Very important:

- copy only the HID payload bytes (`usbhid.data`, 64 bytes)
- do **not** copy full USB frame headers

---

## Step 5) Understand the packet format

Example first 16 bytes:

```text
52 42 10 41 86 01 00 ff 00 3f 40 00 00 00 fe e8
```

Derived structure:

```text
52 42 10 XX 86 01 RR GG BB 3F 40 00 00 00 FE YY
```

Where:

- `XX` = sequence byte
- `RR GG BB` = red/green/blue values (0–255)
- `YY` = checksum

Checksum rule:

```text
YY = sum(first_15_bytes) & 0xFF
```

Final report length is 64 bytes:

- 16-byte header (including checksum)
- then 48 bytes of `00`

---

## Step 6) Control the light on Linux

### CLI

```bash
./dxlight 255 0 0
./dxlight 0 255 0
./dxlight 0 0 255
./dxlight 128 64 255 0x55
```

If you get permissions errors on `/dev/hidraw*`, run with proper permissions or configure udev rules.

### GUI

```bash
./dxlight-picker
```

GUI features:

- hue bar
- saturation/brightness square
- RGB input fields
- live preview + direct send

---

## Files in this repo

- `list_dxlights.py` → Windows helper: list interfaces for this device.
- `dxlights.py` → Windows sender using `hidapi` and MI_00 interface.
- `dxlight` → Linux CLI sender.
- `dxlight-picker` → Linux Tkinter GUI sender.

---

## Why this project matters

Many RGB peripherals use simple custom HID packets. Once you understand the packet format, you can remove vendor lock-in and control hardware directly from Linux.

---

## Future ideas

- animations/effects
- saved presets
- background daemon
- desktop integration (Hyprland/Waybar, etc.)
