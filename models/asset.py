"""素材元数据模型"""

import json
import os
import time
import uuid


class Asset:
    """素材资源模型"""

    TYPE_IMAGE = 'image'
    TYPE_VIDEO = 'video'
    TYPE_AUDIO = 'audio'

    IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'bmp', 'gif'}
    VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm'}
    AUDIO_EXTENSIONS = {'mp3', 'wav', 'aac', 'ogg', 'flac'}

    def __init__(self):
        self.id = str(uuid.uuid4())[:8]
        self.name = ''
        self.original_name = ''
        self.type = self.TYPE_IMAGE
        self.path = ''
        self.thumbnail_path = ''
        self.tags = []
        self.description = ''
        self.created_at = time.time()
        self.file_size = 0  # bytes

    @staticmethod
    def detect_type(filename: str) -> str:
        """根据文件扩展名判断素材类型"""
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        if ext in Asset.IMAGE_EXTENSIONS:
            return Asset.TYPE_IMAGE
        elif ext in Asset.VIDEO_EXTENSIONS:
            return Asset.TYPE_VIDEO
        elif ext in Asset.AUDIO_EXTENSIONS:
            return Asset.TYPE_AUDIO
        return Asset.TYPE_IMAGE  # 默认

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'original_name': self.original_name,
            'type': self.type,
            'path': self.path,
            'thumbnail_path': self.thumbnail_path,
            'tags': self.tags,
            'description': self.description,
            'created_at': self.created_at,
            'file_size': self.file_size,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Asset':
        asset = cls()
        asset.id = data.get('id', asset.id)
        asset.name = data.get('name', '')
        asset.original_name = data.get('original_name', '')
        asset.type = data.get('type', cls.TYPE_IMAGE)
        asset.path = data.get('path', '')
        asset.thumbnail_path = data.get('thumbnail_path', '')
        asset.tags = data.get('tags', [])
        asset.description = data.get('description', '')
        asset.created_at = data.get('created_at', time.time())
        asset.file_size = data.get('file_size', 0)
        return asset


class AssetStore:
    """素材仓库 — JSON 文件存储"""

    def __init__(self, store_path: str):
        self.store_path = store_path
        self.assets: list[Asset] = []
        self._load()

    def _load(self):
        if os.path.exists(self.store_path):
            with open(self.store_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.assets = [Asset.from_dict(a) for a in data.get('assets', [])]
        else:
            self.assets = []

    def _save(self):
        os.makedirs(os.path.dirname(self.store_path), exist_ok=True)
        with open(self.store_path, 'w', encoding='utf-8') as f:
            json.dump(
                {'assets': [a.to_dict() for a in self.assets]},
                f, ensure_ascii=False, indent=2
            )

    def add(self, asset: Asset):
        self.assets.append(asset)
        self._save()

    def remove(self, asset_id: str) -> bool:
        before = len(self.assets)
        self.assets = [a for a in self.assets if a.id != asset_id]
        if len(self.assets) < before:
            self._save()
            return True
        return False

    def get(self, asset_id: str) -> Asset | None:
        for a in self.assets:
            if a.id == asset_id:
                return a
        return None

    def list_all(self) -> list[dict]:
        return [a.to_dict() for a in self.assets]

    def search(self, query: str = '', tag: str = '', asset_type: str = '') -> list[dict]:
        results = self.assets
        if query:
            q = query.lower()
            results = [a for a in results if q in a.name.lower() or q in a.description.lower()]
        if tag:
            results = [a for a in results if tag in a.tags]
        if asset_type:
            results = [a for a in results if a.type == asset_type]
        return [a.to_dict() for a in results]

    def update_tags(self, asset_id: str, tags: list[str]) -> bool:
        asset = self.get(asset_id)
        if asset:
            asset.tags = tags
            self._save()
            return True
        return False
