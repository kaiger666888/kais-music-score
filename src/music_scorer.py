"""音乐类型检测 + 加权评分引擎"""
from .models import (
    PieceInfo, HarmonyResult, MelodyResult, RhythmResult,
    StructureResult, ExpressivenessResult, GenreDetection, ScoreResult,
)

DIM_LABELS = {
    "harmony": "和声复杂度", "melody": "旋律多样性", "rhythm": "节奏创新性",
    "structure": "结构完整性", "expression": "表现力",
}


def detect_genre(piece: PieceInfo, harmony: HarmonyResult, rhythm: RhythmResult,
                 structure: StructureResult, expressiveness: ExpressivenessResult,
                 melody: MelodyResult) -> GenreDetection:
    """基于特征检测音乐类型 — 简化规则"""
    scores = {
        "classical": 0.0,
        "pop": 0.0,
        "jazz": 0.0,
        "electronic": 0.0,
        "rock": 0.0,
    }

    # 基于和弦数量和声部数
    chord_count = len(harmony.chord_events)
    part_count = piece.part_count

    # 古典：多声部 + 有和弦变化 + 结构有段落
    if part_count >= 2 and chord_count >= 4:
        scores["classical"] += 3
    if structure.detected_form in ("ABA", "AB") and chord_count >= 6:
        scores["classical"] += 2

    # 流行：单声部或双声部 + 旋律清晰 + 节奏有变化
    if melody.score > 20 and rhythm.score > 10:
        scores["pop"] += 2
    if part_count <= 2 and melody.pitch_range_semitones >= 7:
        scores["pop"] += 2

    # 爵士：和弦多样性高 + 有扩展和弦
    if harmony.chord_diversity_entropy > 1.5:
        scores["jazz"] += 3
    if harmony.voice_leading_smoothness < 3.0:
        scores["jazz"] += 1

    # 电子：节奏密度高 + 切分多
    if rhythm.notes_per_second > 3:
        scores["electronic"] += 2
    if rhythm.syncopation_ratio > 0.2:
        scores["electronic"] += 1

    # 摇滚：力度范围大 + 节奏强
    if expressiveness.dynamic_range > 60:
        scores["rock"] += 2

    # 默认：如果都没有明显特征，根据声部数和和弦数判断
    if max(scores.values()) == 0:
        if chord_count >= 4 and part_count >= 2:
            scores["classical"] = 1
        elif melody.score > 10:
            scores["pop"] = 1
        else:
            scores["pop"] = 0.5

    sorted_scores = sorted(scores.items(), key=lambda x: -x[1])
    detected = sorted_scores[0][0]
    top_score = sorted_scores[0][1]
    second_score = sorted_scores[1][1] if len(sorted_scores) > 1 else 0
    confidence = min(1.0, (top_score - second_score) / max(top_score, 1.0)) if top_score > 0 else 0.0

    return GenreDetection(
        detected_genre=detected,
        confidence=round(confidence, 3),
        genre_scores={k: round(v, 3) for k, v in sorted_scores},
    )


def score_music(genre: GenreDetection, harmony: HarmonyResult, melody: MelodyResult,
                rhythm: RhythmResult, structure: StructureResult,
                expressiveness: ExpressivenessResult) -> ScoreResult:
    """统一加权评分 — 各类型权重更均衡"""
    detected = genre.detected_genre

    # 统一权重，不因类型差异导致好音乐被错误惩罚
    weights = {
        "harmony": 0.20,
        "melody": 0.25,
        "rhythm": 0.20,
        "structure": 0.20,
        "expression": 0.15,
    }

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
