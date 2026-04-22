"""音乐类型检测 + 加权评分引擎"""
from .models import (
    PieceInfo, HarmonyResult, MelodyResult, RhythmResult,
    StructureResult, ExpressivenessResult, GenreDetection, ScoreResult,
)

# 各类型的理想特征区间
IDEAL_RANGES = {
    "classical": {
        "chord_entropy": (1.5, 3.0),
        "modulation_count": (2, 5),
        "voice_lead": (0.5, 1.5),
        "syncopation": (0.05, 0.15),
        "rhythm_entropy": (1.5, 2.5),
        "repetition": (0.4, 0.6),
        "part_count": (3, 8),
        "dynamic_range": (50, 127),
        "tempo_variation": (10, 30),
        "interval_entropy": (2.0, 3.0),
        "contour_ratio": (0.3, 0.5),
    },
    "pop": {
        "chord_entropy": (0.8, 1.5),
        "modulation_count": (0, 1),
        "voice_lead": (2.0, 3.0),
        "syncopation": (0.05, 0.15),
        "rhythm_entropy": (1.0, 2.0),
        "repetition": (0.4, 0.6),
        "part_count": (2, 5),
        "dynamic_range": (30, 80),
        "tempo_variation": (0, 5),
        "interval_entropy": (1.0, 2.0),
        "contour_ratio": (0.2, 0.4),
    },
    "jazz": {
        "chord_entropy": (2.5, 4.0),
        "modulation_count": (2, 8),
        "voice_lead": (1.0, 2.0),
        "syncopation": (0.30, 0.50),
        "rhythm_entropy": (2.0, 3.5),
        "repetition": (0.2, 0.4),
        "part_count": (2, 6),
        "dynamic_range": (30, 70),
        "tempo_variation": (5, 20),
        "interval_entropy": (2.5, 3.5),
        "contour_ratio": (0.4, 0.6),
    },
    "electronic": {
        "chord_entropy": (0.5, 1.5),
        "modulation_count": (0, 1),
        "voice_lead": (1.0, 4.0),
        "syncopation": (0.15, 0.30),
        "rhythm_entropy": (0.5, 1.5),
        "repetition": (0.5, 0.8),
        "part_count": (1, 4),
        "dynamic_range": (20, 60),
        "tempo_variation": (0, 3),
        "interval_entropy": (1.0, 2.0),
        "contour_ratio": (0.2, 0.4),
    },
    "rock": {
        "chord_entropy": (0.5, 1.2),
        "modulation_count": (0, 1),
        "voice_lead": (2.0, 4.0),
        "syncopation": (0.10, 0.25),
        "rhythm_entropy": (0.8, 1.5),
        "repetition": (0.3, 0.5),
        "part_count": (2, 5),
        "dynamic_range": (60, 127),
        "tempo_variation": (3, 15),
        "interval_entropy": (1.5, 2.5),
        "contour_ratio": (0.3, 0.5),
    },
}

# 类型感知评分权重
GENRE_WEIGHTS = {
    "classical": {"harmony": 0.30, "melody": 0.25, "rhythm": 0.15, "structure": 0.25, "expression": 0.05},
    "pop":      {"harmony": 0.15, "melody": 0.25, "rhythm": 0.20, "structure": 0.20, "expression": 0.20},
    "jazz":     {"harmony": 0.35, "melody": 0.25, "rhythm": 0.25, "structure": 0.10, "expression": 0.05},
    "electronic":{"harmony": 0.10, "melody": 0.15, "rhythm": 0.20, "structure": 0.10, "expression": 0.15},
    "rock":     {"harmony": 0.10, "melody": 0.20, "rhythm": 0.20, "structure": 0.15, "expression": 0.20},
}

GENRE_NAMES = {
    "classical": "古典", "pop": "流行", "jazz": "爵士", "electronic": "电子", "rock": "摇滚",
}

DIM_LABELS = {
    "harmony": "和声复杂度", "melody": "旋律多样性", "rhythm": "节奏创新性",
    "structure": "结构完整性", "expression": "表现力",
}


def _range_match(value: float, ideal: tuple) -> float:
    """计算值与理想区间的匹配度 [0, 1]"""
    lo, hi = ideal
    if lo <= value <= hi:
        return 1.0
    dist = min(abs(value - lo), abs(value - hi))
    width = hi - lo if hi > lo else 1.0
    return max(0.0, 1.0 - dist / width)


def detect_genre(piece: PieceInfo, harmony: HarmonyResult, rhythm: RhythmResult,
                 structure: StructureResult, expressiveness: ExpressivenessResult,
                 melody: MelodyResult) -> GenreDetection:
    """基于特征区间匹配检测音乐类型"""
    features = {
        "chord_entropy": harmony.chord_diversity_entropy,
        "modulation_count": float(harmony.modulation_count),
        "voice_lead": harmony.voice_leading_smoothness,
        "syncopation": rhythm.syncopation_ratio,
        "rhythm_entropy": rhythm.rhythmic_diversity_entropy,
        "repetition": structure.repetition_coverage,
        "part_count": float(piece.part_count),
        "dynamic_range": float(expressiveness.dynamic_range),
        "tempo_variation": expressiveness.tempo_variation_range,
        "interval_entropy": melody.interval_diversity_entropy,
        "contour_ratio": melody.contour_change_ratio,
    }

    genre_scores = {}
    for genre, ranges in IDEAL_RANGES.items():
        matches = [_range_match(features[k], ranges[k]) for k in features if k in ranges]
        genre_scores[genre] = sum(matches) / len(matches) if matches else 0.0

    sorted_scores = sorted(genre_scores.items(), key=lambda x: -x[1])
    detected = sorted_scores[0][0]
    top_score = sorted_scores[0][1]
    second_score = sorted_scores[1][1] if len(sorted_scores) > 1 else 0
    confidence = (top_score - second_score) / top_score if top_score > 0 else 0.0

    return GenreDetection(
        detected_genre=detected,
        confidence=round(confidence, 3),
        genre_scores={k: round(v, 3) for k, v in sorted_scores},
    )


def score_music(genre: GenreDetection, harmony: HarmonyResult, melody: MelodyResult,
                rhythm: RhythmResult, structure: StructureResult,
                expressiveness: ExpressivenessResult) -> ScoreResult:
    """类型感知加权评分"""
    detected = genre.detected_genre
    weights = GENRE_WEIGHTS.get(detected, GENRE_WEIGHTS["pop"])
    ideal = IDEAL_RANGES.get(detected, IDEAL_RANGES["pop"])

    # 各维度的原始子指标值
    dim_values = {
        "harmony": {
            "chord_entropy": harmony.chord_diversity_entropy,
            "modulation_count": float(harmony.modulation_count),
            "voice_lead": harmony.voice_leading_smoothness,
        },
        "melody": {
            "interval_entropy": melody.interval_diversity_entropy,
            "contour_ratio": melody.contour_change_ratio,
            "pitch_range": float(melody.pitch_range_semitones),
        },
        "rhythm": {
            "rhythm_entropy": rhythm.rhythmic_diversity_entropy,
            "syncopation": rhythm.syncopation_ratio,
            "notes_per_second": rhythm.notes_per_second,
        },
        "structure": {
            "repetition": structure.repetition_coverage,
            "symmetry_cv": structure.phrase_symmetry_cv,
        },
        "expression": {
            "dynamic_range": float(expressiveness.dynamic_range),
            "tempo_variation": expressiveness.tempo_variation_range,
            "articulation": float(expressiveness.articulation_types),
        },
    }

    # 简化：直接使用各维度模块计算的 score
    # 再用类型权重加权
    raw_scores = {
        "harmony": harmony.score,
        "melody": melody.score,
        "rhythm": rhythm.score,
        "structure": structure.score,
        "expression": expressiveness.score,
    }

    dimensions = {}
    total = 0.0
    for dim_key, dim_label in DIM_LABELS.items():
        w = weights[dim_key]
        s = raw_scores[dim_key]
        dimensions[dim_key] = {
            "score": s,
            "weight": w,
            "label": dim_label,
        }
        total += s * w

    grade = "S" if total >= 85 else "A" if total >= 70 else "B" if total >= 55 else "C" if total >= 40 else "D"

    return ScoreResult(
        detected_genre=detected,
        genre_confidence=genre.confidence,
        genre_scores=genre.genre_scores,
        dimensions=dimensions,
        total=round(total, 1),
        grade=grade,
    )
