import sys
import os
from pathlib import Path

# Add generic sys.path append to find util
sys.path.append(str(Path(__file__).parent.parent))

from util.config import Config
from util.aws_helper import AWSHelper
from util.db_helper import DBHelper
from util.email_helper import EmailHelper

def test_config():
    print("Testing Config...")
    aws_config = Config.load_aws_config()
    print(f"AWS Config loaded: {bool(aws_config)}")
    
    db_config = Config.get_db_config()
    print(f"DB Config loaded: {bool(db_config)}")
    
    email_config = Config.get_email_config()
    print(f"Email Config loaded: {bool(email_config)}")

def test_aws_helper():
    print("\nTesting AWSHelper...")
    try:
        helper = AWSHelper()
        bedrock = helper.get_bedrock_client()
        print(f"Bedrock client created: {bool(bedrock)}")
        s3 = helper.get_s3_client()
        print(f"S3 client created: {bool(s3)}")
    except Exception as e:
        print(f"AWSHelper test failed: {e}")

def main():
    test_config()
    test_aws_helper()
    # verify imports of other helpers
    print("\nVerifying DB and Email helper imports...")
    try:
        DBHelper(None) # don't connect
        EmailHelper(None)
        print("Helpers instantiated successfully")
    except Exception as e:
        print(f"Helper instantiation failed: {e}")

if __name__ == "__main__":
    main()
