# Leader Election using Azure Blob Storage

## Overview

This Python script implements a leader election mechanism using Azure Blob Storage. The leader election ensures that only one node among multiple instances can acquire leadership at a time using blob leasing. The leader must periodically renew its lease to maintain leadership. If a leader fails, another node can take over.

## Requirements

- Python 3.x
- Azure Storage SDK for Python (`azure-storage-blob`)
- An Azure Storage Account with access keys

## Installation

To install dependencies, run:

```sh
pip install azure-storage-blob
```

## Usage

### Running a Node

Run the script with the following parameters:

```sh
python leader_election.py --account-name <AZURE_STORAGE_ACCOUNT> --account-key <AZURE_STORAGE_KEY> --container <BLOB_CONTAINER>
```

## LeaderElection Class

### Initialization

```python
LeaderElection(storage_account_name, storage_account_key, container_name, blob_name="leader", lease_duration=60, node_id=None)
```

**Parameters:**

- `storage_account_name` (str): Azure Storage account name.
- `storage_account_key` (str): Azure Storage account key.
- `container_name` (str): Name of the Azure Blob container.
- `blob_name` (str, optional): Name of the blob used for leader election (default: "leader").
- `lease_duration` (int, optional): Duration of the lease in seconds (default: 60).
- `node_id` (str, optional): Unique identifier for the node (default: auto-generated hostname + UUID).

### Methods

#### `try_acquire_leadership()`

Attempts to acquire leadership by leasing the blob. Returns `True` if successful, `False` otherwise.

#### `_update_leader_info()`

Updates the blob with the new leader's information.

#### `renew_lease()`

Renews the lease to maintain leadership. Returns `True` if successful, `False` otherwise.

#### `release_leadership()`

Releases the leadership voluntarily.

#### `start()`

Starts the leader election process and launches a heartbeat thread.

#### `stop()`

Stops the leader election process and releases leadership if held.

#### `get_current_leader()`

Returns the current leader's information.

## Simulating a Node

Use the `simulate_node` function to test leader election among multiple nodes:

```python
simulate_node(account_name, account_key, container_name, node_name, duration=120)
```

**Parameters:**

- `account_name` (str): Azure Storage account name.
- `account_key` (str): Azure Storage account key.
- `container_name` (str): Name of the Azure Blob container.
- `node_name` (str): Unique name of the node.
- `duration` (int, optional): Duration of the simulation in seconds (default: 120).
