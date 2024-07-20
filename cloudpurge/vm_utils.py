import time
import base64
import io
from urllib.parse import quote
from PIL import Image
import paramiko
import urllib
import urllib3
from collections import Counter
from pyVmomi import vim,vmodl
from .config import BLUE_SCREEN_COLOR, HELPER_VM_USERNAME, HELPER_VM_PASSWORD, PROBLEMATIC_FILE_PATTERN, DATACENTER_NAME, ROLE_NAME, TARGET_USER,VCENTER_SERVER,VCENTER_USER, VCENTER_PASSWORD
from .privileges import required_privileges

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_all_vms(content):
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
    return container.view

import requests


def get_datacenter_for_datastore(content, datastore_name):
    for datacenter in content.rootFolder.childEntity:
        for datastore in datacenter.datastore:
            if datastore.name == datastore_name:
                return datacenter
    return None

def get_file_bytes_from_datastore(content, remote_path_to_file, datastore_name):
    """
    Downloads file from datastore (with retries) and returns its data.
    Note: keep in mind requested file size, since data are in memory!
    :param content: vSphere content object
    :param remote_path_to_file: path to file in datastore (e.g. my_vm/my_vm.png)
    :param datastore_name: name of datastore
    :return: data
    """


    def sleep_between_tries():
        time.sleep(5)  # Sleep for 5 seconds between retries

    server_name = content.setting.setting[0].value  # Assuming the first setting is the vCenter server name
    datacenter = get_datacenter_for_datastore(content, datastore_name)
    if datacenter is None:
        raise RuntimeError(f'Cannot find datacenter for datastore {datastore_name}')

   # URL encode the path components
    encoded_remote_path = quote(remote_path_to_file)
    encoded_datacenter_name = quote(datacenter.name)
    encoded_datastore_name = quote(datastore_name)

    url = f'https://{VCENTER_SERVER}/folder/{encoded_remote_path}?dcPath={encoded_datacenter_name}&dsName={encoded_datastore_name}'

    # Extracting cookies from the session
    cookies = content.sessionManager.AcquireCloneTicket()

    # Use the cloned ticket for authentication
    headers = {
        'vmware-api-session-id': cookies
    }


    for i in range(3):
        try:
            resp = requests.get(
                url=url,
                verify=False,
                auth=(VCENTER_USER, VCENTER_PASSWORD)
            )
            if resp.status_code == 200:
                return resp.content
            else:
                print(f'Download of {remote_path_to_file} (retry {i}) failed with status code: {resp.status_code}')
                sleep_between_tries()
                continue
        except Exception as e:
            print(f'Downloading of {remote_path_to_file} (retry {i}) failed: {e}')

    return None


def check_vm_permissions(content, vm):
    """
    Check the permissions on a specific VM.
    """
    try:
        auth_manager = content.authorizationManager
        permissions = auth_manager.RetrieveEntityPermissions(entity=vm, inherited=True)
        role_list = {role.roleId: role for role in auth_manager.roleList}
        
        for perm in permissions:
            role = role_list.get(perm.roleId)
            if role:
                print(f"Principal: {perm.principal}, Role: {role.name}, Propagate: {perm.propagate}, Group: {perm.group}")
                print(f"Privileges: {role.privilege}")
            else:
                print(f"Role with ID {perm.roleId} not found in role list.")
    except vmodl.MethodFault as error:
        print(f"Caught vmodl fault: {error.msg}")
    except Exception as e:
        print(f"Caught exception: {str(e)}")

def take_screenshot(content,vm):
    try:
        screenshot_task = vm.CreateScreenshot_Task()

        # Wait for the screenshot task to complete
        while screenshot_task.info.state not in ['success', 'error']:
            time.sleep(1)


        if screenshot_task.info.state == 'success':
            result = screenshot_task.info.result

            result_path = screenshot_task.info.result
            if not result_path:
                return None
            # can't we just use self.destination_datastore.info.name ?
            datastore_name, screenshot_path = result_path.split(' ',1)
            datastore_name = datastore_name.lstrip('[').rstrip(']')
            
            image_data=get_file_bytes_from_datastore(content,screenshot_path,datastore_name)
            
            image = Image.open(io.BytesIO(image_data))

            datastore_path = f'[{datastore_name}] {screenshot_path}'

            # Delete the screenshot from the server
            datacenter=get_datacenter_for_datastore(content,datastore_name)
            #print(datastore_path,datacenter)
            delete_task = content.fileManager.DeleteDatastoreFile_Task(
                name=datastore_path,
                datacenter=datacenter
            )



        # Wait for the delete task to complete
            while delete_task.info.state not in ['success', 'error']:
                time.sleep(1)
            
            if delete_task.info.state == 'success':
                return image
            else:
                raise Exception("Failed to delete the screenshot from the server")
        else:
            raise Exception("Screenshot task failed")
    except Exception as ex:
        name=urllib.parse.unquote(vm.name)
        print(f"Screenshot for {vm},{name} failed")
        #check_vm_permissions(content,vm)
        return None

def is_blue_screen(image):
    # Define thresholds
    blue_threshold = 200  # Adjust this value to be more or less sensitive to blue
    percentage_threshold = 50  # Minimum percentage of blue pixels to consider it a blue screen

    # Get pixels from image
    pixels = list(image.getdata())

    # Count blueish pixels
    blue_pixels = [pixel for pixel in pixels if pixel[0] < blue_threshold and pixel[1] < blue_threshold and pixel[2] > blue_threshold]

    # Calculate percentage of blue pixels
    blue_percentage = len(blue_pixels) / len(pixels) * 100

    return blue_percentage > percentage_threshold

def find_vm_by_name(content, name):
    vms = get_all_vms(content)
    for vm in vms:
        if vm.name == name:
            return vm
    return None

def run_command_on_helper_vm(helper_vm_ip, command):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(helper_vm_ip, username=HELPER_VM_USERNAME, password=HELPER_VM_PASSWORD)
    stdin, stdout, stderr = ssh.exec_command(command)
    stdout.channel.recv_exit_status()
    ssh.close()

def fix_blue_screened_vm(service_instance, vm, helper_vm):
    vm.PowerOffVM_Task().wait_for_completion()
    virtual_disk = vm.config.hardware.device[0].backing.fileName
    helper_vm.ReconfigVM_Task(spec=vim.vm.ConfigSpec(deviceChange=[
        vim.vm.device.VirtualDeviceSpec(
            operation=vim.vm.device.VirtualDeviceSpec.Operation.add,
            device=vim.vm.device.VirtualDisk(
                backing=vim.vm.device.VirtualDisk.FlatVer2BackingInfo(
                    fileName=virtual_disk
                )
            )
        )
    ])).wait_for_completion()

    helper_vm_ip = helper_vm.guest.ipAddress
    while not helper_vm_ip:
        helper_vm_ip = helper_vm.guest.ipAddress

    run_command_on_helper_vm(helper_vm_ip, f'del C:\\Windows\\System32\\drivers\\CrowdStrike\\{PROBLEMATIC_FILE_PATTERN}')

    helper_vm.ReconfigVM_Task(spec=vim.vm.ConfigSpec(deviceChange=[
        vim.vm.device.VirtualDeviceSpec(
            operation=vim.vm.device.VirtualDeviceSpec.Operation.remove,
            device=helper_vm.config.hardware.device[0]
        )
    ])).wait_for_completion()

    vm.PowerOnVM_Task().wait_for_completion()

def create_role(service_instance, role_name):
    content = service_instance.RetrieveContent()
    authorization_manager = content.authorizationManager


    # Create the role if it doesn't exist
    roles = authorization_manager.roleList
    role = next((role for role in roles if role.name == role_name), None)

    if role is None:
        role_id = authorization_manager.AddAuthorizationRole(name=role_name, privIds=required_privileges)
        print(f'Role "{role_name}" created with ID {role_id}')
    else:
        print(f'Role "{role_name}" already exists with ID {role.roleId}')

def assign_role(service_instance, role_name, user, datacenter_name):
    content = service_instance.RetrieveContent()
    authorization_manager = content.authorizationManager

    # Find the role
    roles = authorization_manager.roleList
    role = next((role for role in roles if role.name == role_name), None)

    if role is None:
        print(f'Role "{role_name}" not found.')
        return

    # Retrieve the datacenter
    datacenter = next((dc for dc in content.rootFolder.childEntity if dc.name == datacenter_name), None)

    if datacenter is None:
        print(f'Datacenter "{datacenter_name}" not found.')
        return

    # Assign the role to the user at the datacenter level
    permission = vim.AuthorizationManager.Permission()
    permission.principal = user
    permission.group = False
    permission.roleId = role.roleId
    permission.propagate = True
    authorization_manager.SetEntityPermissions(entity=datacenter, permission=[permission])
    print(f'Role "{role_name}" assigned to user "{user}" for datacenter "{datacenter_name}"')

def get_user_roles(content, user_name):
    """
    Get roles assigned to a specific user.
    """
    
    auth_manager = content.authorizationManager

    # Get all roles
    roles = auth_manager.roleList

    # Get all permissions
    permissions = auth_manager.RetrieveAllPermissions()

    # Create a dictionary to store user roles
    user_roles = {}

    # Iterate through permissions to find user roles
    for perm in permissions:
        principal = perm.principal
        role_id = perm.roleId
        
        # Find the role name for the given role ID
        role_name = next(role.name for role in roles if role.roleId == role_id)
        
        if principal not in user_roles:
            user_roles[principal] = []
        user_roles[principal].append(role_name)
    return user_roles

def list_all_assigned_user_roles(content, user_name):
    """
    List all roles assigned to a specific user and print them.
    """
    user_roles = get_user_roles(content, user_name)
    print(f"Roles for user '{user_name}':")
    
    for principal,role in user_roles.items():
        print(f"{principal}:{role}")
    return user_roles

def user_has_role(service_instance, user_name, role_name):
    """
    Check if a user has a specific role.
    """
    user_roles = get_user_roles(service_instance, user_name)
    for principal,role in user_roles.items():
        if role_name in role:
            return True
    return None

def get_role_by_name(si, role_name):
    content = si.RetrieveContent()
    auth_manager = content.authorizationManager
    roles = auth_manager.roleList
    for role in roles:
        if role.name == role_name:
            return role
    return None
    
def get_vm_permissions(si, vm):
    content = si.RetrieveContent()
    auth_manager = content.authorizationManager
    return auth_manager.RetrieveEntityPermissions(vm, False)


def set_vm_permission(si, vm, user, role_name, propagate=True):
    content = si.RetrieveContent()
    auth_manager = content.authorizationManager
    role = get_role_by_name(si, role_name)
    
    if role is None:
        raise ValueError(f"Role '{role_name}' not found")
    perm = vim.AuthorizationManager.Permission()
    perm.entity = vm
    perm.principal = user
    perm.group = False
    perm.propagate = propagate
    perm.roleId = role.roleId

    auth_manager.SetEntityPermissions(vm, [perm])
    