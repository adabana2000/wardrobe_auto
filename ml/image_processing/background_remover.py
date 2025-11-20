"""
背景除去モジュール
rembgを使用した衣類画像の背景除去
"""

from typing import Optional
from pathlib import Path
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class BackgroundRemover:
    """
    rembgを使用した背景除去クラス
    """

    def __init__(self):
        """
        背景除去モデルを初期化
        """
        self.available = self._check_availability()

    def _check_availability(self) -> bool:
        """rembgの利用可能性をチェック"""
        try:
            import rembg
            logger.info("rembg is available")
            return True
        except ImportError:
            logger.warning(
                "rembg not installed. Install with: pip install rembg"
            )
            return False

    def remove_background(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        alpha_matting: bool = False,
    ) -> str:
        """
        画像から背景を除去

        Args:
            input_path: 入力画像パス
            output_path: 出力画像パス（Noneの場合は入力パスに基づいて自動生成）
            alpha_matting: アルファマッティングを使用するかどうか

        Returns:
            str: 出力画像のパス
        """
        if not self.available:
            logger.warning("rembg not available. Skipping background removal.")
            return input_path  # 背景除去せずに元の画像を返す

        try:
            from rembg import remove

            # 画像を読み込み
            if not Path(input_path).exists():
                raise FileNotFoundError(f"Image not found: {input_path}")

            input_image = Image.open(input_path)

            # 背景除去
            output_image = remove(
                input_image,
                alpha_matting=alpha_matting,
            )

            # 出力パスが指定されていない場合は自動生成
            if output_path is None:
                input_path_obj = Path(input_path)
                output_path = str(
                    input_path_obj.parent / f"{input_path_obj.stem}_nobg.png"
                )

            # 画像を保存（PNG形式で透明度を保持）
            output_image.save(output_path, "PNG")

            logger.info(f"Background removed. Saved to: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Background removal failed: {e}")
            return input_path  # エラー時は元の画像を返す

    def remove_background_batch(
        self,
        input_paths: list[str],
        output_dir: Optional[str] = None,
        alpha_matting: bool = False,
    ) -> list[str]:
        """
        複数画像の一括背景除去

        Args:
            input_paths: 入力画像パスのリスト
            output_dir: 出力ディレクトリ（Noneの場合は各画像と同じディレクトリ）
            alpha_matting: アルファマッティングを使用するかどうか

        Returns:
            list[str]: 出力画像パスのリスト
        """
        output_paths = []

        for input_path in input_paths:
            # 出力パスを生成
            if output_dir:
                Path(output_dir).mkdir(parents=True, exist_ok=True)
                output_filename = Path(input_path).stem + "_nobg.png"
                output_path = str(Path(output_dir) / output_filename)
            else:
                output_path = None

            # 背景除去実行
            result_path = self.remove_background(
                input_path,
                output_path,
                alpha_matting
            )
            output_paths.append(result_path)

        return output_paths

    def create_white_background(
        self,
        input_path: str,
        output_path: Optional[str] = None,
    ) -> str:
        """
        透明背景を白背景に変換

        Args:
            input_path: 入力画像パス（透明背景）
            output_path: 出力画像パス

        Returns:
            str: 出力画像のパス
        """
        try:
            # 画像を読み込み
            image = Image.open(input_path).convert("RGBA")

            # 白背景を作成
            white_bg = Image.new("RGBA", image.size, (255, 255, 255, 255))

            # 画像を白背景に合成
            composite = Image.alpha_composite(white_bg, image)

            # RGB形式に変換
            composite = composite.convert("RGB")

            # 出力パスが指定されていない場合は自動生成
            if output_path is None:
                input_path_obj = Path(input_path)
                output_path = str(
                    input_path_obj.parent / f"{input_path_obj.stem}_white.jpg"
                )

            # 画像を保存
            composite.save(output_path, "JPEG", quality=95)

            logger.info(f"White background created. Saved to: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"White background creation failed: {e}")
            return input_path

    def crop_to_content(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        padding: int = 20,
    ) -> str:
        """
        衣類コンテンツ部分のみにクロップ

        Args:
            input_path: 入力画像パス（透明背景）
            output_path: 出力画像パス
            padding: パディングピクセル数

        Returns:
            str: 出力画像のパス
        """
        try:
            # 画像を読み込み
            image = Image.open(input_path)

            if image.mode != "RGBA":
                logger.warning("Image does not have transparency. Skipping crop.")
                return input_path

            # アルファチャンネルを取得
            alpha = image.split()[3]

            # 非透明領域のバウンディングボックスを取得
            bbox = alpha.getbbox()

            if bbox:
                # パディングを追加
                x1 = max(0, bbox[0] - padding)
                y1 = max(0, bbox[1] - padding)
                x2 = min(image.width, bbox[2] + padding)
                y2 = min(image.height, bbox[3] + padding)

                # クロップ
                cropped = image.crop((x1, y1, x2, y2))

                # 出力パスが指定されていない場合は自動生成
                if output_path is None:
                    input_path_obj = Path(input_path)
                    output_path = str(
                        input_path_obj.parent / f"{input_path_obj.stem}_cropped.png"
                    )

                # 画像を保存
                cropped.save(output_path, "PNG")

                logger.info(f"Cropped to content. Saved to: {output_path}")
                return output_path
            else:
                logger.warning("No content found in image")
                return input_path

        except Exception as e:
            logger.error(f"Cropping failed: {e}")
            return input_path
