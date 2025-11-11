# MLモデル配置ディレクトリ

このディレクトリにはAI/MLモデルファイルを配置します。

## Phase 2で必要なモデル

### 1. YOLOv8 (衣類検出)
```bash
# Pythonスクリプトで自動ダウンロード
from ultralytics import YOLO
model = YOLO('yolov8n.pt')  # nanoモデル（軽量）
```

### 2. CLIP (画像埋め込み)
```bash
# Transformersライブラリで自動ダウンロード
from transformers import CLIPProcessor, CLIPModel
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
```

### 3. ローカルLLM (Phase 2)
最小構成（RTX 3060 12GB）の場合、量子化モデルを使用:

```bash
# Llama 3.2 Vision 11B - GGUF量子化版
# または
# Qwen2-VL-7B-Instruct - AWQ量子化版
```

## 注意事項
- 大きなモデルファイルは.gitignoreで除外されています
- 各モデルは初回起動時に自動ダウンロードされます
- GPU VRAMが不足する場合は量子化レベルを調整してください
