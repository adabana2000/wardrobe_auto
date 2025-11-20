"""
コーディネート生成モジュール
ローカルLLMを使用したコーディネート提案
"""

from typing import Dict, List, Optional
import json
import logging
import requests
from datetime import date, datetime

logger = logging.getLogger(__name__)


class OutfitGenerator:
    """
    ローカルLLMを使用したコーディネート生成クラス
    """

    def __init__(
        self,
        vllm_endpoint: str = "http://localhost:8001/v1/completions",
        model_name: str = "local-model",
    ):
        """
        Args:
            vllm_endpoint: vLLMサーバーのエンドポイント
            model_name: 使用するモデル名
        """
        self.vllm_endpoint = vllm_endpoint
        self.model_name = model_name
        self.rules_engine = OutfitRulesEngine()

    def generate(
        self,
        wardrobe_items: List[Dict],
        weather: Optional[Dict] = None,
        schedule: Optional[List[Dict]] = None,
        recent_outfits: Optional[List[Dict]] = None,
        num_suggestions: int = 3,
    ) -> List[Dict]:
        """
        コーディネートを生成

        Args:
            wardrobe_items: 利用可能な衣類アイテムのリスト
            weather: 天気情報 {"temp": 15, "condition": "曇り", "humidity": 60}
            schedule: スケジュール [{"time": "10:00", "event": "会議"}]
            recent_outfits: 最近の着用履歴
            num_suggestions: 提案数

        Returns:
            List[Dict]: コーディネート提案のリスト
        """
        try:
            # プロンプトを構築
            prompt = self._build_prompt(
                wardrobe_items, weather, schedule, recent_outfits, num_suggestions
            )

            # LLMで生成
            llm_response = self._call_llm(prompt)

            # レスポンスをパース
            suggestions = self._parse_llm_response(llm_response, wardrobe_items)

            # ルールエンジンで検証・スコアリング
            validated_suggestions = []
            for suggestion in suggestions:
                score = self.rules_engine.score_outfit(
                    suggestion, weather, schedule
                )
                suggestion["style_score"] = score
                validated_suggestions.append(suggestion)

            # スコアでソート
            validated_suggestions.sort(
                key=lambda x: x.get("style_score", 0), reverse=True
            )

            return validated_suggestions[:num_suggestions]

        except Exception as e:
            logger.error(f"Outfit generation failed: {e}")
            # フォールバック: ルールベース生成
            return self._fallback_generation(wardrobe_items, weather, num_suggestions)

    def _build_prompt(
        self,
        wardrobe_items: List[Dict],
        weather: Optional[Dict],
        schedule: Optional[List[Dict]],
        recent_outfits: Optional[List[Dict]],
        num_suggestions: int,
    ) -> str:
        """
        LLM用プロンプトを構築

        Args:
            wardrobe_items: 衣類アイテム
            weather: 天気情報
            schedule: スケジュール
            recent_outfits: 最近の着用履歴
            num_suggestions: 提案数

        Returns:
            str: プロンプト
        """
        # ワードローブアイテムをフォーマット
        items_text = ""
        for idx, item in enumerate(wardrobe_items):
            items_text += f"{idx + 1}. {item.get('category', '不明')} - {item.get('color_primary', '不明')}色"
            if item.get('pattern'):
                items_text += f"、{item['pattern']}"
            items_text += f" (ID: {item.get('id', 'unknown')})\n"

        # 天気情報をフォーマット
        weather_text = "情報なし"
        if weather:
            weather_text = f"気温{weather.get('temp', '?')}℃、{weather.get('condition', '晴れ')}"

        # スケジュール情報をフォーマット
        schedule_text = "特になし"
        if schedule and len(schedule) > 0:
            schedule_text = "\n".join(
                [f"- {s.get('time', '')}: {s.get('event', '')}" for s in schedule]
            )

        # 最近の着用履歴をフォーマット
        recent_text = "なし"
        if recent_outfits:
            recent_text = f"過去7日間で{len(recent_outfits)}回の着用記録あり"

        prompt = f"""あなたはファッションコーディネートの専門家です。以下の条件で最適なコーディネートを{num_suggestions}案提案してください。

【天候】
{weather_text}

【予定】
{schedule_text}

【最近の着用】
{recent_text}

【利用可能なアイテム】
{items_text}

【要件】
- TPO（Time, Place, Occasion）を考慮する
- 季節感を大切にする
- 色の組み合わせを考慮する（補色、類似色など）
- 最近着用したアイテムは避ける
- 各提案に理由を付ける

【出力形式】
各提案を以下のJSON形式で出力してください：
{{
  "items": [アイテムIDのリスト],
  "reason": "提案理由",
  "weather_appropriateness": "天候への適合性の説明"
}}

提案:"""

        return prompt

    def _call_llm(self, prompt: str) -> str:
        """
        vLLMサーバーを呼び出し

        Args:
            prompt: プロンプト

        Returns:
            str: LLMのレスポンス
        """
        try:
            # vLLM APIを呼び出し
            response = requests.post(
                self.vllm_endpoint,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "max_tokens": 1000,
                    "temperature": 0.7,
                    "top_p": 0.9,
                },
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("choices", [{}])[0].get("text", "")
            else:
                logger.warning(f"vLLM request failed: {response.status_code}")
                return ""

        except requests.exceptions.RequestException as e:
            logger.warning(f"vLLM server not available: {e}")
            return ""

    def _parse_llm_response(
        self, response: str, wardrobe_items: List[Dict]
    ) -> List[Dict]:
        """
        LLMレスポンスをパース

        Args:
            response: LLMのレスポンス
            wardrobe_items: ワードローブアイテム

        Returns:
            List[Dict]: パースされた提案
        """
        suggestions = []

        try:
            # JSON形式のレスポンスをパース
            # 複数のJSON objectが含まれる可能性がある
            lines = response.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('{') and line.endswith('}'):
                    try:
                        suggestion = json.loads(line)
                        # アイテムIDを検証
                        if "items" in suggestion and isinstance(suggestion["items"], list):
                            suggestions.append(suggestion)
                    except json.JSONDecodeError:
                        continue

            return suggestions

        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return []

    def _fallback_generation(
        self, wardrobe_items: List[Dict], weather: Optional[Dict], num_suggestions: int
    ) -> List[Dict]:
        """
        フォールバック: ルールベースコーディネート生成

        Args:
            wardrobe_items: ワードローブアイテム
            weather: 天気情報
            num_suggestions: 提案数

        Returns:
            List[Dict]: コーディネート提案
        """
        logger.info("Using fallback rule-based outfit generation")

        # カテゴリ別にアイテムを分類
        categorized = {}
        for item in wardrobe_items:
            category = item.get("category", "その他")
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(item)

        suggestions = []

        # 基本的な組み合わせパターン
        tops = categorized.get("トップス", [])
        bottoms = categorized.get("ボトムス", [])
        outers = categorized.get("アウター", [])

        for i in range(min(num_suggestions, len(tops), len(bottoms))):
            items = []

            # トップス
            if i < len(tops):
                items.append(tops[i])

            # ボトムス
            if i < len(bottoms):
                items.append(bottoms[i])

            # 寒い場合はアウターも追加
            if weather and weather.get("temp", 20) < 15 and i < len(outers):
                items.append(outers[i])

            if items:
                suggestion = {
                    "items": [item.get("id") for item in items],
                    "reason": "ルールベース生成: 基本的な組み合わせ",
                    "weather_appropriateness": "天候に応じてアイテムを選択",
                    "style_score": 0.5,
                }
                suggestions.append(suggestion)

        return suggestions


class OutfitRulesEngine:
    """
    コーディネートルールエンジン
    """

    # カラーコーディネート理論
    COMPLEMENTARY_COLORS = {
        "赤": ["緑"],
        "青": ["オレンジ"],
        "黄色": ["紫"],
    }

    ANALOGOUS_COLORS = {
        "赤": ["オレンジ", "ピンク"],
        "青": ["緑", "紫"],
        "黄色": ["オレンジ", "緑"],
    }

    def score_outfit(
        self,
        outfit: Dict,
        weather: Optional[Dict] = None,
        schedule: Optional[List[Dict]] = None,
    ) -> float:
        """
        コーディネートをスコアリング

        Args:
            outfit: コーディネート
            weather: 天気情報
            schedule: スケジュール

        Returns:
            float: スコア（0-1）
        """
        score = 0.5  # ベーススコア

        # カラーコーディネートスコア
        color_score = self._score_color_coordination(outfit)
        score += color_score * 0.3

        # 季節適合性スコア
        season_score = self._score_season_appropriateness(outfit, weather)
        score += season_score * 0.3

        # TPOスコア
        tpo_score = self._score_tpo(outfit, schedule)
        score += tpo_score * 0.2

        return min(1.0, max(0.0, score))

    def _score_color_coordination(self, outfit: Dict) -> float:
        """カラーコーディネートスコア"""
        # 簡易実装: 色が3色以下であればOK
        # TODO: 実際のカラー理論を適用
        return 0.8

    def _score_season_appropriateness(
        self, outfit: Dict, weather: Optional[Dict]
    ) -> float:
        """季節適合性スコア"""
        if not weather:
            return 0.5

        temp = weather.get("temp", 20)

        # 気温に応じたスコアリング
        if temp < 10:
            # 寒い -> アウターが必要
            return 0.8
        elif temp < 20:
            # 涼しい
            return 0.7
        else:
            # 暑い -> 軽装
            return 0.7

    def _score_tpo(self, outfit: Dict, schedule: Optional[List[Dict]]) -> float:
        """TPOスコア"""
        if not schedule:
            return 0.7

        # スケジュールにビジネス系のイベントがあればフォーマル度を上げる
        # TODO: 実装
        return 0.7
