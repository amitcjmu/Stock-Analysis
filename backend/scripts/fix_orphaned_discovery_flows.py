#!/usr/bin/env python3
"""
Fix Orphaned Discovery Flows - Phase 3 Continuation
====================================================

This script specifically addresses orphaned discovery flows by linking them
to their corresponding master flows based on flow_id matching.

Discovery flows should be linked to master flows by matching the flow_id
in discovery_flows table to the flow_id in crewai_flow_state_extensions.

Usage:
    python scripts/fix_orphaned_discovery_flows.py [--dry-run] [--verbose]
"""

import asyncio
import logging
import sys
import argparse
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.database import AsyncSessionLocal


@dataclass
class DiscoveryFlowOrphan:
    """Orphaned discovery flow record."""
    id: str
    flow_id: str
    flow_name: str
    client_account_id: str
    engagement_id: str
    created_at: datetime


@dataclass
class MasterFlowMatch:
    """Master flow that can be matched."""
    id: str
    flow_id: str
    flow_name: str
    client_account_id: str
    engagement_id: str
    created_at: datetime


class DiscoveryFlowLinker:
    """Links orphaned discovery flows to their master flows."""
    
    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.logger = self._setup_logging()
        self.linked_count = 0
        self.failed_count = 0
        
    def _setup_logging(self) -> logging.Logger:
        """Configure logging."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG if self.verbose else logging.INFO)
        
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    async def get_orphaned_discovery_flows(self, session) -> List[DiscoveryFlowOrphan]:
        """Get orphaned discovery flows."""
        self.logger.info("Finding orphaned discovery flows...")
        
        result = await session.execute(
            text("""
                SELECT id, flow_id, flow_name, client_account_id, engagement_id, created_at
                FROM migration.discovery_flows
                WHERE master_flow_id IS NULL
                ORDER BY created_at DESC
            """)
        )
        
        orphans = []
        for row in result.fetchall():
            orphans.append(DiscoveryFlowOrphan(
                id=str(row.id),
                flow_id=str(row.flow_id),
                flow_name=row.flow_name,
                client_account_id=str(row.client_account_id),
                engagement_id=str(row.engagement_id),
                created_at=row.created_at
            ))
        
        self.logger.info(f"Found {len(orphans)} orphaned discovery flows")
        return orphans
    
    async def get_master_flows(self, session) -> List[MasterFlowMatch]:
        """Get available master flows for matching."""
        self.logger.info("Getting master flows...")
        
        result = await session.execute(
            text("""
                SELECT id, flow_id, flow_name, client_account_id, engagement_id, created_at
                FROM migration.crewai_flow_state_extensions
                ORDER BY created_at DESC
            """)
        )
        
        masters = []
        for row in result.fetchall():
            masters.append(MasterFlowMatch(
                id=str(row.id),
                flow_id=str(row.flow_id),
                flow_name=row.flow_name or "",
                client_account_id=str(row.client_account_id),
                engagement_id=str(row.engagement_id),
                created_at=row.created_at
            ))
        
        self.logger.info(f"Found {len(masters)} master flows")
        return masters
    
    def find_matching_master(self, orphan: DiscoveryFlowOrphan, masters: List[MasterFlowMatch]) -> Optional[MasterFlowMatch]:
        """Find matching master flow for an orphaned discovery flow."""
        
        # Strategy 1: Exact flow_id match
        for master in masters:
            if master.flow_id == orphan.flow_id:
                self.logger.debug(f"Found exact flow_id match: {master.flow_id}")
                return master
        
        # Strategy 2: Tenant + timestamp proximity (within 5 minutes)
        tenant_matches = [
            master for master in masters
            if (master.client_account_id == orphan.client_account_id and
                master.engagement_id == orphan.engagement_id)
        ]
        
        if tenant_matches:
            # Find closest by timestamp
            closest_master = min(
                tenant_matches,
                key=lambda m: abs(m.created_at - orphan.created_at)
            )
            
            time_diff = abs(closest_master.created_at - orphan.created_at)
            if time_diff.total_seconds() <= 300:  # 5 minutes
                self.logger.debug(f"Found timestamp match within {time_diff}: {closest_master.flow_name}")
                return closest_master
        
        self.logger.warning(f"No match found for discovery flow {orphan.flow_id}")
        return None
    
    async def link_discovery_flows(self, session) -> bool:
        """Link all orphaned discovery flows."""
        self.logger.info("Starting discovery flow linkage process...")
        
        # Get orphaned flows and master flows
        orphans = await self.get_orphaned_discovery_flows(session)
        masters = await self.get_master_flows(session)
        
        if not orphans:
            self.logger.info("No orphaned discovery flows found")
            return True
        
        if not masters:
            self.logger.error("No master flows found")
            return False
        
        # Process each orphan
        for i, orphan in enumerate(orphans):
            try:
                self.logger.info(f"Processing discovery flow {i+1}/{len(orphans)}: {orphan.flow_id}")
                
                matching_master = self.find_matching_master(orphan, masters)
                
                if not matching_master:
                    self.logger.warning(f"No matching master flow for {orphan.flow_id}")
                    self.failed_count += 1
                    continue
                
                if self.dry_run:
                    self.logger.info(f"DRY RUN: Would link {orphan.flow_id} to master {matching_master.flow_id}")
                    self.linked_count += 1
                else:
                    # Update the discovery flow with master_flow_id
                    await session.execute(
                        text("""
                            UPDATE migration.discovery_flows
                            SET master_flow_id = :master_flow_id,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = :discovery_flow_id
                        """),
                        {
                            'master_flow_id': matching_master.id,
                            'discovery_flow_id': orphan.id
                        }
                    )
                    
                    self.logger.info(f"Linked discovery flow {orphan.flow_id} to master {matching_master.flow_id}")
                    self.linked_count += 1
                    
            except Exception as e:
                self.logger.error(f"Error linking discovery flow {orphan.flow_id}: {str(e)}")
                self.failed_count += 1
        
        if not self.dry_run:
            await session.commit()
            self.logger.info("Changes committed to database")
        
        return True
    
    def print_summary(self):
        """Print summary of operations."""
        print("\n" + "="*50)
        print("DISCOVERY FLOW LINKAGE SUMMARY")
        print("="*50)
        print(f"Successfully linked: {self.linked_count}")
        print(f"Failed to link: {self.failed_count}")
        print(f"Total processed: {self.linked_count + self.failed_count}")
        
        if self.dry_run:
            print("\nDRY RUN MODE - No changes were made")
        else:
            print("\nChanges committed to database")
        
        print("="*50)


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Fix orphaned discovery flows')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    linker = DiscoveryFlowLinker(dry_run=args.dry_run, verbose=args.verbose)
    
    try:
        async with AsyncSessionLocal() as session:
            success = await linker.link_discovery_flows(session)
            linker.print_summary()
            
            if success and linker.linked_count > 0:
                print("\nRun validate_flow_relationships.py to verify the fixes")
            
            sys.exit(0 if success else 1)
            
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())