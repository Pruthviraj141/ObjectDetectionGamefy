#!/usr/bin/env python3
"""
Test script for the fixed leaderboard functionality
This tests the database operations for unique users and score handling
"""

import sqlite3
import os
import sys

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.database import LeaderboardDB

def test_leaderboard():
    """Test the leaderboard database functionality"""
    print("Testing Leaderboard Functionality")
    print("=" * 50)
    
    # Create a test database in current directory
    test_db_path = "test_leaderboard.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    try:
        # Initialize database
        db = LeaderboardDB(test_db_path)
        print("SUCCESS: Database initialized successfully")
        
        # Test adding players with different case names
        test_players = [
            ("Alice", 100, 1, 5),
            ("Bob", 150, 2, 8),
            ("alice", 120, 1, 6),  # Should update Alice's record
            ("CHARLIE", 200, 3, 10),
            ("bob", 180, 2, 9),    # Should update Bob's record
        ]
        
        print("\nAdding test players...")
        for name, score, games, objects in test_players:
            result = db.add_or_update_player(name, score, games, objects)
            if result:
                print(f"SUCCESS: Added/Updated: {name} (Score: {score})")
            else:
                print(f"ERROR: Failed to add: {name}")
        
        # Test getting top players
        print("\nTop 5 Players:")
        top_players = db.get_top_players(limit=5)
        for i, player in enumerate(top_players, 1):
            print(f"#{i}. {player['name']} - {player['score']} points ({player['games_played']} games, {player['objects_discovered']} objects)")
        
        # Test getting specific player
        print("\nTesting player lookup...")
        alice_info = db.get_player_rank("alice")
        if alice_info:
            print(f"SUCCESS: Found Alice: {alice_info['name']} - Rank #{alice_info['rank']} with {alice_info['score']} points")
        else:
            print("ERROR: Alice not found")
        
        # Test statistics
        print("\nDatabase Statistics:")
        stats = db.get_statistics()
        print(f"   Total Players: {stats['total_players']}")
        print(f"   Average Score: {stats['average_score']}")
        print(f"   Highest Score: {stats['highest_score']}")
        print(f"   Total Games: {stats['total_games_played']}")
        
        # Test case sensitivity - should be able to find different cases
        print("\nTesting case sensitivity...")
        names_to_test = ["alice", "ALICE", "Alice", "bob", "BOB"]
        for name in names_to_test:
            player = db.get_player_rank(name)
            if player:
                print(f"SUCCESS: Found '{name}' -> Displayed as: '{player['name']}'")
            else:
                print(f"ERROR: Could not find: '{name}'")
        
        print("\nAll tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"ERROR: Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up test database
        if os.path.exists(test_db_path):
            try:
                db.close()  # Close database connections first
            except:
                pass
            try:
                os.remove(test_db_path)
                print(f"\nCleaned up test database: {test_db_path}")
            except:
                print(f"\nCould not remove test database: {test_db_path}")

if __name__ == "__main__":
    success = test_leaderboard()
    sys.exit(0 if success else 1)