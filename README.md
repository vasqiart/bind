<<<<<<< HEAD
# Bind

Mac用デスクトップアプリ - フォルダ内のJPEG画像を順番通りに1つのPDFにまとめる

## 機能

- フォルダ内のJPEG画像（最大300枚想定）を順番通りに1つのPDFへ変換
- ドラッグ&ドロップ対応
- 進捗表示とプログレスバー
- 自然順ソート（ファイル名の数字列を抽出して比較）
- JPEG再圧縮なし（画質劣化しにくい）

## セットアップ

### 仮想環境作成（Mac）

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 依存インストール

```bash
pip install -r requirements.txt
```

## 実行

### 開発実行

```bash
python app.py
```

### アプリ化（.app作成）

```bash
pip install pyinstaller
pyinstaller --windowed --name Bind app.py
```

生成された `.app` ファイルは `dist/Bind.app` にあります。

## 使い方

1. Bind.app をダブルクリックで起動
2. フォルダをドラッグ＆ドロップ、または「Select Folder」で選択
3. 「Create PDF」を押す
4. PDFはフォルダの親ディレクトリに「フォルダ名.pdf」で保存
   - 例：`/Desktop/KindleShots/` → `/Desktop/KindleShots.pdf`

## 仕様

- **出力PDF名**: フォルダ名.pdf
- **保存先**: 選択したフォルダの親ディレクトリ
- **同名PDFが既にある場合**: 上書き
- **ソート**: ファイル名に含まれる数字列を抽出して自然順ソート
- **対象拡張子**: .jpg/.jpeg（大小文字両対応）
- **枚数**: 300枚以下は一括変換、それ以上は自動的にバッチ処理

## 注意事項

- ローカル完結で画像は外部送信しません
- JPEGは再圧縮しないため画質劣化がありません
- フォルダ以外がドロップされた場合はエラー表示されます
=======
# bind
>>>>>>> e95f4fa92b05e33cd2669bcea8cfd37ac874d357
