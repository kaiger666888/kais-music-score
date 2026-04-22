"""旋律多样性分析"""
import math
from collections import Counter
from music21 import interval as m21interval
from .models import MelodyResult, MelodicPoint


def _shannon_entropy(counter: Counter) -> float:
    total = sum(counter.values())
    if total == 0:
        return 0.0
    return -sum((c / total) * math.log2(c / total) for c in counter.values() if c > 0)


def analyze(melody_notes: list) -> MelodyResult:
    """分析旋律多样性"""
    if not melody_notes:
        return MelodyResult()

    points = []
    pitches = []
    intervals = []
    directions = []

    prev_pitch = None
    for n in melody_notes:
        p = n.pitch.midi if hasattr(n, 'pitch') and n.pitch else 60
        pitches.append(p)

        if prev_pitch is not None:
            iv = p - prev_pitch
            intervals.append(iv)
            d = 1 if iv > 0 else (-1 if iv < 0 else 0)
            directions.append(d)
            points.append(MelodicPoint(
                measure=n.measureNumber or 0,
                beat=n.beat or 0.0,
                pitch=p,
                interval_from_prev=iv,
                direction=d,
            ))
        else:
            points.append(MelodicPoint(
                measure=n.measureNumber or 0,
                beat=n.beat or 0.0,
                pitch=p,
            ))
        prev_pitch = p

    # 1. 音程多样性熵
    interval_counter = Counter(intervals)
    entropy = _shannon_entropy(interval_counter)

    # 2. 轮廓变化率
    changes = sum(1 for i in range(1, len(directions)) if directions[i] != directions[i - 1])
    contour_ratio = changes / len(directions) if directions else 0.0

    # 3. 音域
    pitch_range = max(pitches) - min(pitches) if pitches else 0

    # 4. 动机重复率（3-gram）
    if len(pitches) >= 6:
        trigrams = [tuple(pitches[i:i + 3]) for i in range(len(pitches) - 2)]
        tg_counter = Counter(trigrams)
        repeated = sum(c for c in tg_counter.values() if c > 1)
        motif_rate = repeated / len(trigrams) if trigrams else 0.0
    else:
        motif_rate = 0.0

    # 评分
    entropy_norm = min(entropy / 4.0, 1.0) * 100
    contour_norm = min(contour_ratio / 0.6, 1.0) * 100
    range_norm = min(pitch_range / 36.0, 1.0) * 100
    motif_norm = min(motif_rate / 0.5, 1.0) * 100

    score = 0.30 * entropy_norm + 0.25 * contour_norm + 0.20 * range_norm + 0.25 * motif_norm

    return MelodyResult(
        interval_diversity_entropy=round(entropy, 3),
        contour_change_ratio=round(contour_ratio, 3),
        pitch_range_semitones=pitch_range,
        motivic_repetition_rate=round(motif_rate, 3),
        melodic_points=points,
        score=round(score, 1),
    )
