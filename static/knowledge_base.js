/**
 * 知识库管理页面 - 前端交互逻辑
 */

// ============= DOM 元素 =============
const DOM = {
    // 术语知识库
    termStatus: document.getElementById('term-status'),
    termChunks: document.getElementById('term-chunks'),
    termChars: document.getElementById('term-chars'),
    termAvg: document.getElementById('term-avg'),
    termEditor: document.getElementById('term-editor'),
    loadTermBtn: document.getElementById('load-term-btn'),
    viewTermChunksBtn: document.getElementById('view-term-chunks-btn'),
    rebuildTermBtn: document.getElementById('rebuild-term-btn'),
    
    // 论文知识库
    paperStatus: document.getElementById('paper-status'),
    paperCount: document.getElementById('paper-count'),
    paperChunks: document.getElementById('paper-chunks'),
    paperChars: document.getElementById('paper-chars'),
    addPaperBtn: document.getElementById('add-paper-btn'),
    exportPaperBtn: document.getElementById('export-paper-btn'),
    paperNavSearch: document.getElementById('paper-nav-search'),
    paperNavList: document.getElementById('paper-nav-list'),
    paperDetailEmpty: document.getElementById('paper-detail-empty'),
    paperDetailInner: document.getElementById('paper-detail-inner'),
    paperDetailTitle: document.getElementById('paper-detail-title'),
    paperSegmentStrip: document.getElementById('paper-segment-strip'),
    paperDetailContent: document.getElementById('paper-detail-content'),
    paperAddSegmentBtn: document.getElementById('paper-add-segment-btn'),
    paperDeletePaperBtn: document.getElementById('paper-delete-paper-btn'),
    paperEditChunkBtn: document.getElementById('paper-edit-chunk-btn'),
    paperDeleteChunkBtn: document.getElementById('paper-delete-chunk-btn'),
    
    // 背景知识库
    backgroundStatus: document.getElementById('background-status'),
    backgroundChunks: document.getElementById('background-chunks'),
    backgroundChars: document.getElementById('background-chars'),
    addBackgroundBtn: document.getElementById('add-background-btn'),
    exportBackgroundBtn: document.getElementById('export-background-btn'),
    bgNavSearch: document.getElementById('bg-nav-search'),
    bgNavList: document.getElementById('bg-nav-list'),
    bgDetailEmpty: document.getElementById('bg-detail-empty'),
    bgDetailInner: document.getElementById('bg-detail-inner'),
    bgDetailMeta: document.getElementById('bg-detail-meta'),
    bgDetailContent: document.getElementById('bg-detail-content'),
    bgEditChunkBtn: document.getElementById('bg-edit-chunk-btn'),
    bgDeleteChunkBtn: document.getElementById('bg-delete-chunk-btn'),
    
    // 模态框
    chunksModal: document.getElementById('chunks-modal'),
    chunksModalTitle: document.getElementById('chunks-modal-title'),
    chunksList: document.getElementById('chunks-list'),
    papersModal: document.getElementById('papers-modal'),
    papersList: document.getElementById('papers-list'),
    paperChunksModal: document.getElementById('paper-chunks-modal'),
    paperChunksTitle: document.getElementById('paper-chunks-title'),
    paperChunksList: document.getElementById('paper-chunks-list'),
    addChunkToPaperBtn: document.getElementById('add-chunk-to-paper-btn'),
    editChunkModal: document.getElementById('edit-chunk-modal'),
    editChunkContent: document.getElementById('edit-chunk-content'),
    editChunkIndex: document.getElementById('edit-chunk-index'),
    editChunkPaperId: document.getElementById('edit-chunk-paper-id'),
    editChunkType: document.getElementById('edit-chunk-type'),
    saveChunkBtn: document.getElementById('save-chunk-btn'),
    addPaperModal: document.getElementById('add-paper-modal'),
    newPaperTitle: document.getElementById('new-paper-title'),
    newPaperFilename: document.getElementById('new-paper-filename'),
    newPaperChunks: document.getElementById('new-paper-chunks'),
    saveNewPaperBtn: document.getElementById('save-new-paper-btn'),
    backgroundChunksModal: document.getElementById('background-chunks-modal'),
    backgroundChunksList: document.getElementById('background-chunks-list'),
    addBackgroundModal: document.getElementById('add-background-modal'),
    newBackgroundContent: document.getElementById('new-background-content'),
    saveBackgroundBtn: document.getElementById('save-background-btn'),
    modalClose: document.querySelectorAll('.modal-close, .modal-close-btn')
};

// ============= 状态管理 =============
const State = {
    termStats: null,
    paperStats: null,
    backgroundStats: null,
    currentPaperId: null,
    papers: [],
    paperChunksDetail: [],
    selectedPaperChunkPos: 0,
    backgroundChunksDetail: [],
    selectedBackgroundIdx: 0,
};

// ============= 工具函数 =============

function formatNumber(num) {
    if (num === undefined || num === null) return '-';
    return num.toLocaleString();
}

function setLoading(element, isLoading) {
    if (!element) return;
    if (isLoading) {
        element.classList.add('loading');
        element.textContent = '加载中...';
    } else {
        element.classList.remove('loading');
        element.textContent = '加载成功';
    }
}

function showNotification(message, type = 'info') {
    const existing = document.querySelector('.simple-notification');
    if (existing) existing.remove();

    const notification = document.createElement('div');
    notification.className = `simple-notification ${type}`;

    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };
    const icon = icons[type] || 'ℹ️';

    notification.innerHTML = `
        <div class="simple-notification-content">
            <span class="simple-icon">${icon}</span>
            <span class="simple-message">${message}</span>
            <button class="simple-close">✕</button>
        </div>
    `;

    document.body.appendChild(notification);

    const close = () => {
        notification.style.animation = 'fadeOut 0.2s ease-out';
        setTimeout(() => notification.remove(), 200);
    };

    notification.querySelector('.simple-close').addEventListener('click', close);
    setTimeout(close, 3000);
}

// ============= API 调用 =============

/**
 * 获取知识库统计信息
 */
async function fetchKBStats() {
    try {
        const response = await fetch('/api/kb/stats');
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json();
        
        if (data.success) {
            State.termStats = data.term;
            State.paperStats = data.paper;
            State.backgroundStats = data.background;
            
            updateStatsUI();
        } else {
            throw new Error(data.error || '获取统计信息失败');
        }
    } catch (error) {
        console.error('获取知识库统计失败:', error);
        showNotification('获取知识库统计失败: ' + error.message, 'error');
    }
}

/**
 * 更新统计信息UI
 */
function updateStatsUI() {
    // 术语知识库（仅详情页 term 存在对应 DOM）
    if (State.termStats && DOM.termStatus) {
        DOM.termStatus.textContent = State.termStats.exists ? '✅ 已创建' : '❌ 未创建';
        DOM.termChunks.textContent = formatNumber(State.termStats.chunk_count);
        DOM.termChars.textContent = formatNumber(State.termStats.total_chars);
        DOM.termAvg.textContent = formatNumber(State.termStats.avg_chunk_size);
    }

    // 论文知识库
    if (State.paperStats && DOM.paperStatus) {
        DOM.paperStatus.textContent = State.paperStats.exists ? '✅ 已创建' : '❌ 未创建';
        DOM.paperChunks.textContent = formatNumber(State.paperStats.chunk_count);
        DOM.paperChars.textContent = formatNumber(State.paperStats.total_chars);
        if (State.papers && DOM.paperCount) {
            DOM.paperCount.textContent = formatNumber(State.papers.length);
        }
    }

    // 背景知识库
    if (State.backgroundStats && DOM.backgroundStatus) {
        DOM.backgroundStatus.textContent = State.backgroundStats.exists ? '✅ 已创建' : '❌ 未创建';
        DOM.backgroundChunks.textContent = formatNumber(State.backgroundStats.chunk_count);
        DOM.backgroundChars.textContent = formatNumber(State.backgroundStats.total_chars);
    }
}

/**
 * 加载术语库内容
 */
async function loadTermContent() {
    setLoading(DOM.termStatus, true);
    DOM.termEditor.value = '加载中...';
    
    try {
        const response = await fetch('/api/kb/term/load');
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json();
        
        if (data.success) {
            DOM.termEditor.value = data.content || '';
            // 如果内容为空，显示提示信息
            if (!data.content) {
                DOM.termEditor.value = '# 术语知识库\n# 每行一个术语，格式：术语名：定义\n\n# 请点击"重建索引"创建默认术语库';
            }
            showNotification('术语库加载成功', 'success');
        } else {
            throw new Error(data.error || '加载失败');
        }
    } catch (error) {
        console.error('加载术语库失败:', error);
        DOM.termEditor.value = '// 加载失败: ' + error.message;
        showNotification('加载术语库失败: ' + error.message, 'error');
    } finally {
        setLoading(DOM.termStatus, false);
    }
}

/**
 * 一键保存并重建术语库索引
 */
async function rebuildTermIndex() {
    // 获取编辑器当前内容
    const currentContent = DOM.termEditor.value.trim();
    
    // 如果内容为空，询问是否使用示例内容
    let contentToSave = currentContent;
    if (!contentToSave) {
        const useExample = confirm('术语库为空，是否使用示例内容？\n\n点击"确定"使用示例内容，点击"取消"取消操作。');
        if (!useExample) {
            return;  // 用户取消操作
        }
        // 用户确认使用示例内容，contentToSave 保持为空字符串
        // 后端会处理空字符串并创建默认内容
    }
    
    setLoading(DOM.termStatus, true);
    showNotification('正在重建术语库索引...', 'info');
    
    try {
        // 调用重建接口，传入当前内容（可能为空）
        const response = await fetch('/api/kb/term/rebuild', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ content: contentToSave })  // 传入当前内容（可能为空）
        });
        
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json();
        
        if (data.success) {
            // 成功提示
            const message = `术语库重建成功！\n` +
                           `📊 片段数: ${data.chunk_count}\n` +
                           (data.chunks_file ? `📄 分段文件: ${data.chunks_file}` : '');
            
            showNotification(message, 'success');
            
            // 刷新统计信息
            await fetchKBStats();
            
            // 重新加载编辑器内容（确保显示最新）
            await loadTermContent();
            
            // 如果有分段文件信息，显示额外提示
            if (data.chunks_file) {
                setTimeout(() => {
                    showNotification(`分段可视化已保存至: ${data.chunks_file}`, 'info');
                }, 1000);
            }
        } else {
            throw new Error(data.error || '重建失败');
        }
        
    } catch (error) {
        console.error('重建术语库失败:', error);
        showNotification('重建失败: ' + error.message, 'error');
    } finally {
        setLoading(DOM.termStatus, false);
    }
}

/**
 * 查看知识库分段详情
 */
async function inspectKB(type) {
    const names = {
        paper: '论文知识库',
        background: '背景知识库',
        term: '术语知识库'
    };
    
    try {
        const response = await fetch(`/api/kb/${type}/inspect`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json();
        
        if (data.success) {
            // 显示分段详情
            DOM.chunksModalTitle.textContent = `${names[type]} - 分段详情 (共 ${data.chunks.length} 个片段)`;
            
            let html = '';
            data.chunks.forEach((chunk, index) => {
                html += `
                    <div class="chunk-item">
                        <div class="chunk-header">
                            <span>片段 #${index + 1}</span>
                            <span>长度: ${chunk.length} 字符</span>
                        </div>
                        <div class="chunk-content">${escapeHtml(chunk)}</div>
                    </div>
                `;
            });
            
            DOM.chunksList.innerHTML = html;
            DOM.chunksModal.classList.add('show');
        } else {
            throw new Error(data.error || '获取分段详情失败');
        }
    } catch (error) {
        console.error('获取分段详情失败:', error);
        showNotification('获取分段详情失败: ' + error.message, 'error');
    }
}

/**
 * 导出统计信息
 */
function exportStats(type) {
    let stats, name;
    
    if (type === 'paper') {
        stats = State.paperStats;
        name = '论文知识库';
    } else if (type === 'background') {
        stats = State.backgroundStats;
        name = '背景知识库';
    } else {
        return;
    }
    
    if (!stats || !stats.exists) {
        showNotification('知识库不存在，无法导出', 'error');
        return;
    }
    
    const content = `# ${name}统计报告
生成时间: ${new Date().toLocaleString()}

## 基本信息
- 状态: ${stats.exists ? '已创建' : '未创建'}
- 片段数: ${stats.chunk_count}
- 总字符数: ${stats.total_chars}
- 平均片段长度: ${stats.avg_chunk_size}
- 存储路径: ${stats.path}
- 嵌入模型: ${stats.model}
- 启用归一化: ${stats.normalized ? '是' : '否'}

## 检索配置
- 相似度阈值: ${localStorage.getItem('similarity_threshold') || '0.5'}
- 最大检索数量: ${localStorage.getItem('max_terms') || '15'}
`;
    
    // 创建下载链接
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${name}_stats_${new Date().toISOString().slice(0,10)}.md`;
    a.click();
    URL.revokeObjectURL(url);
    
    showNotification('统计信息已导出', 'success');
}

/**
 * HTML转义
 */
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// ============= 论文知识库 CRUD =============

/**
 * 获取论文列表
 */
async function fetchPapers() {
    try {
        const response = await fetch('/api/kb/paper/papers');
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json();
        if (data.success) {
            State.papers = data.papers || [];
            return data.papers;
        } else {
            throw new Error(data.error || '获取论文列表失败');
        }
    } catch (error) {
        console.error('获取论文列表失败:', error);
        showNotification('获取论文列表失败: ' + error.message, 'error');
        return [];
    }
}

function getPaperNavFilterText() {
    return (DOM.paperNavSearch && DOM.paperNavSearch.value) ? DOM.paperNavSearch.value.trim().toLowerCase() : '';
}

function filterPapersForNav() {
    const q = getPaperNavFilterText();
    if (!q || !State.papers || !State.papers.length) return State.papers || [];
    return State.papers.filter(p => {
        const t = (p.title || '').toLowerCase();
        const f = (p.filename || '').toLowerCase();
        return t.includes(q) || f.includes(q);
    });
}

function renderPaperNavList() {
    if (!DOM.paperNavList) return;
    const list = filterPapersForNav();
    if (!list.length) {
        DOM.paperNavList.innerHTML = '<div class="loading-text" style="padding:12px;">暂无论文或没有匹配项</div>';
        return;
    }
    DOM.paperNavList.innerHTML = list.map(paper => {
        const active = paper.paper_id === State.currentPaperId ? ' is-active' : '';
        const title = escapeHtml(paper.title);
        const meta = `📄 ${paper.chunk_count} 片段 · ${new Date(paper.added_at).toLocaleDateString()}`;
        return (
            `<button type="button" class="kb-md-nav-item${active}" data-paper-id="${escapeHtml(paper.paper_id)}">` +
            `<span class="kb-md-nav-item-icon">📄</span>` +
            `<span class="kb-md-nav-item-body"><span class="kb-md-nav-item-title">${title}</span>` +
            `<div class="kb-md-nav-item-meta">${meta}</div></span></button>`
        );
    }).join('');
}

/**
 * @param {string} paperId
 * @param {(chunks: object[]) => number} [chooseSelection] 根据拉取后的 chunks 返回要选中的下标
 */
async function loadPaperDetail(paperId, chooseSelection) {
    if (!DOM.paperDetailInner || !paperId) return;
    State.currentPaperId = paperId;
    try {
        const response = await fetch(`/api/kb/paper/papers/${paperId}/chunks`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        if (!data.success) throw new Error(data.error || '获取片段失败');
        State.paperChunksDetail = data.chunks || [];
        const chunks = State.paperChunksDetail;
        if (typeof chooseSelection === 'function' && chunks.length) {
            let pos = chooseSelection(chunks);
            if (typeof pos !== 'number' || Number.isNaN(pos)) pos = 0;
            State.selectedPaperChunkPos = Math.max(0, Math.min(pos, chunks.length - 1));
        } else {
            State.selectedPaperChunkPos = chunks.length ? 0 : 0;
        }
        const paper = State.papers.find(p => p.paper_id === paperId);
        if (DOM.paperDetailTitle) {
            DOM.paperDetailTitle.textContent = paper ? paper.title : paperId;
        }
        if (DOM.paperDetailEmpty) DOM.paperDetailEmpty.hidden = true;
        DOM.paperDetailInner.hidden = false;
        renderPaperSegmentStrip();
        selectPaperChunk(State.selectedPaperChunkPos);
        renderPaperNavList();
        updateStatsUI();
    } catch (error) {
        console.error('获取论文片段失败:', error);
        showNotification('获取论文片段失败: ' + error.message, 'error');
    }
}

function renderPaperSegmentStrip() {
    if (!DOM.paperSegmentStrip) return;
    const chunks = State.paperChunksDetail || [];
    if (!chunks.length) {
        DOM.paperSegmentStrip.innerHTML = '<span class="kb-md-meta" style="padding:0;">该论文暂无片段</span>';
        return;
    }
    DOM.paperSegmentStrip.innerHTML = chunks.map((ch, pos) => {
        const cls = pos === State.selectedPaperChunkPos ? 'is-active' : '';
        return `<button type="button" class="${cls}" data-seg-pos="${pos}">片段 ${pos + 1}</button>`;
    }).join('');
}

function selectPaperChunk(pos) {
    const chunks = State.paperChunksDetail || [];
    if (!chunks.length) {
        if (DOM.paperDetailContent) DOM.paperDetailContent.textContent = '';
        return;
    }
    const n = Math.max(0, Math.min(pos, chunks.length - 1));
    State.selectedPaperChunkPos = n;
    const ch = chunks[n];
    if (DOM.paperDetailContent) {
        DOM.paperDetailContent.textContent = ch.content || ch.preview || '';
    }
    if (DOM.paperSegmentStrip) {
        DOM.paperSegmentStrip.querySelectorAll('button[data-seg-pos]').forEach(btn => {
            const p = parseInt(btn.getAttribute('data-seg-pos'), 10);
            btn.classList.toggle('is-active', p === State.selectedPaperChunkPos);
        });
    }
}

async function initPaperMasterDetail() {
    if (!DOM.paperNavList) return;
    await fetchPapers();
    updateStatsUI();
    renderPaperNavList();
    if (State.papers && State.papers.length > 0) {
        await loadPaperDetail(State.papers[0].paper_id, () => 0);
    } else {
        State.currentPaperId = null;
        State.paperChunksDetail = [];
        if (DOM.paperDetailEmpty) DOM.paperDetailEmpty.hidden = false;
        if (DOM.paperDetailInner) DOM.paperDetailInner.hidden = true;
    }
}

/**
 * 打开编辑片段弹窗（论文 / 背景，数据来自当前主从面板状态）
 * @param {'paper'|'background'} type
 */
function openEditChunkModal(type) {
    if (type === 'paper') {
        const ch = State.paperChunksDetail[State.selectedPaperChunkPos];
        if (!ch) {
            showNotification('请先选择片段', 'warning');
            return;
        }
        DOM.editChunkContent.value = ch.content || ch.preview || '';
        DOM.editChunkIndex.value = String(ch.index);
        DOM.editChunkPaperId.value = State.currentPaperId || '';
        DOM.editChunkType.value = 'paper';
    } else {
        const ch = State.backgroundChunksDetail[State.selectedBackgroundIdx];
        if (!ch) {
            showNotification('请先选择片段', 'warning');
            return;
        }
        DOM.editChunkContent.value = ch.content || '';
        DOM.editChunkIndex.value = String(ch.index);
        DOM.editChunkPaperId.value = '';
        DOM.editChunkType.value = 'background';
    }
    DOM.editChunkModal.classList.add('show');
}

/**
 * 保存片段编辑
 */
async function saveChunkEdit() {
    const content = DOM.editChunkContent.value.trim();
    const chunkIndex = parseInt(DOM.editChunkIndex.value, 10);
    const type = DOM.editChunkType.value;
    
    if (!content) {
        showNotification('内容不能为空', 'error');
        return;
    }
    
    try {
        const endpoint = type === 'paper' 
            ? `/api/kb/paper/chunks/${chunkIndex}`
            : `/api/kb/background/chunks/${chunkIndex}`;
        
        const response = await fetch(endpoint, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content })
        });
        
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json();
        if (data.success) {
            showNotification('片段已更新', 'success');
            DOM.editChunkModal.classList.remove('show');
            
            if (type === 'paper' && State.currentPaperId) {
                const pos = State.selectedPaperChunkPos;
                await loadPaperDetail(State.currentPaperId, () => pos);
            } else {
                const apiIdx = chunkIndex;
                await refreshBackgroundDetail((chunks) => {
                    const p = chunks.findIndex(c => c.index === apiIdx);
                    return p >= 0 ? p : 0;
                });
            }
            await fetchKBStats();
        } else {
            throw new Error(data.error || '更新失败');
        }
    } catch (error) {
        console.error('保存片段失败:', error);
        showNotification('保存片段失败: ' + error.message, 'error');
    }
}

/**
 * 删除片段
 */
async function deleteChunk(chunkIndex, type) {
    if (!confirm('确定要删除这个片段吗？此操作不可恢复。')) return;
    
    try {
        const endpoint = type === 'paper'
            ? `/api/kb/paper/chunks/${chunkIndex}`
            : `/api/kb/background/chunks/${chunkIndex}`;
        
        const selPosBefore = type === 'paper'
            ? State.selectedPaperChunkPos
            : State.selectedBackgroundIdx;
        const curApiIdx = type === 'paper'
            ? State.paperChunksDetail[selPosBefore]?.index
            : State.backgroundChunksDetail[selPosBefore]?.index;
        const deletingCurrent = chunkIndex === curApiIdx;
        
        const response = await fetch(endpoint, { method: 'DELETE' });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json();
        if (data.success) {
            showNotification('片段已删除', 'success');
            
            if (type === 'paper' && State.currentPaperId) {
                await fetchPapers();
                await loadPaperDetail(State.currentPaperId, (chunks) => {
                    if (deletingCurrent) {
                        return Math.min(selPosBefore, Math.max(0, chunks.length - 1));
                    }
                    const p = chunks.findIndex(c => c.index === curApiIdx);
                    return p >= 0 ? p : 0;
                });
            } else {
                await refreshBackgroundDetail((chunks) => {
                    if (deletingCurrent) {
                        return Math.min(selPosBefore, Math.max(0, chunks.length - 1));
                    }
                    const p = chunks.findIndex(c => c.index === curApiIdx);
                    return p >= 0 ? p : 0;
                });
            }
            await fetchKBStats();
        } else {
            throw new Error(data.error || '删除失败');
        }
    } catch (error) {
        console.error('删除片段失败:', error);
        showNotification('删除片段失败: ' + error.message, 'error');
    }
}

/**
 * 删除论文
 */
async function deletePaper(paperId) {
    if (!confirm('确定要删除这篇论文及其所有片段吗？此操作不可恢复。')) return;
    
    try {
        const wasCurrent = State.currentPaperId === paperId;
        const response = await fetch(`/api/kb/paper/papers/${paperId}`, { method: 'DELETE' });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json();
        if (data.success) {
            showNotification('论文已删除', 'success');
            await fetchPapers();
            await fetchKBStats();
            updateStatsUI();
            renderPaperNavList();
            if (!State.papers.length) {
                State.currentPaperId = null;
                State.paperChunksDetail = [];
                if (DOM.paperDetailEmpty) DOM.paperDetailEmpty.hidden = false;
                if (DOM.paperDetailInner) DOM.paperDetailInner.hidden = true;
            } else if (wasCurrent) {
                await loadPaperDetail(State.papers[0].paper_id, () => 0);
            } else if (State.currentPaperId) {
                await loadPaperDetail(State.currentPaperId, (chunks) => State.selectedPaperChunkPos);
            }
        } else {
            throw new Error(data.error || '删除失败');
        }
    } catch (error) {
        console.error('删除论文失败:', error);
        showNotification('删除论文失败: ' + error.message, 'error');
    }
}

/**
 * 显示新增论文模态框
 */
function showAddPaperModal() {
    DOM.newPaperTitle.value = '';
    DOM.newPaperFilename.value = '';
    DOM.newPaperChunks.value = '';
    DOM.addPaperModal.classList.add('show');
}

/**
 * 保存新论文
 */
async function saveNewPaper() {
    const title = DOM.newPaperTitle.value.trim();
    const filename = DOM.newPaperFilename.value.trim();
    const content = DOM.newPaperChunks.value.trim();
    
    if (!title) {
        showNotification('请输入论文标题', 'error');
        return;
    }
    if (!content) {
        showNotification('请输入知识片段', 'error');
        return;
    }
    
    // 按空行分割片段
    const chunks = content.split(/\n\n+/).filter(c => c.trim());
    
    try {
        const response = await fetch('/api/kb/paper/papers', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, filename, chunks })
        });
        
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json();
        if (data.success) {
            showNotification('论文添加成功', 'success');
            DOM.addPaperModal.classList.remove('show');
            await fetchKBStats();
            await fetchPapers();
            updateStatsUI();
            renderPaperNavList();
            if (State.papers.length) {
                const last = State.papers[State.papers.length - 1];
                await loadPaperDetail(last.paper_id, (chunks) => Math.max(0, chunks.length - 1));
            }
        } else {
            throw new Error(data.error || '添加失败');
        }
    } catch (error) {
        console.error('添加论文失败:', error);
        showNotification('添加论文失败: ' + error.message, 'error');
    }
}

/**
 * 向论文添加片段
 */
async function addChunkToPaper() {
    if (!State.currentPaperId) return;
    
    const content = prompt('请输入新片段内容：');
    if (!content || !content.trim()) return;
    
    try {
        const response = await fetch(`/api/kb/paper/papers/${State.currentPaperId}/chunks`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ chunks: [content.trim()] })
        });
        
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json();
        if (data.success) {
            showNotification('片段添加成功', 'success');
            await fetchKBStats();
            await fetchPapers();
            renderPaperNavList();
            await loadPaperDetail(State.currentPaperId, (chunks) => Math.max(0, chunks.length - 1));
        } else {
            throw new Error(data.error || '添加失败');
        }
    } catch (error) {
        console.error('添加片段失败:', error);
        showNotification('添加片段失败: ' + error.message, 'error');
    }
}

// ============= 背景知识库 主从布局 =============

function getBgNavFilterText() {
    return (DOM.bgNavSearch && DOM.bgNavSearch.value) ? DOM.bgNavSearch.value.trim().toLowerCase() : '';
}

function filterBackgroundChunksForNav() {
    const q = getBgNavFilterText();
    const all = State.backgroundChunksDetail || [];
    if (!q) return all;
    return all.filter(ch => (ch.content || '').toLowerCase().includes(q));
}

function renderBgNavList() {
    if (!DOM.bgNavList) return;
    const list = filterBackgroundChunksForNav();
    const cur = State.backgroundChunksDetail[State.selectedBackgroundIdx];
    const curIdx = cur ? cur.index : -1;
    if (!list.length) {
        DOM.bgNavList.innerHTML = '<div class="loading-text" style="padding:12px;">暂无片段或没有匹配项</div>';
        return;
    }
    DOM.bgNavList.innerHTML = list.map((ch) => {
        const active = ch.index === curIdx ? ' is-active' : '';
        const raw = ch.preview || ch.content || '';
        const title = escapeHtml(raw.slice(0, 120));
        const len = ch.length != null ? ch.length : (ch.content || '').length;
        const meta = `${len} 字符`;
        return (
            `<button type="button" class="kb-md-nav-item${active}" data-bg-chunk-index="${ch.index}">` +
            `<span class="kb-md-nav-item-icon">📋</span>` +
            `<span class="kb-md-nav-item-body"><span class="kb-md-nav-item-title">${title}</span>` +
            `<div class="kb-md-nav-item-meta">${meta}</div></span></button>`
        );
    }).join('');
}

function selectBackgroundChunk(idx) {
    const list = State.backgroundChunksDetail || [];
    if (!list.length) {
        if (DOM.bgDetailContent) DOM.bgDetailContent.textContent = '';
        return;
    }
    const n = Math.max(0, Math.min(idx, list.length - 1));
    State.selectedBackgroundIdx = n;
    const ch = list[n];
    if (DOM.bgDetailEmpty) DOM.bgDetailEmpty.hidden = true;
    if (DOM.bgDetailInner) DOM.bgDetailInner.hidden = false;
    if (DOM.bgDetailMeta) {
        const total = list.length;
        const len = ch.length != null ? ch.length : (ch.content || '').length;
        DOM.bgDetailMeta.textContent = `片段 ${n + 1} / ${total} · ${len} 字符`;
    }
    if (DOM.bgDetailContent) DOM.bgDetailContent.textContent = ch.content || '';
    renderBgNavList();
}

/**
 * @param {(chunks: object[]) => number} [chooseSelection]
 */
async function refreshBackgroundDetail(chooseSelection) {
    try {
        const response = await fetch('/api/kb/background/chunks');
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

        const data = await response.json();
        if (!data.success) throw new Error(data.error || '获取片段失败');

        State.backgroundChunksDetail = data.chunks || [];
        const chunks = State.backgroundChunksDetail;
        if (typeof chooseSelection === 'function' && chunks.length) {
            let pos = chooseSelection(chunks);
            if (typeof pos !== 'number' || Number.isNaN(pos)) pos = 0;
            State.selectedBackgroundIdx = Math.max(0, Math.min(pos, chunks.length - 1));
        } else {
            State.selectedBackgroundIdx = 0;
        }
        updateStatsUI();
        if (!chunks.length) {
            State.selectedBackgroundIdx = 0;
            if (DOM.bgDetailEmpty) DOM.bgDetailEmpty.hidden = false;
            if (DOM.bgDetailInner) DOM.bgDetailInner.hidden = true;
            if (DOM.bgDetailContent) DOM.bgDetailContent.textContent = '';
            renderBgNavList();
        } else {
            if (DOM.bgDetailEmpty) DOM.bgDetailEmpty.hidden = true;
            if (DOM.bgDetailInner) DOM.bgDetailInner.hidden = false;
            selectBackgroundChunk(State.selectedBackgroundIdx);
        }
    } catch (error) {
        console.error('获取背景知识库片段失败:', error);
        showNotification('获取背景知识库片段失败: ' + error.message, 'error');
    }
}

async function initBackgroundMasterDetail() {
    if (!DOM.bgNavList) return;
    await refreshBackgroundDetail(() => 0);
}

// ============= 背景知识库 CRUD =============

/**
 * 显示新增背景知识模态框
 */
function showAddBackgroundModal() {
    DOM.newBackgroundContent.value = '';
    DOM.addBackgroundModal.classList.add('show');
}

/**
 * 保存背景知识
 */
async function saveBackground() {
    const content = DOM.newBackgroundContent.value.trim();
    
    if (!content) {
        showNotification('请输入知识内容', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/kb/background/chunks', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content })
        });
        
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json();
        if (data.success) {
            showNotification('背景知识添加成功', 'success');
            DOM.addBackgroundModal.classList.remove('show');
            await fetchKBStats();
            await refreshBackgroundDetail((chunks) => Math.max(0, chunks.length - 1));
        } else {
            throw new Error(data.error || '添加失败');
        }
    } catch (error) {
        console.error('添加背景知识失败:', error);
        showNotification('添加背景知识失败: ' + error.message, 'error');
    }
}

// ============= 事件监听 =============

function initEventListeners(kbType) {
    if (kbType === 'term') {
        if (DOM.loadTermBtn) DOM.loadTermBtn.addEventListener('click', loadTermContent);
        if (DOM.viewTermChunksBtn) DOM.viewTermChunksBtn.addEventListener('click', () => inspectKB('term'));
        if (DOM.rebuildTermBtn) DOM.rebuildTermBtn.addEventListener('click', rebuildTermIndex);
    }
    if (kbType === 'paper') {
        if (DOM.addPaperBtn) DOM.addPaperBtn.addEventListener('click', showAddPaperModal);
        if (DOM.exportPaperBtn) DOM.exportPaperBtn.addEventListener('click', () => exportStats('paper'));
        if (DOM.paperNavSearch) DOM.paperNavSearch.addEventListener('input', renderPaperNavList);
        if (DOM.paperNavList) {
            DOM.paperNavList.addEventListener('click', (e) => {
                const btn = e.target.closest('[data-paper-id]');
                if (!btn) return;
                const id = btn.getAttribute('data-paper-id');
                if (id) loadPaperDetail(id, () => 0);
            });
        }
        if (DOM.paperSegmentStrip) {
            DOM.paperSegmentStrip.addEventListener('click', (e) => {
                const seg = e.target.closest('button[data-seg-pos]');
                if (!seg) return;
                const pos = parseInt(seg.getAttribute('data-seg-pos'), 10);
                if (!Number.isNaN(pos)) selectPaperChunk(pos);
            });
        }
        if (DOM.paperAddSegmentBtn) DOM.paperAddSegmentBtn.addEventListener('click', addChunkToPaper);
        if (DOM.paperDeletePaperBtn) DOM.paperDeletePaperBtn.addEventListener('click', () => {
            if (State.currentPaperId) deletePaper(State.currentPaperId);
        });
        if (DOM.paperEditChunkBtn) DOM.paperEditChunkBtn.addEventListener('click', () => openEditChunkModal('paper'));
        if (DOM.paperDeleteChunkBtn) DOM.paperDeleteChunkBtn.addEventListener('click', () => {
            const ch = State.paperChunksDetail[State.selectedPaperChunkPos];
            if (ch) deleteChunk(ch.index, 'paper');
        });
    }
    if (kbType === 'background') {
        if (DOM.addBackgroundBtn) DOM.addBackgroundBtn.addEventListener('click', showAddBackgroundModal);
        if (DOM.exportBackgroundBtn) DOM.exportBackgroundBtn.addEventListener('click', () => exportStats('background'));
        if (DOM.bgNavSearch) DOM.bgNavSearch.addEventListener('input', renderBgNavList);
        if (DOM.bgNavList) {
            DOM.bgNavList.addEventListener('click', (e) => {
                const btn = e.target.closest('[data-bg-chunk-index]');
                if (!btn) return;
                const ix = parseInt(btn.getAttribute('data-bg-chunk-index'), 10);
                if (Number.isNaN(ix)) return;
                const pos = State.backgroundChunksDetail.findIndex(c => c.index === ix);
                if (pos >= 0) selectBackgroundChunk(pos);
            });
        }
        if (DOM.bgEditChunkBtn) DOM.bgEditChunkBtn.addEventListener('click', () => openEditChunkModal('background'));
        if (DOM.bgDeleteChunkBtn) DOM.bgDeleteChunkBtn.addEventListener('click', () => {
            const ch = State.backgroundChunksDetail[State.selectedBackgroundIdx];
            if (ch) deleteChunk(ch.index, 'background');
        });
    }

    if (DOM.saveChunkBtn) DOM.saveChunkBtn.addEventListener('click', saveChunkEdit);
    if (DOM.saveNewPaperBtn) DOM.saveNewPaperBtn.addEventListener('click', saveNewPaper);
    if (DOM.saveBackgroundBtn) DOM.saveBackgroundBtn.addEventListener('click', saveBackground);
    if (DOM.addChunkToPaperBtn) DOM.addChunkToPaperBtn.addEventListener('click', addChunkToPaper);

    DOM.modalClose.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const modal = e.target.closest('.modal');
            if (modal) modal.classList.remove('show');
        });
    });

    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            e.target.classList.remove('show');
        }
    });
}

// ============= 主题切换 =============

// 从localStorage加载主题
function loadTheme() {
    try {
        const settings = JSON.parse(localStorage.getItem('assistantSettings') || '{}');
        const theme = settings.theme || 'light';
        
        if (theme === 'dark') {
            document.body.classList.add('dark-mode');
        } else if (theme === 'light') {
            document.body.classList.remove('dark-mode');
        } else if (theme === 'system') {
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            if (prefersDark) {
                document.body.classList.add('dark-mode');
            } else {
                document.body.classList.remove('dark-mode');
            }
        }
    } catch (e) {
        console.error('加载主题失败:', e);
    }
}

// ============= 初始化函数（页面加载时执行）=============

async function initPage() {
    const page = document.body.dataset.page;
    if (page === 'index') {
        return;
    }

    const kbType = document.body.dataset.kbType || '';
    console.log('🚀 初始化知识库详情页:', kbType);

    loadTheme();
    initEventListeners(kbType);

    await fetchKBStats();

    if (kbType === 'paper') {
        await initPaperMasterDetail();
    } else if (kbType === 'background') {
        await initBackgroundMasterDetail();
    } else {
        updateStatsUI();
    }

    if (kbType === 'term') {
        console.log('📖 自动加载术语库内容...');
        await loadTermContent();
    }

    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        try {
            const settings = JSON.parse(localStorage.getItem('assistantSettings') || '{}');
            if (settings.theme === 'system') {
                if (e.matches) {
                    document.body.classList.add('dark-mode');
                } else {
                    document.body.classList.remove('dark-mode');
                }
            }
        } catch (err) {
            console.error('主题切换失败:', err);
        }
    });
}

// ============= 页面加载完成后执行 =============
document.addEventListener('DOMContentLoaded', initPage);