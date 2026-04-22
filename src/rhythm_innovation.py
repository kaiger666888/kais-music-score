"""节奏创新性分析"""
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
        bs = n.beatStrength if hasattr(n, 'beatStrength') else 1.0
        is_sync = bs is not None and bs < 0.5
        if is_sync:
            syncopated_count += 1
        durations.append(round(dur_q, 4))
        points.append(RhythmicPoint(
            measure=n.measureNumber or 0,
            beat=n.beat or 0.0,
            duration_q=dur_q,
            beat_strength=bs or 1.0,
            is_syncopated=is_sync,
        ))

    # 1. 节奏多样性熵（3-gram duration patterns）
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

    # 4. 复合节奏检测（简化：检查各 part 节奏型差异）
    poly_detected = False
    try:
        if len(score_obj.parts) >= 2:
            part_durs = []
            for part in score_obj.parts[:3]:
                notes_p = list(part.flatten().getElementsByClass(note.Note))
                durs = [round(n.duration.quarterLength, 2) for n in notes_p]
                part_durs.append(set(durs))
            # 如果不同 part 有明显不同的节奏型
            if len(part_durs) >= 2:
                overlap = len(part_durs[0] & part_durs[1])
                total_unique = len(part_durs[0] | part_durs[1])
                if total_unique > 0 and overlap / total_unique < 0.5:
                    poly_detected = True
    except Exception:
        pass

    # 评分
    entropy_norm = min(entropy / 4.0, 1.0) * 100
    sync_norm = min(sync_ratio / 0.5, 1.0) * 100
    density_norm = min(nps / 8.0, 1.0) * 100
    poly_norm = 100.0 if poly_detected else 0.0

    score = 0.30 * entropy_norm + 0.30 * sync_norm + 0.20 * density_norm + 0.20 * poly_norm

    return RhythmResult(
        rhythmic_diversity_entropy=round(entropy, 3),
        syncopation_ratio=round(sync_ratio, 3),
        notes_per_second=round(nps, 2),
        polyrhythm_detected=poly_detected,
        rhythmic_points=points,
        score=round(score, 1),
    )
