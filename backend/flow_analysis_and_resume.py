#!/usr/bin/env python3
"""
Comprehensive Flow Analysis and Resume Script
Analyzes all database tables for flow data and provides intelligent resumption capabilities.
"""

import asyncio
import json
import os
import sys
from typing import Any, Dict, List

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from sqlalchemy import inspect, select, text
from sqlalchemy.ext.asyncio import AsyncSession

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

from app.core.database import AsyncSessionLocal, engine
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.models.data_import.mapping import ImportFieldMapping as FieldMapping
from app.models.discovery_flow import DiscoveryFlow
from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState
from app.services.crewai_flows.unified_discovery_flow.flow_finalization import (
    UnifiedDiscoveryFlowFinalizer,
)
from app.services.crewai_flows.unified_discovery_flow.flow_management import (
    UnifiedDiscoveryFlowManager,
)

console = Console()


class FlowAnalyzer:
    """Comprehensive flow analysis and resumption tool."""

    def __init__(self, flow_id: str):
        self.flow_id = flow_id
        self.flow_data = {}
        self.table_results = {}

    async def analyze_all_tables(self, session: AsyncSession) -> Dict[str, Any]:
        """Scan ALL database tables for references to the flow ID."""
        console.print(
            f"\n[bold cyan]Scanning ALL tables for flow ID: {self.flow_id}[/bold cyan]\n"
        )

        # Get all table names from the database
        inspector = inspect(engine.sync_engine)
        all_tables = inspector.get_table_names()

        results = {}

        for table_name in sorted(all_tables):
            try:
                # Get column names for the table
                columns = inspector.get_columns(table_name)
                column_names = [col["name"] for col in columns]

                # Build dynamic query to search for flow_id in any column
                conditions = []
                for col in column_names:
                    col_type = str(columns[column_names.index(col)]["type"])
                    # Only search in string/text/uuid columns
                    if any(
                        t in col_type.lower()
                        for t in ["char", "text", "uuid", "string"]
                    ):
                        conditions.append(f"{col}::text = '{self.flow_id}'")
                    # Also check JSON/JSONB columns
                    elif "json" in col_type.lower():
                        conditions.append(f"{col}::text LIKE '%{self.flow_id}%'")

                if not conditions:
                    continue

                # Execute search query
                query = f"SELECT * FROM {table_name} WHERE {' OR '.join(conditions)}"
                result = await session.execute(text(query))
                rows = result.fetchall()

                if rows:
                    results[table_name] = {
                        "count": len(rows),
                        "columns": column_names,
                        "data": [dict(zip(column_names, row)) for row in rows],
                    }
                    console.print(
                        f"[green]✓[/green] Found {len(rows)} record(s) in [bold]{table_name}[/bold]"
                    )

            except Exception as e:
                # Skip tables we can't query
                if "permission denied" not in str(e).lower():
                    console.print(
                        f"[yellow]![/yellow] Error scanning {table_name}: {str(e)}"
                    )

        self.table_results = results
        return results

    async def analyze_flow_state(self, session: AsyncSession) -> Dict[str, Any]:
        """Analyze the current flow state and progress."""
        console.print("\n[bold cyan]Analyzing Flow State and Progress[/bold cyan]\n")

        analysis = {
            "unified_state": None,
            "master_state": None,
            "discovery_flow": None,
            "field_mappings": None,
            "persisted_data": {},
            "processing_status": {},
            "gaps": [],
            "resume_point": None,
        }

        # 1. Check UnifiedDiscoveryFlowState
        unified_state = await session.execute(
            select(UnifiedDiscoveryFlowState).filter_by(flow_id=self.flow_id)
        )
        unified_state = unified_state.scalar_one_or_none()

        if unified_state:
            analysis["unified_state"] = {
                "current_phase": unified_state.current_phase,
                "status": unified_state.status,
                "created_at": unified_state.created_at,
                "updated_at": unified_state.updated_at,
                "error": unified_state.error,
                "metadata": unified_state.metadata,
            }

            # Check for persisted data
            if unified_state.raw_data:
                analysis["persisted_data"]["raw_data"] = {
                    "exists": True,
                    "size": len(json.dumps(unified_state.raw_data)),
                    "sample_keys": (
                        list(unified_state.raw_data.keys())[:5]
                        if isinstance(unified_state.raw_data, dict)
                        else "Not a dict"
                    ),
                }

            if unified_state.cleaned_data:
                analysis["persisted_data"]["cleaned_data"] = {
                    "exists": True,
                    "size": len(json.dumps(unified_state.cleaned_data)),
                    "record_count": (
                        len(unified_state.cleaned_data)
                        if isinstance(unified_state.cleaned_data, list)
                        else "Not a list"
                    ),
                }

            if unified_state.field_mappings:
                analysis["persisted_data"]["field_mappings"] = {
                    "exists": True,
                    "count": len(unified_state.field_mappings),
                }

            if unified_state.attribute_maps:
                analysis["persisted_data"]["attribute_maps"] = {
                    "exists": True,
                    "count": len(unified_state.attribute_maps),
                }

        # 2. Check Master Flow State
        master_state = await session.execute(
            select(CrewAIFlowStateExtensions).filter_by(flow_id=self.flow_id)
        )
        master_state = master_state.scalar_one_or_none()

        if master_state:
            analysis["master_state"] = {
                "flow_type": master_state.flow_type,
                "is_active": master_state.is_active,
                "created_at": master_state.created_at,
                "last_accessed": master_state.last_accessed,
                "phase_history": master_state.phase_history,
            }

        # 3. Check DiscoveryFlow
        discovery_flow = await session.execute(
            select(DiscoveryFlow).filter_by(flow_id=self.flow_id)
        )
        discovery_flow = discovery_flow.scalar_one_or_none()

        if discovery_flow:
            analysis["discovery_flow"] = {
                "status": discovery_flow.status,
                "data_sources": discovery_flow.data_sources,
                "created_at": discovery_flow.created_at,
                "updated_at": discovery_flow.updated_at,
            }

        # 4. Check FieldMappings
        field_mappings = await session.execute(
            select(FieldMapping).filter_by(discovery_flow_id=self.flow_id)
        )
        field_mappings = field_mappings.scalars().all()

        if field_mappings:
            analysis["field_mappings"] = {
                "count": len(field_mappings),
                "mappings": [
                    {
                        "source_field": fm.source_field,
                        "target_field": fm.target_field,
                        "confidence_score": fm.confidence_score,
                        "is_approved": fm.is_approved,
                    }
                    for fm in field_mappings
                ],
            }

        # 5. Determine processing status and gaps
        analysis["processing_status"] = self._determine_processing_status(analysis)
        analysis["gaps"] = self._identify_gaps(analysis)
        analysis["resume_point"] = self._determine_resume_point(analysis)

        return analysis

    def _determine_processing_status(self, analysis: Dict[str, Any]) -> Dict[str, str]:
        """Determine what has been processed and what hasn't."""
        status = {}

        # Data Import Phase
        if analysis["persisted_data"].get("raw_data", {}).get("exists"):
            status["data_import"] = "COMPLETE"
        else:
            status["data_import"] = "NOT_STARTED"

        # Data Cleaning Phase
        if analysis["persisted_data"].get("cleaned_data", {}).get("exists"):
            status["data_cleaning"] = "COMPLETE"
        elif analysis["persisted_data"].get("raw_data", {}).get("exists"):
            status["data_cleaning"] = "READY_TO_START"
        else:
            status["data_cleaning"] = "BLOCKED"

        # Field Mapping Phase
        if analysis["field_mappings"] and analysis["field_mappings"]["count"] > 0:
            approved_count = sum(
                1 for m in analysis["field_mappings"]["mappings"] if m["is_approved"]
            )
            if approved_count == analysis["field_mappings"]["count"]:
                status["field_mapping"] = "COMPLETE_APPROVED"
            elif approved_count > 0:
                status["field_mapping"] = "PARTIAL_APPROVED"
            else:
                status["field_mapping"] = "COMPLETE_UNAPPROVED"
        elif analysis["persisted_data"].get("field_mappings", {}).get("exists"):
            status["field_mapping"] = "GENERATED_NOT_SAVED"
        elif analysis["persisted_data"].get("cleaned_data", {}).get("exists"):
            status["field_mapping"] = "READY_TO_START"
        else:
            status["field_mapping"] = "BLOCKED"

        # Attribute Mapping Phase
        if analysis["persisted_data"].get("attribute_maps", {}).get("exists"):
            status["attribute_mapping"] = "COMPLETE"
        elif status.get("field_mapping") in ["COMPLETE_APPROVED", "PARTIAL_APPROVED"]:
            status["attribute_mapping"] = "READY_TO_START"
        else:
            status["attribute_mapping"] = "BLOCKED"

        # Finalization Phase
        if (
            analysis["unified_state"]
            and analysis["unified_state"]["status"] == "completed"
        ):
            status["finalization"] = "COMPLETE"
        elif status.get("attribute_mapping") == "COMPLETE":
            status["finalization"] = "READY_TO_START"
        else:
            status["finalization"] = "BLOCKED"

        return status

    def _identify_gaps(self, analysis: Dict[str, Any]) -> List[str]:
        """Identify gaps in the flow execution."""
        gaps = []
        status = analysis["processing_status"]

        if status["data_import"] == "NOT_STARTED":
            gaps.append("No raw data found - data import never completed")

        if status["data_cleaning"] in ["READY_TO_START", "BLOCKED"]:
            gaps.append("Data cleaning not performed")

        if status["field_mapping"] == "GENERATED_NOT_SAVED":
            gaps.append("Field mappings generated but not saved to database")
        elif status["field_mapping"] in ["READY_TO_START", "BLOCKED"]:
            gaps.append("Field mapping not performed")
        elif status["field_mapping"] == "COMPLETE_UNAPPROVED":
            gaps.append("Field mappings exist but none are approved")

        if status["attribute_mapping"] in ["READY_TO_START", "BLOCKED"]:
            gaps.append("Attribute mapping not performed")

        if status["finalization"] in ["READY_TO_START", "BLOCKED"]:
            gaps.append("Flow not finalized")

        # Check for phase mismatches
        if analysis["unified_state"]:
            current_phase = analysis["unified_state"]["current_phase"]
            expected_phase = self._get_expected_phase(status)
            if current_phase != expected_phase:
                gaps.append(
                    f"Phase mismatch: current='{current_phase}', expected='{expected_phase}'"
                )

        return gaps

    def _get_expected_phase(self, status: Dict[str, str]) -> str:
        """Determine what phase we should be in based on processing status."""
        if status["finalization"] == "COMPLETE":
            return "finalization"
        elif status["attribute_mapping"] in ["COMPLETE", "READY_TO_START"]:
            return "attribute_mapping"
        elif status["field_mapping"] in [
            "COMPLETE_APPROVED",
            "PARTIAL_APPROVED",
            "COMPLETE_UNAPPROVED",
            "READY_TO_START",
        ]:
            return "field_mapping"
        elif status["data_cleaning"] in ["COMPLETE", "READY_TO_START"]:
            return "data_cleaning"
        else:
            return "data_import"

    def _determine_resume_point(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Determine the best point to resume the flow."""
        status = analysis["processing_status"]

        # Find the first incomplete phase
        if status["data_import"] == "NOT_STARTED":
            return {
                "phase": "data_import",
                "action": "start_fresh",
                "reason": "No data has been imported yet",
            }
        elif status["data_cleaning"] == "READY_TO_START":
            return {
                "phase": "data_cleaning",
                "action": "resume",
                "reason": "Raw data exists but cleaning not performed",
            }
        elif status["field_mapping"] == "READY_TO_START":
            return {
                "phase": "field_mapping",
                "action": "resume",
                "reason": "Cleaned data exists but field mapping not performed",
            }
        elif status["field_mapping"] == "GENERATED_NOT_SAVED":
            return {
                "phase": "field_mapping",
                "action": "save_existing",
                "reason": "Field mappings generated but not persisted to database",
            }
        elif status["field_mapping"] == "COMPLETE_UNAPPROVED":
            return {
                "phase": "field_mapping",
                "action": "approve_or_regenerate",
                "reason": "Field mappings exist but need approval",
            }
        elif status["attribute_mapping"] == "READY_TO_START":
            return {
                "phase": "attribute_mapping",
                "action": "resume",
                "reason": "Field mappings approved but attribute mapping not performed",
            }
        elif status["finalization"] == "READY_TO_START":
            return {
                "phase": "finalization",
                "action": "resume",
                "reason": "All mapping complete but flow not finalized",
            }
        else:
            return {
                "phase": "completed",
                "action": "none",
                "reason": "Flow appears to be complete",
            }

    def display_analysis(
        self, table_results: Dict[str, Any], flow_analysis: Dict[str, Any]
    ):
        """Display comprehensive analysis results."""
        # 1. Display table scan results
        console.print("\n[bold]═══ Database Table Scan Results ═══[/bold]\n")

        if table_results:
            table = Table(title="Tables Containing Flow ID")
            table.add_column("Table Name", style="cyan")
            table.add_column("Records", style="green")
            table.add_column("Key Data", style="yellow")

            for table_name, data in table_results.items():
                key_info = []
                if table_name == "unified_discovery_flow_states":
                    if data["data"]:
                        key_info.append(
                            f"Phase: {data['data'][0].get('current_phase', 'N/A')}"
                        )
                        key_info.append(
                            f"Status: {data['data'][0].get('status', 'N/A')}"
                        )
                elif table_name == "field_mappings":
                    key_info.append(f"Mappings: {data['count']}")
                elif table_name == "crewai_flow_state_extensions":
                    if data["data"]:
                        key_info.append(
                            f"Type: {data['data'][0].get('flow_type', 'N/A')}"
                        )

                table.add_row(
                    table_name,
                    str(data["count"]),
                    ", ".join(key_info) if key_info else "See details below",
                )

            console.print(table)
        else:
            console.print("[yellow]No tables found containing this flow ID[/yellow]")

        # 2. Display flow state analysis
        console.print("\n[bold]═══ Flow State Analysis ═══[/bold]\n")

        # Current state panel
        if flow_analysis["unified_state"]:
            state = flow_analysis["unified_state"]
            state_info = f"""
[bold]Current Phase:[/bold] {state['current_phase']}
[bold]Status:[/bold] {state['status']}
[bold]Last Updated:[/bold] {state['updated_at']}
[bold]Error:[/bold] {state['error'] or 'None'}
            """
            console.print(
                Panel(
                    state_info.strip(), title="Current Flow State", border_style="green"
                )
            )

        # 3. Display persisted data status
        console.print("\n[bold]═══ Persisted Data Status ═══[/bold]\n")

        data_table = Table(title="Data Persistence Status")
        data_table.add_column("Data Type", style="cyan")
        data_table.add_column("Status", style="green")
        data_table.add_column("Details", style="yellow")

        for data_type, info in flow_analysis["persisted_data"].items():
            if info.get("exists"):
                details = []
                if "size" in info:
                    details.append(f"Size: {info['size']} bytes")
                if "count" in info:
                    details.append(f"Count: {info['count']}")
                if "record_count" in info:
                    details.append(f"Records: {info['record_count']}")

                data_table.add_row(
                    data_type.replace("_", " ").title(),
                    "[green]✓ Exists[/green]",
                    ", ".join(details),
                )
            else:
                data_table.add_row(
                    data_type.replace("_", " ").title(),
                    "[red]✗ Missing[/red]",
                    "Not found",
                )

        console.print(data_table)

        # 4. Display processing status
        console.print("\n[bold]═══ Processing Status ═══[/bold]\n")

        status_table = Table(title="Phase Processing Status")
        status_table.add_column("Phase", style="cyan")
        status_table.add_column("Status", style="bold")
        status_table.add_column("Description", style="yellow")

        status_colors = {
            "COMPLETE": "green",
            "COMPLETE_APPROVED": "green",
            "PARTIAL_APPROVED": "yellow",
            "COMPLETE_UNAPPROVED": "yellow",
            "GENERATED_NOT_SAVED": "yellow",
            "READY_TO_START": "cyan",
            "BLOCKED": "red",
            "NOT_STARTED": "red",
        }

        for phase, status in flow_analysis["processing_status"].items():
            color = status_colors.get(status, "white")
            status_table.add_row(
                phase.replace("_", " ").title(),
                f"[{color}]{status}[/{color}]",
                self._get_status_description(status),
            )

        console.print(status_table)

        # 5. Display gaps
        if flow_analysis["gaps"]:
            console.print("\n[bold]═══ Identified Gaps ═══[/bold]\n")
            for i, gap in enumerate(flow_analysis["gaps"], 1):
                console.print(f"[red]{i}.[/red] {gap}")

        # 6. Display resume recommendation
        console.print("\n[bold]═══ Resume Recommendation ═══[/bold]\n")

        resume = flow_analysis["resume_point"]
        recommendation = f"""
[bold]Recommended Phase:[/bold] {resume['phase']}
[bold]Action:[/bold] {resume['action']}
[bold]Reason:[/bold] {resume['reason']}
        """

        style = "green" if resume["action"] != "none" else "yellow"
        console.print(
            Panel(recommendation.strip(), title="Resume Point", border_style=style)
        )

        # 7. Display field mappings if present
        if (
            flow_analysis["field_mappings"]
            and flow_analysis["field_mappings"]["count"] > 0
        ):
            console.print("\n[bold]═══ Field Mappings ═══[/bold]\n")

            mapping_table = Table(title="Current Field Mappings")
            mapping_table.add_column("Source Field", style="cyan")
            mapping_table.add_column("Target Field", style="yellow")
            mapping_table.add_column("Confidence", style="green")
            mapping_table.add_column("Approved", style="bold")

            for mapping in flow_analysis["field_mappings"]["mappings"][
                :10
            ]:  # Show first 10
                mapping_table.add_row(
                    mapping["source_field"],
                    mapping["target_field"],
                    f"{mapping['confidence_score']:.2f}",
                    "[green]✓[/green]" if mapping["is_approved"] else "[red]✗[/red]",
                )

            console.print(mapping_table)

            if flow_analysis["field_mappings"]["count"] > 10:
                console.print(
                    f"\n[italic]... and {flow_analysis['field_mappings']['count'] - 10} more mappings[/italic]"
                )

    def _get_status_description(self, status: str) -> str:
        """Get human-readable description for status."""
        descriptions = {
            "COMPLETE": "Phase completed successfully",
            "COMPLETE_APPROVED": "Completed and approved",
            "PARTIAL_APPROVED": "Some items approved, others pending",
            "COMPLETE_UNAPPROVED": "Completed but awaiting approval",
            "GENERATED_NOT_SAVED": "Generated but not persisted",
            "READY_TO_START": "Prerequisites met, can proceed",
            "BLOCKED": "Cannot proceed, prerequisites missing",
            "NOT_STARTED": "Phase has not been initiated",
        }
        return descriptions.get(status, "Unknown status")

    async def resume_flow(
        self, session: AsyncSession, resume_point: Dict[str, Any], force: bool = False
    ):
        """Resume the flow from the identified point."""
        console.print(
            f"\n[bold cyan]Resuming flow from phase: {resume_point['phase']}[/bold cyan]\n"
        )

        if resume_point["action"] == "none":
            console.print(
                "[yellow]Flow appears to be complete. Nothing to resume.[/yellow]"
            )
            return

        # Get the unified state
        unified_state = await session.execute(
            select(UnifiedDiscoveryFlowState).filter_by(flow_id=self.flow_id)
        )
        unified_state = unified_state.scalar_one_or_none()

        if not unified_state:
            console.print("[red]Error: Flow state not found. Cannot resume.[/red]")
            return

        # Create flow manager
        flow_manager = UnifiedDiscoveryFlowManager(
            flow_id=self.flow_id,
            client_account_id=unified_state.client_account_id,
            engagement_id=unified_state.engagement_id,
            user_id=unified_state.user_id,
        )

        try:
            if resume_point["phase"] == "data_cleaning":
                console.print("[yellow]Resuming data cleaning phase...[/yellow]")
                # The flow manager will handle the data cleaning
                result = await flow_manager.process_phase("data_cleaning")
                console.print(f"[green]Data cleaning completed: {result}[/green]")

            elif resume_point["phase"] == "field_mapping":
                if resume_point["action"] == "save_existing":
                    console.print(
                        "[yellow]Saving existing field mappings to database...[/yellow]"
                    )
                    # Field mappings are in the state but not in the field_mappings table
                    if unified_state.field_mappings:
                        # Create FieldMapping records
                        for mapping in unified_state.field_mappings:
                            field_mapping = FieldMapping(
                                discovery_flow_id=self.flow_id,
                                source_field=mapping["source_field"],
                                target_field=mapping["target_field"],
                                confidence_score=mapping.get("confidence_score", 0.0),
                                is_approved=mapping.get("is_approved", False),
                                created_by=unified_state.user_id,
                            )
                            session.add(field_mapping)
                        await session.commit()
                        console.print("[green]Field mappings saved to database[/green]")
                    else:
                        console.print("[red]No field mappings found in state[/red]")

                elif resume_point["action"] == "approve_or_regenerate":
                    console.print("\n[bold]Field Mapping Options:[/bold]")
                    console.print("1. Approve existing mappings")
                    console.print("2. Regenerate mappings")
                    console.print("3. View current mappings")

                    choice = Prompt.ask("Select an option", choices=["1", "2", "3"])

                    if choice == "1":
                        # Approve all mappings
                        await session.execute(
                            text(
                                "UPDATE field_mappings SET is_approved = true WHERE discovery_flow_id = :flow_id"
                            ),
                            {"flow_id": self.flow_id},
                        )
                        await session.commit()
                        console.print("[green]All field mappings approved[/green]")

                    elif choice == "2":
                        # Delete existing mappings and regenerate
                        await session.execute(
                            text(
                                "DELETE FROM field_mappings WHERE discovery_flow_id = :flow_id"
                            ),
                            {"flow_id": self.flow_id},
                        )
                        await session.commit()

                        result = await flow_manager.process_phase("field_mapping")
                        console.print(
                            f"[green]Field mapping regenerated: {result}[/green]"
                        )

                    elif choice == "3":
                        # Show current mappings
                        field_mappings = await session.execute(
                            select(FieldMapping).filter_by(
                                discovery_flow_id=self.flow_id
                            )
                        )
                        field_mappings = field_mappings.scalars().all()

                        table = Table(title="Current Field Mappings")
                        table.add_column("Source", style="cyan")
                        table.add_column("Target", style="yellow")
                        table.add_column("Confidence", style="green")
                        table.add_column("Approved", style="bold")

                        for fm in field_mappings:
                            table.add_row(
                                fm.source_field,
                                fm.target_field,
                                f"{fm.confidence_score:.2f}",
                                (
                                    "[green]✓[/green]"
                                    if fm.is_approved
                                    else "[red]✗[/red]"
                                ),
                            )

                        console.print(table)
                        return await self.resume_flow(session, resume_point, force)

                else:
                    result = await flow_manager.process_phase("field_mapping")
                    console.print(f"[green]Field mapping completed: {result}[/green]")

            elif resume_point["phase"] == "attribute_mapping":
                console.print("[yellow]Resuming attribute mapping phase...[/yellow]")
                result = await flow_manager.process_phase("attribute_mapping")
                console.print(f"[green]Attribute mapping completed: {result}[/green]")

            elif resume_point["phase"] == "finalization":
                console.print("[yellow]Finalizing flow...[/yellow]")
                finalizer = UnifiedDiscoveryFlowFinalizer(flow_manager)
                result = await finalizer.finalize_flow()
                console.print(f"[green]Flow finalized: {result}[/green]")

            else:
                console.print(
                    f"[red]Unknown resume phase: {resume_point['phase']}[/red]"
                )

        except Exception as e:
            console.print(f"[red]Error resuming flow: {str(e)}[/red]")
            import traceback

            traceback.print_exc()


async def main():
    """Main entry point."""
    flow_id = "1e640262-4332-4087-ac4e-1674b08cd8f2"

    console.print(
        Panel.fit(
            f"[bold]Flow Analysis and Resume Tool[/bold]\n\nAnalyzing flow: {flow_id}",
            border_style="bright_blue",
        )
    )

    analyzer = FlowAnalyzer(flow_id)

    async with AsyncSessionLocal() as session:
        # 1. Scan all tables
        table_results = await analyzer.analyze_all_tables(session)

        # 2. Analyze flow state
        flow_analysis = await analyzer.analyze_flow_state(session)

        # 3. Display results
        analyzer.display_analysis(table_results, flow_analysis)

        # 4. Ask if user wants to resume
        if flow_analysis["resume_point"]["action"] != "none":
            console.print("\n")
            if Confirm.ask("[bold]Would you like to resume the flow?[/bold]"):
                await analyzer.resume_flow(session, flow_analysis["resume_point"])

                # Re-analyze after resume
                console.print(
                    "\n[bold cyan]Re-analyzing flow after resume...[/bold cyan]"
                )
                new_analysis = await analyzer.analyze_flow_state(session)

                # Show updated status
                console.print("\n[bold]═══ Updated Processing Status ═══[/bold]\n")

                status_table = Table(title="Updated Phase Status")
                status_table.add_column("Phase", style="cyan")
                status_table.add_column("Previous", style="yellow")
                status_table.add_column("Current", style="green")

                for phase in flow_analysis["processing_status"]:
                    old_status = flow_analysis["processing_status"][phase]
                    new_status = new_analysis["processing_status"][phase]

                    status_table.add_row(
                        phase.replace("_", " ").title(),
                        old_status,
                        f"[{'green' if new_status != old_status else 'yellow'}]{new_status}[/{'green' if new_status != old_status else 'yellow'}]",
                    )

                console.print(status_table)


if __name__ == "__main__":
    asyncio.run(main())
