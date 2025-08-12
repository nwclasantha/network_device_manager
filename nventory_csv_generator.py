import pandas as pd

# Create sample inventory
data = {
    'ip': ['10.1.1.1', '10.1.1.2', '10.1.1.3'],
    'hostname': ['Switch-01', 'Switch-02', 'Switch-03'],
    'model': ['Aruba CX 6300F', 'Aruba CX 6300F', 'Cisco Catalyst 9300'],
    'username': ['xxxx', 'xxxx', 'xxxx'],
    'password': ['', '', 'xxxx']
}

df = pd.DataFrame(data)
df.to_csv('device_inventory.csv', index=False)