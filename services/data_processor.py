import pandas as pd
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from config import Config
from utils.logger import get_logger

logger = get_logger(__name__)

class DataProcessor:
    """Process and export vCenter data for Power BI consumption"""
    
    def __init__(self):
        self.config = Config()
        self.config.ensure_directories()
    
    def process_data(self, parsed_data: Dict[str, Any], job_id: int) -> List[str]:
        """Process parsed data and generate output files"""
        try:
            output_files = []
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Process VM data
            if parsed_data['vms']:
                vm_files = self._process_vm_data(parsed_data['vms'], timestamp, job_id)
                output_files.extend(vm_files)
            
            # Process alarm data
            if parsed_data['alarms']:
                alarm_files = self._process_alarm_data(parsed_data['alarms'], timestamp, job_id)
                output_files.extend(alarm_files)
            
            # Generate summary report
            summary_file = self._generate_summary_report(parsed_data, timestamp, job_id)
            output_files.append(summary_file)
            
            logger.info(f"Generated {len(output_files)} output files for job {job_id}")
            return output_files
            
        except Exception as e:
            logger.error(f"Error processing data for job {job_id}: {str(e)}")
            raise
    
    def _process_vm_data(self, vm_data: List[Dict], timestamp: str, job_id: int) -> List[str]:
        """Process VM data and generate output files"""
        from models import ProcessingJob
        output_files = []
        
        # Get job info for environment segregation
        job = ProcessingJob.query.get(job_id)
        env_suffix = ""
        if job and job.vcenter_environment and job.client_name:
            env_suffix = f"_{job.client_name}_{job.vcenter_environment}"
        
        # Create DataFrame
        df = pd.DataFrame(vm_data)
        
        # Clean and validate data
        df = self._clean_vm_dataframe(df)
        
        # Add metadata columns
        df['processing_job_id'] = job_id
        df['processed_at'] = datetime.now()
        df['data_source'] = 'ansible_vcenter'
        if job:
            df['vcenter_environment'] = job.vcenter_environment
            df['client_name'] = job.client_name
        
        # Group by environment if configured
        if self.config.SEPARATE_BY_ENVIRONMENT and 'vcenter_environment' in df.columns:
            # Generate separate files per environment
            for env in df['vcenter_environment'].unique():
                if pd.isna(env):
                    continue
                env_df = df[df['vcenter_environment'] == env]
                client = env_df['client_name'].iloc[0] if not env_df['client_name'].empty else 'unknown'
                
                base_filename = f"vcenter_vms_{client}_{env}_{timestamp}"
                output_files.extend(self._export_dataframe(env_df, base_filename, 'vm'))
        else:
            # Generate single file
            base_filename = f"vcenter_vms{env_suffix}_{timestamp}"
            output_files.extend(self._export_dataframe(df, base_filename, 'vm'))
        
        return output_files
    
    def _process_alarm_data(self, alarm_data: List[Dict], timestamp: str, job_id: int) -> List[str]:
        """Process alarm data and generate output files"""
        from models import ProcessingJob
        output_files = []
        
        # Get job info for environment segregation
        job = ProcessingJob.query.get(job_id)
        env_suffix = ""
        if job and job.vcenter_environment and job.client_name:
            env_suffix = f"_{job.client_name}_{job.vcenter_environment}"
        
        # Create DataFrame
        df = pd.DataFrame(alarm_data)
        
        # Clean and validate data
        df = self._clean_alarm_dataframe(df)
        
        # Add metadata columns
        df['processing_job_id'] = job_id
        df['processed_at'] = datetime.now()
        df['data_source'] = 'ansible_vcenter'
        if job:
            df['vcenter_environment'] = job.vcenter_environment
            df['client_name'] = job.client_name
        
        # Group by environment if configured
        if self.config.SEPARATE_BY_ENVIRONMENT and 'vcenter_environment' in df.columns:
            # Generate separate files per environment
            for env in df['vcenter_environment'].unique():
                if pd.isna(env):
                    continue
                env_df = df[df['vcenter_environment'] == env]
                client = env_df['client_name'].iloc[0] if not env_df['client_name'].empty else 'unknown'
                
                base_filename = f"vcenter_alarms_{client}_{env}_{timestamp}"
                output_files.extend(self._export_dataframe(env_df, base_filename, 'alarm'))
        else:
            # Generate single file
            base_filename = f"vcenter_alarms{env_suffix}_{timestamp}"
            output_files.extend(self._export_dataframe(df, base_filename, 'alarm'))
        
        return output_files
    
    def _clean_vm_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate VM DataFrame"""
        # Fill missing values
        df['name'] = df['name'].fillna('Unknown VM')
        df['power_state'] = df['power_state'].fillna('unknown')
        df['cpu_count'] = pd.to_numeric(df['cpu_count'], errors='coerce').fillna(0).astype(int)
        df['memory_mb'] = pd.to_numeric(df['memory_mb'], errors='coerce').fillna(0).astype(int)
        df['disk_gb'] = pd.to_numeric(df['disk_gb'], errors='coerce').fillna(0).astype(float)
        df['network_count'] = pd.to_numeric(df['network_count'], errors='coerce').fillna(0).astype(int)
        
        # Calculate derived columns for Power BI
        df['memory_gb'] = (df['memory_mb'] / 1024).round(2)
        df['cpu_memory_ratio'] = (df['memory_gb'] / df['cpu_count'].replace(0, 1)).round(2)
        df['total_resources_score'] = (
            df['cpu_count'] * 0.3 + 
            df['memory_gb'] * 0.4 + 
            df['disk_gb'] * 0.3
        ).round(2)
        
        # Add status indicators
        df['is_powered_on'] = df['power_state'].str.lower() == 'poweredon'
        df['resource_category'] = pd.cut(
            df['total_resources_score'],
            bins=[0, 10, 50, 100, float('inf')],
            labels=['Low', 'Medium', 'High', 'Critical']
        )
        
        return df
    
    def _clean_alarm_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate alarm DataFrame"""
        # Fill missing values
        df['name'] = df['name'].fillna('Unknown Alarm')
        df['vm_name'] = df['vm_name'].fillna('Unknown VM')
        df['severity'] = df['severity'].fillna('unknown')
        df['status'] = df['status'].fillna('unknown')
        df['acknowledged'] = df['acknowledged'].fillna(False)
        
        # Standardize severity levels
        severity_mapping = {
            'critical': 'Critical',
            'error': 'Critical',
            'warning': 'Warning',
            'info': 'Information',
            'information': 'Information',
            'normal': 'Normal',
            'unknown': 'Unknown'
        }
        df['severity_normalized'] = df['severity'].str.lower().map(severity_mapping).fillna('Unknown')
        
        # Add priority scoring
        priority_scores = {
            'Critical': 5,
            'Warning': 3,
            'Information': 1,
            'Normal': 0,
            'Unknown': 2
        }
        df['priority_score'] = df['severity_normalized'].map(priority_scores)
        
        # Handle triggered_time
        if 'triggered_time' in df.columns:
            df['triggered_time'] = pd.to_datetime(df['triggered_time'], errors='coerce')
            df['days_since_triggered'] = (datetime.now() - df['triggered_time']).dt.days
        
        return df
    
    def _export_vm_excel(self, df: pd.DataFrame, filepath: str):
        """Export VM data to Excel with formatting"""
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='VM_Details', index=False)
            
            # Get workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['VM_Details']
            
            # Apply formatting
            self._format_excel_headers(worksheet, workbook)
            self._format_vm_data_columns(worksheet, workbook, len(df))
    
    def _export_alarm_excel(self, df: pd.DataFrame, filepath: str):
        """Export alarm data to Excel with formatting"""
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='VM_Alarms', index=False)
            
            # Get workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['VM_Alarms']
            
            # Apply formatting
            self._format_excel_headers(worksheet, workbook)
            self._format_alarm_data_columns(worksheet, workbook, len(df))
    
    def _format_excel_headers(self, worksheet, workbook):
        """Format Excel headers"""
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")
        
        for cell in worksheet[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
    
    def _format_vm_data_columns(self, worksheet, workbook, row_count):
        """Format VM data columns"""
        # Auto-adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
        
        # Apply conditional formatting for power state
        from openpyxl.formatting.rule import Rule
        from openpyxl.styles.differential import DifferentialStyle
        
        # Power state column formatting would go here
        # This is a simplified version - full implementation would include more formatting
    
    def _format_alarm_data_columns(self, worksheet, workbook, row_count):
        """Format alarm data columns"""
        # Similar to VM formatting but for alarm-specific columns
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    def _generate_summary_report(self, parsed_data: Dict, timestamp: str, job_id: int) -> str:
        """Generate a summary report of the processing"""
        summary = {
            'processing_summary': {
                'job_id': job_id,
                'processed_at': datetime.now().isoformat(),
                'total_vms': len(parsed_data['vms']),
                'total_alarms': len(parsed_data['alarms'])
            },
            'vm_statistics': self._calculate_vm_statistics(parsed_data['vms']),
            'alarm_statistics': self._calculate_alarm_statistics(parsed_data['alarms']),
            'metadata': parsed_data.get('metadata', {})
        }
        
        summary_path = os.path.join(
            self.config.OUTPUT_DIRECTORY, 
            f"processing_summary_{timestamp}.json"
        )
        
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        return summary_path
    
    def _calculate_vm_statistics(self, vm_data: List[Dict]) -> Dict:
        """Calculate VM statistics"""
        if not vm_data:
            return {}
        
        df = pd.DataFrame(vm_data)
        df = self._clean_vm_dataframe(df)
        
        stats = {
            'total_count': len(df),
            'power_state_distribution': df['power_state'].value_counts().to_dict(),
            'average_cpu_count': df['cpu_count'].mean(),
            'average_memory_gb': (df['memory_mb'] / 1024).mean(),
            'total_disk_gb': df['disk_gb'].sum(),
            'guest_os_distribution': df['guest_os'].value_counts().head(10).to_dict()
        }
        
        return stats
    
    def _calculate_alarm_statistics(self, alarm_data: List[Dict]) -> Dict:
        """Calculate alarm statistics"""
        if not alarm_data:
            return {}
        
        df = pd.DataFrame(alarm_data)
        df = self._clean_alarm_dataframe(df)
        
        stats = {
            'total_count': len(df),
            'severity_distribution': df['severity_normalized'].value_counts().to_dict(),
            'acknowledged_count': df['acknowledged'].sum(),
            'unacknowledged_count': (~df['acknowledged']).sum(),
            'unique_vms_with_alarms': df['vm_name'].nunique()
        }
        
        return stats
    
    def _export_dataframe(self, df: pd.DataFrame, base_filename: str, data_type: str) -> List[str]:
        """Export DataFrame to multiple formats"""
        output_files = []
        
        # CSV export
        csv_path = os.path.join(self.config.OUTPUT_DIRECTORY, f"{base_filename}.csv")
        df.to_csv(csv_path, index=False)
        output_files.append(csv_path)
        
        # Excel export with formatting
        excel_path = os.path.join(self.config.OUTPUT_DIRECTORY, f"{base_filename}.xlsx")
        if data_type == 'vm':
            self._export_vm_excel(df, excel_path)
        else:
            self._export_alarm_excel(df, excel_path)
        output_files.append(excel_path)
        
        # JSON export
        json_path = os.path.join(self.config.OUTPUT_DIRECTORY, f"{base_filename}.json")
        df.to_json(json_path, orient='records', date_format='iso', indent=2)
        output_files.append(json_path)
        
        return output_files
