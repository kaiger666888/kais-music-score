"""节奏创新性分析 — 奖励有规律律动，惩罚随机"""
import math
from collections import Counter
from music21 import note, stream
from .models import RhythmResult, RhythmicPoint


def _shannon_entropy(counter: Counter) -> float:
    total = sum(counter.values())
    if total == 0:
        return 0.0
    return -sum((c / total) * math.log2(c / total) for c in counter.values() if c > 0)


def analyze(score_obj, all_notes: list, duration_seconds: float) -> RhythmResult:
    """分析节奏创新性"""
    if not all_notes:
        return RhythmResult()

    points = []
    durations = []
    syncopated_count = 0
    total = len(all_notes)

    for n in all_notes:
        dur_q = n.duration.quarterLength if n.duration else 1.0
        bs = getattr(n, 'beatStrength', 1.0) or 1.0
        is_sync = bs < 0.5
        if is_sync:
            syncopated_count += 1
        durations.append(round(dur_q, 4))
        points.append(RhythmicPoint(
            measure=getattr(n, 'measureNumber', 0) or 0,
            beat=getattr(n, 'beat', 0.0) or 0.0,
            duration_q=dur_q,
            beat_strength=bs,
            is_syncopated=is_sync,
        ))

    unique_durs = set(durations)
    dur_counter = Counter(durations)
    sync_ratio = syncopated_count / total if total > 0 else 0.0
    nps = total / duration_seconds if duration_seconds > 0 else 0.0

    # === 音符数量门控 ===
    # 太少音符无法评估节奏（需要至少8个音才有意义）
    if total <= 4:
        # 太少音符，给极低分
        score = 5.0
        return RhythmResult(
            rhythmic_diversity_entropy=0.0,
            syncopation_ratio=round(sync_ratio, 3),
            notes_per_second=round(nps, 2),
            polyrhythm_detected=False,
            rhythmic_points=points,
            score=round(score, 1),
        )
    
    note_count_factor = min(total / 12.0, 1.0)  # 12个音符才满权重

    # === 随机性检测 ===
    randomness_score = 0.0
    most_common_bg_ratio = 0.0
    
    if len(durations) >= 4:
        bigrams = [tuple(durations[i:i + 2]) for i in range(len(durations) - 1)]
        bg_counter = Counter(bigrams)
        most_common_bg_count = bg_counter.most_common(1)[0][1] if bg_counter else 0
        most_common_bg_ratio = most_common_bg_count / len(bigrams) if bigrams else 0
        
        dur_diversity = len(unique_durs) / len(durations)
        
        if dur_diversity > 0.4 and most_common_bg_ratio < 0.15:
            randomness_score = 1.0
        elif dur_diversity > 0.25 and most_common_bg_ratio < 0.25:
            randomness_score = 0.6
        elif dur_diversity > 0.15 and most_common_bg_ratio < 0.35:
            randomness_score = 0.3

    # === 规律性 ===
    pattern_score = 0.0
    if len(durations) >= 4:
        if most_common_bg_ratio > 0.5:
            pattern_score = 1.0
        elif most_common_bg_ratio > 0.3:
            pattern_score = 0.7
        elif most_common_bg_ratio > 0.2:
            pattern_score = 0.4
        else:
            pattern_score = 0.1

    # === 切分 ===
    sync_score = min(sync_ratio / 0.3, 1.0)

    # === 复合节奏 ===
    poly_detected = False
    try:
        if len(score_obj.parts) >= 2:
            part_durs = []
            for part in score_obj.parts[:3]:
                notes_p = list(part.flatten().getElementsByClass(note.Note))
                durs = [round(n.duration.quarterLength, 2) for n in notes_p]
                part_durs.append(set(durs))
            if len(part_durs) >= 2:
                overlap = len(part_durs[0] & part_durs[1])
                total_unique = len(part_durs[0] | part_durs[1])
                if total_unique > 0 and overlap / total_unique < 0.5:
                    poly_detected = True
    except Exception:
        pass

    # === 评分 ===
    base = 8.0
    pattern_bonus = pattern_score * 30
    sync_bonus = sync_score * 18
    density_bonus = min(nps / 4.0, 1.0) * 8
    
    if 2 <= len(unique_durs) <= 4:
        variety_bonus = 12.0
    elif len(unique_durs) == 1:
        variety_bonus = 6.0
    else:
        variety_bonus = 3.0
    
    poly_bonus = 8.0 if poly_detected else 0.0
    
    raw = base + pattern_bonus + sync_bonus + density_bonus + variety_bonus + poly_bonus
    raw -= randomness_score * 45
    
    if len(unique_durs) == 1 and total > 2:
        raw -= 3.0

    # 应用音符数量因子
    raw *= note_count_factor

    score = max(0.0, min(100.0, raw))

    if len(durations) >= 3:
        trigrams = [tuple(durations[i:i + 3]) for i in range(len(durations) - 2)]
        tg_counter = Counter(trigrams)
        entropy = _shannon_entropy(tg_counter)
    else:
        entropy = 0.0

    return RhythmResult(
        rhythmic_diversity_entropy=round(entropy, 3),
        syncopation_ratio=round(sync_ratio, 3),
        notes_per_second=round(nps, 2),
        polyrhythm_detected=poly_detected,
        rhythmic_points=points,
        score=round(score, 1),
    )
