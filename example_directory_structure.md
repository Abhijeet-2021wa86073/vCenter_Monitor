# Multi-Environment Directory Structure Examples

The vCenter Data Processor supports multiple VMware environments and clients through intelligent file path detection and configuration mapping.

## Recommended Directory Structure

```
ansible_outputs/
├── client-a/
│   ├── prod-vcenter1/
│   │   ├── vm_inventory_20250128.json
│   │   ├── vm_alarms_20250128.json
│   │   └── datacenter_info.yaml
│   ├── dev-vcenter/
│   │   ├── vm_inventory_20250128.json
│   │   └── vm_alarms_20250128.json
│   └── test-vcenter/
│       ├── vm_inventory_20250128.json
│       └── vm_alarms_20250128.json
├── client-b/
│   ├── prod-vcenter2/
│   │   ├── vm_inventory_20250128.json
│   │   ├── vm_alarms_20250128.json
│   │   └── cluster_data.yaml
│   └── staging-vcenter/
│       ├── vm_inventory_20250128.json
│       └── vm_alarms_20250128.json
└── internal/
    ├── corporate-vcenter/
    │   ├── vm_inventory_20250128.json
    │   └── vm_alarms_20250128.json
    └── lab-vcenter/
        ├── vm_inventory_20250128.json
        └── vm_alarms_20250128.json
```

## Configuration Mapping

The system automatically maps file paths to environments using the `ENVIRONMENT_MAPPING` in `config.py`:

```python
ENVIRONMENT_MAPPING = {
    "prod-vcenter1": {"environment": "production-vc1", "client": "client-a"},
    "prod-vcenter2": {"environment": "production-vc2", "client": "client-b"},
    "dev-vcenter": {"environment": "development", "client": "internal"},
    "test-vcenter": {"environment": "testing", "client": "internal"}
}
```

## Output File Segregation

When `SEPARATE_BY_ENVIRONMENT = True`, the system generates separate output files:

```
powerbi_outputs/
├── vcenter_vms_client-a_production-vc1_20250128_143022.csv
├── vcenter_vms_client-a_production-vc1_20250128_143022.xlsx
├── vcenter_vms_client-a_production-vc1_20250128_143022.json
├── vcenter_alarms_client-a_production-vc1_20250128_143022.csv
├── vcenter_vms_client-b_production-vc2_20250128_143055.csv
├── vcenter_vms_client-b_production-vc2_20250128_143055.xlsx
└── vcenter_vms_client-b_production-vc2_20250128_143055.json
```

## Benefits for Multiple Clients

1. **Data Isolation**: Each client's data is processed separately
2. **Environment Tracking**: Production, development, and test environments are clearly identified
3. **Scalable Processing**: Handles 100+ VMs per environment efficiently
4. **Power BI Ready**: Separate datasets for each client/environment combination
5. **Audit Trail**: Complete tracking of which environment and client each VM belongs to

## Ansible Playbook Integration

Your Ansible playbooks should save outputs to the appropriate directory structure:

```yaml
- name: Save VM inventory for Client A Production
  copy:
    content: "{{ vcenter_vm_data | to_nice_json }}"
    dest: "./ansible_outputs/client-a/prod-vcenter1/vm_inventory_{{ ansible_date_time.date }}.json"

- name: Save VM alarms for Client A Production  
  copy:
    content: "{{ vcenter_alarm_data | to_nice_json }}"
    dest: "./ansible_outputs/client-a/prod-vcenter1/vm_alarms_{{ ansible_date_time.date }}.json"
```

The system will automatically detect new files and process them with the correct environment and client identification.