import json
import yaml
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

class AnsibleParser:
    """Parser for Ansible playbook outputs containing vCenter VM details and alarms"""
    
    def __init__(self):
        self.supported_formats = ['.json', '.yaml', '.yml']
    
    def parse_file(self, filepath: str) -> Dict[str, Any]:
        """Parse an Ansible output file and extract VM and alarm data"""
        try:
            file_ext = os.path.splitext(filepath)[1].lower()
            
            if file_ext not in self.supported_formats:
                raise ValueError(f"Unsupported file format: {file_ext}")
            
            with open(filepath, 'r', encoding='utf-8') as file:
                if file_ext == '.json':
                    data = json.load(file)
                else:  # yaml or yml
                    data = yaml.safe_load(file)
            
            return self._extract_vcenter_data(data)
            
        except Exception as e:
            logger.error(f"Error parsing file {filepath}: {str(e)}")
            raise
    
    def _extract_vcenter_data(self, data: Any) -> Dict[str, Any]:
        """Extract VM and alarm data from parsed Ansible output"""
        result = {
            'vms': [],
            'alarms': [],
            'metadata': {
                'parsed_at': datetime.utcnow().isoformat(),
                'total_vms': 0,
                'total_alarms': 0
            }
        }
        
        try:
            # Handle different Ansible output structures
            if isinstance(data, dict):
                # Check for common Ansible playbook structure
                if 'plays' in data:
                    self._parse_playbook_structure(data, result)
                elif 'results' in data:
                    self._parse_results_structure(data, result)
                elif 'ansible_facts' in data:
                    self._parse_facts_structure(data, result)
                else:
                    # Try to find VM data in the top level
                    self._parse_direct_structure(data, result)
            elif isinstance(data, list):
                # Handle list of results
                for item in data:
                    if isinstance(item, dict):
                        self._parse_direct_structure(item, result)
            
            result['metadata']['total_vms'] = len(result['vms'])
            result['metadata']['total_alarms'] = len(result['alarms'])
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting vCenter data: {str(e)}")
            raise
    
    def _parse_playbook_structure(self, data: Dict, result: Dict):
        """Parse Ansible playbook output structure"""
        for play in data.get('plays', []):
            for task in play.get('tasks', []):
                for host, host_result in task.get('hosts', {}).items():
                    self._extract_vm_data_from_result(host_result, result)
                    self._extract_alarm_data_from_result(host_result, result)
    
    def _parse_results_structure(self, data: Dict, result: Dict):
        """Parse results-based structure"""
        results = data.get('results', [])
        if isinstance(results, list):
            for item in results:
                self._extract_vm_data_from_result(item, result)
                self._extract_alarm_data_from_result(item, result)
        else:
            self._extract_vm_data_from_result(results, result)
            self._extract_alarm_data_from_result(results, result)
    
    def _parse_facts_structure(self, data: Dict, result: Dict):
        """Parse ansible_facts structure"""
        facts = data.get('ansible_facts', {})
        self._extract_vm_data_from_result(facts, result)
        self._extract_alarm_data_from_result(facts, result)
    
    def _parse_direct_structure(self, data: Dict, result: Dict):
        """Parse direct data structure"""
        self._extract_vm_data_from_result(data, result)
        self._extract_alarm_data_from_result(data, result)
    
    def _extract_vm_data_from_result(self, data: Dict, result: Dict):
        """Extract VM data from a result structure"""
        # Look for VM data in various possible locations
        vm_locations = [
            'vm_info', 'virtual_machines', 'vms', 'instances',
            'vm_facts', 'vmware_vm_info', 'vcenter_vm_info'
        ]
        
        for location in vm_locations:
            if location in data:
                vm_data = data[location]
                if isinstance(vm_data, list):
                    for vm in vm_data:
                        result['vms'].append(self._normalize_vm_data(vm))
                elif isinstance(vm_data, dict):
                    # Could be a dict of VMs keyed by name/id
                    for vm_key, vm_info in vm_data.items():
                        if isinstance(vm_info, dict):
                            vm_info['name'] = vm_info.get('name', vm_key)
                            result['vms'].append(self._normalize_vm_data(vm_info))
                break
        
        # Also check if the entire data structure is a VM
        if self._looks_like_vm_data(data):
            result['vms'].append(self._normalize_vm_data(data))
    
    def _extract_alarm_data_from_result(self, data: Dict, result: Dict):
        """Extract alarm data from a result structure"""
        # Look for alarm data in various possible locations
        alarm_locations = [
            'alarms', 'vm_alarms', 'alerts', 'events',
            'alarm_info', 'vmware_alarms'
        ]
        
        for location in alarm_locations:
            if location in data:
                alarm_data = data[location]
                if isinstance(alarm_data, list):
                    for alarm in alarm_data:
                        result['alarms'].append(self._normalize_alarm_data(alarm))
                elif isinstance(alarm_data, dict):
                    for alarm_key, alarm_info in alarm_data.items():
                        if isinstance(alarm_info, dict):
                            alarm_info['name'] = alarm_info.get('name', alarm_key)
                            result['alarms'].append(self._normalize_alarm_data(alarm_info))
                        elif isinstance(alarm_info, list):
                            for alarm in alarm_info:
                                result['alarms'].append(self._normalize_alarm_data(alarm))
                break
    
    def _looks_like_vm_data(self, data: Dict) -> bool:
        """Check if data structure looks like VM information"""
        vm_indicators = [
            'name', 'uuid', 'instance_uuid', 'power_state',
            'num_cpu', 'memory_mb', 'guest_fullname'
        ]
        return any(indicator in data for indicator in vm_indicators)
    
    def _normalize_vm_data(self, vm_data: Dict) -> Dict[str, Any]:
        """Normalize VM data to a consistent format"""
        normalized = {}
        
        # VM identification
        normalized['name'] = vm_data.get('name') or vm_data.get('vm_name') or vm_data.get('guest_name', 'Unknown')
        normalized['uuid'] = vm_data.get('uuid') or vm_data.get('instance_uuid') or vm_data.get('vm_uuid')
        
        # Power state
        power_state = vm_data.get('power_state') or vm_data.get('runtime.powerState')
        normalized['power_state'] = power_state.lower() if power_state else 'unknown'
        
        # Resource information
        normalized['cpu_count'] = vm_data.get('num_cpu') or vm_data.get('cpu_count') or vm_data.get('config.hardware.numCPU')
        normalized['memory_mb'] = vm_data.get('memory_mb') or vm_data.get('memory_size_mb') or vm_data.get('config.hardware.memoryMB')
        
        # Disk information
        disk_gb = vm_data.get('disk_gb') or vm_data.get('disk_size_gb')
        if not disk_gb and 'disk' in vm_data:
            # Calculate total disk size if individual disks are provided
            disks = vm_data['disk']
            if isinstance(disks, list):
                total_kb = sum(disk.get('size_kb', 0) for disk in disks)
                disk_gb = total_kb / (1024 * 1024) if total_kb > 0 else None
        normalized['disk_gb'] = disk_gb
        
        # Network information
        normalized['network_count'] = vm_data.get('network_count') or len(vm_data.get('networks', []))
        
        # Guest OS
        normalized['guest_os'] = (
            vm_data.get('guest_fullname') or 
            vm_data.get('guest_os') or 
            vm_data.get('config.guestFullName')
        )
        
        # Host and cluster information
        normalized['host_name'] = vm_data.get('host_name') or vm_data.get('runtime.host')
        normalized['cluster_name'] = vm_data.get('cluster_name') or vm_data.get('cluster')
        normalized['datacenter_name'] = vm_data.get('datacenter_name') or vm_data.get('datacenter')
        
        return normalized
    
    def _normalize_alarm_data(self, alarm_data: Dict) -> Dict[str, Any]:
        """Normalize alarm data to a consistent format"""
        normalized = {}
        
        # Alarm identification
        normalized['name'] = alarm_data.get('name') or alarm_data.get('alarm_name', 'Unknown Alarm')
        normalized['description'] = alarm_data.get('description') or alarm_data.get('alarm_description', '')
        
        # Severity and status
        severity = alarm_data.get('severity') or alarm_data.get('alarm_severity', 'unknown')
        normalized['severity'] = severity.lower()
        
        status = alarm_data.get('status') or alarm_data.get('alarm_status', 'unknown')
        normalized['status'] = status.lower()
        
        # VM association
        normalized['vm_name'] = (
            alarm_data.get('vm_name') or 
            alarm_data.get('entity_name') or 
            alarm_data.get('object_name', 'Unknown VM')
        )
        
        # Timing information
        triggered_time = alarm_data.get('triggered_time') or alarm_data.get('time') or alarm_data.get('created_time')
        if triggered_time:
            try:
                if isinstance(triggered_time, str):
                    # Try to parse various datetime formats
                    from dateutil import parser
                    normalized['triggered_time'] = parser.parse(triggered_time)
                else:
                    normalized['triggered_time'] = triggered_time
            except:
                normalized['triggered_time'] = None
        else:
            normalized['triggered_time'] = None
        
        # Acknowledgment status
        normalized['acknowledged'] = alarm_data.get('acknowledged', False)
        
        return normalized
