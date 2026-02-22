"""Gemini AI 服务 — Prompt 结构化生成 + 素材图片生成"""

import base64
import os
import sys
import time
import uuid

from google import genai
from google.genai import types

import config
from services import asset_service
from utils.logger import logger


def _get_client():
    """获取 Gemini 客户端"""
    if not config.GEMINI_API_KEY:
        raise RuntimeError('未配置 GEMINI_API_KEY，请在 .env 文件中设置')
    return genai.Client(api_key=config.GEMINI_API_KEY)


# ── AI 生成五要素 Prompt ──────────────────────────────────────

PROMPT_SYSTEM = """你是一位顶级视频创意导演，精通 Seedance 2.0 的"导演法"提示词体系。

用户将给你一段简短的创意描述，你需要将其扩展为结构化的五要素 Prompt：

1. **subject（角色/主体）**：详细描述画面核心主体（人物外貌、衣着、物品形态等）
2. **scene（场景/环境）**：描述场景布局、光照、道具、环境氛围
3. **action（动作/变化）**：描述主体的动态行为、物体的运动变化
4. **camera（运镜/构图）**：描述镜头运动（推、拉、摇、移、跟、升降、环绕等）和角度
5. **atmosphere（氛围/风格）**：描述整体视觉风格（色调、光影、画质、配乐感觉）

要求：
- 每个要素 30-80 字，中文描述
- 描述应具体、有画面感、可直接用于 AI 视频生成
- 风格偏电影级质感"""


def generate_prompt(idea: str) -> dict:
    """
    根据用户创意描述，生成五要素结构化 Prompt。

    Args:
        idea: 用户的简短创意描述

    Returns:
        dict: {subject, scene, action, camera, atmosphere}
    """
    logger.info(f"正在使用 Gemini 生成五要素 Prompt: {idea[:50]}...")
    client = _get_client()

    response = client.models.generate_content(
        model=config.GEMINI_PROMPT_MODEL,
        contents=f'请根据以下创意描述，生成五要素结构化 Prompt：\n\n{idea}',
        config=types.GenerateContentConfig(
            system_instruction=PROMPT_SYSTEM,
            response_mime_type='application/json',
            response_schema={
                'type': 'OBJECT',
                'properties': {
                    'subject': {'type': 'STRING', 'description': '角色/主体描述'},
                    'scene': {'type': 'STRING', 'description': '场景/环境描述'},
                    'action': {'type': 'STRING', 'description': '动作/变化描述'},
                    'camera': {'type': 'STRING', 'description': '运镜/构图描述'},
                    'atmosphere': {'type': 'STRING', 'description': '氛围/风格描述'},
                },
                'required': ['subject', 'scene', 'action', 'camera', 'atmosphere'],
            },
            temperature=0.9,
        ),
    )

    import json
    try:
        return json.loads(response.text)
    except (json.JSONDecodeError, TypeError) as e:
        logger.error(f'AI Prompt 解析失败: {e}')
        raise RuntimeError(f'AI 返回格式异常: {e}')


# ── AI 生成素材图片 ───────────────────────────────────────────

def generate_image(prompt: str, aspect_ratio: str = '16:9') -> dict:
    """
    使用 Gemini 图片生成模型创建素材图片。

    Args:
        prompt: 图片描述（中/英文均可）
        aspect_ratio: 宽高比，如 "16:9", "1:1", "9:16"

    Returns:
        dict: 已保存的素材元数据
    """
    logger.info(f"正在使用 Gemini 生成图片素材: {prompt[:50]}...")
    client = _get_client()

    response = client.models.generate_content(
        model=config.GEMINI_IMAGE_MODEL,
        contents=f'请根据以下描述生成一张高质量图片：\n\n{prompt}',
        config=types.GenerateContentConfig(
            response_modalities=['IMAGE', 'TEXT'],
        ),
    )

    # 提取图片数据
    image_data = None
    mime_type = 'image/png'

    for part in response.candidates[0].content.parts:
        if part.inline_data:
            image_data = part.inline_data.data
            mime_type = part.inline_data.mime_type or 'image/png'
            break

    if not image_data:
        raise RuntimeError('AI 未返回图片数据')

    # 确定文件扩展名
    ext_map = {
        'image/png': '.png',
        'image/jpeg': '.jpg',
        'image/webp': '.webp',
    }
    ext = ext_map.get(mime_type, '.png')

    # 保存文件
    asset_id = str(uuid.uuid4())[:8]
    filename = f'ai_gen_{asset_id}{ext}'
    filepath = os.path.join(config.ASSETS_DIR, filename)

    # image_data 已经是 bytes
    if isinstance(image_data, str):
        raw_bytes = base64.b64decode(image_data)
    else:
        raw_bytes = image_data

    with open(filepath, 'wb') as f:
        f.write(raw_bytes)

    # 注册到素材库并生成缩略图
    from models.asset import Asset
    asset = Asset(
        asset_id=asset_id,
        name=f'AI 生成 - {prompt[:20]}',
        original_name=filename,
        file_path=filename,
        file_size=len(raw_bytes),
        asset_type=Asset.TYPE_IMAGE,
        tags=['AI生成'],
    )

    # 生成缩略图
    thumbnail_filename = asset_service.generate_thumbnail(filepath, asset_id, Asset.TYPE_IMAGE)
    asset.thumbnail_path = thumbnail_filename

    # 保存元数据
    from models.asset import AssetStore
    store = AssetStore()
    store.add(asset)

    return asset.to_dict()
