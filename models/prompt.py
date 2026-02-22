"""Prompt 五要素数据模型 — 对齐 Seedance 2.0 导演法结构"""

import json
import time
import uuid


class PromptElement:
    """单个提示词要素"""

    def __init__(self, label: str, key: str, placeholder: str, value: str = ''):
        self.label = label
        self.key = key
        self.placeholder = placeholder
        self.value = value

    def to_dict(self) -> dict:
        return {
            'label': self.label,
            'key': self.key,
            'placeholder': self.placeholder,
            'value': self.value,
        }


class SeedancePrompt:
    """Seedance Prompt 五要素模型

    五要素导演法:
    1. 角色指定 (subject)  — 主体描述：外貌、服装、表情
    2. 场景设定 (scene)    — 环境、时代、光照
    3. 动作/剧情 (action)  — 运动序列，支持多步描述
    4. 镜头语言 (camera)   — 推/拉/摇/移/环绕/跟随
    5. 氛围/声音 (atmosphere) — 风格、色调、音效、BGM
    """

    ELEMENTS = [
        PromptElement(
            '角色指定', 'subject',
            '描述主体：外貌特征、服装、表情、姿态。\n例：一位穿着红色汉服的年轻女子，长发飘逸，眼神温柔'
        ),
        PromptElement(
            '场景设定', 'scene',
            '描述环境：时代背景、地点、光照条件。\n例：19世纪的伦敦大街，黄昏暖光，街道两旁有维多利亚式建筑'
        ),
        PromptElement(
            '动作/剧情', 'action',
            '描述运动序列：主体动作、互动、时间顺序。\n例：她缓缓转身，微笑着向镜头走来，裙摆随风飘动'
        ),
        PromptElement(
            '镜头语言', 'camera',
            '描述运镜方式：推/拉/摇/移/环绕/跟随/升降。\n例：慢推镜头，从全景逐渐推进到面部特写'
        ),
        PromptElement(
            '氛围/声音', 'atmosphere',
            '描述风格、色调、音效。\n例：电影感，暖色调，背景有轻微虚化，柔和的钢琴配乐'
        ),
    ]

    def __init__(self):
        self.id = str(uuid.uuid4())[:8]
        self.name = ''
        self.created_at = time.time()
        self.updated_at = time.time()

        # 五要素
        self.subject = ''
        self.scene = ''
        self.action = ''
        self.camera = ''
        self.atmosphere = ''

        # 视频参数
        self.task_type = 'text2video'
        self.model = 'doubao-seedance-2-0-260128'
        self.resolution = '720p'
        self.duration = 5
        self.ratio = '16:9'

        # 素材引用
        self.ref_assets = []  # [{'id': ..., 'role': 'reference_image'}, ...]

    def build_prompt_text(self) -> str:
        """将五要素组合为最终 Prompt 文本"""
        parts = []
        if self.subject:
            parts.append(self.subject)
        if self.scene:
            parts.append(self.scene)
        if self.action:
            parts.append(self.action)
        if self.camera:
            parts.append(self.camera)
        if self.atmosphere:
            parts.append(self.atmosphere)
        return '，'.join(parts) if parts else ''

    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'subject': self.subject,
            'scene': self.scene,
            'action': self.action,
            'camera': self.camera,
            'atmosphere': self.atmosphere,
            'task_type': self.task_type,
            'model': self.model,
            'resolution': self.resolution,
            'duration': self.duration,
            'ratio': self.ratio,
            'ref_assets': self.ref_assets,
            'prompt_text': self.build_prompt_text(),
        }

    def to_api_payload(self) -> dict:
        """导出为 Seedance API 兼容的 JSON 格式"""
        payload = {
            'model': self.model,
            'content': [
                {'type': 'text', 'text': self.build_prompt_text()}
            ],
            'video_config': {
                'resolution': self.resolution,
                'duration': self.duration,
                'ratio': self.ratio,
                'fps': 24,
            }
        }
        # 添加素材引用
        for ref in self.ref_assets:
            payload['content'].append({
                'type': 'image_url' if ref.get('type') == 'image' else ref.get('type', 'image_url'),
                'image_url': {'url': ref.get('path', '')},
                'image_role': ref.get('role', 'reference_image'),
            })
        return payload

    @classmethod
    def from_dict(cls, data: dict) -> 'SeedancePrompt':
        """从字典反序列化"""
        prompt = cls()
        prompt.id = data.get('id', prompt.id)
        prompt.name = data.get('name', '')
        prompt.created_at = data.get('created_at', prompt.created_at)
        prompt.updated_at = data.get('updated_at', prompt.updated_at)
        prompt.subject = data.get('subject', '')
        prompt.scene = data.get('scene', '')
        prompt.action = data.get('action', '')
        prompt.camera = data.get('camera', '')
        prompt.atmosphere = data.get('atmosphere', '')
        prompt.task_type = data.get('task_type', 'text2video')
        prompt.model = data.get('model', 'doubao-seedance-2-0-260128')
        prompt.resolution = data.get('resolution', '720p')
        prompt.duration = data.get('duration', 5)
        prompt.ratio = data.get('ratio', '16:9')
        prompt.ref_assets = data.get('ref_assets', [])
        return prompt

    def save(self, filepath: str):
        """保存到 JSON 文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, filepath: str) -> 'SeedancePrompt':
        """从 JSON 文件加载"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return cls.from_dict(json.load(f))
