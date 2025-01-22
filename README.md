# Lab 2 - Virtual Machines Setup and Configuration

## Table of Contents
- [Lab 2 - Virtual Machines Setup and Configuration](#lab-2---virtual-machines-setup-and-configuration)
  - [Table of Contents](#table-of-contents)
  - [Prerequisites](#prerequisites)
  - [Running the script](#running-the-script)
  - [Google Cloud Setup](#google-cloud-setup)
  - [Instance Creation](#instance-creation)
    - [Console UI Method](#console-ui-method)
    - [Programmatic Method](#programmatic-method)
  - [SSH Configuration](#ssh-configuration)
    - [Quick Setup](#quick-setup)
    - [Manual Setup](#manual-setup)
  - [Benchmarking Tools](#benchmarking-tools)
    - [System Information Commands](#system-information-commands)
    - [Initial Setup](#initial-setup)
    - [Running Benchmarks](#running-benchmarks)
  - [Important Notes](#important-notes)
  - [Useful Commands](#useful-commands)
  - [References](#references)

## Prerequisites

- Google Cloud SDK (gcloud CLI tools) installed
- Python environment with google-cloud-compute package
- Access to Google Cloud Console with compute.admin permissions
- SSH key pair for VM access

## Running the program
1. Make sure you're defaults like region and project are setup, refer to [Google Cloud Setup](#google-cloud-setup)
2. Run the script (python3 for mac:
```python
python manage_vm.py
```

> NOTE: only use the interactive approach. Creating an instance using a json file still needs some corrections

## Google Cloud Setup

1. Install the [gcloud CLI tools](https://cloud.google.com/sdk/docs/install):
   - Download and extract the installation package
   - Run the `install.sh` script
   - Execute `gcloud init`

2. Configure project settings:
   - Default zone: `europe-west2-a` (closest to London)
   - Ensure compute.admin permissions are granted for running instances of other projects
   - Verify project access:
     ```bash
     gcloud config list --format="value(core.project)"
     ```

3. Tips for Instance Creation:
   - Use the Google Cloud Console UI's "Equivalent Code" feature to generate commands
   - Access this by clicking "<> Equivalent Code" in the instance creation interface

## Instance Creation

### Console UI Method

1. Navigate to the [Google Cloud Console Instance Creation page](https://console.cloud.google.com/compute/instancesAdd)
2. Configure the following settings:
   - Region: europe-west2 (London)
   - Machine type: n2d-standard-2
   - Tag: cloud-systems
   - Storage: 100GB disk

### Programmatic Method

1. Set up your local environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip install google-cloud-compute
```

2. Configure Google Cloud authentication:
```bash
gcloud auth application-default login
gcloud config set project cs-lab2
```

3. The Python script was created following the Google Cloud documentation [here](https://cloud.google.com/compute/docs/instances/create-vm-from-instance-template) for VM creation from templates.

## SSH Configuration

### Quick Setup
```bash
gcloud compute config-ssh
```

### Manual Setup

1. Generate SSH key:
```bash
ssh-keygen -t ed25519 -C "$(whoami)@$(hostname)"
```

2. Verify current user configuration:
```bash
gcloud config list --format="value(core.account)"
```

3. Add key to project metadata:
```bash
gcloud compute project-info add-metadata \
--metadata ssh-keys="$(gcloud compute project-info describe \
--format="value(commonInstanceMetadata.items.filter(key:ssh-keys).firstof(value))")
$(whoami):$(cat ~/.ssh/id_ed25519.pub)"
```

4. Connect to VM:
```bash
# List available instances and their IPs
gcloud compute instances list \
--format=table"[box=true](name:label=NAME, networkInterfaces[].accessConfigs[].natIP.flatten():label=EXTERNAL_IP)"

# Connect using SSH
ssh $(whoami)@$VM_IP_ADDRESS
```

## Benchmarking Tools

### System Information Commands
```bash
lscpu      # CPU information
lsblk      # Block device information
uname -a   # System information
vmstat     # Virtual memory statistics
whoami     # Current user
hostname   # System hostname
```

### Initial Setup

1. Update system packages:
```bash
sudo apt-get update
```

2. Install benchmarking tools:
```bash
sudo apt-get install sysbench
```

### Running Benchmarks

Example CPU benchmark:
```bash
sysbench cpu --cpu-max-prime=500 --threads=1 run
```

The benchmark can be run with different thread counts (1, 2, 4) to test multi-core performance.

## Important Notes

- Remember to suspend VM instances when not in use
- For new projects, ensure proper IAM permissions are configured
- The closest Google Cloud zone to London is europe-west2-a

## Useful Commands

```bash
# Basic instance management
gcloud compute instances --help    # Access help documentation
gcloud compute instances list      # List all instances
gcloud compute instances create    # Create new instance
gcloud compute instances create-with-container  # Create container-optimized instance
gcloud compute ssh                # SSH into instance

# Project configuration
gcloud config list                # View current configuration
gcloud config set project PROJECT_ID  # Set project
```

## References

- [Google Cloud Compute Instances Documentation](https://cloud.google.com/compute/docs/instances)
- [Machine Family Resource Guide](https://cloud.google.com/compute/docs/machine-resource)
- [Sysbench Documentation](https://github.com/akopytov/sysbench)
- [Google Cloud SDK Installation Guide](https://cloud.google.com/sdk/docs/install)
