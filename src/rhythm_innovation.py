"""节奏创新性分析 — 奖励有变化的节奏，惩罚完全均匀"""
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

    # 1. 节奏多样性熵
    if len(durations) >= 3:
        trigrams = [tuple(durations[i:i + 3]) for i in range(len(durations) - 2)]
        tg_counter = Counter(trigrams)
        entropy = _shannon_entropy(tg_counter)
    else:
        entropy = 0.0

    # 2. 切分比例
    sync_ratio = syncopated_count / total if total > 0 else 0.0

    # 3. 节奏密度
    nps = total / duration_seconds if duration_seconds > 0 else 0.0

    # 4. 节奏均匀度惩罚 — 所有时值完全相同 = 坏节奏
    unique_durs = set(durations)
    dur_diversity = len(unique_durs) / max(len(durations), 1)
    if len(unique_durs) == 1:
        uniform_penalty = 1.0  # 完全均匀
    elif len(unique_durs) == 2:
        uniform_penalty = 0.3
    else:
        uniform_penalty = 0.0

    # 5. 复合节奏检测
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
    entropy_norm = min(entropy / 3.0, 1.0) * 100
    sync_norm = min(sync_ratio / 0.4, 1.0) * 100
    density_norm = min(nps / 6.0, 1.0) * 100
    poly_norm = 100.0 if poly_detected else 0.0

    # 时值多样性奖励
    diversity_bonus = min(dur_diversity * 100, 50) if dur_diversity > 0.05 else 0.0

    # 基础节奏活力分 — 即使时值均匀，只要音符密度合理就给基线分
    base_rhythm = 25.0 if nps > 1.0 else 0.0

    raw = (0.20 * entropy_norm + 0.20 * sync_norm + 0.15 * density_norm +
           0.10 * poly_norm + 0.15 * diversity_bonus + 0.20 * base_rhythm)

    # 均匀惩罚（但不把基线分也扣光）
    raw -= uniform_penalty * 25

    score = max(0.0, min(100.0, raw))

    return RhythmResult(
        rhythmic_diversity_entropy=round(entropy, 3),
        syncopation_ratio=round(sync_ratio, 3),
        notes_per_second=round(nps, 2),
        polyrhythm_detected=poly_detected,
        rhythmic_points=points,
        score=round(score, 1),
    )
