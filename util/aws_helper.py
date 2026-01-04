import boto3
import json
from typing import Dict, Any, Optional
from .config import Config

class AWSHelper:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or Config.load_aws_config()
        self._bedrock_client = None
        self._s3_client = None

    def _get_client(self, service: str, region_name: str = 'ap-south-1'):
        """Helper to create boto3 client"""
        if not self.config:
            # Fallback to default boto3 credential chain
            return boto3.client(service, region_name=region_name)
            
        # Support nested config (e.g. config['bedrock']) or flat config
        service_config = self.config.get(service)
        
        # Special case for bedrock-runtime -> bedrock config key
        if not service_config and (service == 'bedrock_runtime' or service == 'bedrock-runtime'):
            service_config = self.config.get('bedrock')
            
        # If still not found, try to use the root config (flat structure)
        if not service_config:
            service_config = self.config

        session = boto3.Session(
            aws_access_key_id=service_config.get('aws_access_key_id'),
            aws_secret_access_key=service_config.get('aws_secret_access_key'),
            region_name=region_name
        )
        return session.client(service)

    def get_bedrock_client(self, region_name: str = 'ap-south-1'):
        if not self._bedrock_client:
            service_name = 'bedrock-runtime'
            self._bedrock_client = self._get_client(service_name, region_name)
        return self._bedrock_client

    def get_s3_client(self, region_name: str = 'ap-south-1'):
        if not self._s3_client:
            self._s3_client = self._get_client('s3', region_name)
        return self._s3_client

    def converse(self, messages: list, model_id: str, temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """
        Generic wrapper for Bedrock Converse API
        """
        client = self.get_bedrock_client()
        try:
            response = client.converse(
                modelId=model_id,
                messages=messages,
                inferenceConfig={
                    "maxTokens": max_tokens,
                    "temperature": temperature
                }
            )
            return response['output']['message']['content'][0]['text']
        except Exception as e:
            print(f"Error invoking Bedrock converse: {e}")
            raise

    def upload_file(self, file_path: str, bucket_name: str, object_name: str, content_type: str = None):
        """
        Upload a file to an S3 bucket
        """
        client = self.get_s3_client()
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type
            
        try:
            client.upload_file(file_path, bucket_name, object_name, ExtraArgs=extra_args)
            return True
        except Exception as e:
            print(f"Error uploading file to S3: {e}")
            return False
