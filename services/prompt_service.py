"""Prompt 构建服务 — 模板管理、构建、导出"""

import json
import os
import time

from models.prompt import SeedancePrompt
import config
from utils.logger import logger


# ── 预置模板库 ──────────────────────────────────────────────────

TEMPLATES = [
    {
        'id': 'commercial_ad',
        'name': '🎬 商业广告',
        'description': '适用于产品展示、品牌宣传类短视频',
        'subject': '一瓶精致的香水瓶，瓶身晶莹剔透，金色瓶盖闪烁光泽',
        'scene': '纯白色大理石台面，背景是柔和的渐变光影，有花瓣和水珠点缀',
        'action': '香水瓶缓缓旋转展示，一滴水珠从瓶身滑落，花瓣随微风轻轻飘落',
        'camera': '慢速环绕镜头，从侧面360度旋转到正面，最后推进到瓶身标志特写',
        'atmosphere': '高端奢华质感，柔和暖光，浅景深虚化背景，4K超清画质',
        'task_type': 'text2video',
        'resolution': '720p',
        'duration': 5,
        'ratio': '16:9',
    },
    {
        'id': 'film_scene',
        'name': '🎥 影视制作',
        'description': '适用于影视片段、剧情短片、电影预告',
        'subject': '一位身穿深色风衣的男子，面容坚毅，站在雨中',
        'scene': '深夜的城市街道，霓虹灯倒映在湿漉漉的地面上，雨丝在灯光中清晰可见',
        'action': '男子缓缓抬起头，雨水从脸颊滑落，眼神中透露出坚定，然后转身大步走入黑暗',
        'camera': '低角度仰拍，缓慢推进到面部特写，然后切换到背影远景',
        'atmosphere': '电影感浓烈，冷色调，强烈明暗对比，背景有低沉的大提琴配乐',
        'task_type': 'text2video',
        'resolution': '720p',
        'duration': 8,
        'ratio': '16:9',
    },
    {
        'id': 'social_media',
        'name': '📱 社交媒体',
        'description': '适用于抖音、小红书等短视频平台',
        'subject': '一只可爱的橘猫，毛茸茸的，大眼睛，戴着一顶小帽子',
        'scene': '温馨的家庭客厅，阳光透过窗帘洒进来，沙发上放着柔软的靠垫',
        'action': '猫咪对着镜头打了个大哈欠，然后懒洋洋地翻了个身，露出肚皮，四脚朝天',
        'camera': '固定近景镜头，稍微俯拍，保持猫咪始终在画面中心',
        'atmosphere': '温馨治愈风格，暖色调，自然光线，背景有轻快的吉他旋律',
        'task_type': 'text2video',
        'resolution': '720p',
        'duration': 4,
        'ratio': '9:16',
    },
    {
        'id': 'ancient_china',
        'name': '🏯 古风国潮',
        'description': '适用于中国风、国潮、汉服展示类视频',
        'subject': '一位穿着白色汉服的年轻女子，发髻高挽，簪花点缀，手持纸伞',
        'scene': '烟雨朦胧的江南水乡，白墙黛瓦，石桥流水，远处有模糊的亭台楼阁',
        'action': '女子撑伞沿着石板路缓缓走来，裙摆轻拂地面，偶尔低头微笑，纸伞上滑落雨珠',
        'camera': '缓慢跟随镜头，从远景逐渐推近到半身特写，保持平稳运动',
        'atmosphere': '水墨画风格，淡雅色调，烟雨朦胧感，背景有古琴悠扬乐声',
        'task_type': 'text2video',
        'resolution': '720p',
        'duration': 6,
        'ratio': '16:9',
    },
    {
        'id': 'product_demo',
        'name': '📦 产品演示',
        'description': '适用于电商产品展示、开箱视频',
        'subject': '一款全新的无线耳机，白色磨砂质感外壳，耳机盒半开状态',
        'scene': '极简灰色背景桌面，柔和的侧光照射，轻微的阴影勾勒出产品轮廓',
        'action': '耳机盒盖缓缓打开，耳机自动升起，LED指示灯亮起蓝色光芒',
        'camera': '微距特写镜头，从正面缓慢推进，对焦从盒体转移到耳机细节',
        'atmosphere': '科技感，干净利落，冷白色调，未来主义光影效果',
        'task_type': 'text2video',
        'resolution': '720p',
        'duration': 5,
        'ratio': '16:9',
    },
]


def get_templates() -> list[dict]:
    """获取所有预置模板"""
    return TEMPLATES


def get_template(template_id: str) -> dict | None:
    """根据 ID 获取指定模板"""
    for t in TEMPLATES:
        if t['id'] == template_id:
            return t
    return None


def build_prompt(data: dict) -> str:
    """将五要素数据组合为 Prompt 文本"""
    prompt = SeedancePrompt.from_dict(data)
    return prompt.build_prompt_text()


def export_prompt(data: dict) -> dict:
    """将 Prompt 数据导出为 Seedance API 兼容格式"""
    prompt = SeedancePrompt.from_dict(data)
    return prompt.to_api_payload()


def save_project(data: dict) -> str:
    """保存 Prompt 项目到本地"""
    prompt = SeedancePrompt.from_dict(data)
    if not prompt.name:
        prompt.name = f'项目_{prompt.id}'
    prompt.updated_at = time.time()

    filepath = os.path.join(config.PROJECTS_DIR, f'{prompt.id}.json')
    prompt.save(filepath)
    logger.info(f"项目已保存: {prompt.name} (ID: {prompt.id})")
    return prompt.id


def load_project(project_id: str) -> dict | None:
    """加载指定项目"""
    filepath = os.path.join(config.PROJECTS_DIR, f'{project_id}.json')
    if os.path.exists(filepath):
        prompt = SeedancePrompt.load(filepath)
        return prompt.to_dict()
    return None


def list_projects() -> list[dict]:
    """列出所有已保存的项目"""
    projects = []
    if not os.path.exists(config.PROJECTS_DIR):
        return projects

    for filename in os.listdir(config.PROJECTS_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(config.PROJECTS_DIR, filename)
            try:
                prompt = SeedancePrompt.load(filepath)
                projects.append({
                    'id': prompt.id,
                    'name': prompt.name,
                    'task_type': prompt.task_type,
                    'created_at': prompt.created_at,
                    'updated_at': prompt.updated_at,
                })
            except Exception:
                pass

    projects.sort(key=lambda x: x['updated_at'], reverse=True)
    return projects


def delete_project(project_id: str) -> bool:
    """删除项目"""
    filepath = os.path.join(config.PROJECTS_DIR, f'{project_id}.json')
    if os.path.exists(filepath):
        os.remove(filepath)
        logger.info(f"项目已删除: {project_id}")
        return True
    return False
