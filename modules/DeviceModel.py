
from dataclasses import dataclass, field
from typing import List

@dataclass
class DeviceModel:
    """Device model configuration"""
    vendor: str
    model: str
    device_type: str  # Netmiko device type
    default_username: str
    default_password: str
    default_enable: str = ""
    port: int = 22
    icon: str = "🔧"
    capabilities: List[str] = field(default_factory=list)