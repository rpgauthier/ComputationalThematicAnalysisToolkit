# -*- mode: python ; coding: utf-8 -*-

# python3 -m PyInstaller --windowed --additional-hooks-dir=. pyinstaller-OSX.spec

import sys
sys.setrecursionlimit(5000)

block_cipher = None


a = Analysis(['src/Main.py'],
             binaries=[],
             datas=[('src/Images/*', 'Images'),
                    ('src/Fonts/*', 'Fonts'),
                    ('src/External/XSD/*', 'External/XSD'),
                    ('/Library/Frameworks/Python.framework/Versions/3.9/lib/python3.9/site-packages/wordcloud/stopwords', 'wordcloud' ),
                    ('/Library/Frameworks/Python.framework/Versions/3.9/lib/python3.9/site-packages/wordcloud/DroidSansMono.ttf', 'wordcloud' ),
                    ('/Library/Frameworks/Python.framework/Versions/3.9/lib/python3.9/site-packages/xmlschema/schemas', 'xmlschema/schemas')],
             hiddenimports=['sklearn.utils._weight_vector', 'wx._xml', 'PIL.ImageFont'],
             hookspath=['.'],
             hooksconfig={},
             runtime_hooks=[],
             excludes=['torch'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='Toolkit',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='bin')
app = BUNDLE(coll,
             name='Computational Thematic Analysis Toolkit.app',
             icon=None,
             bundle_identifier=None,
             version='0.8.10')
