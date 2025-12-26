"""
Cassandra Service - Stores user stock search related information
Designed for high-volume, time-series data with fast reads
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)

# Try to import cassandra driver
try:
    from cassandra.cluster import Cluster, ExecutionProfile, EXEC_PROFILE_DEFAULT
    from cassandra.policies import DCAwareRoundRobinPolicy, TokenAwarePolicy
    from cassandra.query import ConsistencyLevel
    from cassandra.auth import PlainTextAuthProvider

    CASSANDRA_AVAILABLE = True
except ImportError:
    CASSANDRA_AVAILABLE = False
    logger.warning(
        "cassandra-driver not available. Install with: pip install cassandra-driver"
    )


class CassandraService:
    """
    Service for storing user stock search data in Cassandra.

    Schema Design:
    - Keyspace: stock_analysis
    - Tables:
      1. user_stock_searches - Time-series search history
      2. user_search_results - Search results cache
      3. user_search_analytics - Aggregated analytics
    """

    def __init__(self):
        # Always initialize these attributes
        self.cluster = None
        self.session = None
        self._initialized = False

        if not CASSANDRA_AVAILABLE:
            logger.warning("Cassandra driver not available - using mock mode")
            self.keyspace = "stock_analysis"
            return

        from app.core.config import settings

        # Get Cassandra configuration
        self.contact_points = getattr(
            settings, "CASSANDRA_CONTACT_POINTS", "localhost"
        ).split(",")
        self.port = getattr(settings, "CASSANDRA_PORT", 9042)
        self.keyspace = getattr(settings, "CASSANDRA_KEYSPACE", "stock_analysis")
        self.username = getattr(settings, "CASSANDRA_USERNAME", None)
        self.password = getattr(settings, "CASSANDRA_PASSWORD", None)

    async def initialize(self) -> bool:
        """Initialize Cassandra connection and create schema if needed"""
        if not CASSANDRA_AVAILABLE:
            logger.warning("Cassandra not available - skipping initialization")
            return False

        try:
            # Create execution profile for better performance
            profile = ExecutionProfile(
                load_balancing_policy=TokenAwarePolicy(DCAwareRoundRobinPolicy()),
                consistency_level=ConsistencyLevel.ONE,  # Fast writes
            )

            # Create cluster connection
            if self.username and self.password:
                auth_provider = PlainTextAuthProvider(
                    username=self.username, password=self.password
                )
                self.cluster = Cluster(
                    self.contact_points,
                    port=self.port,
                    auth_provider=auth_provider,
                    execution_profiles={EXEC_PROFILE_DEFAULT: profile},
                )
            else:
                self.cluster = Cluster(
                    self.contact_points,
                    port=self.port,
                    execution_profiles={EXEC_PROFILE_DEFAULT: profile},
                )

            self.session = self.cluster.connect()

            # Create keyspace if it doesn't exist
            await self._create_keyspace()

            # Create tables if they don't exist
            await self._create_tables()

            self._initialized = True
            logger.info("✅ Cassandra service initialized successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Error initializing Cassandra: {e}", exc_info=True)
            return False

    async def _create_keyspace(self):
        """Create keyspace if it doesn't exist"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.session.execute(
                    f"""
                    CREATE KEYSPACE IF NOT EXISTS {self.keyspace}
                    WITH REPLICATION = {{
                        'class': 'SimpleStrategy',
                        'replication_factor': 1
                    }}
                    AND DURABLE_WRITES = true;
                    """
                ),
            )
            await loop.run_in_executor(
                None, lambda: self.session.set_keyspace(self.keyspace)
            )
            logger.info(f"✅ Keyspace '{self.keyspace}' ready")
        except Exception as e:
            logger.error(f"Error creating keyspace: {e}")
            raise

    async def _create_tables(self):
        """Create tables for stock search data"""
        try:
            loop = asyncio.get_event_loop()

            # Table 1: User Stock Searches (Time-series data)
            # Partition by (client_account_id, user_id, date)
            # Cluster by timestamp for time-ordered queries
            await loop.run_in_executor(
                None,
                lambda: self.session.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self.keyspace}.user_stock_searches (
                        client_account_id UUID,
                        engagement_id UUID,
                        user_id TEXT,
                        search_date DATE,
                        search_timestamp TIMESTAMP,
                        search_id UUID,
                        search_query TEXT,
                        search_type TEXT,
                        results_count INT,
                        execution_time_ms INT,
                        source TEXT,
                        PRIMARY KEY ((client_account_id, user_id, search_date), search_timestamp, search_id)
                    ) WITH CLUSTERING ORDER BY (search_timestamp DESC);
                    """
                ),
            )

            # Table 2: Search Results Cache (for quick lookup)
            # Partition by search query hash
            # Note: TTL is set per-row during INSERT, not at table level
            await loop.run_in_executor(
                None,
                lambda: self.session.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self.keyspace}.user_search_results (
                        search_query_hash TEXT,
                        client_account_id UUID,
                        engagement_id UUID,
                        user_id TEXT,
                        search_id UUID,
                        search_query TEXT,
                        results TEXT,
                        created_at TIMESTAMP,
                        expires_at TIMESTAMP,
                        PRIMARY KEY (search_query_hash, client_account_id, user_id, search_id)
                    );
                    """
                ),
            )

            # Table 3: Search Analytics (aggregated data)
            # Partition by (client_account_id, user_id, month)
            await loop.run_in_executor(
                None,
                lambda: self.session.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self.keyspace}.user_search_analytics (
                        client_account_id UUID,
                        user_id TEXT,
                        year_month TEXT,
                        total_searches INT,
                        unique_queries INT,
                        avg_results_count DOUBLE,
                        avg_execution_time_ms DOUBLE,
                        most_searched_symbols MAP<TEXT, INT>,
                        search_sources MAP<TEXT, INT>,
                        updated_at TIMESTAMP,
                        PRIMARY KEY ((client_account_id, user_id), year_month)
                    );
                    """
                ),
            )

            # Create indexes for common queries
            await loop.run_in_executor(
                None,
                lambda: self.session.execute(
                    f"""
                    CREATE INDEX IF NOT EXISTS idx_search_query
                    ON {self.keyspace}.user_stock_searches (search_query);
                    """
                ),
            )

            await loop.run_in_executor(
                None,
                lambda: self.session.execute(
                    f"""
                    CREATE INDEX IF NOT EXISTS idx_search_type
                    ON {self.keyspace}.user_stock_searches (search_type);
                    """
                ),
            )

            logger.info("✅ Cassandra tables created successfully")

        except Exception as e:
            logger.error(f"Error creating tables: {e}", exc_info=True)
            raise

    async def log_stock_search(
        self,
        client_account_id: Union[UUID, str],
        engagement_id: Union[UUID, str],
        user_id: str,
        search_query: str,
        search_type: str = "symbol",
        results_count: int = 0,
        execution_time_ms: int = 0,
        source: str = "api",
        results: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[UUID]:
        """
        Log a stock search to Cassandra.

        Args:
            client_account_id: Client account ID (UUID or string)
            engagement_id: Engagement ID (UUID or string)
            user_id: User ID
            search_query: The search query string
            search_type: Type of search ('symbol', 'company_name', 'fuzzy')
            results_count: Number of results returned
            execution_time_ms: Execution time in milliseconds
            source: Data source ('database', 'api', 'cache')
            results: Optional search results to cache

        Returns:
            search_id: UUID of the logged search
        """
        if not CASSANDRA_AVAILABLE:
            logger.debug("Cassandra driver not available - skipping search log")
            return None

        if not self._initialized:
            if not await self.initialize():
                logger.warning("Cassandra not initialized - skipping search log")
                return None

        try:
            # Convert string UUIDs to UUID objects if needed
            if isinstance(client_account_id, str):
                client_account_id = UUID(client_account_id)
            if isinstance(engagement_id, str):
                engagement_id = UUID(engagement_id)

            search_id = uuid4()
            now = datetime.utcnow()
            search_date = now.date()

            # Insert into user_stock_searches table (run in executor for async)
            loop = asyncio.get_event_loop()
            insert_query_str = (
                f"INSERT INTO {self.keyspace}.user_stock_searches ("
                f"client_account_id, engagement_id, user_id, search_date, "
                f"search_timestamp, search_id, search_query, search_type, "
                f"results_count, execution_time_ms, source"
                f") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
            )

            # Use prepared statement for parameterized queries (recommended approach)
            prepared = self.session.prepare(insert_query_str)

            # Capture parameters for lambda
            params = (
                client_account_id,
                engagement_id,
                user_id,
                search_date,
                now,
                search_id,
                search_query,
                search_type,
                results_count,
                execution_time_ms,
                source,
            )

            def execute_insert(stmt=prepared, p=params):
                return self.session.execute(stmt, p)

            await loop.run_in_executor(None, execute_insert)

            # Cache results if provided
            if results:
                await self._cache_search_results(
                    client_account_id,
                    engagement_id,
                    user_id,
                    search_query,
                    search_id,
                    results,
                )

            # Update analytics (async, non-blocking)
            asyncio.create_task(
                self._update_analytics(
                    client_account_id,
                    user_id,
                    search_query,
                    results_count,
                    execution_time_ms,
                    source,
                )
            )

            logger.debug(f"✅ Logged stock search: {search_query} (ID: {search_id})")
            return search_id

        except Exception as e:
            logger.error(f"Error logging stock search to Cassandra: {e}", exc_info=True)
            return None

    async def _cache_search_results(
        self,
        client_account_id: Union[UUID, str],
        engagement_id: Union[UUID, str],
        user_id: str,
        search_query: str,
        search_id: UUID,
        results: List[Dict[str, Any]],
    ):
        """Cache search results for quick lookup"""
        try:
            import hashlib
            import json

            # Convert string UUIDs to UUID objects if needed
            if isinstance(client_account_id, str):
                client_account_id = UUID(client_account_id)
            if isinstance(engagement_id, str):
                engagement_id = UUID(engagement_id)

            # Create hash of search query for partitioning
            query_hash = hashlib.md5(search_query.lower().encode()).hexdigest()

            # Convert results to JSON string (Cassandra doesn't have native JSONB, use TEXT)
            results_json = json.dumps(results)

            insert_query_str = (
                f"INSERT INTO {self.keyspace}.user_search_results ("
                f"search_query_hash, client_account_id, engagement_id, "
                f"user_id, search_id, search_query, results, created_at, expires_at"
                f") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) USING TTL 86400"
            )

            # Use prepared statement for parameterized queries (recommended approach)
            prepared = self.session.prepare(insert_query_str)

            now = datetime.utcnow()
            expires_at = now + timedelta(hours=24)  # 24 hour cache

            # Capture parameters for lambda
            params = (
                query_hash,
                client_account_id,
                engagement_id,
                user_id,
                search_id,
                search_query,
                results_json,
                now,
                expires_at,
            )

            loop = asyncio.get_event_loop()

            def execute_cache_insert(stmt=prepared, p=params):
                return self.session.execute(stmt, p)

            await loop.run_in_executor(None, execute_cache_insert)

        except Exception as e:
            logger.debug(f"Error caching search results: {e}")

    async def _update_analytics(
        self,
        client_account_id: UUID,
        user_id: str,
        search_query: str,
        results_count: int,
        execution_time_ms: int,
        source: str,
    ):
        """Update aggregated analytics (non-blocking)"""
        try:
            loop = asyncio.get_event_loop()
            now = datetime.utcnow()
            year_month = now.strftime("%Y-%m")

            # Get current analytics
            select_query = f"""
                SELECT total_searches, unique_queries, avg_results_count,
                       avg_execution_time_ms, most_searched_symbols, search_sources
                FROM {self.keyspace}.user_search_analytics
                WHERE client_account_id = ? AND user_id = ? AND year_month = ?
            """

            try:
                result = await loop.run_in_executor(
                    None,
                    lambda: self.session.execute(
                        select_query, (client_account_id, user_id, year_month)
                    ).one(),
                )
            except Exception:
                # No existing record
                result = None

            if result:
                # Update existing analytics
                total_searches = result.total_searches + 1
                avg_results = (
                    result.avg_results_count * result.total_searches + results_count
                ) / total_searches
                avg_time = (
                    result.avg_execution_time_ms * result.total_searches
                    + execution_time_ms
                ) / total_searches
                most_searched = result.most_searched_symbols or {}
                search_sources = result.search_sources or {}

                # Update symbol count (safely extract first word, fallback to query if empty)
                query_parts = search_query.strip().upper().split()
                symbol = query_parts[0] if query_parts else search_query.strip().upper() or "unknown"
                most_searched[symbol] = most_searched.get(symbol, 0) + 1
                search_sources[source] = search_sources.get(source, 0) + 1

                update_query_str = (
                    f"UPDATE {self.keyspace}.user_search_analytics "
                    f"SET total_searches = ?, "
                    f"avg_results_count = ?, "
                    f"avg_execution_time_ms = ?, "
                    f"most_searched_symbols = ?, "
                    f"search_sources = ?, "
                    f"updated_at = ? "
                    f"WHERE client_account_id = ? AND user_id = ? AND year_month = ?"
                )

                # Use prepared statement for parameterized queries (recommended approach)
                prepared = self.session.prepare(update_query_str)

                update_params = (
                    total_searches,
                    avg_results,
                    avg_time,
                    most_searched,
                    search_sources,
                    now,
                    client_account_id,
                    user_id,
                    year_month,
                )

                def execute_update(stmt=prepared, p=update_params):
                    return self.session.execute(stmt, p)

                await loop.run_in_executor(None, execute_update)
            else:
                # Create new analytics record
                # Safely extract first word, fallback to query if empty
                query_parts = search_query.strip().upper().split()
                symbol = query_parts[0] if query_parts else search_query.strip().upper() or "unknown"
                most_searched = {symbol: 1}
                search_sources = {source: 1}

                insert_query_str = (
                    f"INSERT INTO {self.keyspace}.user_search_analytics ("
                    f"client_account_id, user_id, year_month, "
                    f"total_searches, unique_queries, avg_results_count, "
                    f"avg_execution_time_ms, most_searched_symbols, search_sources, updated_at"
                    f") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                )

                # Use prepared statement for parameterized queries (recommended approach)
                prepared = self.session.prepare(insert_query_str)

                insert_params = (
                    client_account_id,
                    user_id,
                    year_month,
                    1,  # total_searches
                    1,  # unique_queries
                    float(results_count),  # avg_results_count
                    float(execution_time_ms),  # avg_execution_time_ms
                    most_searched,
                    search_sources,
                    now,
                )

                def execute_insert_analytics(stmt=prepared, p=insert_params):
                    return self.session.execute(stmt, p)

                await loop.run_in_executor(None, execute_insert_analytics)

        except Exception as e:
            logger.debug(f"Error updating analytics: {e}")

    async def get_search_history(
        self,
        client_account_id: Union[UUID, str],
        user_id: str,
        days: int = 30,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get user's stock search history.

        Args:
            client_account_id: Client account ID (UUID or string)
            user_id: User ID
            days: Number of days to look back
            limit: Maximum number of results

        Returns:
            List of search records
        """
        if not CASSANDRA_AVAILABLE:
            logger.warning("Cassandra driver not available - returning empty history")
            return []

        if not self._initialized:
            if not await self.initialize():
                return []

        try:
            from datetime import date

            # Convert string UUID to UUID object if needed
            if isinstance(client_account_id, str):
                client_account_id = UUID(client_account_id)

            searches = []
            end_date = date.today()
            start_date = end_date - timedelta(days=days)

            # Query each day in the range
            loop = asyncio.get_event_loop()
            current_date = start_date
            while current_date <= end_date and len(searches) < limit:
                # Build query string - use f-string for keyspace (safe, from config)
                # and ? placeholders for parameters (Cassandra uses ? for parameterized queries)
                # Keyspace name is safe to use in f-string as it comes from config
                keyspace_name = self.keyspace
                query_str = (
                    f"SELECT search_timestamp, search_id, search_query, search_type, "
                    f"results_count, execution_time_ms, source "
                    f"FROM {keyspace_name}.user_stock_searches "
                    f"WHERE client_account_id = ? AND user_id = ? AND search_date = ? "
                    f"ORDER BY search_timestamp DESC LIMIT ?"
                )

                # Use prepared statement for parameterized queries (recommended approach)
                prepared = self.session.prepare(query_str)
                select_query = prepared

                # Capture variables for lambda (avoid closure issues)
                date_param = current_date
                limit_param = limit - len(searches)
                ca_id = client_account_id
                u_id = user_id
                stmt = select_query

                def execute_query(
                    d=date_param, limit_val=limit_param, c=ca_id, u=u_id, s=stmt
                ):
                    return self.session.execute(s, (c, u, d, limit_val))

                results = await loop.run_in_executor(None, execute_query)

                for row in results:
                    searches.append(
                        {
                            "search_id": str(row.search_id),
                            "search_query": row.search_query,
                            "search_type": row.search_type,
                            "results_count": row.results_count,
                            "execution_time_ms": row.execution_time_ms,
                            "source": row.source,
                            "timestamp": row.search_timestamp.isoformat(),
                        }
                    )

                current_date += timedelta(days=1)

            return searches[:limit]

        except Exception as e:
            logger.error(f"Error getting search history: {e}", exc_info=True)
            return []

    async def get_search_analytics(
        self,
        client_account_id: Union[UUID, str],
        user_id: str,
        year_month: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get aggregated search analytics for a user.

        Args:
            client_account_id: Client account ID
            user_id: User ID
            year_month: Year-month string (e.g., '2025-01'), defaults to current month

        Returns:
            Analytics dictionary or None
        """
        if not CASSANDRA_AVAILABLE:
            logger.warning("Cassandra driver not available - returning None")
            return None

        if not self._initialized:
            if not await self.initialize():
                return None

        try:
            # Convert string UUID to UUID object if needed
            if isinstance(client_account_id, str):
                client_account_id = UUID(client_account_id)

            loop = asyncio.get_event_loop()
            if not year_month:
                year_month = datetime.utcnow().strftime("%Y-%m")

            select_query_str = (
                f"SELECT total_searches, unique_queries, avg_results_count, "
                f"avg_execution_time_ms, most_searched_symbols, search_sources "
                f"FROM {self.keyspace}.user_search_analytics "
                f"WHERE client_account_id = ? AND user_id = ? AND year_month = ?"
            )

            # Use prepared statement for parameterized queries (recommended approach)
            prepared = self.session.prepare(select_query_str)

            select_params = (client_account_id, user_id, year_month)

            def execute_select(stmt=prepared, p=select_params):
                return self.session.execute(stmt, p).one()

            result = await loop.run_in_executor(None, execute_select)

            if result:
                return {
                    "year_month": year_month,
                    "total_searches": result.total_searches,
                    "unique_queries": result.unique_queries,
                    "avg_results_count": result.avg_results_count,
                    "avg_execution_time_ms": result.avg_execution_time_ms,
                    "most_searched_symbols": dict(result.most_searched_symbols or {}),
                    "search_sources": dict(result.search_sources or {}),
                }

            return None

        except Exception as e:
            logger.error(f"Error getting search analytics: {e}", exc_info=True)
            return None

    async def get_cached_results(
        self,
        client_account_id: Union[UUID, str],
        user_id: str,
        search_query: str,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached search results if available and not expired.

        Args:
            client_account_id: Client account ID
            user_id: User ID
            search_query: Search query string

        Returns:
            Cached results or None
        """
        if not CASSANDRA_AVAILABLE:
            logger.warning("Cassandra driver not available - returning None")
            return None

        if not self._initialized:
            if not await self.initialize():
                return None

        try:
            import hashlib
            import json

            # Convert string UUID to UUID object if needed
            if isinstance(client_account_id, str):
                client_account_id = UUID(client_account_id)

            loop = asyncio.get_event_loop()
            query_hash = hashlib.md5(search_query.lower().encode()).hexdigest()

            select_query_str = (
                f"SELECT results, expires_at "
                f"FROM {self.keyspace}.user_search_results "
                f"WHERE search_query_hash = ? AND client_account_id = ? AND user_id = ? "
                f"AND expires_at > ? LIMIT 1"
            )

            # Use prepared statement for parameterized queries (recommended approach)
            prepared = self.session.prepare(select_query_str)

            now = datetime.utcnow()
            select_params = (query_hash, client_account_id, user_id, now)

            def execute_select_cache(stmt=prepared, p=select_params):
                return self.session.execute(stmt, p).one()

            result = await loop.run_in_executor(None, execute_select_cache)

            if result and result.expires_at > now:
                return json.loads(result.results)

            return None

        except Exception as e:
            logger.debug(f"No cached results found or error: {e}")
            return None

    def close(self):
        """Close Cassandra connection"""
        if self.session:
            self.session.shutdown()
        if self.cluster:
            self.cluster.shutdown()
        logger.info("Cassandra connection closed")


# Global instance
cassandra_service = CassandraService()
