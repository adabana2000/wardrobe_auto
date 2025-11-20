"""
Tests for service layer
"""

import pytest
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.services.weather import WeatherService
from app.services.gap_analyzer import WardrobeGapAnalyzer

# MLモジュールをインポート
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "ml"))
from ml.llm.outfit_generator import OutfitGenerator, OutfitRulesEngine


@pytest.mark.unit
class TestWeatherService:
    """WeatherServiceのテスト"""

    def test_initialization(self):
        """初期化テスト"""
        service = WeatherService()
        assert service is not None

    def test_get_mock_weather(self):
        """モック天気データ取得テスト"""
        service = WeatherService()
        weather = service._get_mock_weather()

        assert "date" in weather
        assert "temp" in weather
        assert "condition" in weather
        assert isinstance(weather["temp"], float)

    def test_should_wear_outer_cold(self):
        """アウター必要判定テスト（寒い）"""
        service = WeatherService()
        weather = {"temp": 10, "condition": "Clear"}

        assert service.should_wear_outer(weather) is True

    def test_should_wear_outer_warm(self):
        """アウター必要判定テスト（暖かい）"""
        service = WeatherService()
        weather = {"temp": 25, "condition": "Clear"}

        assert service.should_wear_outer(weather) is False

    def test_should_wear_rainwear(self):
        """雨具必要判定テスト"""
        service = WeatherService()

        # 雨の場合
        rain_weather = {"temp": 20, "condition": "Rain"}
        assert service.should_wear_rainwear(rain_weather) is True

        # 晴れの場合
        clear_weather = {"temp": 20, "condition": "Clear"}
        assert service.should_wear_rainwear(clear_weather) is False

    def test_get_clothing_recommendation_cold(self):
        """衣類推奨テスト（寒い）"""
        service = WeatherService()
        weather = {"temp": 5, "condition": "Clear"}

        recommendation = service.get_clothing_recommendation(weather)

        assert recommendation["needs_outer"] is True
        assert "ウール" in recommendation["suggested_material"]

    def test_get_clothing_recommendation_hot(self):
        """衣類推奨テスト（暑い）"""
        service = WeatherService()
        weather = {"temp": 30, "condition": "Clear"}

        recommendation = service.get_clothing_recommendation(weather)

        assert recommendation["needs_outer"] is False
        assert "半袖" in recommendation["suggested_style"]


@pytest.mark.unit
class TestWardrobeGapAnalyzer:
    """WardrobeGapAnalyzerのテスト"""

    def test_initialization(self):
        """初期化テスト"""
        analyzer = WardrobeGapAnalyzer()
        assert analyzer is not None

    def test_analyze_empty_wardrobe(self):
        """空のワードローブ分析テスト"""
        analyzer = WardrobeGapAnalyzer()
        result = analyzer.analyze([])

        assert result["total_items"] == 0
        assert "gap_score" in result
        assert result["gap_score"] >= 0
        assert isinstance(result["recommendations"], list)

    def test_category_distribution(self):
        """カテゴリ分布分析テスト"""
        analyzer = WardrobeGapAnalyzer()
        items = [
            {"category": "トップス", "color_primary": "白"},
            {"category": "トップス", "color_primary": "黒"},
            {"category": "ボトムス", "color_primary": "青"},
        ]

        distribution = analyzer._analyze_category_distribution(items)

        assert distribution["distribution"]["トップス"] == 2
        assert distribution["distribution"]["ボトムス"] == 1
        assert distribution["most_common"] == "トップス"

    def test_color_distribution(self):
        """色分布分析テスト"""
        analyzer = WardrobeGapAnalyzer()
        items = [
            {"color_primary": "白"},
            {"color_primary": "白"},
            {"color_primary": "黒"},
        ]

        distribution = analyzer._analyze_color_distribution(items)

        assert distribution["variety"] == 2
        assert distribution["most_common"] == "白"

    def test_style_coverage(self):
        """スタイルカバレッジテスト"""
        analyzer = WardrobeGapAnalyzer()
        items = [
            {"style_tags": ["カジュアル"]},
            {"style_tags": ["カジュアル", "フォーマル"]},
        ]

        coverage = analyzer._analyze_style_coverage(items)

        assert "カジュアル" in coverage
        assert coverage["カジュアル"]["count"] == 2

    def test_season_coverage(self):
        """季節カバレッジテスト"""
        analyzer = WardrobeGapAnalyzer()
        items = [
            {"season_tags": ["春", "夏"]},
            {"season_tags": ["夏"]},
        ]

        coverage = analyzer._analyze_season_coverage(items)

        assert "春" in coverage
        assert "夏" in coverage
        assert coverage["夏"]["count"] == 2

    def test_calculate_gap_score(self):
        """ギャップスコア計算テスト"""
        analyzer = WardrobeGapAnalyzer()

        # 充実したワードローブ
        analysis = {
            "category_distribution": {
                "distribution": {
                    "トップス": 5,
                    "ボトムス": 3,
                    "アウター": 2,
                }
            },
            "style_coverage": {
                "カジュアル": {"coverage": 80},
                "フォーマル": {"coverage": 60},
                "ビジネス": {"coverage": 50},
                "スポーツ": {"coverage": 40},
            },
            "season_coverage": {
                "春": {"coverage": 70},
                "夏": {"coverage": 70},
                "秋": {"coverage": 60},
                "冬": {"coverage": 60},
            },
            "color_distribution": {"variety": 8},
        }

        score = analyzer._calculate_gap_score(analysis)

        assert 0 <= score <= 100
        assert score > 50  # 充実している

    def test_calculate_outfit_combinations(self):
        """組み合わせ数計算テスト"""
        analyzer = WardrobeGapAnalyzer()
        items = [
            {"category": "トップス"},
            {"category": "トップス"},
            {"category": "ボトムス"},
            {"category": "ボトムス"},
            {"category": "アウター"},
        ]

        combinations = analyzer.calculate_outfit_combinations(items)

        # トップス2 × ボトムス2 × (アウター1+なし1) = 8
        assert combinations == 8


@pytest.mark.unit
class TestOutfitGenerator:
    """OutfitGeneratorのテスト"""

    def test_initialization(self):
        """初期化テスト"""
        generator = OutfitGenerator()
        assert generator is not None
        assert generator.rules_engine is not None

    def test_fallback_generation(self):
        """フォールバック生成テスト"""
        generator = OutfitGenerator()
        items = [
            {"id": "1", "category": "トップス", "color_primary": "白"},
            {"id": "2", "category": "ボトムス", "color_primary": "青"},
        ]
        weather = {"temp": 20, "condition": "Clear"}

        suggestions = generator._fallback_generation(items, weather, 1)

        assert len(suggestions) >= 1
        assert "items" in suggestions[0]
        assert "reason" in suggestions[0]

    def test_build_prompt(self):
        """プロンプト構築テスト"""
        generator = OutfitGenerator()
        items = [{"id": "1", "category": "トップス", "color_primary": "白"}]
        weather = {"temp": 20, "condition": "晴れ"}
        schedule = [{"time": "10:00", "event": "会議"}]

        prompt = generator._build_prompt(items, weather, schedule, None, 3)

        assert "トップス" in prompt
        assert "20℃" in prompt
        assert "会議" in prompt


@pytest.mark.unit
class TestOutfitRulesEngine:
    """OutfitRulesEngineのテスト"""

    def test_initialization(self):
        """初期化テスト"""
        engine = OutfitRulesEngine()
        assert engine is not None
        assert len(engine.COMPLEMENTARY_COLORS) > 0

    def test_score_outfit(self):
        """コーディネートスコアリングテスト"""
        engine = OutfitRulesEngine()
        outfit = {"items": ["1", "2"]}
        weather = {"temp": 20, "condition": "Clear"}

        score = engine.score_outfit(outfit, weather, None)

        assert 0 <= score <= 1

    def test_season_appropriateness_cold(self):
        """季節適合性テスト（寒い）"""
        engine = OutfitRulesEngine()
        outfit = {}
        weather = {"temp": 5}

        score = engine._score_season_appropriateness(outfit, weather)

        assert score > 0

    def test_season_appropriateness_hot(self):
        """季節適合性テスト（暑い）"""
        engine = OutfitRulesEngine()
        outfit = {}
        weather = {"temp": 35}

        score = engine._score_season_appropriateness(outfit, weather)

        assert score > 0
