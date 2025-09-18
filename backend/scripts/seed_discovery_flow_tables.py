#!/usr/bin/env python3
"""
Discovery Flow Database Seeding Script - Entry Point
"""

import asyncio
import sys
from seed_discovery_flow_tables.main import main

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
