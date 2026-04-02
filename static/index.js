/**
 * 图论学术助手 - 前端交互逻辑
 * 支持Markdown渲染、流式响应、PDF上传、高级设置、主题切换
 */

// ============= DOM 元素 =============
const DOM = {
    chatBox: document.getElementById('chat-box'),
    messageInput: document.getElementById('message'),
    sendBtn: document.getElementById('send'),
    charCount: document.getElementById('char-count'),
    sendText: document.getElementById('send-text'),
    sendIcon: document.getElementById('send-icon'),
    fileInput: document.getElementById('file-input'),
    uploadBtn: document.getElementById('upload-btn'),
    uploadStatus: document.getElementById('upload-status'),
    clearHistoryBtn: document.getElementById('clear-history-btn'),
    settingsBtn: document.getElementById('settings-btn'),
    settingsModal: document.getElementById('settings-modal'),
    modalClose: document.querySelector('.modal-close'),
    settingsCancel: document.getElementById('settings-cancel'),
    settingsSave: document.getElementById('settings-save'),
    themeToggle: document.getElementById('theme-toggle'),
    themeLight: document.getElementById('theme-light'),
    themeDark: document.getElementById('theme-dark'),
    themeSystem: document.getElementById('theme-system'),
    apiBaseUrl: document.getElementById('api-base-url'),
    apiProvider: document.getElementById('api-provider'),
    apiKey: document.getElementById('api-key'),
    modelName: document.getElementById('model-name'),
    temperature: document.getElementById('temperature'),
    temperatureValue: document.getElementById('temperature-value'),
    termSimilarityThreshold: document.getElementById('term-similarity-threshold'),
    termThresholdValue: document.getElementById('term-threshold-value'),
    termMaxResults: document.getElementById('term-max-results'),
    backgroundSimilarityThreshold: document.getElementById('background-similarity-threshold'),
    backgroundThresholdValue: document.getElementById('background-threshold-value'),
    backgroundMaxResults: document.getElementById('background-max-results'),
    paperSimilarityThreshold: document.getElementById('paper-similarity-threshold'),
    paperThresholdValue: document.getElementById('paper-threshold-value'),
    paperMaxResults: document.getElementById('paper-max-results'),
    testMode: document.getElementById('test-mode'),
    testModeText: document.getElementById('test-mode-text'),
    modeStatus: document.getElementById('mode-status'),
    toggleApiKey: document.getElementById('toggle-api-key'),
    toggleIcon: document.getElementById('toggle-icon'),
    assistantLog: document.getElementById('assistant-log'),
    assistantLogPanel: document.getElementById('assistant-log-panel')
};

// ============= 模型配置 =============
const modelOptions = {
    custom: [
        { value: 'gpt-5.2-chat', text: 'gpt-5.2-chat' },
        { value: 'gemini-3-pro-preview', text: 'gemini-3-pro-preview' },
        { value: 'claude-haiku-4-5-20251001', text: 'claude-haiku-4-5-20251001' },
        { value: 'deepseek-v3.2', text: 'deepseek-v3.2' },
        { value: 'glm-4.5', text: 'glm-4.5' }
    ],
    alibaba: [
        { value: 'glm-4.5', text: 'glm-4.5' },
        { value: 'qwen-plus-2025-07-28', text: 'qwen-plus-2025-07-28' },
        { value: 'deepseek-v3', text: 'deepseek-v3' },
        { value: 'kimi-k2.5', text: 'kimi-k2.5' },
        { value: 'MiniMax-M2.5', text: 'MiniMax-M2.5' }
    ]
};

// ============= 状态管理 =============
const State = {
    uploadedFileContent: null,
    uploadedFileName: null,
    isSending: false,
    useRealAPI: false,

    settings: {
        apiBaseUrl: '',
        apiProvider: 'custom',
        apiKey: '',
        modelName: '',
        temperature: 0.7,
        theme: 'light',
        termSimilarityThreshold: 0.5,
        backgroundSimilarityThreshold: 0.5,
        paperSimilarityThreshold: 0.5,
        termMaxResults: 15,
        backgroundMaxResults: 5,
        paperMaxResults: 5,
        testMode: false
    }
};

function updateModeStatus() {
    if (!DOM.modeStatus) return;
    const isTest = !!State.settings.testMode;
    DOM.modeStatus.textContent = isTest ? '模式：测试模式' : '模式：正常模式';
    DOM.modeStatus.classList.toggle('testing', isTest);

    if (DOM.testModeText) {
        DOM.testModeText.textContent = isTest ? '开启' : '关闭';
    }
}

/** 有输入时再显示字数，避免空框旁常驻「0/5000」 */
function syncCharCountUI() {
    if (!DOM.messageInput || !DOM.charCount) return;
    const len = DOM.messageInput.value.length;
    const wrapper = DOM.messageInput.closest('.input-wrapper');
    if (wrapper) {
        wrapper.classList.toggle('input-wrapper--has-count', len > 0);
    }
    DOM.charCount.textContent = `${len}/5000`;
    DOM.charCount.setAttribute('aria-hidden', len === 0 ? 'true' : 'false');
}

// ============= 加载保存的设置 =============
function loadSettings() {
    try {
        const saved = localStorage.getItem('assistantSettings');
        if (saved) {
            const parsed = JSON.parse(saved);
            State.settings = {
                ...State.settings,
                ...parsed,
                termSimilarityThreshold: parsed.termSimilarityThreshold ?? parsed.similarityThreshold ?? 0.5,
                backgroundSimilarityThreshold: parsed.backgroundSimilarityThreshold ?? parsed.similarityThreshold ?? 0.5,
                paperSimilarityThreshold: parsed.paperSimilarityThreshold ?? parsed.similarityThreshold ?? 0.5,
                termMaxResults: parsed.termMaxResults ?? parsed.maxTerms ?? 15,
                backgroundMaxResults: parsed.backgroundMaxResults ?? 5,
                paperMaxResults: parsed.paperMaxResults ?? 5
            };
            
            // 填充表单 - 检查每个元素是否存在
            if (DOM.apiBaseUrl) DOM.apiBaseUrl.value = State.settings.apiBaseUrl || '';
            if (DOM.apiKey) DOM.apiKey.value = State.settings.apiKey || '';
            
            // 供应商和模型下拉框的值在事件绑定初始化时设置
            // 这里只保存状态，不直接操作DOM，避免与初始化逻辑冲突
            
            if (DOM.temperature) {
                DOM.temperature.value = State.settings.temperature || 0.7;
            }
            if (DOM.temperatureValue) {
                DOM.temperatureValue.textContent = State.settings.temperature || 0.7;
            }
            
            if (DOM.termSimilarityThreshold) {
                DOM.termSimilarityThreshold.value = State.settings.termSimilarityThreshold || 0.5;
            }
            if (DOM.termThresholdValue) {
                DOM.termThresholdValue.textContent = (State.settings.termSimilarityThreshold || 0.5).toFixed(2);
            }
            if (DOM.backgroundSimilarityThreshold) {
                DOM.backgroundSimilarityThreshold.value = State.settings.backgroundSimilarityThreshold || 0.5;
            }
            if (DOM.backgroundThresholdValue) {
                DOM.backgroundThresholdValue.textContent = (State.settings.backgroundSimilarityThreshold || 0.5).toFixed(2);
            }
            if (DOM.paperSimilarityThreshold) {
                DOM.paperSimilarityThreshold.value = State.settings.paperSimilarityThreshold || 0.5;
            }
            if (DOM.paperThresholdValue) {
                DOM.paperThresholdValue.textContent = (State.settings.paperSimilarityThreshold || 0.5).toFixed(2);
            }
            if (DOM.termMaxResults) {
                DOM.termMaxResults.value = State.settings.termMaxResults || 15;
            }
            if (DOM.backgroundMaxResults) {
                DOM.backgroundMaxResults.value = State.settings.backgroundMaxResults || 5;
            }
            if (DOM.paperMaxResults) {
                DOM.paperMaxResults.value = State.settings.paperMaxResults || 5;
            }

            if (DOM.testMode) {
                DOM.testMode.checked = !!State.settings.testMode;
            }

            // 应用主题
            applyTheme(State.settings.theme || 'light');
            
            // 检查是否有API配置
            State.useRealAPI = !!(State.settings.apiBaseUrl && State.settings.apiKey);
        }
    } catch (e) {
        console.error('加载设置失败:', e);
    }

    updateModeStatus();
    
    // 设置默认模型
    if (DOM.modelName && !State.settings.modelName && DOM.modelName.options.length > 0) {
        DOM.modelName.selectedIndex = 0;
        State.settings.modelName = DOM.modelName.value;
    }
}

// ============= 保存设置 =============
function saveSettings() {
    State.settings = {
        apiBaseUrl: DOM.apiBaseUrl ? DOM.apiBaseUrl.value.trim() : '',
        apiKey: DOM.apiKey ? DOM.apiKey.value.trim() : '',
        apiProvider: DOM.apiProvider ? DOM.apiProvider.value : 'custom',
        modelName: DOM.modelName ? DOM.modelName.value.trim() : '',
        temperature: DOM.temperature ? parseFloat(DOM.temperature.value) : 0.7,
        theme: State.settings.theme || 'light',
        termSimilarityThreshold: DOM.termSimilarityThreshold ? parseFloat(DOM.termSimilarityThreshold.value) : 0.5,
        backgroundSimilarityThreshold: DOM.backgroundSimilarityThreshold ? parseFloat(DOM.backgroundSimilarityThreshold.value) : 0.5,
        paperSimilarityThreshold: DOM.paperSimilarityThreshold ? parseFloat(DOM.paperSimilarityThreshold.value) : 0.5,
        termMaxResults: DOM.termMaxResults ? parseInt(DOM.termMaxResults.value, 10) : 15,
        backgroundMaxResults: DOM.backgroundMaxResults ? parseInt(DOM.backgroundMaxResults.value, 10) : 5,
        paperMaxResults: DOM.paperMaxResults ? parseInt(DOM.paperMaxResults.value, 10) : 5,
        testMode: DOM.testMode ? DOM.testMode.checked : false
    };
    
    localStorage.setItem('assistantSettings', JSON.stringify(State.settings));
    
    // 检查是否可以使用真实API
    State.useRealAPI = !!(State.settings.apiBaseUrl && State.settings.apiKey);
    
    // 关闭模态框
    if (DOM.settingsModal) {
        DOM.settingsModal.classList.remove('show');
    }

    updateModeStatus();
    
    // 显示保存成功提示
    showUploadStatus('成功', '设置已保存', 'success');
}

// ============= 主题切换 =============
function applyTheme(theme) {
    State.settings.theme = theme;
    
    // 更新按钮状态 - 检查元素是否存在
    if (DOM.themeLight) DOM.themeLight.classList.remove('active');
    if (DOM.themeDark) DOM.themeDark.classList.remove('active');
    if (DOM.themeSystem) DOM.themeSystem.classList.remove('active');
    
    if (theme === 'light') {
        document.body.classList.remove('dark-mode');
        if (DOM.themeLight) DOM.themeLight.classList.add('active');
        if (DOM.themeToggle) {
            const icon = DOM.themeToggle.querySelector('.theme-icon');
            if (icon) icon.textContent = '☀️';
        }
    } else if (theme === 'dark') {
        document.body.classList.add('dark-mode');
        if (DOM.themeDark) DOM.themeDark.classList.add('active');
        if (DOM.themeToggle) {
            const icon = DOM.themeToggle.querySelector('.theme-icon');
            if (icon) icon.textContent = '🌙';
        }
    } else {
        // 跟随系统
        if (DOM.themeSystem) DOM.themeSystem.classList.add('active');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        if (prefersDark) {
            document.body.classList.add('dark-mode');
            if (DOM.themeToggle) {
                const icon = DOM.themeToggle.querySelector('.theme-icon');
                if (icon) icon.textContent = '🌙';
            }
        } else {
            document.body.classList.remove('dark-mode');
            if (DOM.themeToggle) {
                const icon = DOM.themeToggle.querySelector('.theme-icon');
                if (icon) icon.textContent = '☀️';
            }
        }
    }
    
    // 保存主题设置
    localStorage.setItem('assistantSettings', JSON.stringify(State.settings));
}

// ============= Markdown 配置 =============
marked.setOptions({
    breaks: true,
    gfm: true,
    headerIds: true,
    mangle: false,
    highlight: (code, lang) => code
});

/**
 * 安全渲染 Markdown
 */
function renderMarkdown(text) {
    if (!text) return '';
    try {
        const html = marked.parse(text);
        return DOMPurify.sanitize(html, {
            USE_PROFILES: { html: true },
            ADD_TAGS: ['math', 'svg', 'path'],
            ADD_ATTR: ['xmlns', 'viewBox', 'd', 'width', 'height']
        });
    } catch (e) {
        console.error('Markdown渲染失败:', e);
        return `<pre>${text}</pre>`;
    }
}

// ============= 消息管理 =============

/**
 * 添加消息到聊天框
 */
function addMessage(role, text, isMarkdown = true) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const time = new Date().toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit'
    });

    const contentHtml = (role === 'assistant' && isMarkdown) 
        ? renderMarkdown(text) 
        : text.replace(/\n/g, '<br>');

    messageDiv.innerHTML = `
        <div class="avatar">${role === 'user' ? '你' : 'AI'}</div>
        <div class="message-wrapper">
            <div class="message-content markdown-body">${contentHtml}</div>
            <div class="message-time">${time}</div>
        </div>
    `;

    // 移除欢迎信息
    const welcome = DOM.chatBox.querySelector('.welcome-message');
    if (welcome && DOM.chatBox.children.length > 1) {
        welcome.remove();
    }

    DOM.chatBox.appendChild(messageDiv);
    DOM.chatBox.scrollTop = DOM.chatBox.scrollHeight;
    
    return messageDiv.querySelector('.message-content');
}

/**
 * 显示打字指示器
 */
function showTypingIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'message assistant';
    indicator.innerHTML = `
        <div class="avatar">AI</div>
        <div class="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    DOM.chatBox.appendChild(indicator);
    DOM.chatBox.scrollTop = DOM.chatBox.scrollHeight;
    return indicator;
}

/**
 * 显示PDF上下文提示
 */
function showPDFContext() {
    if (!State.uploadedFileName) return;
    
    // 移除已有的PDF上下文
    const existing = document.querySelector('.pdf-context');
    if (existing) existing.remove();
    
    const contextDiv = document.createElement('div');
    contextDiv.className = 'pdf-context';
    contextDiv.innerHTML = `
        <span class="pdf-icon">📄</span>
        <span class="pdf-filename">${State.uploadedFileName}</span>
        <span>已加载，可进行问答</span>
        <button class="clear-pdf" title="清除PDF上下文">✕</button>
    `;
    
    DOM.chatBox.parentNode.insertBefore(contextDiv, DOM.chatBox.nextSibling);
    
    // 绑定清除事件
    contextDiv.querySelector('.clear-pdf').addEventListener('click', () => {
        State.uploadedFileContent = null;
        State.uploadedFileName = null;
        contextDiv.remove();
        showUploadStatus('成功', 'PDF上下文已清除', 'success');
    });
}

// ============= 文件上传 =============

/**
 * 显示上传状态
 */
function showUploadStatus(title, message, type) {
    const icons = { success: '✅', error: '❌', processing: '⏳' };
    const icon = icons[type] || '📄';
    
    DOM.uploadStatus.style.display = 'flex';
    DOM.uploadStatus.className = `upload-status ${type}`;
    
    DOM.uploadStatus.innerHTML = `
        <div class="upload-info">
            <span class="file-icon">${icon}</span>
            <span class="upload-filename">${title}</span>
            <span>${message}</span>
            ${type === 'processing' ? '<span class="upload-progress"></span>' : ''}
        </div>
        <button class="upload-close">✕</button>
    `;

    // 只有处理中状态自动隐藏，成功/错误状态保持显示直到用户主动关闭
    if (type === 'processing') {
        // 处理中状态不自动隐藏
    }
    // 成功和错误状态保持显示，让用户可以看到上传的文件信息
}

/**
 * 上传PDF文件
 */
async function uploadPDF(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    showUploadStatus('处理中', `正在上传 ${file.name}...`, 'processing');
    
    try {
        const response = await fetch('/upload_pdf', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) throw new Error(`上传失败: ${response.status}`);
        
        const data = await response.json();
        
        if (data.success) {
            State.uploadedFileContent = data.content;
            State.uploadedFileName = file.name;
            
            showUploadStatus('成功', `已上传: ${file.name} (${data.page_count}页)`, 'success');
            // showPDFContext();
            
            // DOM.messageInput.value = `请分析这篇PDF文档：${file.name}`;
            syncCharCountUI();
        } else {
            throw new Error(data.error || '上传失败');
        }
    } catch (error) {
        console.error('上传错误:', error);
        showUploadStatus('错误', error.message, 'error');
    }
    
    DOM.fileInput.value = '';
}

// ============= 模拟响应生成 =============

/**
 * 生成PDF分析响应
 */
function generatePDFResponse(question, filename) {
    return `📄 **PDF文档分析**

关于您上传的文档 **《${filename}》**，我将为您进行分析：

## 📊 文档概览
- 文件名：${filename}
- 分析模式：基于文档内容的智能问答
- 当前问题：${question}

## 💡 回答
由于当前使用的是模拟数据模式，我无法真正解析PDF内容。要获得真实的PDF分析能力，请：

1. ⚙️ 点击右上角的"设置"按钮
2. 🔑 配置您的API Key和基础地址
3. 🚀 重新发送问题

## 📝 模拟回答示例
如果您配置了API，我可以：
- 提取论文的核心创新点
- 总结研究方法与实验结果
- 回答关于论文内容的具体问题
- 解释专业术语和技术细节

---
*当前处于模拟数据模式，配置API后即可获得真实的PDF解析功能*`;
}

/**
 * 生成普通对话响应
 */
function generateChatResponse(question) {
    return `🤖 **AI助手回复 (模拟模式)**

关于您的问题："${question}"

## 当前模式说明
目前处于**模拟数据模式**，因为我还没有配置API密钥。

## 配置方式
1. ⚙️ 点击右上角的"设置"按钮
2. 🔑 填写您的API信息：
   - API基础地址
   - API Key
   - 模型名称
3. 💾 保存设置后即可使用真实AI能力

## 预留功能
配置API后，您可以：
- 📄 上传PDF进行智能问答
- 🔬 深入分析科研论文
- 📊 获取专业的学术建议
- 💬 进行自然对话交流
`;
}

// ============= 流式通信 =============

function escapeHtml(s) {
    if (s === null || s === undefined) return '';
    if (typeof s === 'object') {
        try {
            const raw = JSON.stringify(s, null, 2);
            const d = document.createElement('div');
            d.textContent = raw;
            return d.innerHTML;
        } catch (e) {
            const d = document.createElement('div');
            d.textContent = String(s);
            return d.innerHTML;
        }
    }
    const d = document.createElement('div');
    d.textContent = String(s);
    return d.innerHTML;
}

/**
 * 将 SSE 中的 log 规范为单条对象或数组（兼容字符串 JSON、数组批量）
 */
function normalizeLogPayload(raw) {
    if (raw == null || raw === '') return null;
    if (typeof raw === 'string') {
        const t = raw.trim();
        if ((t.startsWith('{') && t.endsWith('}')) || (t.startsWith('[') && t.endsWith(']'))) {
            try {
                return JSON.parse(t);
            } catch (e) {
                return raw;
            }
        }
        return raw;
    }
    return raw;
}

/**
 * 将后端结构化日志（或兼容旧版字符串）渲染为运行日志条目
 */
function renderLogEntry(entry) {
    if (entry == null || entry === '') return null;

    if (typeof entry === 'string') {
        const pre = document.createElement('pre');
        pre.className = 'log-entry log-entry-legacy';
        pre.textContent = String(entry).replace(/\*\*/g, '');
        return pre;
    }

    if (typeof entry !== 'object') return null;

    const kind = entry.kind || entry.type || 'unknown';
    const v = entry.v;
    const article = document.createElement('article');
    article.className = 'log-entry';
    article.dataset.kind = kind;

    const head = document.createElement('div');
    head.className = 'log-entry-head';
    head.innerHTML = `<span class="log-kind">${escapeHtml(kind)}</span>` +
        (v != null && v !== 1 ? `<span class="log-schema-v">schema v${escapeHtml(v)}</span>` : '');
    article.appendChild(head);

    const body = document.createElement('div');
    body.className = 'log-entry-body';

    function addKv(label, value) {
        if (value === null || value === undefined || value === '') return;
        const row = document.createElement('div');
        row.className = 'log-kv';
        row.innerHTML = `<span class="log-k">${escapeHtml(label)}</span>` +
            `<span class="log-v">${escapeHtml(value)}</span>`;
        body.appendChild(row);
    }

    if (kind === 'intent') {
        addKv('整体意图', entry.overall_label || entry.overall_intent);
        addKv('识别方法', entry.overall_method);
        addKv('测试模式', entry.test_mode ? '是' : '否');
        if (entry.text_intent) {
            addKv('文本意图', entry.text_label || entry.text_intent);
            addKv('文本识别方法', entry.text_method);
        }
    } else if (kind === 'term_query_source') {
        addKv('Query 来源', entry.source);
    } else if (kind === 'term_retrieval') {
        addKv('Agent', entry.agent);
        if (entry.query_preview) addKv('检索 Query', entry.query_preview);
        addKv('命中数量', String(entry.count));
        addKv('相似度阈值', String(entry.threshold));
        addKv('最大条数', String(entry.max_terms));
        if (entry.count === 0) addKv('召回', '无高于阈值的片段');
        if (Array.isArray(entry.terms) && entry.terms.length) {
            const tbl = document.createElement('table');
            tbl.className = 'log-terms-table';
            tbl.innerHTML = '<thead><tr><th>#</th><th>相似度</th><th>预览</th></tr></thead>';
            const tb = document.createElement('tbody');
            entry.terms.forEach((t, i) => {
                const tr = document.createElement('tr');
                tr.innerHTML = `<td>${i + 1}</td><td>${escapeHtml(t.similarity)}</td><td class="log-term-preview">${escapeHtml(t.preview)}</td>`;
                tb.appendChild(tr);
            });
            tbl.appendChild(tb);
            body.appendChild(tbl);
        }
    } else if (kind === 'background_retrieval') {
        addKv('Agent', entry.agent);
        if (entry.query_preview) addKv('检索 Query', entry.query_preview);
        addKv('命中数量', String(entry.count));
        addKv('阈值', String(entry.threshold));
        addKv('最大条数', String(entry.max_results));
        if (entry.count === 0) addKv('召回', '无高于阈值的片段');
        if (Array.isArray(entry.chunks) && entry.chunks.length) {
            const tbl = document.createElement('table');
            tbl.className = 'log-terms-table';
            tbl.innerHTML = '<thead><tr><th>#</th><th>相似度</th><th>片段预览</th></tr></thead>';
            const tb = document.createElement('tbody');
            entry.chunks.forEach((c, i) => {
                const tr = document.createElement('tr');
                tr.innerHTML = `<td>${i + 1}</td><td>${escapeHtml(c.similarity)}</td><td class="log-term-preview">${escapeHtml(c.preview)}</td>`;
                tb.appendChild(tr);
            });
            tbl.appendChild(tb);
            body.appendChild(tbl);
        }
    } else if (kind === 'qa_mode') {
        addKv('子模式', entry.mode === 'fact' ? '事实型（短答）' : '思路探讨型（分析模板）');
        addKv('判定说明', entry.reason);
        if (entry.retrieval_boost_threshold != null) {
            addKv('检索强化阈值', String(entry.retrieval_boost_threshold));
        }
    } else if (kind === 'qa_paper_retrieval' || kind === 'qa_background_retrieval') {
        addKv('Agent', entry.agent);
        addKv('知识库', kind === 'qa_paper_retrieval' ? '论文库' : '背景库');
        if (entry.query_preview) addKv('检索 Query', entry.query_preview);
        addKv('命中数量', String(entry.count));
        addKv('阈值', String(entry.threshold));
        addKv('最大条数', String(entry.max_results));
        if (entry.count === 0) addKv('召回', '无高于阈值的片段');
        if (Array.isArray(entry.chunks) && entry.chunks.length) {
            const tbl = document.createElement('table');
            tbl.className = 'log-terms-table';
            tbl.innerHTML = '<thead><tr><th>#</th><th>相似度</th><th>片段预览</th></tr></thead>';
            const tb = document.createElement('tbody');
            entry.chunks.forEach((c, i) => {
                const tr = document.createElement('tr');
                tr.innerHTML = `<td>${i + 1}</td><td>${escapeHtml(c.similarity)}</td><td class="log-term-preview">${escapeHtml(c.preview)}</td>`;
                tb.appendChild(tr);
            });
            tbl.appendChild(tb);
            body.appendChild(tbl);
        }
    } else if (kind === 'pipeline_step') {
        addKv('步骤', String(entry.step));
        addKv('阶段', entry.phase);
        addKv('说明', entry.label);
    } else if (kind === 'kb_update') {
        addKv('知识库', entry.kb_name || entry.kb_key);
        addKv('成功', entry.success ? '是' : '否');
        if (entry.mode) addKv('模式', entry.mode);
        if (entry.chunk_count != null) addKv('总片段数', String(entry.chunk_count));
        if (entry.new_chunks != null) addKv('新增片段', String(entry.new_chunks));
        if (entry.paper_title) addKv('论文标题', entry.paper_title);
        if (entry.filename) addKv('文件名', entry.filename);
        if (entry.index_path) addKv('索引路径', entry.index_path);
        if (entry.chunks_inspect_path) addKv('分段可视化', entry.chunks_inspect_path);
        if (entry.hint_prefix) addKv('来源摘要', entry.hint_prefix);
        if (entry.error) addKv('错误', entry.error);
    } else {
        const pre = document.createElement('pre');
        pre.className = 'log-json-fallback';
        pre.textContent = JSON.stringify(entry, null, 2);
        body.appendChild(pre);
    }

    article.appendChild(body);
    return article;
}

function appendAssistantLog(entry) {
    if (!DOM.assistantLog) return;
    if (Array.isArray(entry)) {
        entry.forEach((item) => appendAssistantLog(item));
        return;
    }
    const el = renderLogEntry(entry);
    if (el) {
        DOM.assistantLog.appendChild(el);
        DOM.assistantLog.scrollTop = DOM.assistantLog.scrollHeight;
    }
    DOM.chatBox.scrollTop = DOM.chatBox.scrollHeight;
}

async function handleStreamResponse(response, assistantContent) {
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let fullContent = '';

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const jsonStr = line.replace(/^data: /, '');
                if (jsonStr === '[DONE]') continue;
                
                try {
                    const data = JSON.parse(jsonStr);
                    if (data.log != null && data.log !== '') {
                        const normalized = normalizeLogPayload(data.log);
                        if (normalized != null) {
                            appendAssistantLog(normalized);
                        }
                    }
                    if (data.text) {
                        fullContent += data.text;
                        assistantContent.innerHTML = renderMarkdown(fullContent);
                        DOM.chatBox.scrollTop = DOM.chatBox.scrollHeight;
                    }
                } catch (e) {
                    console.error('解析错误:', e);
                }
            }
        }
    }
}

/**
 * 模拟流式响应
 */
async function* generateMockStream(text) {
    const chunkSize = 4;
    const delay = 20;
    
    for (let i = 0; i < text.length; i += chunkSize) {
        const chunk = text.slice(i, i + chunkSize);
        yield chunk;
        await new Promise(resolve => setTimeout(resolve, delay));
    }
}

/**
 * 发送消息
 */
async function sendMessage() {
    const msg = DOM.messageInput.value.trim();
    if (!msg || State.isSending) return;

    // 构建用户消息内容（包含PDF信息）
    let userMessageContent = msg;
    if (State.uploadedFileName) {
        userMessageContent = `[📄 ${State.uploadedFileName}]\n${msg}`;
    }
    
    // 添加用户消息
    addMessage('user', userMessageContent);
    DOM.messageInput.value = '';
    DOM.messageInput.style.height = 'auto';
    syncCharCountUI();

    // 锁定界面
    State.isSending = true;
    DOM.messageInput.disabled = true;
    DOM.sendBtn.disabled = true;
    DOM.sendBtn.innerHTML = '<span class="loading"></span>';

    if (DOM.assistantLog) {
        DOM.assistantLog.innerHTML = '';
    }
    if (DOM.assistantLogPanel) {
        DOM.assistantLogPanel.open = true;
    }

    // 显示打字指示器
    const typingIndicator = showTypingIndicator();

    try {
        const shouldUseBackend = State.settings.testMode || State.useRealAPI;

        if (shouldUseBackend) {
            // 使用真实API
            const requestData = {
                message: msg,
                settings: State.settings,
                ...(State.uploadedFileContent && {
                    file_content: State.uploadedFileContent,
                    file_name: State.uploadedFileName
                })
            };

            const response = await fetch('/chat_stream_real', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'text/event-stream'
                },
                body: JSON.stringify(requestData)
            });

            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

            typingIndicator.remove();

            const assistantDiv = addMessage('assistant', '');
            const assistantContent = assistantDiv.parentElement.parentElement.querySelector('.message-content');

            await handleStreamResponse(response, assistantContent);
        } else {
            // 使用模拟数据
            typingIndicator.remove();
            
            const assistantDiv = addMessage('assistant', '');
            const assistantContent = assistantDiv.parentElement.parentElement.querySelector('.message-content');
            
            // 根据是否有PDF生成不同响应
            let fullResponse;
            if (State.uploadedFileName) {
                fullResponse = generatePDFResponse(msg, State.uploadedFileName);
            } else {
                fullResponse = generateChatResponse(msg);
            }
            
            // 模拟流式输出 - 修复换行问题
            assistantContent.innerHTML = '';
            let accumulatedText = '';
            
            for await (const chunk of generateMockStream(fullResponse)) {
                accumulatedText += chunk;
                // 每次都重新渲染完整的Markdown，确保格式正确
                assistantContent.innerHTML = renderMarkdown(accumulatedText);
                DOM.chatBox.scrollTop = DOM.chatBox.scrollHeight;
            }
        }
    } catch (error) {
        console.error('请求失败:', error);
        typingIndicator.remove();

        const errorDiv = addMessage('assistant', '');
        const errorContent = errorDiv.parentElement.parentElement.querySelector('.message-content');
        errorContent.innerHTML = `❌ 抱歉，出现了错误: ${error.message}<br>请稍后重试。`;
        errorContent.style.color = '#ef4444';
    } finally {
        // 解锁界面
        State.isSending = false;
        DOM.messageInput.disabled = false;
        DOM.sendBtn.disabled = false;
        DOM.sendBtn.innerHTML = '<span id="send-text">发送</span><span id="send-icon" style="display: none;">⏎</span>';
        DOM.messageInput.focus();
        
        // 发送完成后清除上传状态
        if (State.uploadedFileName) {
            State.uploadedFileContent = null;
            State.uploadedFileName = null;
            if (DOM.uploadStatus) {
                DOM.uploadStatus.style.display = 'none';
            }
        }
    }
}

/**
 * 清除对话历史
 */
async function clearHistory() {
    if (!confirm('确定要清除所有对话历史吗？此操作不可恢复。')) return;
    
    try {
        const response = await fetch('/clear_history', { method: 'POST' });
        if (!response.ok) throw new Error(`清除失败: ${response.status}`);
        
        const data = await response.json();
        
        if (data.success) {
            // 重置聊天界面（不显示欢迎内容）
            DOM.chatBox.innerHTML = '';
            if (DOM.assistantLog) {
                DOM.assistantLog.innerHTML = '';
            }
            
            // 清除PDF上下文
            State.uploadedFileContent = null;
            State.uploadedFileName = null;
            const pdfContext = document.querySelector('.pdf-context');
            if (pdfContext) pdfContext.remove();
            
            showUploadStatus('成功', '对话历史已清除', 'success');
        }
    } catch (error) {
        console.error('清除历史失败:', error);
        alert('清除历史失败: ' + error.message);
    }
}

// ============= 事件监听 =============

function initEventListeners() {
    // 示例按钮
    document.querySelectorAll('.example-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            if (DOM.messageInput) {
                DOM.messageInput.value = btn.dataset.question;
                sendMessage();
            }
        });
    });

    // 字符计数
    if (DOM.messageInput) {
        // 自动调整高度函数
        function autoResizeTextarea() {
            DOM.messageInput.style.height = 'auto';
            DOM.messageInput.style.height = Math.min(DOM.messageInput.scrollHeight, 200) + 'px';
        }
        
        DOM.messageInput.addEventListener('input', () => {
            syncCharCountUI();
            // 自动调整高度
            autoResizeTextarea();
        });

        // 输入框焦点
        DOM.messageInput.addEventListener('focus', () => {
            if (DOM.sendText) DOM.sendText.style.display = 'none';
            if (DOM.sendIcon) DOM.sendIcon.style.display = 'inline';
        });

        DOM.messageInput.addEventListener('blur', () => {
            if (!DOM.messageInput.value.trim()) {
                if (DOM.sendText) DOM.sendText.style.display = 'inline';
                if (DOM.sendIcon) DOM.sendIcon.style.display = 'none';
            }
        });

        // 键盘事件 - 支持Shift+Enter换行，Enter发送
        DOM.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    // 发送消息
    if (DOM.sendBtn) {
        DOM.sendBtn.addEventListener('click', sendMessage);
    }

    // 文件上传
    if (DOM.uploadBtn && DOM.fileInput) {
        DOM.uploadBtn.addEventListener('click', () => DOM.fileInput.click());
        DOM.fileInput.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;
            
            if (file.type !== 'application/pdf') {
                showUploadStatus('错误', '请上传PDF文件', 'error');
                return;
            }
            
            if (file.size > 20 * 1024 * 1024) {
                showUploadStatus('错误', '文件大小不能超过20MB', 'error');
                return;
            }
            
            await uploadPDF(file);
        });
    }

    // 清除历史 / 新对话
    if (DOM.clearHistoryBtn) {
        DOM.clearHistoryBtn.addEventListener('click', clearHistory);
    }
    // 设置按钮
    if (DOM.settingsBtn && DOM.settingsModal) {
        DOM.settingsBtn.addEventListener('click', () => {
            DOM.settingsModal.classList.add('show');
        });
    }

    // 关闭模态框
    const closeModal = () => {
        if (DOM.settingsModal) {
            DOM.settingsModal.classList.remove('show');
        }
    };

    if (DOM.modalClose) {
        DOM.modalClose.addEventListener('click', closeModal);
    }
    if (DOM.settingsCancel) {
        DOM.settingsCancel.addEventListener('click', closeModal);
    }

    // 点击模态框外部关闭
    window.addEventListener('click', (e) => {
        if (e.target === DOM.settingsModal) {
            closeModal();
        }
    });

    // 保存设置
    if (DOM.settingsSave) {
        DOM.settingsSave.addEventListener('click', saveSettings);
    }

    // 温度滑块
    if (DOM.temperature && DOM.temperatureValue) {
        DOM.temperature.addEventListener('input', () => {
            DOM.temperatureValue.textContent = DOM.temperature.value;
        });
    }

    // 三个知识库相似度阈值滑块
    if (DOM.termSimilarityThreshold && DOM.termThresholdValue) {
        DOM.termSimilarityThreshold.addEventListener('input', () => {
            DOM.termThresholdValue.textContent = parseFloat(DOM.termSimilarityThreshold.value).toFixed(2);
        });
    }
    if (DOM.backgroundSimilarityThreshold && DOM.backgroundThresholdValue) {
        DOM.backgroundSimilarityThreshold.addEventListener('input', () => {
            DOM.backgroundThresholdValue.textContent = parseFloat(DOM.backgroundSimilarityThreshold.value).toFixed(2);
        });
    }
    if (DOM.paperSimilarityThreshold && DOM.paperThresholdValue) {
        DOM.paperSimilarityThreshold.addEventListener('input', () => {
            DOM.paperThresholdValue.textContent = parseFloat(DOM.paperSimilarityThreshold.value).toFixed(2);
        });
    }

    if (DOM.testMode) {
        DOM.testMode.addEventListener('change', () => {
            const isTest = DOM.testMode.checked;
            if (DOM.testModeText) {
                DOM.testModeText.textContent = isTest ? '开启' : '关闭';
            }
        });
    }

    // API Key 显示/隐藏切换
    if (DOM.toggleApiKey && DOM.apiKey && DOM.toggleIcon) {
        DOM.toggleApiKey.addEventListener('click', () => {
            const isPassword = DOM.apiKey.type === 'password';
            DOM.apiKey.type = isPassword ? 'text' : 'password';
            DOM.toggleIcon.textContent = isPassword ? '🙈' : '👁️';
            DOM.toggleApiKey.title = isPassword ? '隐藏密码' : '显示密码';
        });
    }

    // 模型供应商切换
    function updateModelOptions(provider) {
        if (!DOM.modelName) return;
        const options = modelOptions[provider] || modelOptions.custom;
        DOM.modelName.innerHTML = options.map(opt => 
            `<option value="${opt.value}">${opt.text}</option>`
        ).join('');
    }

    if (DOM.apiProvider) {
        DOM.apiProvider.addEventListener('change', () => {
            const provider = DOM.apiProvider.value;
            updateModelOptions(provider);
            // 保存当前选择到状态
            State.settings.apiProvider = provider;
            State.settings.modelName = DOM.modelName.value;
        });
        // 初始化时根据保存的供应商更新模型列表，并恢复保存的模型
        if (State.settings.apiProvider) {
            DOM.apiProvider.value = State.settings.apiProvider;
            updateModelOptions(State.settings.apiProvider);
            // 恢复保存的模型选择
            if (State.settings.modelName && DOM.modelName) {
                // 检查保存的模型是否在当前供应商的选项中
                const options = modelOptions[State.settings.apiProvider] || modelOptions.custom;
                const modelExists = options.some(opt => opt.value === State.settings.modelName);
                if (modelExists) {
                    DOM.modelName.value = State.settings.modelName;
                } else {
                    // 如果保存的模型不在当前供应商列表中，选择第一个并更新状态
                    DOM.modelName.selectedIndex = 0;
                    State.settings.modelName = DOM.modelName.value;
                }
            }
        }
    }

    // 主题切换按钮
    if (DOM.themeToggle) {
        DOM.themeToggle.addEventListener('click', () => {
            if (State.settings.theme === 'light') {
                applyTheme('dark');
            } else if (State.settings.theme === 'dark') {
                applyTheme('light');
            } else {
                applyTheme('light');
            }
        });
    }

    // 主题选项
    if (DOM.themeLight) {
        DOM.themeLight.addEventListener('click', () => applyTheme('light'));
    }
    if (DOM.themeDark) {
        DOM.themeDark.addEventListener('click', () => applyTheme('dark'));
    }
    if (DOM.themeSystem) {
        DOM.themeSystem.addEventListener('click', () => applyTheme('system'));
    }

    // 上传状态关闭
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('upload-close')) {
            e.target.parentElement.style.display = 'none';
        }
    });

    // 监听系统主题变化
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (State.settings.theme === 'system') {
            if (e.matches) {
                document.body.classList.add('dark-mode');
                if (DOM.themeToggle) {
                    const icon = DOM.themeToggle.querySelector('.theme-icon');
                    if (icon) icon.textContent = '🌙';
                }
            } else {
                document.body.classList.remove('dark-mode');
                if (DOM.themeToggle) {
                    const icon = DOM.themeToggle.querySelector('.theme-icon');
                    if (icon) icon.textContent = '☀️';
                }
            }
        }
    });
}

// ============= 初始化 =============
document.addEventListener('DOMContentLoaded', () => {
    loadSettings();
    initEventListeners();
    syncCharCountUI();
    if (DOM.messageInput) {
        DOM.messageInput.focus();
    }
});