import ssl
import atexit
import argparse
import urllib.parse
from pyVim import connect
from pyVim.connect import Disconnect
from pyVmomi import vim
from .vm_utils import get_all_vms,  take_screenshot, is_blue_screen, list_all_assigned_user_roles, user_has_role, create_role, assign_role,get_vm_permissions,set_vm_permission
from .config import VCENTER_SERVER, VCENTER_USER, VCENTER_PASSWORD, HELPER_VM_NAME,TARGET_USER,ROLE_NAME


def main():
    parser = argparse.ArgumentParser(description='VM Management CLI')
    subparsers = parser.add_subparsers(dest='command', help='Sub-command help')

    subparsers.add_parser('inventory', help='Inventory all VMs')
    subparsers.add_parser('check-bluescreen', help='Check for blue screens')
    subparsers.add_parser('inventory-bluescreen', help='Inventory and fix blue screens')

    parser_create_role = subparsers.add_parser('create-role', help='Create role with necessary permissions')
    parser_create_role.add_argument('--role-name', required=True, help='Role name to create')

    parser_assign_role = subparsers.add_parser('assign-role', help='Assign role to a user')
    parser_assign_role.add_argument('--role-name', required=True, help='Role name to assign')
    parser_assign_role.add_argument('--user', required=True, help='User to assign the role to')
    parser_assign_role.add_argument('--datacenter', required=True, help='Datacenter name')

    parser_list_user_roles = subparsers.add_parser('list-user-roles', help='List all roles assigned to a user')
    parser_list_user_roles.add_argument('--user', required=True, help='User to list the roles for')

    parser_check_user_role = subparsers.add_parser('check-user-role', help='Check if a user has a specific role')
    parser_check_user_role.add_argument('--user', required=True, help='User to check the role for')
    parser_check_user_role.add_argument('--role-name', required=True, help='Role name to check')

    args = parser.parse_args()



    context = ssl._create_unverified_context()
    service_instance = connect.SmartConnect(host=VCENTER_SERVER, user=VCENTER_USER, pwd=VCENTER_PASSWORD, sslContext=context)
    atexit.register(Disconnect, service_instance)

    #check_permissions(service_instance)
    content = service_instance.RetrieveContent()

    if args.command == 'create-role':
        create_role(service_instance, args.role_name)
    elif args.command == 'assign-role':
        assign_role(service_instance, args.role_name, args.user, args.datacenter)
    elif args.command == 'list-user-roles':
        list_all_assigned_user_roles(content, args.user)
    elif args.command == 'check-user-role':
        has_role = user_has_role(content, args.user, args.role_name)
        print(f"User '{args.user}' has role '{args.role_name}': {has_role}")
    elif args.command == 'inventory':
        inventory(content)
    elif args.command == 'check-bluescreen':
        inventory_bluescreen(service_instance,content)
    elif args.command == 'inventory-bluescreen':
        inventory_bluescreen(service_instance,content)

def inventory(content):
    vms = get_all_vms(content)
    for vm in vms:
        print(f'VM Name: {vm.name}, Power State: {vm.summary.runtime.powerState}')


def inventory_bluescreen(si,content):
    
    vms = get_all_vms(content)

    for vm in vms:
        if vm.summary.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
            permission=get_vm_permissions(si,vm)
            #set_vm_permission(si,vm,TARGET_USER,ROLE_NAME)
            screenshot = take_screenshot(content,vm)
            #set_vm_permission(si,vm,TARGET_USER,ROLE_NAME)
            name=urllib.parse.unquote(vm.name)
            if None==screenshot:
                continue

            elif is_blue_screen(screenshot):
                print(f'{name} has a blue screen')
            else:
                print(f'{name} is good')

if __name__ == '__main__':
    main()
