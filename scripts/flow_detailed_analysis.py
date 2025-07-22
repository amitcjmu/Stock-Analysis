#!/usr/bin/env python3
"""
Detailed Flow Analysis Tool
Provides deep inspection of flow data and manual intervention capabilities.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.prompt import Prompt, Confirm
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from app.core.database import AsyncSessionLocal
from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState
from app.models.master_flow_extensions import CrewAIFlowStateExtensions
from app.models.field_mapping import FieldMapping

console = Console()

class DetailedFlowAnalyzer:
    """Provides detailed analysis and manual intervention capabilities."""
    
    def __init__(self, flow_id: str):
        self.flow_id = flow_id
        
    async def get_raw_data_analysis(self, session: AsyncSession) -> Dict[str, Any]:
        """Analyze the raw data structure and content."""
        unified_state = await session.execute(
            select(UnifiedDiscoveryFlowState).filter_by(flow_id=self.flow_id)
        )
        unified_state = unified_state.scalar_one_or_none()
        
        if not unified_state or not unified_state.raw_data:
            return {'error': 'No raw data found'}
        
        raw_data = unified_state.raw_data
        
        analysis = {
            'structure': self._analyze_structure(raw_data),
            'data_types': self._analyze_data_types(raw_data),
            'sample_records': self._get_sample_records(raw_data),
            'field_statistics': self._analyze_fields(raw_data)
        }
        
        return analysis
    
    def _analyze_structure(self, data: Any) -> Dict[str, Any]:
        """Analyze the structure of the data."""
        if isinstance(data, dict):
            if 'servers' in data:
                # Likely CMDB data
                return {
                    'type': 'CMDB Export',
                    'top_level_keys': list(data.keys()),
                    'server_count': len(data.get('servers', [])) if isinstance(data.get('servers'), list) else 0,
                    'has_metadata': 'metadata' in data,
                    'has_export_info': 'export_info' in data
                }
            else:
                return {
                    'type': 'Dictionary',
                    'keys': list(data.keys())[:20],  # First 20 keys
                    'key_count': len(data.keys())
                }
        elif isinstance(data, list):
            return {
                'type': 'List',
                'length': len(data),
                'first_item_type': type(data[0]).__name__ if data else 'Empty'
            }
        else:
            return {
                'type': type(data).__name__,
                'info': 'Unexpected data type'
            }
    
    def _analyze_data_types(self, data: Any) -> Dict[str, Any]:
        """Analyze data types in the dataset."""
        if isinstance(data, dict) and 'servers' in data and isinstance(data['servers'], list):
            # Analyze CMDB server data
            if not data['servers']:
                return {'error': 'No server records found'}
            
            # Sample first record
            sample = data['servers'][0]
            field_types = {}
            
            for key, value in sample.items():
                field_types[key] = {
                    'type': type(value).__name__,
                    'sample': str(value)[:50] if value is not None else 'None'
                }
            
            return field_types
        
        return {'error': 'Unable to analyze data types'}
    
    def _get_sample_records(self, data: Any, count: int = 3) -> List[Dict[str, Any]]:
        """Get sample records from the data."""
        if isinstance(data, dict) and 'servers' in data and isinstance(data['servers'], list):
            return data['servers'][:count]
        elif isinstance(data, list):
            return data[:count]
        return []
    
    def _analyze_fields(self, data: Any) -> Dict[str, Any]:
        """Analyze fields across all records."""
        if isinstance(data, dict) and 'servers' in data and isinstance(data['servers'], list):
            servers = data['servers']
            if not servers:
                return {'error': 'No servers to analyze'}
            
            # Collect all unique fields
            all_fields = set()
            field_presence = {}
            field_values = {}
            
            for server in servers:
                for field in server.keys():
                    all_fields.add(field)
                    if field not in field_presence:
                        field_presence[field] = 0
                        field_values[field] = set()
                    
                    field_presence[field] += 1
                    if server[field] is not None:
                        field_values[field].add(str(server[field])[:50])
            
            # Calculate statistics
            stats = {}
            total_records = len(servers)
            
            for field in sorted(all_fields):
                stats[field] = {
                    'presence_count': field_presence[field],
                    'presence_percentage': (field_presence[field] / total_records) * 100,
                    'unique_values': len(field_values[field]),
                    'sample_values': list(field_values[field])[:5]
                }
            
            return {
                'total_fields': len(all_fields),
                'total_records': total_records,
                'field_stats': stats
            }
        
        return {'error': 'Unable to analyze fields'}
    
    async def display_raw_data_analysis(self, session: AsyncSession):
        """Display detailed raw data analysis."""
        console.print("\n[bold cyan]═══ Raw Data Analysis ═══[/bold cyan]\n")
        
        analysis = await self.get_raw_data_analysis(session)
        
        if 'error' in analysis:
            console.print(f"[red]Error: {analysis['error']}[/red]")
            return
        
        # 1. Structure Analysis
        structure = analysis['structure']
        structure_info = f"""
[bold]Data Type:[/bold] {structure.get('type', 'Unknown')}
[bold]Server Count:[/bold] {structure.get('server_count', 'N/A')}
[bold]Top Level Keys:[/bold] {', '.join(structure.get('top_level_keys', [])[:5])}
        """
        console.print(Panel(structure_info.strip(), title="Data Structure", border_style="green"))
        
        # 2. Field Statistics
        if 'field_stats' in analysis['field_statistics']:
            stats = analysis['field_statistics']['field_stats']
            
            # Create table for fields
            table = Table(title="Field Analysis")
            table.add_column("Field Name", style="cyan", width=30)
            table.add_column("Presence", style="green", width=10)
            table.add_column("Unique", style="yellow", width=10)
            table.add_column("Sample Values", style="white", width=50)
            
            # Sort by presence percentage
            sorted_fields = sorted(stats.items(), key=lambda x: x[1]['presence_percentage'], reverse=True)
            
            for field, field_stats in sorted_fields[:20]:  # Top 20 fields
                presence = f"{field_stats['presence_percentage']:.1f}%"
                unique = str(field_stats['unique_values'])
                samples = ", ".join(field_stats['sample_values'][:3])
                
                table.add_row(field, presence, unique, samples)
            
            console.print(table)
            
            if len(stats) > 20:
                console.print(f"\n[italic]... and {len(stats) - 20} more fields[/italic]")
        
        # 3. Sample Records
        if analysis['sample_records']:
            console.print("\n[bold]Sample Records:[/bold]\n")
            for i, record in enumerate(analysis['sample_records'], 1):
                console.print(f"[bold]Record {i}:[/bold]")
                # Format as JSON for readability
                json_str = json.dumps(record, indent=2, default=str)
                syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
                console.print(syntax)
                console.print("")
    
    async def analyze_field_mapping_details(self, session: AsyncSession):
        """Analyze field mapping details and quality."""
        console.print("\n[bold cyan]═══ Field Mapping Analysis ═══[/bold cyan]\n")
        
        # Get field mappings
        field_mappings = await session.execute(
            select(FieldMapping).filter_by(discovery_flow_id=self.flow_id)
        )
        field_mappings = field_mappings.scalars().all()
        
        if not field_mappings:
            # Check if mappings exist in unified state
            unified_state = await session.execute(
                select(UnifiedDiscoveryFlowState).filter_by(flow_id=self.flow_id)
            )
            unified_state = unified_state.scalar_one_or_none()
            
            if unified_state and unified_state.field_mappings:
                console.print("[yellow]Field mappings exist in state but not in database![/yellow]")
                console.print(f"Found {len(unified_state.field_mappings)} mappings in state")
                
                # Display mappings from state
                table = Table(title="Field Mappings (from state)")
                table.add_column("Source Field", style="cyan")
                table.add_column("Target Field", style="yellow")
                table.add_column("Confidence", style="green")
                
                for mapping in unified_state.field_mappings[:20]:
                    table.add_row(
                        mapping.get('source_field', 'N/A'),
                        mapping.get('target_field', 'N/A'),
                        f"{mapping.get('confidence_score', 0):.2f}"
                    )
                
                console.print(table)
            else:
                console.print("[red]No field mappings found[/red]")
            return
        
        # Analyze mapping quality
        total_mappings = len(field_mappings)
        approved_mappings = sum(1 for fm in field_mappings if fm.is_approved)
        high_confidence = sum(1 for fm in field_mappings if fm.confidence_score >= 0.8)
        medium_confidence = sum(1 for fm in field_mappings if 0.5 <= fm.confidence_score < 0.8)
        low_confidence = sum(1 for fm in field_mappings if fm.confidence_score < 0.5)
        
        # Display summary
        summary = f"""
[bold]Total Mappings:[/bold] {total_mappings}
[bold]Approved:[/bold] {approved_mappings} ({(approved_mappings/total_mappings*100):.1f}%)
[bold]High Confidence (≥0.8):[/bold] {high_confidence} ({(high_confidence/total_mappings*100):.1f}%)
[bold]Medium Confidence (0.5-0.8):[/bold] {medium_confidence} ({(medium_confidence/total_mappings*100):.1f}%)
[bold]Low Confidence (<0.5):[/bold] {low_confidence} ({(low_confidence/total_mappings*100):.1f}%)
        """
        console.print(Panel(summary.strip(), title="Mapping Quality Summary", border_style="green"))
        
        # Show mappings by confidence
        console.print("\n[bold]Mappings by Confidence Level:[/bold]\n")
        
        # Low confidence mappings (potential issues)
        low_conf_mappings = [fm for fm in field_mappings if fm.confidence_score < 0.5]
        if low_conf_mappings:
            table = Table(title="Low Confidence Mappings (Needs Review)")
            table.add_column("Source", style="cyan")
            table.add_column("Target", style="yellow")
            table.add_column("Confidence", style="red")
            table.add_column("Approved", style="bold")
            
            for fm in low_conf_mappings[:10]:
                table.add_row(
                    fm.source_field,
                    fm.target_field,
                    f"{fm.confidence_score:.2f}",
                    "[green]✓[/green]" if fm.is_approved else "[red]✗[/red]"
                )
            
            console.print(table)
    
    async def export_flow_data(self, session: AsyncSession, export_path: str = None):
        """Export all flow data to a JSON file for backup or analysis."""
        console.print("\n[bold cyan]Exporting Flow Data...[/bold cyan]\n")
        
        # Gather all data
        export_data = {
            'flow_id': self.flow_id,
            'export_timestamp': datetime.now().isoformat(),
            'unified_state': None,
            'master_state': None,
            'discovery_flow': None,
            'field_mappings': [],
            'raw_data_sample': None
        }
        
        # Get unified state
        unified_state = await session.execute(
            select(UnifiedDiscoveryFlowState).filter_by(flow_id=self.flow_id)
        )
        unified_state = unified_state.scalar_one_or_none()
        
        if unified_state:
            export_data['unified_state'] = {
                'current_phase': unified_state.current_phase,
                'status': unified_state.status,
                'created_at': unified_state.created_at.isoformat(),
                'updated_at': unified_state.updated_at.isoformat(),
                'error': unified_state.error,
                'metadata': unified_state.metadata,
                'has_raw_data': bool(unified_state.raw_data),
                'has_cleaned_data': bool(unified_state.cleaned_data),
                'has_field_mappings': bool(unified_state.field_mappings),
                'has_attribute_maps': bool(unified_state.attribute_maps)
            }
            
            # Include sample of raw data
            if unified_state.raw_data:
                if isinstance(unified_state.raw_data, dict) and 'servers' in unified_state.raw_data:
                    export_data['raw_data_sample'] = {
                        'type': 'CMDB',
                        'server_count': len(unified_state.raw_data['servers']),
                        'sample_record': unified_state.raw_data['servers'][0] if unified_state.raw_data['servers'] else None
                    }
        
        # Get master state
        master_state = await session.execute(
            select(CrewAIFlowStateExtensions).filter_by(flow_id=self.flow_id)
        )
        master_state = master_state.scalar_one_or_none()
        
        if master_state:
            export_data['master_state'] = {
                'flow_type': master_state.flow_type,
                'is_active': master_state.is_active,
                'created_at': master_state.created_at.isoformat(),
                'last_accessed': master_state.last_accessed.isoformat() if master_state.last_accessed else None,
                'phase_history': master_state.phase_history
            }
        
        # Get field mappings
        field_mappings = await session.execute(
            select(FieldMapping).filter_by(discovery_flow_id=self.flow_id)
        )
        field_mappings = field_mappings.scalars().all()
        
        for fm in field_mappings:
            export_data['field_mappings'].append({
                'source_field': fm.source_field,
                'target_field': fm.target_field,
                'confidence_score': fm.confidence_score,
                'is_approved': fm.is_approved,
                'created_at': fm.created_at.isoformat()
            })
        
        # Save to file
        if not export_path:
            export_path = f"flow_export_{self.flow_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(export_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        console.print(f"[green]✓ Flow data exported to: {export_path}[/green]")
        console.print(f"  - Unified state: {'✓' if export_data['unified_state'] else '✗'}")
        console.print(f"  - Master state: {'✓' if export_data['master_state'] else '✗'}")
        console.print(f"  - Field mappings: {len(export_data['field_mappings'])}")
    
    async def manual_phase_update(self, session: AsyncSession, new_phase: str):
        """Manually update the flow phase (use with caution)."""
        console.print(f"\n[bold yellow]WARNING: Manually updating phase to '{new_phase}'[/bold yellow]\n")
        
        if not Confirm.ask("Are you sure you want to manually update the phase?"):
            return
        
        # Update unified state
        unified_state = await session.execute(
            select(UnifiedDiscoveryFlowState).filter_by(flow_id=self.flow_id)
        )
        unified_state = unified_state.scalar_one_or_none()
        
        if not unified_state:
            console.print("[red]Error: Flow state not found[/red]")
            return
        
        old_phase = unified_state.current_phase
        unified_state.current_phase = new_phase
        unified_state.updated_at = datetime.utcnow()
        
        # Update metadata
        if not unified_state.metadata:
            unified_state.metadata = {}
        
        unified_state.metadata['manual_phase_updates'] = unified_state.metadata.get('manual_phase_updates', [])
        unified_state.metadata['manual_phase_updates'].append({
            'from': old_phase,
            'to': new_phase,
            'timestamp': datetime.utcnow().isoformat(),
            'reason': 'Manual intervention'
        })
        
        await session.commit()
        
        console.print(f"[green]✓ Phase updated from '{old_phase}' to '{new_phase}'[/green]")
    
    async def show_phase_history(self, session: AsyncSession):
        """Show the complete phase transition history."""
        console.print("\n[bold cyan]═══ Phase History ═══[/bold cyan]\n")
        
        # Get master state for phase history
        master_state = await session.execute(
            select(CrewAIFlowStateExtensions).filter_by(flow_id=self.flow_id)
        )
        master_state = master_state.scalar_one_or_none()
        
        if not master_state or not master_state.phase_history:
            console.print("[yellow]No phase history found[/yellow]")
            return
        
        # Display phase history
        table = Table(title="Phase Transition History")
        table.add_column("Timestamp", style="cyan")
        table.add_column("Phase", style="yellow")
        table.add_column("Status", style="green")
        table.add_column("Duration", style="white")
        
        prev_time = None
        for i, entry in enumerate(master_state.phase_history):
            timestamp = datetime.fromisoformat(entry['timestamp'])
            phase = entry.get('phase', 'Unknown')
            status = entry.get('status', 'Unknown')
            
            # Calculate duration
            duration = ""
            if prev_time:
                delta = timestamp - prev_time
                duration = f"{delta.total_seconds():.1f}s"
            
            table.add_row(
                timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                phase,
                status,
                duration
            )
            
            prev_time = timestamp
        
        console.print(table)


async def main():
    """Main entry point for detailed analysis."""
    flow_id = "1e640262-4332-4087-ac4e-1674b08cd8f2"
    
    console.print(Panel.fit(
        f"[bold]Detailed Flow Analysis Tool[/bold]\n\nFlow ID: {flow_id}",
        border_style="bright_blue"
    ))
    
    analyzer = DetailedFlowAnalyzer(flow_id)
    
    while True:
        console.print("\n[bold]Select an option:[/bold]")
        console.print("1. Analyze raw data structure")
        console.print("2. Analyze field mappings")
        console.print("3. Show phase history")
        console.print("4. Export flow data")
        console.print("5. Manual phase update (advanced)")
        console.print("6. Exit")
        
        choice = Prompt.ask("Enter your choice", choices=['1', '2', '3', '4', '5', '6'])
        
        async with AsyncSessionLocal() as session:
            if choice == '1':
                await analyzer.display_raw_data_analysis(session)
            elif choice == '2':
                await analyzer.analyze_field_mapping_details(session)
            elif choice == '3':
                await analyzer.show_phase_history(session)
            elif choice == '4':
                await analyzer.export_flow_data(session)
            elif choice == '5':
                phases = ['data_import', 'data_cleaning', 'field_mapping', 'attribute_mapping', 'finalization']
                console.print(f"\nAvailable phases: {', '.join(phases)}")
                new_phase = Prompt.ask("Enter new phase", choices=phases)
                await analyzer.manual_phase_update(session, new_phase)
            elif choice == '6':
                break
        
        if choice != '6':
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    asyncio.run(main())