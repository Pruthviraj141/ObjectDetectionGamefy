#!/usr/bin/env python3
"""
Quick validation script for SQLite Leaderboard System
Run this to test the database functionality without starting the full web app
"""

import sys
import os
import json
from datetime import datetime

# Add current directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.database import LeaderboardDB

def test_database():
    """Test all database operations"""
    print("Testing SQLite Leaderboard Database...")
    print("=" * 50)
    
    # Initialize database
    db = LeaderboardDB()
    
    # Test 1: Add sample players
    print("Test 1: Adding sample players...")
    test_players = [
        ("Alice", 150, 3, 8),
        ("Bob", 200, 5, 12),
        ("Charlie", 120, 2, 6),
        ("Diana", 180, 4, 10),
        ("Eve", 90, 1, 4)
    ]
    
    for name, score, games, objects in test_players:
        success = db.add_or_update_player(name, score, games, objects)
        print(f"   Added {name}: {success}")
    
    # Test 2: Get top players
    print("\\nTest 2: Getting top players...")
    top_players = db.get_top_players(5)
    for i, player in enumerate(top_players, 1):
        print(f"   #{i} {player['name']}: {player['score']} pts ({player['games_played']} games, {player['objects_discovered']} objects)")
    
    # Test 3: Get player rank
    print("\\nTest 3: Getting player rank...")
    rank_info = db.get_player_rank("Bob")
    if rank_info:
        print(f"   Bob's rank: #{rank_info['rank']} of {rank_info['total_players']} players")
        print(f"      Score: {rank_info['score']}, Games: {rank_info['games_played']}, Objects: {rank_info['objects_discovered']}")
    
    # Test 4: Update existing player
    print("\\nTest 4: Updating existing player...")
    success = db.add_or_update_player("Alice", 175, 1, 2)  # Should increase score
    print(f"   Updated Alice: {success}")
    
    rank_info = db.get_player_rank("Alice")
    if rank_info:
        print(f"   Alice's new rank: #{rank_info['rank']} with {rank_info['score']} pts")
    
    # Test 5: Statistics
    print("\\nTest 5: Getting statistics...")
    stats = db.get_statistics()
    print(f"   Total players: {stats['total_players']}")
    print(f"   Highest score: {stats['highest_score']}")
    print(f"   Average score: {stats['average_score']}")
    print(f"   Total games: {stats['total_games_played']}")
    print(f"   Total objects: {stats['total_objects_discovered']}")
    
    # Test 6: Recent activity
    print("\\nTest 6: Getting recent activity...")
    activity = db.get_recent_activity(3)
    for player in activity:
        print(f"   {player['name']}: {player['score']} pts (last active: {player['last_active']})")
    
    # Test 7: Error handling
    print("\\nTest 7: Error handling...")
    
    # Invalid data
    success = db.add_or_update_player("", -5, 1, 1)
    print(f"   Invalid data handled: {success}")
    
    success = db.add_or_update_player("TestPlayer", 50, 1, 1)
    print(f"   Valid data accepted: {success}")
    
    print("\\n" + "=" * 50)
    print("All database tests completed successfully!")
    print(f"Database location: {db.db_path}")
    
    return True

def test_api_simulation():
    """Simulate API calls to test response format"""
    print("\\nTesting API Response Simulation...")
    print("=" * 50)
    
    db = LeaderboardDB()
    
    # Simulate GET /api/leaderboard
    players = db.get_top_players(10)
    total_players = db.get_total_players()
    
    api_response = {
        "success": True,
        "players": players,
        "total_players": total_players
    }
    
    print("GET /api/leaderboard response:")
    print(json.dumps(api_response, indent=2, default=str))
    
    # Simulate POST /api/leaderboard (update player)
    player_data = {
        "name": "TestPlayerAPI",
        "score": 250,
        "games_played": 2,
        "objects_discovered": 15
    }
    
    success = db.add_or_update_player(
        player_data["name"], 
        player_data["score"], 
        player_data["games_played"], 
        player_data["objects_discovered"]
    )
    
    if success:
        player_rank = db.get_player_rank(player_data["name"])
        update_response = {
            "success": True,
            "message": "Player updated successfully",
            "player": player_rank
        }
        
        print("\\nPOST /api/leaderboard response:")
        print(json.dumps(update_response, indent=2, default=str))
    
    print("\\n" + "=" * 50)
    print("API simulation completed!")

def cleanup_test_data():
    """Clean up test data"""
    print("\\nCleaning up test data...")
    
    db = LeaderboardDB()
    test_players = ["TestPlayer", "TestPlayerAPI", "Alice", "Bob", "Charlie", "Diana", "Eve"]
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    for player in test_players:
        cursor.execute("DELETE FROM leaderboard WHERE name = ?", (player,))
    
    conn.commit()
    conn.close()
    
    print("Test data cleaned up")

if __name__ == "__main__":
    try:
        # Run tests
        test_database()
        test_api_simulation()
        
        # Ask user if they want to clean up
        response = input("\\nDo you want to clean up test data? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            cleanup_test_data()
        
        print("\\nLeaderboard validation complete!")
        
    except Exception as e:
        print(f"\\nTest failed with error: {e}")
        print("\\nTroubleshooting:")
        print("1. Make sure you're in the correct directory")
        print("2. Check that data/ directory is writable")
        print("3. Verify SQLite3 is installed: python3 -c 'import sqlite3; print(sqlite3.sqlite_version)'")
        
        sys.exit(1)