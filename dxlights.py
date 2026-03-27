import sys
import hid

VENDOR_ID = 0x1A86
PRODUCT_ID = 0xFE07


def open_dxlight():
    for d in hid.enumerate(VENDOR_ID, PRODUCT_ID):
        path = d["path"]
        if d.get("interface_number") == 0 and b"MI_00" in path:
            dev = hid.device()
            dev.open_path(path)
            return dev
    raise RuntimeError("DX light control interface MI_00 not found")


def make_packet(r: int, g: int, b: int, seq: int) -> bytes:
    packet = [
        0x52, 0x42, 0x10, seq,
        0x86, 0x01,
        r, g, b,
        0x3F, 0x40,
        0x00, 0x00, 0x00,
        0xFE,
    ]
    checksum = sum(packet) & 0xFF
    packet.append(checksum)
    packet += [0x00] * 48
    return bytes(packet)


def main():
    if len(sys.argv) not in (4, 5):
        print("Usage: python dxlights.py R G B [seq]")
        raise SystemExit(1)

    r = int(sys.argv[1])
    g = int(sys.argv[2])
    b = int(sys.argv[3])

    if not all(0 <= x <= 255 for x in (r, g, b)):
        print("R, G, B must be between 0 and 255")
        raise SystemExit(1)

    seq = int(sys.argv[4], 0) if len(sys.argv) == 5 else 0x50
    packet = make_packet(r, g, b, seq)

    dev = open_dxlight()
    try:
        written = dev.write(b"\x00" + packet)
        print("Wrote", written, "bytes")
    finally:
        dev.close()

    print(f"Set color to {r},{g},{b} with seq=0x{seq:02X}")
    print("Packet:", packet[:16].hex(" "))


if __name__ == "__main__":
    main()
