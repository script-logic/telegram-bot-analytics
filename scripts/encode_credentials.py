"""
Script for encoding Google Service Account JSON to base64.
Simplifies credentials setup for .env file.
"""

import base64
import json
import sys
from pathlib import Path


def print_usage():
    """Displays usage help."""
    print("📦 Google Service Account JSON to Base64 Encoder")
    print("\nUsage:")
    print("  python encode_credentials.py <path_to_json_file>")
    print("\nExamples:")
    print("  python encode_credentials.py credentials/service-account.json")
    print(
        "  python encode_credentials.py"
        " ~/Downloads/my-project-credentials.json"
    )
    print("\nHow to get JSON file:")
    print("  1. Go to Google Cloud Console")
    print("  2. Create Service Account")
    print("  3. Download JSON key")
    print("\nAfter encoding add output to .env file:")
    print("  GOOGLE_CREDENTIALS_BASE64=your_base64_string")


def validate_json(data: dict) -> bool:
    """Validates that JSON is a valid service account."""
    required_fields = [
        "type",
        "project_id",
        "private_key_id",
        "private_key",
        "client_email",
        "client_id",
    ]

    # Check required fields
    for field in required_fields:
        if field not in data:
            print(f"❌ Missing required field: {field}")
            return False

    # Check type
    if data.get("type") != "service_account":
        print(
            f"❌ Invalid type: {data.get('type')} (expected 'service_account')"
        )
        return False

    return True


def main():
    """Main script function."""
    if len(sys.argv) != 2:
        print_usage()
        sys.exit(1)

    json_path = Path(sys.argv[1])

    # Check if file exists
    if not json_path.exists():
        print(f"❌ File not found: {json_path}")
        print("   Check file path")
        sys.exit(1)

    # Check extension
    if json_path.suffix.lower() != ".json":
        print(
            f"⚠️  Warning: file has extension {json_path.suffix},"
            " expected .json"
        )

    try:
        # Read and parse JSON
        with open(
            json_path,
            encoding="utf-8",
        ) as f:
            json_data = json.load(f)

        # Validate JSON
        if not validate_json(json_data):
            print("\n❌ File is not a valid Google Service Account JSON")
            sys.exit(1)

        # Convert JSON to string (minified)
        json_str = json.dumps(
            json_data,
            separators=(
                ",",
                ":",
            ),
        )

        # Encode to base64
        base64_str = base64.b64encode(json_str.encode("utf-8")).decode("ascii")

        # Display result
        project_id = json_data.get(
            "project_id",
            "Not specified",
        )
        client_email = json_data.get(
            "client_email",
            "Not specified",
        )
        private_key_id = json_data.get(
            "private_key_id",
            "Not specified",
        )

        print("\n" + "=" * 70)
        print("✅ GOOGLE_CREDENTIALS_BASE64 successfully generated!")
        print("=" * 70)

        print("\n📋 Service Account information:")
        print(f"   Project: {project_id}")
        print(f"   Client Email: {client_email}")
        print(f"   Key ID: {private_key_id[:20]}...")

        print(f"\n📏 Base64 string length: {len(base64_str)} characters")

        print("\n🔐 Base64 string for .env file:")
        print("-" * 70)
        print(base64_str)
        print("-" * 70)

        print("\n📝 Instructions for adding to .env:")
        print("1. Open .env file in editor")
        print("2. Find line GOOGLE_CREDENTIALS_BASE64=")
        print("3. Replace value with string above")
        print("4. Save file")

        print("\n✨ Example line in .env:")
        print(f'GOOGLE_CREDENTIALS_BASE64="{base64_str}"')

        # Decoding test
        print("\n🧪 Testing decoding...")
        try:
            decoded = base64.b64decode(base64_str).decode("utf-8")
            decoded_json = json.loads(decoded)
            if decoded_json:
                print("✅ Base64 successfully decodes to valid JSON")
        except Exception as e:
            print(f"❌ Error during test: {e}")

        print("\n" + "=" * 70)

    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        print("   Ensure file contains valid JSON")
        sys.exit(1)
    except UnicodeDecodeError:
        print("❌ File encoding error")
        print("   Ensure file is UTF-8 encoded")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
