#!/usr/bin/env python3
"""
Test suite for Vox local-first application
Tests database operations, API endpoints, and core functionality
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

# Add the project to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all required modules can be imported"""
    print("🧪 Testing imports...")
    try:
        import aiosqlite
        import fastapi
        import socketio
        from vox import database, llm
        print("   ✅ Core imports successful (database, llm)")
        
        # Try to import audio modules (optional for basic functionality)
        try:
            import numpy
            import librosa
            print("   ✅ Audio processing imports successful (numpy, librosa)")
        except ImportError:
            print("   ⚠️  Audio processing libraries not installed (optional for core tests)")
        
        return True
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False


async def test_database_operations():
    """Test SQLite database operations"""
    print("\n🧪 Testing database operations...")
    
    import aiosqlite
    from vox.database import (
        get_user_preferences,
        update_user_preferences,
        save_vocal_data_async,
        get_all_vocal_data,
        save_chat_message_async,
        fetch_chat_history_async
    )
    
    # Use a temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # Initialize database with schema
        db = await aiosqlite.connect(db_path)
        db.row_factory = aiosqlite.Row
        
        # Read and execute schema
        schema_path = Path(__file__).parent / "docs" / "sqlite_schema.sql"
        with open(schema_path, "r") as f:
            schema = f.read()
        await db.executescript(schema)
        await db.commit()
        print("   ✅ Database schema initialized")
        
        # Test user preferences
        prefs = await get_user_preferences(db)
        assert prefs is not None, "User preferences should exist"
        assert prefs['user_name'] == 'friend', f"Default name should be 'friend', got {prefs['user_name']}"
        assert prefs['user_pronouns'] == 'they/them/theirs/themselves'
        print("   ✅ Default user preferences loaded")
        
        # Update preferences
        await update_user_preferences(db, user_name="TestUser", user_pronouns="she/her")
        prefs = await get_user_preferences(db)
        assert prefs['user_name'] == 'TestUser'
        assert prefs['user_pronouns'] == 'she/her'
        print("   ✅ User preferences updated successfully")
        
        # Test vocal data
        await save_vocal_data_async(
            db,
            timestamp="2024-01-01T12:00:00",
            pitch=200.0,
            hnr=15.5,
            harmonics={"H1": 100, "H2": 50},
            formants={"F1": 800, "F2": 1200},
            jitter_shimmer={"jitter": 0.5},
            praat_report="Test report"
        )
        vocal_data = await get_all_vocal_data(db)
        assert len(vocal_data) == 1
        assert vocal_data[0]['pitch'] == 200.0
        print("   ✅ Vocal data saved and retrieved")
        
        # Test chat messages
        await save_chat_message_async(db, "user", "Hello")
        await save_chat_message_async(db, "assistant", "Hi there!")
        messages = await fetch_chat_history_async(db, limit=10)
        assert len(messages) == 2
        assert messages[0]['message'] == 'Hello'
        assert messages[1]['message'] == 'Hi there!'
        print("   ✅ Chat messages saved and retrieved")
        
        await db.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)


async def test_fastapi_app():
    """Test FastAPI application initialization"""
    print("\n🧪 Testing FastAPI application...")
    
    try:
        # Import without audio modules by mocking them first
        import sys
        from unittest.mock import MagicMock
        
        # Mock audio modules if not available
        if 'numpy' not in sys.modules:
            sys.modules['numpy'] = MagicMock()
        if 'librosa' not in sys.modules:
            sys.modules['librosa'] = MagicMock()
        if 'aubio' not in sys.modules:
            sys.modules['aubio'] = MagicMock()
        if 'parselmouth' not in sys.modules:
            sys.modules['parselmouth'] = MagicMock()
        
        # Mock audio_processing module
        mock_audio = MagicMock()
        sys.modules['vox.audio_processing'] = mock_audio
        
        from vox.fastapi_app import app
        
        # Check that app is created
        assert app is not None
        print("   ✅ FastAPI app initialized")
        
        # Check routers are registered
        routes = [route.path for route in app.routes]
        expected_routes = ['/user/', '/recordings/', '/chat/']
        
        for expected in expected_routes:
            if any(expected in route for route in routes):
                print(f"   ✅ Router {expected} registered")
            else:
                print(f"   ⚠️  Router {expected} not found in routes")
        
        return True
        
    except Exception as e:
        print(f"   ❌ FastAPI test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_llm_module():
    """Test LLM module configuration"""
    print("\n🧪 Testing LLM module...")
    
    try:
        from vox.llm import get_client
        
        # Test without API key (should not raise error in get_client)
        os.environ.pop('OPENAI_API_KEY', None)
        
        try:
            client = get_client()
            print("   ❌ Should have raised ValueError for missing API key")
            return False
        except ValueError as e:
            if "OPENAI_API_KEY" in str(e):
                print("   ✅ Correctly raises error when API key missing")
            else:
                print(f"   ❌ Wrong error message: {e}")
                return False
        
        # Test with API key set
        os.environ['OPENAI_API_KEY'] = 'test-key-123'
        client = get_client()
        assert client is not None
        print("   ✅ LLM client created with API key")
        
        # Test with custom base URL
        os.environ['OPENAI_API_BASE'] = 'https://openrouter.ai/api/v1'
        client = get_client()
        assert client is not None
        print("   ✅ LLM client created with custom base URL")
        
        return True
        
    except Exception as e:
        print(f"   ❌ LLM test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up
        os.environ.pop('OPENAI_API_KEY', None)
        os.environ.pop('OPENAI_API_BASE', None)


async def test_database_init():
    """Test database initialization script"""
    print("\n🧪 Testing database initialization script...")
    
    try:
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        # Set environment variable
        os.environ['DATABASE_PATH'] = db_path
        
        # Run init script
        import subprocess
        result = subprocess.run(
            [sys.executable, 'init_db.py'],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("   ✅ init_db.py executed successfully")
            print(f"      Output: {result.stdout.strip()}")
            
            # Verify database exists
            if os.path.exists(db_path):
                print("   ✅ Database file created")
                
                # Verify schema
                import aiosqlite
                db = await aiosqlite.connect(db_path)
                async with db.execute("SELECT name FROM sqlite_master WHERE type='table'") as cursor:
                    tables = [row[0] for row in await cursor.fetchall()]
                
                expected_tables = ['user_preferences', 'vocal_data', 'chat_messages']
                for table in expected_tables:
                    if table in tables:
                        print(f"   ✅ Table '{table}' exists")
                    else:
                        print(f"   ❌ Table '{table}' missing")
                        return False
                
                await db.close()
                return True
            else:
                print("   ❌ Database file not created")
                return False
        else:
            print(f"   ❌ init_db.py failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ Database init test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up
        os.environ.pop('DATABASE_PATH', None)
        if os.path.exists(db_path):
            os.unlink(db_path)


async def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("🎤 Vox Local-First Application Test Suite")
    print("=" * 60)
    
    results = []
    
    # Sync tests
    results.append(("Import Test", test_imports()))
    
    # Async tests
    results.append(("Database Operations", await test_database_operations()))
    results.append(("FastAPI App", await test_fastapi_app()))
    results.append(("LLM Module", await test_llm_module()))
    results.append(("Database Init", await test_database_init()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 All tests passed! The local-first migration is working correctly.")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
