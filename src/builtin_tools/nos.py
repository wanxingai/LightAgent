import hashlib
import json
import os
import traceback
from typing import Optional
import boto3
from botocore.client import Config

# 阿里云OSS配置（建议从环境变量读取，避免硬编码）
# 您可以在环境变量中设置以下值，或在创建Agent时传入
ALIYUN_OSS_CONFIG = {
    "access_key_id": "**********",
    "access_key_secret": "*****************",
    "endpoint": "https://oss-cn-shanghai.aliyuncs.com",
    "bucket_name": "wxuserfile"
}


def _get_oss_client(access_key_id: str = None, access_key_secret: str = None, endpoint: str = None):
    """
    获取OSS客户端实例

    Args:
        access_key_id: 阿里云AccessKey ID
        access_key_secret: 阿里云AccessKey Secret
        endpoint: OSS endpoint

    Returns:
        boto3 S3客户端实例
    """
    # 使用传入的参数或环境变量中的默认值
    ak = access_key_id or ALIYUN_OSS_CONFIG["access_key_id"]
    sk = access_key_secret or ALIYUN_OSS_CONFIG["access_key_secret"]
    ep = endpoint or ALIYUN_OSS_CONFIG["endpoint"]

    if not ak or not sk:
        raise ValueError(
            "未设置阿里云AccessKey，请通过参数传入或设置环境变量ALIYUN_OSS_ACCESS_KEY_ID和ALIYUN_OSS_ACCESS_KEY_SECRET")

    # 创建OSS客户端（兼容S3协议）
    client = boto3.client(
        's3',
        aws_access_key_id=ak,
        aws_secret_access_key=sk,
        endpoint_url=ep,
        config=Config(signature_version='s3v4')  # 使用v4签名
    )

    return client


def _calculate_md5(file_path: str) -> str:
    """
    计算文件的MD5值

    Args:
        file_path: 文件路径

    Returns:
        文件的MD5哈希值
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def upload_file_to_oss(
        file_path: str,
        bucket_name: str = None,
        access_key_id: str = None,
        access_key_secret: str = None,
        endpoint: str = None,
        preserve_original_name: bool = False,
        prefix: str = "",
        public_read: bool = False
) -> str:
    """
    上传文件到阿里云OSS

    Args:
        file_path: 要上传的本地文件路径
        bucket_name: OSS存储桶名称
        access_key_id: 阿里云AccessKey ID
        access_key_secret: 阿里云AccessKey Secret
        endpoint: OSS endpoint
        preserve_original_name: 是否保留原文件名（如果False，则使用MD5重命名）
        prefix: 文件在OSS中的前缀路径
        public_read: 是否设置文件为公共读

    Returns:
        上传成功后的文件URL或错误信息
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return f"错误：文件 '{file_path}' 不存在"

        if not os.path.isfile(file_path):
            return f"错误：'{file_path}' 不是文件"

        # 获取文件名和后缀
        original_filename = os.path.basename(file_path)
        file_name, file_ext = os.path.splitext(original_filename)

        # 计算MD5值作为新文件名
        if preserve_original_name:
            oss_filename = original_filename
        else:
            file_md5 = _calculate_md5(file_path)
            oss_filename = f"{file_md5}{file_ext}"

        # 构建OSS中的完整路径
        if prefix and not prefix.endswith('/'):
            prefix += '/'
        oss_key = f"{prefix}{oss_filename}" if prefix else oss_filename

        # 获取OSS客户端
        bucket = bucket_name or ALIYUN_OSS_CONFIG["bucket_name"]
        client = _get_oss_client(access_key_id, access_key_secret, endpoint)

        # 设置上传参数
        extra_args = {}
        if public_read:
            extra_args['ACL'] = 'public-read'

        # 上传文件
        print(f"正在上传文件到OSS: {oss_key}")
        client.upload_file(
            Filename=file_path,
            Bucket=bucket,
            Key=oss_key,
            ExtraArgs=extra_args if extra_args else None
        )

        # 生成文件URL
        endpoint_clean = endpoint or ALIYUN_OSS_CONFIG["endpoint"]
        if endpoint_clean.startswith('http://') or endpoint_clean.startswith('https://'):
            base_url = endpoint_clean.rstrip('/')
        else:
            base_url = f"https://{endpoint_clean}"

        file_url = f"{base_url}/{bucket}/{oss_key}"

        result = {
            "success": True,
            "file_url": file_url,
            "bucket": bucket,
            "key": oss_key,
            "original_filename": original_filename,
            "oss_filename": oss_filename,
            "file_size": os.path.getsize(file_path),
            "md5": _calculate_md5(file_path) if not preserve_original_name else None
        }

        return json.dumps(result, ensure_ascii=False, indent=2)

    except ImportError as e:
        return f"错误：缺少必要的依赖库，请安装：pip install boto3\n详细信息：{str(e)}"
    except Exception as e:
        return f"上传文件到OSS失败：{str(e)}\n{traceback.format_exc()}"


# 添加工具信息
upload_file_to_oss.tool_info = {
    "tool_name": "upload_file_to_oss",
    "tool_title": "上传文件到阿里云OSS",
    "tool_description": "将本地文件上传到阿里云OSS，自动使用MD5重命名文件，支持设置公共读权限",
    "tool_params": [
        {
            "name": "file_path",
            "description": "要上传的本地文件路径",
            "type": "string",
            "required": True
        }
    ]
}
