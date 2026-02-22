/* ═══════════════════════════════════════════════════════
   prompt.js — Prompt 编辑器交互逻辑
   ═══════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {
    const state = {
        currentProjectId: null,
        subject: '',
        scene: '',
        action: '',
        camera: '',
        atmosphere: '',
        task_type: 'text2video',
        model: 'doubao-seedance-2-0-260128',
        resolution: '720p',
        ratio: '16:9',
        duration: 5,
        ref_assets: [],
    };

    // ── DOM 元素 ─────────────────────────────────────
    const inputs = {
        subject: document.getElementById('input-subject'),
        scene: document.getElementById('input-scene'),
        action: document.getElementById('input-action'),
        camera: document.getElementById('input-camera'),
        atmosphere: document.getElementById('input-atmosphere'),
    };

    const params = {
        taskType: document.getElementById('param-task-type'),
        model: document.getElementById('param-model'),
        duration: document.getElementById('param-duration'),
        durationDisplay: document.getElementById('duration-display'),
    };

    const preview = {
        text: document.getElementById('preview-text'),
        json: document.getElementById('preview-json'),
        metaModel: document.getElementById('meta-model'),
        metaTask: document.getElementById('meta-task'),
        metaResolution: document.getElementById('meta-resolution'),
        metaRatio: document.getElementById('meta-ratio'),
        metaDuration: document.getElementById('meta-duration'),
    };

    // ── 五要素输入监听 ───────────────────────────────
    Object.keys(inputs).forEach(key => {
        inputs[key].addEventListener('input', () => {
            state[key] = inputs[key].value;
            updatePreview();
        });
    });

    // ── 参数监听 ─────────────────────────────────────
    params.taskType.addEventListener('change', () => {
        state.task_type = params.taskType.value;
        updatePreview();
    });

    params.model.addEventListener('change', () => {
        state.model = params.model.value;
        updatePreview();
    });

    params.duration.addEventListener('input', () => {
        state.duration = parseInt(params.duration.value);
        params.durationDisplay.textContent = state.duration;
        updatePreview();
    });

    // 分辨率 chips
    document.getElementById('param-resolution').addEventListener('click', (e) => {
        const chip = e.target.closest('.chip');
        if (!chip) return;
        document.querySelectorAll('#param-resolution .chip').forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        state.resolution = chip.dataset.value;
        updatePreview();
    });

    // 宽高比 chips
    document.getElementById('param-ratio').addEventListener('click', (e) => {
        const chip = e.target.closest('.chip');
        if (!chip) return;
        document.querySelectorAll('#param-ratio .chip').forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        state.ratio = chip.dataset.value;
        updatePreview();
    });

    // ── 模板加载 ─────────────────────────────────────
    document.getElementById('template-chips').addEventListener('click', async (e) => {
        const chip = e.target.closest('.chip');
        if (!chip) return;
        const templateId = chip.dataset.templateId;

        try {
            const template = await api.get(`/api/templates/${templateId}`);
            // 填充五要素
            ['subject', 'scene', 'action', 'camera', 'atmosphere'].forEach(key => {
                if (template[key]) {
                    state[key] = template[key];
                    inputs[key].value = template[key];
                }
            });
            // 填充参数
            if (template.task_type) {
                state.task_type = template.task_type;
                params.taskType.value = template.task_type;
            }
            if (template.resolution) {
                state.resolution = template.resolution;
                document.querySelectorAll('#param-resolution .chip').forEach(c => {
                    c.classList.toggle('active', c.dataset.value === template.resolution);
                });
            }
            if (template.ratio) {
                state.ratio = template.ratio;
                document.querySelectorAll('#param-ratio .chip').forEach(c => {
                    c.classList.toggle('active', c.dataset.value === template.ratio);
                });
            }
            if (template.duration) {
                state.duration = template.duration;
                params.duration.value = template.duration;
                params.durationDisplay.textContent = template.duration;
            }

            updatePreview();
            Toast.success(`已加载模板: ${template.name}`);
        } catch (err) {
            Toast.error(`加载模板失败: ${err.message}`);
        }
    });

    // ── 预览更新 ─────────────────────────────────────
    function updatePreview() {
        // 合成 Prompt 文本
        const parts = [];
        if (state.subject) parts.push(state.subject);
        if (state.scene) parts.push(state.scene);
        if (state.action) parts.push(state.action);
        if (state.camera) parts.push(state.camera);
        if (state.atmosphere) parts.push(state.atmosphere);

        const promptText = parts.join('，');

        if (promptText) {
            preview.text.textContent = promptText;
            preview.text.classList.remove('preview-placeholder');
        } else {
            preview.text.innerHTML = '<span class="preview-placeholder">在左侧填写五要素，此处将实时显示合成的 Prompt 文本...</span>';
        }

        // 参数汇总
        const modelNames = {
            'doubao-seedance-2-0-260128': 'Seedance 2.0',
            'doubao-seedance-1-5-pro': 'Seedance 1.5 Pro',
            'doubao-seedance-1-0-pro': 'Seedance 1.0 Pro',
            'doubao-seedance-1-0-pro-fast': 'Seedance 1.0 Pro Fast',
        };
        const taskNames = {
            'text2video': '文生视频',
            'image2video': '图生视频',
            'video_edit': '视频编辑',
            'video_extend': '视频延长',
        };

        preview.metaModel.textContent = modelNames[state.model] || state.model;
        preview.metaTask.textContent = taskNames[state.task_type] || state.task_type;
        preview.metaResolution.textContent = state.resolution;
        preview.metaRatio.textContent = state.ratio;
        preview.metaDuration.textContent = `${state.duration}秒`;

        // API JSON 预览
        const apiPayload = {
            model: state.model,
            content: [
                { type: 'text', text: promptText }
            ],
            video_config: {
                resolution: state.resolution,
                duration: state.duration,
                ratio: state.ratio,
                fps: 24,
            }
        };

        // 添加素材引用
        state.ref_assets.forEach(ref => {
            apiPayload.content.push({
                type: 'image_url',
                image_url: { url: ref.path || '' },
                image_role: ref.role || 'reference_image',
            });
        });

        preview.json.textContent = JSON.stringify(apiPayload, null, 2);
    }

    // ── 保存项目 ─────────────────────────────────────
    const saveModal = document.getElementById('save-modal');
    const saveNameInput = document.getElementById('save-project-name');

    document.getElementById('btn-save-project').addEventListener('click', () => {
        saveModal.style.display = 'flex';
        saveNameInput.value = state.name || '';
        saveNameInput.focus();
    });

    document.getElementById('btn-close-save').addEventListener('click', () => {
        saveModal.style.display = 'none';
    });

    document.getElementById('btn-cancel-save').addEventListener('click', () => {
        saveModal.style.display = 'none';
    });

    document.getElementById('btn-confirm-save').addEventListener('click', async () => {
        const name = saveNameInput.value.trim();
        if (!name) {
            Toast.error('请输入项目名称');
            return;
        }

        try {
            const data = { ...state, name };
            if (state.currentProjectId) data.id = state.currentProjectId;
            const result = await api.post('/api/prompts', data);
            state.currentProjectId = result.id;
            state.name = name;
            saveModal.style.display = 'none';
            Toast.success('项目保存成功');
            loadProjectsList();
        } catch (err) {
            Toast.error(`保存失败: ${err.message}`);
        }
    });

    // 回车保存
    saveNameInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') document.getElementById('btn-confirm-save').click();
    });

    // ── 加载项目 ─────────────────────────────────────
    const projectsSection = document.getElementById('projects-section');
    const projectsList = document.getElementById('projects-list');

    document.getElementById('btn-load-project').addEventListener('click', () => {
        if (projectsSection.style.display === 'none') {
            projectsSection.style.display = 'block';
            loadProjectsList();
        } else {
            projectsSection.style.display = 'none';
        }
    });

    async function loadProjectsList() {
        try {
            const data = await api.get('/api/prompts');
            if (data.projects.length === 0) {
                projectsList.innerHTML = '<div style="color:var(--text-muted);font-size:0.85rem;padding:8px;">暂无保存的项目</div>';
                return;
            }

            const taskNames = {
                'text2video': '✍️', 'image2video': '🖼️',
                'video_edit': '✂️', 'video_extend': '⏩',
            };

            projectsList.innerHTML = data.projects.map(p => `
                <div class="project-item" data-id="${p.id}">
                    <div>
                        <div class="project-name">${taskNames[p.task_type] || ''} ${p.name}</div>
                        <div class="project-meta">${utils.formatDate(p.updated_at)}</div>
                    </div>
                    <div class="project-actions">
                        <button class="btn-icon btn-load-proj" data-id="${p.id}" title="加载">📂</button>
                        <button class="btn-icon btn-del-proj" data-id="${p.id}" title="删除">🗑️</button>
                    </div>
                </div>
            `).join('');

            // 绑定事件
            projectsList.querySelectorAll('.btn-load-proj').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    loadProject(btn.dataset.id);
                });
            });

            projectsList.querySelectorAll('.btn-del-proj').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    if (confirm('确认删除此项目？')) {
                        await api.delete(`/api/prompts/${btn.dataset.id}`);
                        Toast.success('项目已删除');
                        loadProjectsList();
                    }
                });
            });

        } catch (err) {
            Toast.error(`加载项目列表失败: ${err.message}`);
        }
    }

    async function loadProject(projectId) {
        try {
            const data = await api.get(`/api/prompts/${projectId}`);

            // 还原五要素
            ['subject', 'scene', 'action', 'camera', 'atmosphere'].forEach(key => {
                state[key] = data[key] || '';
                inputs[key].value = state[key];
            });

            // 还原参数
            state.currentProjectId = data.id;
            state.name = data.name;
            state.task_type = data.task_type || 'text2video';
            state.model = data.model || 'doubao-seedance-2-0-260128';
            state.resolution = data.resolution || '720p';
            state.ratio = data.ratio || '16:9';
            state.duration = data.duration || 5;
            state.ref_assets = data.ref_assets || [];

            params.taskType.value = state.task_type;
            params.model.value = state.model;
            params.duration.value = state.duration;
            params.durationDisplay.textContent = state.duration;

            document.querySelectorAll('#param-resolution .chip').forEach(c => {
                c.classList.toggle('active', c.dataset.value === state.resolution);
            });
            document.querySelectorAll('#param-ratio .chip').forEach(c => {
                c.classList.toggle('active', c.dataset.value === state.ratio);
            });

            updatePreview();
            Toast.success(`已加载项目: ${data.name}`);
        } catch (err) {
            Toast.error(`加载项目失败: ${err.message}`);
        }
    }

    // ── 复制与导出 ───────────────────────────────────
    document.getElementById('btn-copy-prompt').addEventListener('click', () => {
        const text = preview.text.textContent;
        if (!text || text.includes('在左侧填写')) {
            Toast.info('请先填写 Prompt 内容');
            return;
        }
        utils.copyToClipboard(text);
    });

    document.getElementById('btn-export-json').addEventListener('click', () => {
        const jsonText = preview.json.textContent;
        try {
            const payload = JSON.parse(jsonText);
            const filename = `seedance_prompt_${state.currentProjectId || 'draft'}.json`;
            utils.downloadJSON(payload, filename);
            Toast.success('JSON 已导出');
        } catch {
            Toast.error('导出失败');
        }
    });

    // ── 初始化预览 ───────────────────────────────────
    updatePreview();
});
