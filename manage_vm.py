import json
import sys
from typing import Any, Optional
from google.api_core.extended_operation import ExtendedOperation
from google.cloud import compute_v1


def wait_for_extended_operation(
    operation: ExtendedOperation, verbose_name: str = "operation", timeout: int = 300
) -> Any:
    """
    Waits for the extended (long-running) operation to complete.
    """
    result = operation.result(timeout=timeout)

    if operation.error_code:
        print(
            f"Error during {verbose_name}: [Code: {operation.error_code}]: {operation.error_message}",
            file=sys.stderr,
            flush=True,
        )
        print(f"Operation ID: {operation.name}", file=sys.stderr, flush=True)
        raise operation.exception() or RuntimeError(operation.error_message)

    if operation.warnings:
        print(f"Warnings during {verbose_name}:\n", file=sys.stderr, flush=True)
        for warning in operation.warnings:
            print(f" - {warning.code}: {warning.message}", file=sys.stderr, flush=True)

    return result


def prompt_user_input(prompt: str, default: Optional[str] = None) -> str:
    """
    Prompts the user for input and returns their response.
    If the user provides no input, returns the default value.
    """
    if default:
        prompt = f"{prompt} [Default: {default}]: "
    response = input(prompt).strip()
    return response or default


def create_instance_interactively():
    """
    Prompts the user for instance configuration details to create a VM.
    """
    project_id = prompt_user_input("Enter your Google Cloud project ID:")
    zone = prompt_user_input("Enter the zone for the instance:", "europe-west2")
    instance_name = prompt_user_input("Enter the name for the instance:")
    machine_type = prompt_user_input(
        f"Enter the machine type (e.g., n2-standard-2):", "n2-standard-2"
    )
    add_disk = prompt_user_input(
        "Do you want to add an additional disk? (yes/no):", "no"
    ).lower() == "yes"

    disk_size_gb = None
    if add_disk:
        disk_size_gb = int(
            prompt_user_input("Enter the size of the additional disk in GB:", "100")
        )

    create_instance(
        project_id=project_id,
        zone=zone,
        instance_name=instance_name,
        machine_type=machine_type,
        additional_disk_size=disk_size_gb,
    )


def create_instance(
    project_id: str,
    zone: str,
    instance_name: str,
    machine_type: str,
    additional_disk_size: Optional[int] = None,
):
    """
    Creates a Compute Engine VM instance with the specified configuration.
    """
    instance_client = compute_v1.InstancesClient()

    instance = compute_v1.Instance()
    instance.name = instance_name
    instance.machine_type = f"zones/{zone}/machineTypes/{machine_type}"

    # Configure a boot disk
    boot_disk = compute_v1.AttachedDisk()
    boot_disk.initialize_params = compute_v1.AttachedDiskInitializeParams()
    boot_disk.initialize_params.source_image = (
        "projects/debian-cloud/global/images/family/debian-12"
    )
    boot_disk.initialize_params.disk_size_gb = 10
    boot_disk.boot = True
    boot_disk.auto_delete = True
    instance.disks = [boot_disk]

    # Configure additional disk if specified
    if additional_disk_size:
        additional_disk = compute_v1.AttachedDisk()
        additional_disk.initialize_params = compute_v1.AttachedDiskInitializeParams()
        additional_disk.initialize_params.disk_size_gb = additional_disk_size
        additional_disk.boot = False
        additional_disk.auto_delete = True
        instance.disks.append(additional_disk)

    # Configure network interface
    network_interface = compute_v1.NetworkInterface()
    network_interface.name = "nic0"
    network_interface.network = f"projects/{project_id}/global/networks/default"
    network_interface.access_configs = [
        compute_v1.AccessConfig(name="External NAT", type_="ONE_TO_ONE_NAT")
    ]
    instance.network_interfaces = [network_interface]

    # Insert the instance
    instance_insert_request = compute_v1.InsertInstanceRequest(
        project=project_id, zone=zone, instance_resource=instance
    )
    operation = instance_client.insert(instance_insert_request)
    wait_for_extended_operation(operation, "instance creation")

    print(f"Instance {instance_name} created successfully.")


def create_instance_from_json(project_id: str, zone: str, json_file_path: str):
    """
    Creates a Compute Engine VM instance based on the configuration in a JSON file.
    """
    with open(json_file_path, "r") as f:
        vm_config = json.load(f)

    instance_client = compute_v1.InstancesClient()

    instance = compute_v1.Instance()
    instance.name = vm_config["name"]
    instance.machine_type = vm_config["machineType"]
    instance.can_ip_forward = vm_config.get("canIpForward", False)
    instance.description = vm_config.get("description", "")

    instance.disks = []
    for disk_config in vm_config["disks"]:
        disk = compute_v1.AttachedDisk()
        disk.type_ = disk_config["type"]
        disk.boot = disk_config["boot"]
        disk.auto_delete = disk_config["autoDelete"]
        disk.device_name = disk_config["deviceName"]
        disk.initialize_params = compute_v1.AttachedDiskInitializeParams()
        disk.initialize_params.disk_size_gb = int(disk_config["diskSizeGb"])
        if "source" in disk_config:
            disk.source = disk_config["source"]
        instance.disks.append(disk)

    instance.network_interfaces = []
    for network_config in vm_config["networkInterfaces"]:
        network_interface = compute_v1.NetworkInterface()
        network_interface.name = network_config["name"]
        network_interface.network = network_config["network"]
        if "subnetwork" in network_config:
            network_interface.subnetwork = network_config["subnetwork"]
        if "accessConfigs" in network_config:
            network_interface.access_configs = [
                compute_v1.AccessConfig(**ac) for ac in network_config["accessConfigs"]
            ]
        instance.network_interfaces.append(network_interface)

    instance_insert_request = compute_v1.InsertInstanceRequest(
        project=project_id, zone=zone, instance_resource=instance
    )
    operation = instance_client.insert(instance_insert_request)
    wait_for_extended_operation(operation, "instance creation")

    print(f"Instance {instance.name} created successfully.")


def main():
    json_file_path = prompt_user_input(
        "Enter the path to the JSON configuration file (or leave blank to configure interactively):"
    )
    if json_file_path:
        project_id = prompt_user_input("Enter your Google Cloud project ID:")
        zone = prompt_user_input("Enter the zone for the instance:", "europe-west2")
        create_instance_from_json(project_id, zone, json_file_path)
    else:
        create_instance_interactively()


if __name__ == "__main__":
    main()
