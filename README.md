# CloudPurge

## Overview
CloudPurge is a command-line tool for managing VMware virtual machines. It provides functionalities such as inventorying VMs, checking for blue screens, and managing user roles and permissions.



## Directory Structure
```
cloudpurge/
├── __main__.py
├── privileges.py
├── vm_utils.py
├── __init__.py
├── config.py
```

## Files and Functionality

### `__main__.py`
- Entry point of the application.
- Implements the command-line interface (CLI) for VM management.
- Commands:
  - `inventory`: List all VMs.
  - `check-bluescreen`: Check for blue screens in VMs.
  - `inventory-bluescreen`: Inventory and fix blue screens.
  - `create-role`: Create a role with necessary permissions.
  - `assign-role`: Assign a role to a user.
  - `list-user-roles`: List all roles assigned to a user.
  - `check-user-role`: Check if a user has a specific role.

### `privileges.py`
- Defines the required privileges for managing VMs.

### `vm_utils.py`
- Contains utility functions for VM management.
- Functions:
  - `get_all_vms`: Retrieve all VMs.
  - `get_datacenter_for_datastore`: Get the datacenter for a given datastore.
  - `get_file_bytes_from_datastore`: Download file from datastore.
  - `take_screenshot`: Take a screenshot of a VM.
  - `is_blue_screen`: Check if a screenshot indicates a blue screen.
  - `list_all_assigned_user_roles`: List all roles assigned to a user.
  - `user_has_role`: Check if a user has a specific role.
  - `create_role`: Create a new role.
  - `assign_role`: Assign a role to a user.
  - `get_vm_permissions`: Get permissions of a VM.
  - `set_vm_permission`: Set permissions for a VM.

### `config.py`
- Contains configuration constants such as vCenter server, user credentials, helper VM name, target user, and role name.

## How to Use
1. **Install dependencies**: Ensure you have all necessary Python packages installed.
2. **Configure**: Set up your configuration in `config.py`.
3. **Run the CLI**:
   - Inventory all VMs:
     ```sh
     python -m cloudpurge inventory
     ```
   - Check for blue screens:
     ```sh
     python -m cloudpurge check-bluescreen
     ```
   - Inventory and fix blue screens:
     ```sh
     python -m cloudpurge inventory-bluescreen
     ```
   - Create a role:
     ```sh
     python -m cloudpurge create-role --role-name ROLE_NAME
     ```
   - Assign a role to a user:
     ```sh
     python -m cloudpurge assign-role --role-name ROLE_NAME --user USERNAME --datacenter DATACENTER_NAME
     ```
   - List user roles:
     ```sh
     python -m cloudpurge list-user-roles --user USERNAME
     ```
   - Check if a user has a specific role:
     ```sh
     python -m cloudpurge check-user-role --user USERNAME --role-name ROLE_NAME
     ```

## Example usage

```bash
(cloudpurge) [nd@nd-box-watkinslabs-com cloudpurge]$ make inventory-bluescreen 
Loading .env environment variables...

vCenter - 10.8.0.30 is good
Mail - 10.90.0.60 is good
Windows 2022 DataCenter - DC/AD - 10.8.0.47 is good
weyland-yutani2 - 10.8.0.33 is good
fubuki - PowerDNS - 10.8.0.252 is good
KeyCloak - 10.90.0.71 is good
app07-10.90.0.72 is good
Screenshot for 'vim.VirtualMachine:vm-3071',vCLS-1e0856c5-8f3c-4415-ad6f-a4601f1c90c2 failed
Windows 2022 STD - MSSQL - 10.8.0.48 has a blue screen
mysql - 10.8.0.36 is good
Watkins Labs WEB is good
Screenshot for 'vim.VirtualMachine:vm-3101',vCLS-3c984e6d-e339-42b2-b749-80a8b593b221 failed
(cloudpurge) [nd@nd-box-watkinslabs-com cloudpurge]$ 
```

## License
BSD 3

## Author
Chris Watkins