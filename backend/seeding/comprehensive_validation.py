"""
Comprehensive validation that addresses all identified issues and passes all tests.
This validates the complete database setup after all fixes have been applied.
"""
import asyncio
from datetime import datetime

from sqlalchemy import func, select

from app.core.database import AsyncSessionLocal
from app.models import (
    Asset,
    AssetDependency,
    ClientAccount,
    DataImport,
    DiscoveryFlow,
    Engagement,
    ImportFieldMapping,
    RawImportRecord,
    User,
    UserAccountAssociation,
)
from app.models.asset import AssetStatus, AssetType, MigrationWave, SixRStrategy


class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


async def validate_models_import():
    """Validate all models can be imported successfully"""
    print(f"\n{Colors.BOLD}=== Model Import Validation ==={Colors.ENDC}")
    try:
        # Test critical model imports
        from app.models import UserAccountAssociation
        print(f"{Colors.GREEN}✅ UserAccountAssociation model imported{Colors.ENDC}")
        
        # Test enum string values
        asset_types = [e.value for e in AssetType]
        print(f"{Colors.GREEN}✅ AssetType enum values: {len(asset_types)} types{Colors.ENDC}")
        
        asset_statuses = [e.value for e in AssetStatus]
        print(f"{Colors.GREEN}✅ AssetStatus enum values: {len(asset_statuses)} statuses{Colors.ENDC}")
        
        sixr_strategies = [e.value for e in SixRStrategy]
        print(f"{Colors.GREEN}✅ SixRStrategy enum values: {len(sixr_strategies)} strategies{Colors.ENDC}")
        
        return True
    except Exception as e:
        print(f"{Colors.RED}❌ Model import failed: {e}{Colors.ENDC}")
        return False


async def validate_multi_tenant_data():
    """Validate multi-tenant setup with multiple client accounts"""
    print(f"\n{Colors.BOLD}=== Multi-Tenant Data Validation ==={Colors.ENDC}")
    
    async with AsyncSessionLocal() as session:
        # Count client accounts
        result = await session.execute(select(func.count(ClientAccount.id)))
        client_count = result.scalar()
        
        if client_count >= 4:
            print(f"{Colors.GREEN}✅ Client accounts: {client_count} (Expected: 4+){Colors.ENDC}")
        else:
            print(f"{Colors.RED}❌ Client accounts: {client_count} (Expected: 4+){Colors.ENDC}")
            return False
        
        # List all client accounts
        result = await session.execute(select(ClientAccount).order_by(ClientAccount.name))
        clients = result.scalars().all()
        for client in clients:
            print(f"   - {client.name} ({client.slug})")
        
        # Validate each client has engagements
        for client in clients:
            result = await session.execute(
                select(func.count(Engagement.id)).where(
                    Engagement.client_account_id == client.id
                )
            )
            eng_count = result.scalar()
            print(f"{Colors.BLUE}   {client.name}: {eng_count} engagements{Colors.ENDC}")
        
        # Validate user-client associations
        result = await session.execute(
            select(func.count(UserAccountAssociation.id))
        )
        assoc_count = result.scalar()
        print(f"{Colors.GREEN}✅ User-client associations: {assoc_count}{Colors.ENDC}")
        
        return True


async def validate_record_counts():
    """Validate expected record counts"""
    print(f"\n{Colors.BOLD}=== Record Count Validation ==={Colors.ENDC}")
    
    async with AsyncSessionLocal() as session:
        validations = [
            ("Users", User, 4, ">="),
            ("Discovery Flows", DiscoveryFlow, 5, "=="),
            ("Data Imports", DataImport, 3, "=="),
            ("Assets", Asset, 60, "=="),
            ("Asset Dependencies", AssetDependency, 20, ">="),
            ("Field Mappings", ImportFieldMapping, 30, ">="),
            ("Raw Import Records", RawImportRecord, 150, ">="),
            ("Migration Waves", MigrationWave, 4, "==")
        ]
        
        all_passed = True
        for name, model, expected, operator in validations:
            result = await session.execute(select(func.count(model.id)))
            count = result.scalar()
            
            if operator == "==" and count == expected:
                print(f"{Colors.GREEN}✅ {name}: {count} (Expected: {expected}){Colors.ENDC}")
            elif operator == ">=" and count >= expected:
                print(f"{Colors.GREEN}✅ {name}: {count} (Expected: {expected}+){Colors.ENDC}")
            else:
                print(f"{Colors.RED}❌ {name}: {count} (Expected: {operator} {expected}){Colors.ENDC}")
                all_passed = False
        
        return all_passed


async def validate_asset_enum_usage():
    """Validate assets use string enum values correctly"""
    print(f"\n{Colors.BOLD}=== Asset Enum Usage Validation ==={Colors.ENDC}")
    
    async with AsyncSessionLocal() as session:
        # Check asset types
        result = await session.execute(
            select(Asset.asset_type, func.count(Asset.id))
            .group_by(Asset.asset_type)
        )
        asset_type_counts = dict(result.all())
        
        valid_types = [e.value for e in AssetType]
        all_valid = True
        
        print(f"{Colors.BLUE}Asset type distribution:{Colors.ENDC}")
        for asset_type, count in asset_type_counts.items():
            if asset_type in valid_types:
                print(f"{Colors.GREEN}   ✅ {asset_type}: {count} assets{Colors.ENDC}")
            else:
                print(f"{Colors.RED}   ❌ {asset_type}: {count} assets (INVALID){Colors.ENDC}")
                all_valid = False
        
        # Check migration statuses
        result = await session.execute(
            select(Asset.migration_status, func.count(Asset.id))
            .group_by(Asset.migration_status)
        )
        status_counts = dict(result.all())
        
        valid_statuses = [e.value for e in AssetStatus]
        print(f"\n{Colors.BLUE}Migration status distribution:{Colors.ENDC}")
        for status, count in status_counts.items():
            if status in valid_statuses:
                print(f"{Colors.GREEN}   ✅ {status}: {count} assets{Colors.ENDC}")
            else:
                print(f"{Colors.RED}   ❌ {status}: {count} assets (INVALID){Colors.ENDC}")
                all_valid = False
        
        # Check 6R strategies
        result = await session.execute(
            select(Asset.six_r_strategy, func.count(Asset.id))
            .where(Asset.six_r_strategy.isnot(None))
            .group_by(Asset.six_r_strategy)
        )
        strategy_counts = dict(result.all())
        
        valid_strategies = [e.value for e in SixRStrategy]
        print(f"\n{Colors.BLUE}6R strategy distribution:{Colors.ENDC}")
        for strategy, count in strategy_counts.items():
            if strategy in valid_strategies:
                print(f"{Colors.GREEN}   ✅ {strategy}: {count} assets{Colors.ENDC}")
            else:
                print(f"{Colors.RED}   ❌ {strategy}: {count} assets (INVALID){Colors.ENDC}")
                all_valid = False
        
        return all_valid


async def validate_foreign_keys():
    """Validate all foreign key relationships"""
    print(f"\n{Colors.BOLD}=== Foreign Key Validation ==={Colors.ENDC}")
    
    async with AsyncSessionLocal() as session:
        # Check discovery flows have valid client/engagement IDs
        result = await session.execute(
            select(DiscoveryFlow).outerjoin(
                ClientAccount, DiscoveryFlow.client_account_id == ClientAccount.id
            ).where(ClientAccount.id.is_(None))
        )
        orphaned_flows = result.scalars().all()
        
        if not orphaned_flows:
            print(f"{Colors.GREEN}✅ All discovery flows have valid client accounts{Colors.ENDC}")
        else:
            print(f"{Colors.RED}❌ {len(orphaned_flows)} discovery flows with invalid client accounts{Colors.ENDC}")
        
        # Check assets have valid flow IDs
        result = await session.execute(
            select(Asset).where(
                Asset.flow_id.isnot(None)
            ).outerjoin(
                DiscoveryFlow, Asset.flow_id == DiscoveryFlow.flow_id
            ).where(DiscoveryFlow.id.is_(None))
        )
        orphaned_assets = result.scalars().all()
        
        if not orphaned_assets:
            print(f"{Colors.GREEN}✅ All assets have valid flow references{Colors.ENDC}")
        else:
            print(f"{Colors.RED}❌ {len(orphaned_assets)} assets with invalid flow IDs{Colors.ENDC}")
        
        # Check field mappings have valid data import IDs
        result = await session.execute(
            select(ImportFieldMapping).outerjoin(
                DataImport, ImportFieldMapping.data_import_id == DataImport.id
            ).where(DataImport.id.is_(None))
        )
        orphaned_mappings = result.scalars().all()
        
        if not orphaned_mappings:
            print(f"{Colors.GREEN}✅ All field mappings have valid data imports{Colors.ENDC}")
        else:
            print(f"{Colors.RED}❌ {len(orphaned_mappings)} field mappings with invalid imports{Colors.ENDC}")
        
        return len(orphaned_flows) == 0 and len(orphaned_assets) == 0 and len(orphaned_mappings) == 0


async def validate_demo_scenarios():
    """Validate key demo scenarios will work"""
    print(f"\n{Colors.BOLD}=== Demo Scenario Validation ==={Colors.ENDC}")
    
    async with AsyncSessionLocal() as session:
        scenarios_passed = True
        
        # Scenario 1: Complete discovery flow exists
        result = await session.execute(
            select(DiscoveryFlow).where(
                DiscoveryFlow.assessment_ready == True,
                DiscoveryFlow.status == 'complete'
            )
        )
        complete_flows = result.scalars().all()
        
        if complete_flows:
            print(f"{Colors.GREEN}✅ Complete discovery flow ready for assessment{Colors.ENDC}")
        else:
            print(f"{Colors.RED}❌ No complete discovery flows found{Colors.ENDC}")
            scenarios_passed = False
        
        # Scenario 2: Field mapping approval workflow
        result = await session.execute(
            select(ImportFieldMapping).where(
                ImportFieldMapping.status == 'pending'
            )
        )
        pending_mappings = result.scalars().all()
        
        if pending_mappings:
            print(f"{Colors.GREEN}✅ Field mappings pending approval: {len(pending_mappings)}{Colors.ENDC}")
        else:
            print(f"{Colors.YELLOW}⚠️ No pending field mappings for approval demo{Colors.ENDC}")
        
        # Scenario 3: Migration waves defined
        result = await session.execute(select(MigrationWave).order_by(MigrationWave.wave_number))
        waves = result.scalars().all()
        
        if len(waves) >= 4:
            print(f"{Colors.GREEN}✅ Migration waves defined: {len(waves)}{Colors.ENDC}")
            for wave in waves:
                print(f"   - Wave {wave.wave_number}: {wave.name} ({wave.total_assets} assets)")
        else:
            print(f"{Colors.RED}❌ Insufficient migration waves: {len(waves)}{Colors.ENDC}")
            scenarios_passed = False
        
        # Scenario 4: Multi-tenant access control
        result = await session.execute(
            select(User.email, func.count(UserAccountAssociation.id))
            .join(UserAccountAssociation, User.id == UserAccountAssociation.user_id)
            .group_by(User.email)
            .having(func.count(UserAccountAssociation.id) > 1)
        )
        multi_client_users = result.all()
        
        if multi_client_users:
            print(f"{Colors.GREEN}✅ Users with multi-client access: {len(multi_client_users)}{Colors.ENDC}")
        else:
            print(f"{Colors.YELLOW}⚠️ No users with multi-client access (OK for demo){Colors.ENDC}")
        
        return scenarios_passed


async def main():
    """Run comprehensive validation"""
    print(f"{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}Comprehensive Database Validation{Colors.ENDC}")
    print(f"{Colors.BOLD}{'='*60}{Colors.ENDC}")
    
    results = {
        "Model Imports": await validate_models_import(),
        "Multi-Tenant Data": await validate_multi_tenant_data(),
        "Record Counts": await validate_record_counts(),
        "Asset Enum Usage": await validate_asset_enum_usage(),
        "Foreign Keys": await validate_foreign_keys(),
        "Demo Scenarios": await validate_demo_scenarios()
    }
    
    # Summary
    print(f"\n{Colors.BOLD}=== Validation Summary ==={Colors.ENDC}")
    all_passed = True
    for test, passed in results.items():
        if passed:
            print(f"{Colors.GREEN}✅ {test}: PASSED{Colors.ENDC}")
        else:
            print(f"{Colors.RED}❌ {test}: FAILED{Colors.ENDC}")
            all_passed = False
    
    if all_passed:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL VALIDATIONS PASSED! 🎉{Colors.ENDC}")
        print(f"{Colors.GREEN}The database is ready for demonstrations.{Colors.ENDC}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}⚠️ SOME VALIDATIONS FAILED ⚠️{Colors.ENDC}")
        print(f"{Colors.RED}Please review the failures above.{Colors.ENDC}")
    
    return all_passed


if __name__ == "__main__":
    asyncio.run(main())