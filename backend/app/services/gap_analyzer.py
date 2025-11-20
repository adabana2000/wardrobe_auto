"""
ワードローブギャップ分析サービス
手持ちの衣類を分析し、不足しているアイテムを推奨
"""

from typing import Dict, List, Optional
from collections import Counter
import logging

logger = logging.getLogger(__name__)


class WardrobeGapAnalyzer:
    """
    ワードローブの充実度分析と不足アイテム検出
    """

    # 基本ワードローブアイテム（ミニマリスト版）
    ESSENTIAL_ITEMS = {
        "トップス": {
            "白シャツ": {"count": 2, "style": ["カジュアル", "フォーマル"]},
            "Tシャツ": {"count": 3, "style": ["カジュアル"]},
            "ニット": {"count": 2, "style": ["カジュアル", "フォーマル"]},
        },
        "ボトムス": {
            "デニムパンツ": {"count": 1, "style": ["カジュアル"]},
            "スラックス": {"count": 1, "style": ["フォーマル", "ビジネス"]},
            "チノパン": {"count": 1, "style": ["カジュアル"]},
        },
        "アウター": {
            "ジャケット": {"count": 1, "style": ["フォーマル", "ビジネス"]},
            "カーディガン": {"count": 1, "style": ["カジュアル"]},
            "コート": {"count": 1, "style": ["カジュアル", "フォーマル"]},
        },
        "靴": {
            "スニーカー": {"count": 1, "style": ["カジュアル"]},
            "革靴": {"count": 1, "style": ["フォーマル", "ビジネス"]},
        },
    }

    # 季節別必要アイテム
    SEASONAL_ITEMS = {
        "春": ["薄手のアウター", "長袖シャツ"],
        "夏": ["Tシャツ", "半袖シャツ", "薄手のボトムス"],
        "秋": ["ニット", "長袖シャツ", "ジャケット"],
        "冬": ["厚手のコート", "セーター", "厚手のボトムス"],
    }

    def __init__(self):
        """
        ギャップ分析エンジンの初期化
        """
        pass

    def analyze(self, wardrobe_items: List[Dict]) -> Dict:
        """
        ワードローブ全体を分析

        Args:
            wardrobe_items: ワードローブアイテムのリスト

        Returns:
            Dict: 分析結果
        """
        analysis = {
            "total_items": len(wardrobe_items),
            "category_distribution": self._analyze_category_distribution(wardrobe_items),
            "color_distribution": self._analyze_color_distribution(wardrobe_items),
            "style_coverage": self._analyze_style_coverage(wardrobe_items),
            "season_coverage": self._analyze_season_coverage(wardrobe_items),
            "essential_items_check": self._check_essential_items(wardrobe_items),
            "gap_score": 0.0,
            "recommendations": [],
        }

        # ギャップスコアを計算（0-100）
        analysis["gap_score"] = self._calculate_gap_score(analysis)

        # 推奨アイテムを生成
        analysis["recommendations"] = self._generate_recommendations(analysis, wardrobe_items)

        return analysis

    def _analyze_category_distribution(self, items: List[Dict]) -> Dict:
        """
        カテゴリ別分布を分析

        Args:
            items: ワードローブアイテム

        Returns:
            Dict: カテゴリ別アイテム数
        """
        categories = [item.get("category", "不明") for item in items]
        distribution = dict(Counter(categories))

        return {
            "distribution": distribution,
            "most_common": max(distribution, key=distribution.get) if distribution else None,
            "least_common": min(distribution, key=distribution.get) if distribution else None,
        }

    def _analyze_color_distribution(self, items: List[Dict]) -> Dict:
        """
        色別分布を分析

        Args:
            items: ワードローブアイテム

        Returns:
            Dict: 色別アイテム数
        """
        colors = [item.get("color_primary", "不明") for item in items if item.get("color_primary")]
        distribution = dict(Counter(colors))

        return {
            "distribution": distribution,
            "variety": len(distribution),
            "most_common": max(distribution, key=distribution.get) if distribution else None,
        }

    def _analyze_style_coverage(self, items: List[Dict]) -> Dict:
        """
        スタイル別カバレッジを分析

        Args:
            items: ワードローブアイテム

        Returns:
            Dict: スタイル別充実度
        """
        style_counts = Counter()

        for item in items:
            style_tags = item.get("style_tags", [])
            for style in style_tags:
                style_counts[style] += 1

        # スタイル別の充実度を計算
        coverage = {}
        for style in ["カジュアル", "フォーマル", "ビジネス", "スポーツ"]:
            count = style_counts.get(style, 0)
            coverage[style] = {
                "count": count,
                "coverage": min(100, (count / 5) * 100) if count > 0 else 0,  # 5アイテム以上で100%
            }

        return coverage

    def _analyze_season_coverage(self, items: List[Dict]) -> Dict:
        """
        季節別カバレッジを分析

        Args:
            items: ワードローブアイテム

        Returns:
            Dict: 季節別充実度
        """
        season_counts = Counter()

        for item in items:
            season_tags = item.get("season_tags", [])
            for season in season_tags:
                season_counts[season] += 1

        coverage = {}
        for season in ["春", "夏", "秋", "冬"]:
            count = season_counts.get(season, 0)
            coverage[season] = {
                "count": count,
                "coverage": min(100, (count / 5) * 100) if count > 0 else 0,
            }

        return coverage

    def _check_essential_items(self, items: List[Dict]) -> Dict:
        """
        基本アイテムの充足度をチェック

        Args:
            items: ワードローブアイテム

        Returns:
            Dict: 基本アイテムの充足状況
        """
        result = {}

        for category, essentials in self.ESSENTIAL_ITEMS.items():
            category_items = [item for item in items if item.get("category") == category]

            result[category] = {}
            for item_name, requirements in essentials.items():
                required_count = requirements["count"]
                # 簡易的に、カテゴリが一致していれば存在するとみなす
                # 実際には、より詳細なマッチングが必要
                actual_count = len(category_items)

                result[category][item_name] = {
                    "required": required_count,
                    "actual": min(actual_count, required_count),
                    "satisfied": actual_count >= required_count,
                }

        return result

    def _calculate_gap_score(self, analysis: Dict) -> float:
        """
        ワードローブのギャップスコアを計算（0-100）

        スコアが高いほどワードローブが充実している

        Args:
            analysis: 分析結果

        Returns:
            float: ギャップスコア
        """
        score = 0.0
        max_score = 100.0

        # カテゴリバランス（25点）
        category_dist = analysis["category_distribution"]["distribution"]
        if len(category_dist) >= 3:
            score += 25
        else:
            score += (len(category_dist) / 3) * 25

        # スタイルカバレッジ（25点）
        style_coverage = analysis["style_coverage"]
        avg_style_coverage = sum(s["coverage"] for s in style_coverage.values()) / len(style_coverage)
        score += (avg_style_coverage / 100) * 25

        # 季節カバレッジ（25点）
        season_coverage = analysis["season_coverage"]
        avg_season_coverage = sum(s["coverage"] for s in season_coverage.values()) / len(season_coverage)
        score += (avg_season_coverage / 100) * 25

        # 色のバラエティ（25点）
        color_variety = analysis["color_distribution"]["variety"]
        score += min(25, (color_variety / 8) * 25)  # 8色以上で満点

        return round(score, 1)

    def _generate_recommendations(self, analysis: Dict, items: List[Dict]) -> List[Dict]:
        """
        不足アイテムの推奨を生成

        Args:
            analysis: 分析結果
            items: ワードローブアイテム

        Returns:
            List[Dict]: 推奨アイテムのリスト
        """
        recommendations = []

        # カテゴリ不足チェック
        category_dist = analysis["category_distribution"]["distribution"]

        if category_dist.get("トップス", 0) < 3:
            recommendations.append({
                "item": "トップス",
                "reason": "基本的なトップスが不足しています",
                "priority": "high",
                "suggested": "白シャツ、Tシャツ、ニット",
            })

        if category_dist.get("ボトムス", 0) < 2:
            recommendations.append({
                "item": "ボトムス",
                "reason": "ボトムスのバリエーションが少ないです",
                "priority": "high",
                "suggested": "デニムパンツ、スラックス",
            })

        if category_dist.get("アウター", 0) < 1:
            recommendations.append({
                "item": "アウター",
                "reason": "アウターが不足しています",
                "priority": "medium",
                "suggested": "ジャケット、カーディガン",
            })

        # スタイル不足チェック
        style_coverage = analysis["style_coverage"]
        for style, data in style_coverage.items():
            if data["coverage"] < 30:
                recommendations.append({
                    "item": f"{style}用アイテム",
                    "reason": f"{style}スタイルのアイテムが不足しています",
                    "priority": "medium",
                    "suggested": f"{style}に適したアイテムを追加",
                })

        # 季節不足チェック
        season_coverage = analysis["season_coverage"]
        for season, data in season_coverage.items():
            if data["coverage"] < 30:
                recommendations.append({
                    "item": f"{season}用アイテム",
                    "reason": f"{season}用のアイテムが不足しています",
                    "priority": "medium",
                    "suggested": ", ".join(self.SEASONAL_ITEMS.get(season, [])),
                })

        # 色のバラエティチェック
        color_variety = analysis["color_distribution"]["variety"]
        if color_variety < 4:
            recommendations.append({
                "item": "多様な色のアイテム",
                "reason": "色のバリエーションが少ないです",
                "priority": "low",
                "suggested": "ベーシックカラー以外のアイテムを追加",
            })

        return recommendations

    def calculate_outfit_combinations(self, items: List[Dict]) -> int:
        """
        可能なコーディネート組み合わせ数を計算

        Args:
            items: ワードローブアイテム

        Returns:
            int: 組み合わせ数
        """
        # カテゴリ別にアイテムをカウント
        categories = {}
        for item in items:
            category = item.get("category", "その他")
            categories[category] = categories.get(category, 0) + 1

        tops = categories.get("トップス", 0)
        bottoms = categories.get("ボトムス", 0)
        outers = categories.get("アウター", 0)

        # 基本的な組み合わせ数（トップス × ボトムス）
        base_combinations = tops * bottoms

        # アウターを含む組み合わせ
        with_outer = base_combinations * (outers + 1)  # アウターなしも含む

        return with_outer
