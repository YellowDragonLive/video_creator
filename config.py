"""Seedance 视频制作工具 - 全局配置"""

import os
from dotenv import load_dotenv

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 加载 .env 文件
load_dotenv(os.path.join(BASE_DIR, '.env'))

# Gemini AI 配置
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GEMINI_PROMPT_MODEL = 'gemini-2.5-flash'
GEMINI_IMAGE_MODEL = 'gemini-2.0-flash-preview-image-generation'

# 数据目录
DATA_DIR = os.path.join(BASE_DIR, 'data')
PROJECTS_DIR = os.path.join(DATA_DIR, 'projects')
ASSETS_DIR = os.path.join(DATA_DIR, 'assets')
THUMBNAILS_DIR = os.path.join(DATA_DIR, 'thumbnails')
LOGS_DIR = os.path.join(DATA_DIR, 'logs')
LOG_FILE = os.path.join(LOGS_DIR, 'app.log')

# Flask 配置
HOST = '0.0.0.0'
PORT = 5000
DEBUG = True

# 允许上传的文件类型
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'bmp', 'gif'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm'}
ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'aac', 'ogg', 'flac'}
ALLOWED_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | ALLOWED_VIDEO_EXTENSIONS | ALLOWED_AUDIO_EXTENSIONS

# 缩略图配置
THUMBNAIL_SIZE = (256, 256)

# Seedance 模型配置
SEEDANCE_MODELS = [
    {'id': 'doubao-seedance-2-0-260128', 'name': 'Seedance 2.0', 'recommended': True},
    {'id': 'doubao-seedance-1-5-pro', 'name': 'Seedance 1.5 Pro', 'recommended': False},
    {'id': 'doubao-seedance-1-0-pro', 'name': 'Seedance 1.0 Pro', 'recommended': False},
    {'id': 'doubao-seedance-1-0-pro-fast', 'name': 'Seedance 1.0 Pro Fast', 'recommended': False},
]

RESOLUTIONS = ['480p', '720p']
RATIOS = ['16:9', '4:3', '1:1', '9:16', '3:4']
FPS = 24
DURATION_RANGE = (2, 12)  # 秒

TASK_TYPES = [
    {'id': 'text2video', 'name': '文生视频', 'icon': '✍️'},
    {'id': 'image2video', 'name': '图生视频', 'icon': '🖼️'},
    {'id': 'video_edit', 'name': '视频编辑', 'icon': '✂️'},
    {'id': 'video_extend', 'name': '视频延长', 'icon': '⏩'},
]
