"""
Device Models Database
Contains all supported network device models
"""

# Fix the import - use relative import since both files are in modules/ directory
from modules.DeviceModel import DeviceModel

# Device Models Database
DEVICE_MODELS = {
    "Aruba CX 6300F": DeviceModel(
        vendor="HPE Aruba",
        model="CX 6300F",
        device_type="aruba_osswitch",
        default_username="admin",
        default_password="",
        icon="🔷",
        capabilities=["PoE+", "Stacking", "10G Uplink", "Layer 3"]
    ),
    "Aruba CX 6200F": DeviceModel(
        vendor="HPE Aruba",
        model="CX 6200F",
        device_type="aruba_osswitch",
        default_username="admin",
        default_password="",
        icon="🔶",
        capabilities=["PoE+", "Layer 2", "1G Uplink"]
    ),
    "Cisco Catalyst 9300": DeviceModel(
        vendor="Cisco",
        model="Catalyst 9300",
        device_type="cisco_ios",
        default_username="admin",
        default_password="admin",
        default_enable="cisco",
        icon="🔵",
        capabilities=["PoE++", "StackWise", "UADP 3.0", "Layer 3"]
    ),
    "Cisco Catalyst 9200": DeviceModel(
        vendor="Cisco",
        model="Catalyst 9200",
        device_type="cisco_ios",
        default_username="admin",
        default_password="admin",
        icon="🔴",
        capabilities=["PoE+", "StackWise", "Layer 2"]
    ),
    "Cisco ISR 4451": DeviceModel(
        vendor="Cisco",
        model="ISR 4451",
        device_type="cisco_ios",
        default_username="admin",
        default_password="admin",
        default_enable="cisco",
        icon="🟣",
        capabilities=["Router", "4 Gbps", "SD-WAN"]
    ),
    "Juniper EX4300": DeviceModel(
        vendor="Juniper",
        model="EX4300",
        device_type="juniper_junos",
        default_username="root",
        default_password="",
        icon="🟢",
        capabilities=["Virtual Chassis", "PoE+", "Layer 3"]
    ),
    "Fortinet FortiSwitch 448E": DeviceModel(
        vendor="Fortinet",
        model="FortiSwitch 448E",
        device_type="fortinet",
        default_username="admin",
        default_password="",
        icon="🔺",
        capabilities=["FortiLink", "PoE+", "Layer 2"]
    ),
    "Huawei S5720": DeviceModel(
        vendor="Huawei",
        model="S5720",
        device_type="huawei",
        default_username="admin",
        default_password="admin@123",
        icon="🔻",
        capabilities=["iStack", "PoE+", "Layer 3"]
    ),
}