import boto3
import os
import json


def trigger_hls_transcode(video_id, s3_input_key):
    """
    Triggers an AWS MediaConvert job to convert an MP4 to HLS.
    Called after a video is uploaded to S3.
    """
    client = boto3.client(
        'mediaconvert',
        region_name=os.environ.get('AWS_S3_REGION_NAME', 'us-east-2'),
        endpoint_url=os.environ.get('AWS_MEDIACONVERT_ENDPOINT'),
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
    )

    bucket = os.environ.get('AWS_STORAGE_BUCKET_NAME')
    cloudfront_domain = os.environ.get('AWS_CLOUDFRONT_DOMAIN')

    input_s3_uri = f"s3://{bucket}/{s3_input_key}"
    output_s3_uri = f"s3://{bucket}/hls/{video_id}/"

    job_settings = {
        "Inputs": [
            {
                "FileInput": input_s3_uri,
                "AudioSelectors": {
                    "Audio Selector 1": {"DefaultSelection": "DEFAULT"}
                },
            }
        ],
        "OutputGroups": [
            {
                "Name": "Apple HLS",
                "OutputGroupSettings": {
                    "Type": "HLS_GROUP_SETTINGS",
                    "HlsGroupSettings": {
                        "Destination": output_s3_uri,
                        "SegmentLength": 6,          # 6 second chunks
                        "MinSegmentLength": 0,
                    },
                },
                "Outputs": [
                    # 1080p
                    {
                        "NameModifier": "_1080p",
                        "VideoDescription": {
                            "Width": 1920, "Height": 1080,
                            "CodecSettings": {
                                "Codec": "H_264",
                                "H264Settings": {"Bitrate": 5000000, "RateControlMode": "CBR"}
                            }
                        },
                        "AudioDescriptions": [{"CodecSettings": {"Codec": "AAC", "AacSettings": {"Bitrate": 128000}}}],
                        "OutputSettings": {"HlsSettings": {"SegmentModifier": "_1080p"}},
                        "ContainerSettings": {"Container": "M3U8"}
                    },
                    # 720p
                    {
                        "NameModifier": "_720p",
                        "VideoDescription": {
                            "Width": 1280, "Height": 720,
                            "CodecSettings": {
                                "Codec": "H_264",
                                "H264Settings": {"Bitrate": 2500000, "RateControlMode": "CBR"}
                            }
                        },
                        "AudioDescriptions": [{"CodecSettings": {"Codec": "AAC", "AacSettings": {"Bitrate": 128000}}}],
                        "OutputSettings": {"HlsSettings": {"SegmentModifier": "_720p"}},
                        "ContainerSettings": {"Container": "M3U8"}
                    },
                    # 480p
                    {
                        "NameModifier": "_480p",
                        "VideoDescription": {
                            "Width": 854, "Height": 480,
                            "CodecSettings": {
                                "Codec": "H_264",
                                "H264Settings": {"Bitrate": 1000000, "RateControlMode": "CBR"}
                            }
                        },
                        "AudioDescriptions": [{"CodecSettings": {"Codec": "AAC", "AacSettings": {"Bitrate": 96000}}}],
                        "OutputSettings": {"HlsSettings": {"SegmentModifier": "_480p"}},
                        "ContainerSettings": {"Container": "M3U8"}
                    },
                ],
            }
        ],
    }

    response = client.create_job(
        Role=os.environ.get('AWS_MEDIACONVERT_ROLE_ARN'),
        Settings=job_settings,
    )

    job_id = response['Job']['Id']

    # The master playlist URL via CloudFront
    hls_url = f"https://{cloudfront_domain}/hls/{video_id}/.m3u8"

    return job_id, hls_url