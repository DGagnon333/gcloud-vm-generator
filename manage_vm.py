from google.cloud import compute_v1
from google.oauth2 import service_account

# Set up your project, zone, and instance name
project = 'cs-lab2'  # Your Google Cloud Project ID
zone = 'europe-west2-a'  # Zone where the VM will be created
instance_name = 'instance-20250121-225909'  # Instance name
image_family = 'ubuntu-2404-lts'  # Image: Ubuntu 24.04 LTS
image_project = 'ubuntu-os-cloud'  # Image Project
machine_type = 'n2d-standard-2'  # Machine type
disk_size_gb = 100  # Disk size (in GB)
tags = ['cloud-systems']  # Tags for the instance

# Path to your service account key JSON file
access_key = 'service_account_key.json'

# Authenticate using service account
credentials = service_account.Credentials.from_service_account_file(access_key)
compute_client = compute_v1.InstancesClient(credentials=credentials)

# Step 1: Create VM instance
def create_instance():
    instance = compute_v1.Instance(
        name=instance_name,
        machine_type=f"zones/{zone}/machineTypes/{machine_type}",
        disks=[compute_v1.AttachedDisk(
            boot=True,
            auto_delete=True,
            initialize_params=compute_v1.AttachedDiskInitializeParams(
                source_image=f"projects/{image_project}/global/images/family/{image_family}",
                disk_size_gb=disk_size_gb
            )
        )],
        network_interfaces=[compute_v1.NetworkInterface(
            network="global/networks/default",
            access_configs=[compute_v1.AccessConfig(name="External NAT", type_="ONE_TO_ONE_NAT")]
        )],
        tags=compute_v1.Tags(items=tags),
        service_accounts=[compute_v1.ServiceAccount(
            email="490729708489-compute@developer.gserviceaccount.com",
            scopes=[
                "https://www.googleapis.com/auth/devstorage.read_only",
                "https://www.googleapis.com/auth/logging.write",
                "https://www.googleapis.com/auth/monitoring.write",
                "https://www.googleapis.com/auth/service.management.readonly",
                "https://www.googleapis.com/auth/servicecontrol",
                "https://www.googleapis.com/auth/trace.append"
            ]
        )]
    )

    # Create the VM instance
    operation = compute_client.insert(project=project, zone=zone, instance_resource=instance)
    operation.result()  # Wait for the operation to complete
    print(f"Instance '{instance_name}' created.")

# Step 2: Resize the VM disk
def resize_disk():
    # Get the current disk configuration
    disk_client = compute_v1.DisksClient(credentials=credentials)
    disk = disk_client.get(project=project, zone=zone, disk=instance_name)

    # Resize the disk
    disk_client.resize(project=project, zone=zone, disk=instance_name, size_gb=disk_size_gb)
    print(f"Disk resized to {disk_size_gb} GB.")

# Step 3: Suspend the VM instance
def suspend_instance():
    operation = compute_client.suspend(project=project, zone=zone, instance=instance_name)
    operation.result()  # Wait for the operation to complete
    print(f"Instance '{instance_name}' suspended.")

# Main execution
if __name__ == "__main__":
    create_instance()
    resize_disk()
    suspend_instance()
