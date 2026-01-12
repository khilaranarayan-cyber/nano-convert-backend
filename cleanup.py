# cleanup.py
# A simple cleanup utility to remove expired objects from S3.
# This should ideally be run as a scheduled job (cron/Kubernetes CronJob/Render cron job).
# It lists objects under 'temp/' and 'output/' and deletes those older than JOB_TTL_SECONDS.

import logging
import time
import boto3
from botocore.config import Config
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cleanup")


def main():
    boto_config = Config(signature_version="s3v4", region_name=settings.s3_region)
    sess = boto3.session.Session()
    s3 = sess.client(
        "s3",
        endpoint_url=settings.s3_endpoint or None,
        aws_access_key_id=settings.s3_access_key_id or None,
        aws_secret_access_key=settings.s3_secret_access_key or None,
        config=boto_config,
    )
    bucket = settings.s3_bucket
    ttl_ms = settings.job_ttl_seconds * 1000
    now = int(time.time() * 1000)

    for prefix in ("temp/", "output/"):
        paginator = s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                last_modified = obj["LastModified"]
                # last_modified is datetime
                age = now - int(last_modified.timestamp() * 1000)
                if age > ttl_ms:
                    logger.info("Deleting expired object %s", key)
                    s3.delete_object(Bucket=bucket, Key=key)


if __name__ == "__main__":
    main()