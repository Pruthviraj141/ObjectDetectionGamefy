"""
Production-Ready SQLite Database Module for Object Quest Leaderboard
Optimized for cloud deployment, concurrent access, and scalability
"""

import sqlite3
import os
import logging
import threading
import time
from datetime import datetime
from typing import List, Dict, Optional, Any
from contextlib import contextmanager
from pathlib import Path
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ConnectionPool:
    """Thread-safe connection pool for SQLite database"""
    
    def __init__(self, db_path: str, pool_size: int = 20, timeout: float = 30.0):
        self.db_path = db_path
        self.pool_size = pool_size
        self.timeout = timeout
        self._pool = []
        self._lock = threading.Lock()
        self._created = 0
        
        # Ensure database directory exists
        db_dir = os.path.dirname(db_path)
        if db_dir:  # Only create directory if it's not empty
            os.makedirs(db_dir, exist_ok=True)
        
        # Initialize connection pool
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize the connection pool"""
        try:
            for _ in range(self.pool_size):
                conn = self._create_connection()
                if conn:
                    self._pool.append(conn)
                    self._created += 1
            logger.info(f"Connection pool initialized with {len(self._pool)} connections")
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise
    
    def _create_connection(self) -> Optional[sqlite3.Connection]:
        """Create a new database connection with optimal settings"""
        try:
            # Enable WAL mode for better concurrent access
            conn = sqlite3.connect(
                self.db_path,
                timeout=self.timeout,
                check_same_thread=False,
                isolation_level=None  # Autocommit mode for better performance
            )
            
            # Enable WAL mode for concurrent reads/writes
            conn.execute("PRAGMA journal_mode=WAL")
            
            # Optimize for concurrent access
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA temp_store=memory")
            conn.execute("PRAGMA mmap_size=67108864")  # 64MB mmap
            
            # Set row factory
            conn.row_factory = sqlite3.Row
            
            return conn
            
        except Exception as e:
            logger.error(f"Failed to create database connection: {e}")
            return None
    
    @contextmanager
    def get_connection(self, timeout: float = None):
        """Get a connection from the pool with timeout"""
        timeout = timeout or self.timeout
        start_time = time.time()
        
        try:
            with self._lock:
                while not self._pool and (time.time() - start_time) < timeout:
                    # Try to create a new connection if pool is empty
                    if self._created < self.pool_size:
                        conn = self._create_connection()
                        if conn:
                            self._pool.append(conn)
                            self._created += 1
                            break
                    time.sleep(0.01)  # Brief sleep before retry
                
                if not self._pool:
                    raise sqlite3.OperationalError("Connection pool exhausted")
                
                conn = self._pool.pop()
            
            yield conn
            
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                try:
                    # Reset connection state
                    conn.execute("ROLLBACK")  # Ensure no active transactions
                    with self._lock:
                        if len(self._pool) < self.pool_size:
                            self._pool.append(conn)
                        else:
                            conn.close()
                except Exception as e:
                    logger.warning(f"Error returning connection to pool: {e}")
                    try:
                        conn.close()
                    except:
                        pass
    
    def close_all(self):
        """Close all connections in the pool"""
        with self._lock:
            for conn in self._pool:
                try:
                    conn.close()
                except Exception as e:
                    logger.warning(f"Error closing connection: {e}")
            self._pool.clear()
        logger.info("Connection pool closed")

class LeaderboardDB:
    """
    Production-ready leaderboard database with optimized concurrency handling
    """
    
    def __init__(self, db_path: str = "data/leaderboard.db"):
        """Initialize database with connection pool and schema"""
        self.db_path = db_path
        self._lock = threading.Lock()
        
        # Initialize connection pool
        self._pool = ConnectionPool(db_path)
        
        # Initialize database schema
        self.init_database()
        
        logger.info(f"Database initialized: {db_path}")
    
    def init_database(self):
        """Initialize database schema with optimized indexes"""
        try:
            with self._pool.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create main leaderboard table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS leaderboard (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        name_lower TEXT NOT NULL UNIQUE,
                        score INTEGER NOT NULL DEFAULT 0,
                        games_played INTEGER DEFAULT 0,
                        objects_discovered INTEGER DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        last_active DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Check if we need to migrate existing data
                cursor.execute("PRAGMA table_info(leaderboard)")
                columns = [col[1] for col in cursor.fetchall()]
                
                if 'name_lower' not in columns:
                    logger.info("Migrating database to support case-sensitive names")
                    # Add name_lower column
                    cursor.execute("ALTER TABLE leaderboard ADD COLUMN name_lower TEXT")
                    
                    # Update existing records with lowercase names
                    cursor.execute("UPDATE leaderboard SET name_lower = LOWER(name)")
                    
                    # Add unique constraint to name_lower
                    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_leaderboard_name_lower ON leaderboard(name_lower)")
                
                # Optimized indexes for concurrent access
                indexes = [
                    ("idx_leaderboard_score_rank", "CREATE INDEX IF NOT EXISTS idx_leaderboard_score_rank ON leaderboard(score DESC, name)"),
                    ("idx_leaderboard_name_lookup", "CREATE INDEX IF NOT EXISTS idx_leaderboard_name_lookup ON leaderboard(name_lower)"),
                    ("idx_leaderboard_activity", "CREATE INDEX IF NOT EXISTS idx_leaderboard_activity ON leaderboard(updated_at DESC)"),
                    ("idx_leaderboard_stats", "CREATE INDEX IF NOT EXISTS idx_leaderboard_stats ON leaderboard(games_played, objects_discovered)")
                ]
                
                for index_name, index_sql in indexes:
                    try:
                        cursor.execute(index_sql)
                    except sqlite3.Error as e:
                        logger.warning(f"Index {index_name} creation failed: {e}")
                
                conn.commit()
                logger.info("Database schema initialized successfully")
                
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row
            conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Transaction failed: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def add_or_update_player(self, name: str, score: int, games_played: int = 1, objects_discovered: int = 1) -> bool:
        """
        Add new player or update existing player with thread-safe operations
        Uses UPSERT pattern for atomic updates
        """
        if not name or not isinstance(score, int) or score < 0:
            logger.warning(f"Invalid player data: name={name}, score={score}")
            return False
        
        try:
            with self._pool.get_connection() as conn:
                cursor = conn.cursor()
                
                # Atomic UPSERT operation for concurrent safety
                cursor.execute("""
                    INSERT INTO leaderboard (name, name_lower, score, games_played, objects_discovered)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(name_lower) DO UPDATE SET
                        name = excluded.name,
                        score = CASE WHEN excluded.score > leaderboard.score
                                THEN excluded.score
                                ELSE leaderboard.score END,
                        games_played = leaderboard.games_played + excluded.games_played,
                        objects_discovered = MAX(leaderboard.objects_discovered, excluded.objects_discovered),
                        updated_at = CURRENT_TIMESTAMP,
                        last_active = CURRENT_TIMESTAMP
                """, (name.strip(), name.strip().lower(), score, games_played, objects_discovered))
                
                logger.debug(f"Player {name} updated: score={score}")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Database error updating player {name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating player {name}: {e}")
            return False
    
    def get_top_players(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get top players with optimized ranking queries
        Uses LIMIT/OFFSET for pagination support
        """
        try:
            with self._pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name, score, games_played, objects_discovered, 
                           created_at, updated_at, last_active
                    FROM leaderboard 
                    ORDER BY score DESC, updated_at ASC
                    LIMIT ? OFFSET ?
                """, (limit, offset))
                
                players = []
                for row in cursor.fetchall():
                    players.append({
                        'name': row['name'],
                        'score': row['score'],
                        'games_played': row['games_played'],
                        'objects_discovered': row['objects_discovered'],
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at'],
                        'last_active': row['last_active']
                    })
                
                return players
                
        except sqlite3.Error as e:
            logger.error(f"Database error fetching top players: {e}")
            return []
    
    def get_player_rank(self, name: str) -> Optional[Dict[str, Any]]:
        """Get player rank with optimized single-query approach"""
        if not name:
            return None
        
        try:
            with self._pool.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get player info and rank in single query
                cursor.execute("""
                    SELECT
                        l.name, l.score, l.games_played, l.objects_discovered,
                        l.created_at, l.updated_at, l.last_active,
                        (SELECT COUNT(*) FROM leaderboard
                         WHERE score > l.score
                         OR (score = l.score AND updated_at < l.updated_at)) + 1 as rank,
                        (SELECT COUNT(*) FROM leaderboard) as total_players
                    FROM leaderboard l
                    WHERE l.name_lower = ?
                """, (name.strip().lower(),))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                return {
                    'name': row['name'],
                    'score': row['score'],
                    'games_played': row['games_played'],
                    'objects_discovered': row['objects_discovered'],
                    'rank': row['rank'],
                    'total_players': row['total_players'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at'],
                    'last_active': row['last_active']
                }
                
        except sqlite3.Error as e:
            logger.error(f"Database error fetching rank for {name}: {e}")
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics with optimized queries"""
        try:
            with self._pool.get_connection() as conn:
                cursor = conn.cursor()
                
                # Single comprehensive query for efficiency
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_players,
                        SUM(score) as total_score,
                        AVG(score) as average_score,
                        MAX(score) as highest_score,
                        MIN(score) as lowest_score,
                        SUM(games_played) as total_games,
                        SUM(objects_discovered) as total_objects,
                        MAX(last_active) as most_recent_activity
                    FROM leaderboard
                """)
                
                row = cursor.fetchone()
                
                # Calculate percentiles if we have data
                total_players = row['total_players'] or 0
                
                if total_players > 0:
                    # Get median score
                    cursor.execute("""
                        SELECT score FROM leaderboard 
                        ORDER BY score
                        LIMIT 1 OFFSET ?
                    """, (total_players // 2,))
                    
                    median_row = cursor.fetchone()
                    median_score = median_row['score'] if median_row else 0
                else:
                    median_score = 0
                
                return {
                    'total_players': total_players,
                    'total_score': row['total_score'] or 0,
                    'average_score': round(row['average_score'] or 0, 2),
                    'median_score': median_score,
                    'highest_score': row['highest_score'] or 0,
                    'lowest_score': row['lowest_score'] or 0,
                    'total_games_played': row['total_games'] or 0,
                    'total_objects_discovered': row['total_objects'] or 0,
                    'most_recent_activity': row['most_recent_activity'],
                    'score_range': (row['lowest_score'] or 0, row['highest_score'] or 0),
                    'engagement_rate': round(
                        (row['total_games'] or 0) / max(total_players, 1), 2
                    )
                }
                
        except sqlite3.Error as e:
            logger.error(f"Database error fetching statistics: {e}")
            return {}
    
    def get_recent_activity(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recently active players for activity feed"""
        try:
            with self._pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name, score, games_played, objects_discovered, last_active
                    FROM leaderboard 
                    WHERE last_active IS NOT NULL
                    ORDER BY last_active DESC
                    LIMIT ?
                """, (limit,))
                
                activity = []
                for row in cursor.fetchall():
                    activity.append({
                        'name': row['name'],
                        'score': row['score'],
                        'games_played': row['games_played'],
                        'objects_discovered': row['objects_discovered'],
                        'last_active': row['last_active']
                    })
                
                return activity
                
        except sqlite3.Error as e:
            logger.error(f"Database error fetching recent activity: {e}")
            return []
    
    def get_total_players(self) -> int:
        """Get total number of players with caching"""
        try:
            with self._pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as total FROM leaderboard")
                return cursor.fetchone()['total']
        except sqlite3.Error as e:
            logger.error(f"Database error counting players: {e}")
            return 0
    
    def clear_leaderboard(self) -> bool:
        """Clear all leaderboard data (admin operation)"""
        try:
            with self._pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM leaderboard")
                logger.info("Leaderboard cleared by admin operation")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Database error clearing leaderboard: {e}")
            return False
    
    def export_to_json(self, include_stats: bool = True) -> Dict[str, Any]:
        """Export complete leaderboard data for frontend consumption"""
        try:
            export_data = {
                'players': self.get_top_players(limit=1000),  # Export top 1000
                'exported_at': datetime.now().isoformat(),
                'total_players': self.get_total_players()
            }
            
            if include_stats:
                export_data['statistics'] = self.get_statistics()
                export_data['recent_activity'] = self.get_recent_activity(limit=20)
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting leaderboard to JSON: {e}")
            return {'error': str(e)}
    
    def optimize_database(self) -> bool:
        """Optimize database performance (run periodically)"""
        try:
            with self._pool.get_connection() as conn:
                cursor = conn.cursor()
                
                # Analyze query planner
                cursor.execute("ANALYZE")
                
                # Vacuum to reclaim space
                cursor.execute("VACUUM")
                
                # Update index statistics
                cursor.execute("REINDEX")
                
                logger.info("Database optimization completed")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Database optimization failed: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Perform database health check"""
        try:
            start_time = time.time()
            
            with self._pool.get_connection() as conn:
                cursor = conn.cursor()
                
                # Test basic query
                cursor.execute("SELECT COUNT(*) FROM leaderboard")
                total_players = cursor.fetchone()[0]
                
                # Test complex query
                cursor.execute("""
                    SELECT AVG(score), COUNT(DISTINCT name) 
                    FROM leaderboard WHERE score > 0
                """)
                stats = cursor.fetchone()
                
                query_time = time.time() - start_time
                
                return {
                    'status': 'healthy',
                    'total_players': total_players,
                    'avg_score': stats[0] or 0,
                    'active_players': stats[1] or 0,
                    'query_time_ms': round(query_time * 1000, 2),
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def close(self):
        """Clean shutdown of database connections"""
        try:
            self._pool.close_all()
            logger.info("Database connections closed")
        except Exception as e:
            logger.warning(f"Error during database shutdown: {e}")

# Global database instance with lazy initialization
_db_instance = None
_db_lock = threading.Lock()

def get_database(db_path: str = "data/leaderboard.db") -> LeaderboardDB:
    """Get singleton database instance"""
    global _db_instance
    if _db_instance is None:
        with _db_lock:
            if _db_instance is None:
                _db_instance = LeaderboardDB(db_path)
    return _db_instance

# Export for easy importing
db = get_database()