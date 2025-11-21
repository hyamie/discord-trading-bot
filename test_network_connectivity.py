#!/usr/bin/env python3
"""
Network connectivity test for Railway to Supabase connection.
Tests raw TCP connectivity before application layer.
"""
import socket
import sys

def test_connection(host, port, description):
    """Test TCP connection to host:port"""
    print(f"\n{'='*50}")
    print(f"Testing: {description}")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"{'='*50}")

    try:
        # Create socket with 10 second timeout
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)

        # Attempt connection
        result = sock.connect_ex((host, port))
        sock.close()

        if result == 0:
            print(f"✅ SUCCESS: Connected to {host}:{port}")
            return True
        else:
            print(f"❌ FAILED: Could not connect to {host}:{port}")
            print(f"   Error code: {result}")
            return False

    except socket.gaierror as e:
        print(f"❌ DNS ERROR: Could not resolve {host}")
        print(f"   Error: {e}")
        return False
    except socket.timeout:
        print(f"❌ TIMEOUT: Connection to {host}:{port} timed out")
        return False
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "="*50)
    print("RAILWAY TO SUPABASE NETWORK CONNECTIVITY TEST")
    print("="*50)

    # Test configurations
    tests = [
        {
            "host": "db.isjvcytbwanionrtvplq.supabase.co",
            "port": 5432,
            "description": "Supabase Direct (PostgreSQL port 5432)"
        },
        {
            "host": "aws-0-us-east-1.pooler.supabase.com",
            "port": 6543,
            "description": "Supabase Pooler (port 6543)"
        },
        {
            "host": "db.isjvcytbwanionrtvplq.supabase.co",
            "port": 6543,
            "description": "Supabase Direct (Pooler port 6543)"
        }
    ]

    # Run tests
    results = []
    for test in tests:
        success = test_connection(test["host"], test["port"], test["description"])
        results.append(success)

    # Summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")

    if passed == 0:
        print("\n❌ CRITICAL: No connections succeeded")
        print("   Root cause: Railway likely blocks PostgreSQL ports")
        print("   Solution: Use Supabase REST API instead of direct PostgreSQL")
        sys.exit(1)
    elif passed < total:
        print("\n⚠️  WARNING: Some connections failed")
        print("   Review failed tests above")
        sys.exit(0)
    else:
        print("\n✅ SUCCESS: All network tests passed")
        print("   Network connectivity is OK")
        print("   Issue is likely at application layer")
        sys.exit(0)
