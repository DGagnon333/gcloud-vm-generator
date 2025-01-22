import sys
import uuid
import json
from typing import Optional
from google.api_core.extended_operation import ExtendedOperation
from google.cloud import compute_v1
from google.auth.exceptions import DefaultCredentialsError
from tqdm import tqdm


def wait_for_extended_operation(
    operation: ExtendedOperation, verbose_name: str = "operation", timeout: int = 300
):
    result = operation.result(timeout=timeout)
    if operation.error_code:
        raise RuntimeError(f"Error during {verbose_name}: {operation.error_message}")
    if operation.warnings:
        print(f"Warnings during {verbose_name}: {operation.warnings}", file=sys.stderr)
    return result

def sanitize_instance_config(instance_config):
    """Sanitize the instance configuration by removing unsupported fields."""
    unsupported_fields = ['shieldedVmConfig', 'shieldedVmIntegrityPolicy']
    for field in unsupported_fields:
        if field in instance_config:
            print(f"Warning: Removing unsupported field '{field}' from the configuration.")
            del instance_config[field]
    return instance_config

def create_instance_from_json(project_id, zone, json_file_path):
    """Create an instance from a JSON configuration."""
    with open(json_file_path, "r") as f:
        instance_config = json.load(f)

    # Sanitize the instance config before passing it to the API
    instance_config = sanitize_instance_config(instance_config)

    instance_client = compute_v1.InstancesClient()
    request = compute_v1.InsertInstanceRequest(
        project=project_id, 
        zone=zone, 
        instance_resource=compute_v1.Instance.from_json(json.dumps(instance_config))  # Convert dict to JSON string
    )
    
    operation = instance_client.insert(request=request)
    wait_for_extended_operation(operation, "instance creation")
    print(f"Instance created successfully in project '{project_id}' and zone '{zone}'.")

def get_default_project_id():
    """Retrieve the default project ID from gcloud configuration."""
    from subprocess import check_output
    try:
        return check_output(["gcloud", "config", "get-value", "project"], text=True).strip()
    except Exception as e:
        raise RuntimeError("Failed to retrieve default project from gcloud.") from e

def get_default_zone():
    """Retrieve the default zone from gcloud configuration."""
    from subprocess import check_output
    try:
        return check_output(["gcloud", "config", "get-value", "compute/zone"], text=True).strip()
    except Exception as e:
        print("Default zone not found in gcloud configuration. Listing all zones instead.")
        return None

def list_zones(project_id):
    """List all available zones for the given project."""
    compute_client = compute_v1.ZonesClient()
    return [zone.name for zone in compute_client.list(project=project_id)]

def generate_default_instance_name():
    """Generate a default instance name using a GUID."""
    return f"instance-from-script-{uuid.uuid4().hex[:8]}"

def create_instance_interactively(project_id, zone):
    """Interactively create an instance."""
    instance_name = input("Enter instance name (leave blank for default): ") or generate_default_instance_name()
    print(f"Using instance name: {instance_name}")

    disk_size = input("Enter additional disk size in GB (leave blank for none): ").strip()
    disk_size = int(disk_size) if disk_size else None

    instance_config = {
        "name": instance_name,
        "machineType": f"zones/{zone}/machineTypes/n1-standard-1",
        "disks": [
            {
                "boot": True,
                "initializeParams": {
                    "sourceImage": "projects/debian-cloud/global/images/family/debian-12",
                },
            }
        ],
        "networkInterfaces": [
            {
                "network": "global/networks/default",
                "accessConfigs": [{"type": "ONE_TO_ONE_NAT", "name": "External NAT"}],
            }
        ],
    }

    if disk_size:
        additional_disk = {
            "initializeParams": {
                "diskSizeGb": disk_size,
                "diskType": f"zones/{zone}/diskTypes/pd-standard",
            },
            "autoDelete": True,
            "boot": False,
            "type": "PERSISTENT",
        }
        instance_config["disks"].append(additional_disk)

    instance_client = compute_v1.InstancesClient()
    request = compute_v1.InsertInstanceRequest(
        project=project_id, 
        zone=zone, 
        instance_resource=compute_v1.Instance.from_json(json.dumps(instance_config))  # Convert dict to JSON string
    )
    operation = instance_client.insert(request=request)
    wait_for_extended_operation(operation, "instance creation")
    print(f"Instance '{instance_name}' created successfully in project '{project_id}' and zone '{zone}'.")

def main():
    try:
        project_id = get_default_project_id()
        print(f"Using project: {project_id}")

        default_zone = get_default_zone()
        if not default_zone:
            zones = list_zones(project_id)
            print("Available zones:")
            for zone in zones:
                print(f" - {zone}")
            default_zone = input("Enter the zone to use: ").strip()
        print(f"Using zone: {default_zone}")

        json_file_path = input("Enter the path to the JSON configuration file (leave blank for interactive): ").strip()
        if json_file_path:
            create_instance_from_json(project_id, default_zone, json_file_path)
        else:
            create_instance_interactively(project_id, default_zone)

    except DefaultCredentialsError:
        print("Authentication failed. Please run 'gcloud auth application-default login'.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
