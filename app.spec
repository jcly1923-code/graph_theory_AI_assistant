# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[('templates', 'templates'), ('static', 'static'), ('local_models', 'local_models')],
    hiddenimports=[
        'flask',
        'web',
        'web.routes',
        'web.routes.pages',
        'web.routes.chat',
        'web.routes.kb',
        'web.knowledge_bases',
        'web.config',
        'web.agents',
        'web.retrieval',
        'web.history',
        'web.sse',
        'web.kb_operations',
        'web.qa_professional_mode',
        'knowledge_base',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
