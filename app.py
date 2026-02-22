"""Seedance 视频制作工具 — Flask 主入口"""

import json
import os
import sys

from flask import Flask, render_template, request, jsonify, send_from_directory

import config
from services import prompt_service, asset_service, gemini_service
from utils.logger import logger

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB

# 确保目录存在
for d in [config.PROJECTS_DIR, config.ASSETS_DIR, config.THUMBNAILS_DIR, config.LOGS_DIR]:
    os.makedirs(d, exist_ok=True)


# ── 全局异常捕获 ──────────────────────────────────────────────

@app.errorhandler(Exception)
def handle_exception(e):
    """记录所有未处理的异常到日志"""
    logger.error(f"未处理的全局异常: {str(e)}", exc_info=True)
    return jsonify({"error": "服务器内部错误，请检查日志", "details": str(e)}), 500


# ── 页面路由 ──────────────────────────────────────────────────

@app.route('/')
def index():
    """Prompt 编辑器首页"""
    return render_template('prompt_editor.html',
                           templates=prompt_service.get_templates(),
                           models=config.SEEDANCE_MODELS,
                           resolutions=config.RESOLUTIONS,
                           ratios=config.RATIOS,
                           task_types=config.TASK_TYPES,
                           duration_range=config.DURATION_RANGE)


@app.route('/assets')
def assets_page():
    """素材管理页面"""
    return render_template('asset_manager.html')


# ── Prompt API ────────────────────────────────────────────────

@app.route('/api/prompts', methods=['POST'])
def save_prompt():
    """保存 Prompt 项目"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '无效的请求数据'}), 400
    project_id = prompt_service.save_project(data)
    return jsonify({'id': project_id, 'message': '保存成功'})


@app.route('/api/prompts', methods=['GET'])
def list_prompts():
    """获取 Prompt 项目列表"""
    projects = prompt_service.list_projects()
    return jsonify({'projects': projects})


@app.route('/api/prompts/<project_id>', methods=['GET'])
def get_prompt(project_id):
    """获取指定 Prompt 项目"""
    project = prompt_service.load_project(project_id)
    if project:
        return jsonify(project)
    return jsonify({'error': '项目不存在'}), 404


@app.route('/api/prompts/<project_id>', methods=['DELETE'])
def delete_prompt(project_id):
    """删除 Prompt 项目"""
    if prompt_service.delete_project(project_id):
        return jsonify({'message': '删除成功'})
    return jsonify({'error': '项目不存在'}), 404


@app.route('/api/prompts/build', methods=['POST'])
def build_prompt():
    """构建 Prompt 文本"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '无效的请求数据'}), 400
    text = prompt_service.build_prompt(data)
    return jsonify({'prompt_text': text})


@app.route('/api/prompts/export', methods=['POST'])
def export_prompt():
    """导出为 API 格式"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '无效的请求数据'}), 400
    payload = prompt_service.export_prompt(data)
    return jsonify({'api_payload': payload})


@app.route('/api/templates', methods=['GET'])
def get_templates():
    """获取模板列表"""
    return jsonify({'templates': prompt_service.get_templates()})


@app.route('/api/templates/<template_id>', methods=['GET'])
def get_template(template_id):
    """获取指定模板"""
    template = prompt_service.get_template(template_id)
    if template:
        return jsonify(template)
    return jsonify({'error': '模板不存在'}), 404


# ── 素材 API ──────────────────────────────────────────────────

@app.route('/api/assets/upload', methods=['POST'])
def upload_asset():
    """上传素材"""
    if 'file' not in request.files:
        return jsonify({'error': '未找到文件'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'error': '文件名为空'}), 400

    # 检查文件类型
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in config.ALLOWED_EXTENSIONS:
        return jsonify({'error': f'不支持的文件类型: .{ext}'}), 400

    asset_data = asset_service.import_asset(file, file.filename)
    return jsonify({'asset': asset_data, 'message': '上传成功'})


@app.route('/api/assets', methods=['GET'])
def list_assets():
    """列出素材"""
    query = request.args.get('q', '')
    tag = request.args.get('tag', '')
    asset_type = request.args.get('type', '')
    assets = asset_service.list_assets(query=query, tag=tag, asset_type=asset_type)
    return jsonify({'assets': assets})


@app.route('/api/assets/<asset_id>', methods=['GET'])
def get_asset(asset_id):
    """获取素材详情"""
    asset = asset_service.get_asset(asset_id)
    if asset:
        return jsonify(asset)
    return jsonify({'error': '素材不存在'}), 404


@app.route('/api/assets/<asset_id>', methods=['DELETE'])
def delete_asset(asset_id):
    """删除素材"""
    if asset_service.delete_asset(asset_id):
        return jsonify({'message': '删除成功'})
    return jsonify({'error': '素材不存在'}), 404


@app.route('/api/assets/<asset_id>/tags', methods=['PUT'])
def update_asset_tags(asset_id):
    """更新素材标签"""
    data = request.get_json()
    tags = data.get('tags', []) if data else []
    if asset_service.update_asset_tags(asset_id, tags):
        return jsonify({'message': '标签更新成功'})
    return jsonify({'error': '素材不存在'}), 404


@app.route('/api/assets/tags', methods=['GET'])
def get_all_tags():
    """获取所有标签"""
    tags = asset_service.get_all_tags()
    return jsonify({'tags': tags})


# ── AI API ────────────────────────────────────────────────────

@app.route('/api/ai/generate-prompt', methods=['POST'])
def ai_generate_prompt():
    """AI 生成五要素 Prompt"""
    data = request.get_json()
    idea = data.get('idea', '').strip() if data else ''
    if not idea:
        return jsonify({'error': '请输入创意描述'}), 400

    try:
        result = gemini_service.generate_prompt(idea)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'AI 生成失败: {str(e)}'}), 500


@app.route('/api/ai/generate-image', methods=['POST'])
def ai_generate_image():
    """AI 生成素材图片"""
    data = request.get_json()
    prompt = data.get('prompt', '').strip() if data else ''
    if not prompt:
        return jsonify({'error': '请输入图片描述'}), 400

    aspect_ratio = data.get('aspect_ratio', '16:9')

    try:
        asset = gemini_service.generate_image(prompt, aspect_ratio)
        return jsonify({'asset': asset, 'message': 'AI 素材生成成功'})
    except Exception as e:
        return jsonify({'error': f'AI 图片生成失败: {str(e)}'}), 500


# ── 静态文件服务 ──────────────────────────────────────────────

@app.route('/data/thumbnails/<filename>')
def serve_thumbnail(filename):
    """提供缩略图访问"""
    return send_from_directory(config.THUMBNAILS_DIR, filename)


@app.route('/data/assets/<filename>')
def serve_asset(filename):
    """提供素材文件访问"""
    return send_from_directory(config.ASSETS_DIR, filename)


# ── 入口 ──────────────────────────────────────────────────────

if __name__ == '__main__':
    logger.info('🎬 Seedance 视频制作工具启动中...')
    logger.info(f'📁 项目根目录: {config.BASE_DIR}')
    logger.info(f'🌐 访问地址: http://{config.HOST}:{config.PORT}')
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
