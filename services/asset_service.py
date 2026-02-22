"""素材管理服务 — 导入、缩略图、分类"""

import os
import shutil
import subprocess
import sys

from models.asset import Asset, AssetStore
import config
from utils.logger import logger

# 素材仓库单例
_store: AssetStore | None = None


def get_store() -> AssetStore:
    """获取素材仓库实例"""
    global _store
    if _store is None:
        store_path = os.path.join(config.DATA_DIR, 'asset_store.json')
        _store = AssetStore(store_path)
    return _store


def import_asset(file_storage, original_filename: str) -> dict:
    """导入素材文件

    Args:
        file_storage: Flask FileStorage 对象
        original_filename: 原始文件名

    Returns:
        素材信息字典
    """
    store = get_store()

    # 创建素材对象
    asset = Asset()
    asset.original_name = original_filename
    asset.name = os.path.splitext(original_filename)[0]
    asset.type = Asset.detect_type(original_filename)

    # 保存文件
    ext = original_filename.rsplit('.', 1)[-1].lower() if '.' in original_filename else 'bin'
    saved_filename = f'{asset.id}.{ext}'
    saved_path = os.path.join(config.ASSETS_DIR, saved_filename)
    logger.info(f"正在导入素材: {original_filename} (类型: {asset.type})")
    os.makedirs(config.ASSETS_DIR, exist_ok=True)
    file_storage.save(saved_path)

    asset.path = saved_filename
    asset.file_size = os.path.getsize(saved_path)

    # 生成缩略图
    thumbnail_filename = generate_thumbnail(saved_path, asset.id, asset.type)
    asset.thumbnail_path = thumbnail_filename

    # 存入仓库
    store.add(asset)

    return asset.to_dict()


def generate_thumbnail(source_path: str, asset_id: str, asset_type: str) -> str:
    """生成缩略图

    Args:
        source_path: 源文件路径
        asset_id: 素材 ID
        asset_type: 素材类型

    Returns:
        缩略图文件名
    """
    os.makedirs(config.THUMBNAILS_DIR, exist_ok=True)
    thumbnail_filename = f'{asset_id}_thumb.jpg'
    thumbnail_path = os.path.join(config.THUMBNAILS_DIR, thumbnail_filename)

    try:
        if asset_type == Asset.TYPE_IMAGE:
            _thumbnail_image(source_path, thumbnail_path)
        elif asset_type == Asset.TYPE_VIDEO:
            _thumbnail_video(source_path, thumbnail_path)
        elif asset_type == Asset.TYPE_AUDIO:
            _thumbnail_audio(thumbnail_path)
    except Exception as e:
        logger.error(f'缩略图生成失败 ({asset_id}): {e}')
        _thumbnail_placeholder(thumbnail_path, asset_type)

    return thumbnail_filename


def _thumbnail_image(source: str, dest: str):
    """图片缩略图 — 使用 Pillow"""
    from PIL import Image
    with Image.open(source) as img:
        img.thumbnail(config.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        img.save(dest, 'JPEG', quality=85)


def _thumbnail_video(source: str, dest: str):
    """视频缩略图 — 提取首帧 (通过 ffmpeg subprocess)"""
    try:
        subprocess.run(
            ['ffmpeg', '-i', source, '-vframes', '1', '-q:v', '2',
             '-vf', f'scale={config.THUMBNAIL_SIZE[0]}:{config.THUMBNAIL_SIZE[1]}:force_original_aspect_ratio=decrease',
             '-y', dest],
            check=True, capture_output=True, timeout=10
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        _thumbnail_placeholder(dest, Asset.TYPE_VIDEO)


def _thumbnail_audio(dest: str):
    """音频占位缩略图"""
    _thumbnail_placeholder(dest, Asset.TYPE_AUDIO)


def _thumbnail_placeholder(dest: str, asset_type: str):
    """生成占位缩略图"""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new('RGB', config.THUMBNAIL_SIZE, color='#1a1a2e')
    draw = ImageDraw.Draw(img)

    icons = {
        Asset.TYPE_IMAGE: '🖼️',
        Asset.TYPE_VIDEO: '🎬',
        Asset.TYPE_AUDIO: '🎵',
    }
    icon = icons.get(asset_type, '📁')

    # 画一个简单的标识
    try:
        draw.text(
            (config.THUMBNAIL_SIZE[0] // 2, config.THUMBNAIL_SIZE[1] // 2),
            icon, fill='white', anchor='mm'
        )
    except Exception:
        # 如果 emoji 渲染失败，画文字
        label = {'image': 'IMG', 'video': 'VID', 'audio': 'AUD'}.get(asset_type, 'FILE')
        draw.text(
            (config.THUMBNAIL_SIZE[0] // 2, config.THUMBNAIL_SIZE[1] // 2),
            label, fill='white', anchor='mm'
        )

    img.save(dest, 'JPEG', quality=85)


def list_assets(query: str = '', tag: str = '', asset_type: str = '') -> list[dict]:
    """列出/搜索素材"""
    store = get_store()
    return store.search(query=query, tag=tag, asset_type=asset_type)


def get_asset(asset_id: str) -> dict | None:
    """获取单个素材信息"""
    store = get_store()
    asset = store.get(asset_id)
    return asset.to_dict() if asset else None


def delete_asset(asset_id: str) -> bool:
    """删除素材及其文件"""
    store = get_store()
    asset = store.get(asset_id)
    if not asset:
        return False

    # 删除文件
    asset_path = os.path.join(config.ASSETS_DIR, asset.path)
    if os.path.exists(asset_path):
        os.remove(asset_path)

    thumb_path = os.path.join(config.THUMBNAILS_DIR, asset.thumbnail_path)
    if os.path.exists(thumb_path):
        os.remove(thumb_path)

    return store.remove(asset_id)


def update_asset_tags(asset_id: str, tags: list[str]) -> bool:
    """更新素材标签"""
    store = get_store()
    return store.update_tags(asset_id, tags)


def get_all_tags() -> list[str]:
    """获取所有已使用的标签"""
    store = get_store()
    tags = set()
    for asset in store.assets:
        tags.update(asset.tags)
    return sorted(tags)
