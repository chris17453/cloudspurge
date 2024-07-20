import os
from dotenv import load_dotenv

load_dotenv()

VCENTER_SERVER = os.getenv('VCENTER_SERVER')
VCENTER_USER = os.getenv('VCENTER_USER')
VCENTER_PASSWORD = os.getenv('VCENTER_PASSWORD')
TARGET_USER = os.getenv('TARGET_USER')
PROBLEMATIC_FILE_PATTERN = 'C-00000291*.sys'
BLUE_SCREEN_COLOR = (0, 0, 255)
DATACENTER_NAME = os.getenv('DATACENTER_NAME')
HELPER_VM_NAME= os.getenv('HELPER_VM_NAME')
HELPER_VM_USERNAME = os.getenv('HELPER_VM_USERNAME')
HELPER_VM_PASSWORD = os.getenv('HELPER_VM_PASSWORD')
ROLE_NAME = 'BlueScreenFixRole'