import hid

VENDOR_ID = 0x1A86
PRODUCT_ID = 0xFE07

for d in hid.enumerate(VENDOR_ID, PRODUCT_ID):
    print("path:", d.get("path"))
    print("interface_number:", d.get("interface_number"))
    print("usage_page:", hex(d.get("usage_page", 0)))
    print("usage:", hex(d.get("usage", 0)))
    print("product_string:", d.get("product_string"))
    print("manufacturer_string:", d.get("manufacturer_string"))
    print("-" * 60)
