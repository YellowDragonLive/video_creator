/* ═══════════════════════════════════════════════════════
   assets.js — 素材管理交互逻辑
   ═══════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {

    // ── DOM 元素 ─────────────────────────────────────
    const uploadZone = document.getElementById('upload-zone');
    const fileInput = document.getElementById('file-input');
    const uploadProgress = document.getElementById('upload-progress');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const assetsGrid = document.getElementById('assets-grid');
    const assetsEmpty = document.getElementById('assets-empty');
    const searchInput = document.getElementById('search-input');
    const typeFilter = document.getElementById('type-filter');
    const viewToggle = document.getElementById('view-toggle');
    const tagsBar = document.getElementById('tags-bar');
    const tagChips = document.getElementById('tag-chips');
    const sidebar = document.getElementById('asset-sidebar');

    let currentView = 'grid';
    let currentFilter = '';
    let currentSearch = '';
    let currentTag = '';
    let selectedAssetId = null;

    // ── 初始加载 ─────────────────────────────────────
    loadAssets();
    loadTags();

    // ── 上传区事件 ───────────────────────────────────
    uploadZone.addEventListener('click', (e) => {
        if (e.target.closest('.upload-progress')) return;
        fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            uploadFiles(Array.from(e.target.files));
        }
    });

    // 拖拽上传
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('drag-over');
    });

    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('drag-over');
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('drag-over');
        if (e.dataTransfer.files.length > 0) {
            uploadFiles(Array.from(e.dataTransfer.files));
        }
    });

    async function uploadFiles(files) {
        uploadProgress.style.display = 'block';
        let uploaded = 0;

        for (const file of files) {
            try {
                progressText.textContent = `上传中: ${file.name} (${uploaded + 1}/${files.length})`;
                await api.upload('/api/assets/upload', file, (progress) => {
                    const total = ((uploaded + progress) / files.length) * 100;
                    progressFill.style.width = `${total}%`;
                });
                uploaded++;
            } catch (err) {
                Toast.error(`上传失败: ${file.name} - ${err.message}`);
            }
        }

        uploadProgress.style.display = 'none';
        progressFill.style.width = '0%';
        fileInput.value = '';

        if (uploaded > 0) {
            Toast.success(`成功上传 ${uploaded} 个文件`);
            loadAssets();
            loadTags();
        }
    }

    // ── 素材列表加载 ─────────────────────────────────
    async function loadAssets() {
        try {
            const params = new URLSearchParams();
            if (currentSearch) params.set('q', currentSearch);
            if (currentFilter) params.set('type', currentFilter);
            if (currentTag) params.set('tag', currentTag);

            const data = await api.get(`/api/assets?${params.toString()}`);
            renderAssets(data.assets);
        } catch (err) {
            Toast.error(`加载素材失败: ${err.message}`);
        }
    }

    function renderAssets(assets) {
        if (assets.length === 0) {
            assetsGrid.innerHTML = '';
            assetsGrid.appendChild(assetsEmpty);
            assetsEmpty.style.display = 'block';
            return;
        }

        assetsEmpty.style.display = 'none';

        const typeIcons = { image: '🖼️', video: '🎬', audio: '🎵' };
        const typeLabels = { image: '图片', video: '视频', audio: '音频' };

        assetsGrid.innerHTML = assets.map(a => `
            <div class="asset-card" data-id="${a.id}">
                <img class="asset-thumb" src="/data/thumbnails/${a.thumbnail_path}" alt="${a.name}"
                     onerror="this.style.display='none'">
                <div class="asset-info">
                    <div class="asset-name" title="${a.original_name}">${a.name}</div>
                    <span class="asset-type-badge">${typeIcons[a.type] || ''} ${typeLabels[a.type] || a.type}</span>
                </div>
            </div>
        `).join('');

        // 点击打开侧边栏
        assetsGrid.querySelectorAll('.asset-card').forEach(card => {
            card.addEventListener('click', () => {
                openSidebar(card.dataset.id);
            });
        });
    }

    // ── 搜索 ─────────────────────────────────────────
    let searchTimeout;
    searchInput.addEventListener('input', () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            currentSearch = searchInput.value.trim();
            loadAssets();
        }, 300);
    });

    // ── 类型过滤 ─────────────────────────────────────
    typeFilter.addEventListener('click', (e) => {
        const chip = e.target.closest('.chip');
        if (!chip) return;
        typeFilter.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        currentFilter = chip.dataset.type;
        loadAssets();
    });

    // ── 视图切换 ─────────────────────────────────────
    viewToggle.addEventListener('click', (e) => {
        const btn = e.target.closest('.btn-icon');
        if (!btn) return;
        viewToggle.querySelectorAll('.btn-icon').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentView = btn.dataset.view;
        assetsGrid.classList.toggle('list-view', currentView === 'list');
    });

    // ── 标签加载 ─────────────────────────────────────
    async function loadTags() {
        try {
            const data = await api.get('/api/assets/tags');
            if (data.tags.length > 0) {
                tagsBar.style.display = 'flex';
                tagChips.innerHTML = `<button class="chip chip-sm ${!currentTag ? 'active' : ''}" data-tag="">全部</button>`
                    + data.tags.map(t =>
                        `<button class="chip chip-sm ${currentTag === t ? 'active' : ''}" data-tag="${t}">${t}</button>`
                    ).join('');

                tagChips.querySelectorAll('.chip').forEach(chip => {
                    chip.addEventListener('click', () => {
                        tagChips.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
                        chip.classList.add('active');
                        currentTag = chip.dataset.tag;
                        loadAssets();
                    });
                });
            } else {
                tagsBar.style.display = 'none';
            }
        } catch (err) {
            // 静默失败
        }
    }

    // ── 侧边栏 ──────────────────────────────────────
    async function openSidebar(assetId) {
        try {
            const asset = await api.get(`/api/assets/${assetId}`);
            selectedAssetId = assetId;

            document.getElementById('sidebar-title').textContent = asset.name;

            // 预览
            const previewEl = document.getElementById('sidebar-preview');
            if (asset.type === 'image') {
                previewEl.innerHTML = `<img src="/data/assets/${asset.path}" alt="${asset.name}">`;
            } else if (asset.type === 'video') {
                previewEl.innerHTML = `<video src="/data/assets/${asset.path}" controls></video>`;
            } else if (asset.type === 'audio') {
                previewEl.innerHTML = `
                    <div style="padding:30px;text-align:center;">
                        <div style="font-size:3rem;margin-bottom:10px;">🎵</div>
                        <audio src="/data/assets/${asset.path}" controls style="width:100%;"></audio>
                    </div>
                `;
            }

            // 信息
            const typeLabels = { image: '图片', video: '视频', audio: '音频' };
            document.getElementById('info-type').textContent = typeLabels[asset.type] || asset.type;
            document.getElementById('info-original').textContent = asset.original_name;
            document.getElementById('info-size').textContent = utils.formatBytes(asset.file_size);
            document.getElementById('info-date').textContent = utils.formatDate(asset.created_at);

            // 标签
            renderSidebarTags(asset.tags || []);

            sidebar.style.display = 'block';
        } catch (err) {
            Toast.error(`获取素材详情失败: ${err.message}`);
        }
    }

    function renderSidebarTags(tags) {
        const tagsList = document.getElementById('sidebar-tags');
        tagsList.innerHTML = tags.map(t =>
            `<span class="tag-item">${t}<span class="tag-remove" data-tag="${t}">✕</span></span>`
        ).join('');

        tagsList.querySelectorAll('.tag-remove').forEach(btn => {
            btn.addEventListener('click', async () => {
                const tag = btn.dataset.tag;
                const newTags = tags.filter(t => t !== tag);
                await updateTags(newTags);
            });
        });
    }

    // 添加标签
    const tagInput = document.getElementById('tag-input');
    tagInput.addEventListener('keydown', async (e) => {
        if (e.key === 'Enter' && tagInput.value.trim()) {
            const tag = tagInput.value.trim();
            tagInput.value = '';
            try {
                const asset = await api.get(`/api/assets/${selectedAssetId}`);
                const tags = asset.tags || [];
                if (!tags.includes(tag)) {
                    tags.push(tag);
                    await updateTags(tags);
                }
            } catch (err) {
                Toast.error(`添加标签失败: ${err.message}`);
            }
        }
    });

    async function updateTags(tags) {
        try {
            await api.put(`/api/assets/${selectedAssetId}/tags`, { tags });
            renderSidebarTags(tags);
            loadTags();
            Toast.success('标签已更新');
        } catch (err) {
            Toast.error(`更新标签失败: ${err.message}`);
        }
    }

    // 关闭侧边栏
    document.getElementById('btn-close-sidebar').addEventListener('click', () => {
        sidebar.style.display = 'none';
        selectedAssetId = null;
    });

    // 删除素材
    document.getElementById('btn-delete-asset').addEventListener('click', async () => {
        if (!selectedAssetId) return;
        if (!confirm('确认删除此素材？此操作不可撤销。')) return;

        try {
            await api.delete(`/api/assets/${selectedAssetId}`);
            sidebar.style.display = 'none';
            selectedAssetId = null;
            Toast.success('素材已删除');
            loadAssets();
            loadTags();
        } catch (err) {
            Toast.error(`删除失败: ${err.message}`);
        }
    });

    // ── AI 生成图片 ──────────────────────────────────
    const aiImageModal = document.getElementById('ai-image-modal');
    const aiImagePrompt = document.getElementById('ai-image-prompt');
    const aiImageBtnText = document.getElementById('ai-image-btn-text');
    let aiImageRatio = '16:9';

    document.getElementById('btn-ai-image').addEventListener('click', () => {
        aiImageModal.style.display = 'flex';
        aiImagePrompt.value = '';
        aiImagePrompt.focus();
    });

    document.getElementById('btn-close-ai-image').addEventListener('click', () => {
        aiImageModal.style.display = 'none';
    });

    document.getElementById('btn-cancel-ai-image').addEventListener('click', () => {
        aiImageModal.style.display = 'none';
    });

    // 宽高比选择
    document.getElementById('ai-image-ratio').addEventListener('click', (e) => {
        const chip = e.target.closest('.chip');
        if (!chip) return;
        document.querySelectorAll('#ai-image-ratio .chip').forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        aiImageRatio = chip.dataset.value;
    });

    document.getElementById('btn-confirm-ai-image').addEventListener('click', async () => {
        const prompt = aiImagePrompt.value.trim();
        if (!prompt) {
            Toast.error('请输入图片描述');
            return;
        }

        aiImageBtnText.textContent = '⏳ AI 生成中...';
        document.getElementById('btn-confirm-ai-image').disabled = true;

        try {
            const result = await api.post('/api/ai/generate-image', {
                prompt,
                aspect_ratio: aiImageRatio,
            });

            aiImageModal.style.display = 'none';
            Toast.success('🎨 AI 素材图片生成成功');
            loadAssets();
            loadTags();
        } catch (err) {
            Toast.error(`AI 图片生成失败: ${err.message}`);
        } finally {
            aiImageBtnText.textContent = '🎨 生成';
            document.getElementById('btn-confirm-ai-image').disabled = false;
        }
    });

    // 回车触发 AI 图片生成
    aiImagePrompt.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            document.getElementById('btn-confirm-ai-image').click();
        }
    });
});
