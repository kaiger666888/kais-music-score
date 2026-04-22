"""旋律多样性分析 — 综合评估旋律质量"""
import math
from collections import Counter
from .models import MelodyResult, MelodicPoint


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
                measure=getattr(n, 'measureNumber', 0) or 0,
                beat=getattr(n, 'beat', 0.0) or 0.0,
                pitch=p,
                interval_from_prev=iv,
                direction=d,
            ))
        else:
            points.append(MelodicPoint(
                measure=getattr(n, 'measureNumber', 0) or 0,
                beat=getattr(n, 'beat', 0.0) or 0.0,
                pitch=p,
            ))
        prev_pitch = p

    if not intervals:
        return MelodyResult()

    # === 核心指标 ===

    # 1. 音高多样性（关键区分指标）
    unique_pitches = len(set(pitches))
    # 2音交替=2, 单音=1, 音阶=7-8, 儿歌~5-6, 爵士/巴赫>8

    # 2. 级进比例
    step_count = sum(1 for iv in intervals if abs(iv) <= 2)
    step_ratio = step_count / len(intervals)

    # 3. 小跳比例 (3-5 semitones)
    small_leap_count = sum(1 for iv in intervals if 3 <= abs(iv) <= 5)
    small_leap_ratio = small_leap_count / len(intervals)

    # 4. 大跳惩罚
    large_leap_count = sum(1 for iv in intervals if abs(iv) > 7)
    large_leap_ratio = large_leap_count / len(intervals)
    extreme_leap_count = sum(1 for iv in intervals if abs(iv) > 12)
    extreme_leap_ratio = extreme_leap_count / len(intervals)

    # 5. 轮廓变化率
    changes = sum(1 for i in range(1, len(directions)) if directions[i] != directions[i - 1])
    contour_ratio = changes / len(directions) if directions else 0.0

    # 6. 音域
    pitch_range = max(pitches) - min(pitches)

    # 7. 动机重复率（3-gram）
    motif_rate = 0.0
    if len(pitches) >= 6:
        trigrams = [tuple(pitches[i:i + 3]) for i in range(len(pitches) - 2)]
        tg_counter = Counter(trigrams)
        repeated = sum(c for c in tg_counter.values() if c > 1)
        motif_rate = repeated / len(trigrams) if trigrams else 0.0

    # 8. 单音重复惩罚
    same_note_runs = 0
    run_len = 1
    for i in range(1, len(pitches)):
        if pitches[i] == pitches[i-1]:
            run_len += 1
        else:
            if run_len > 3:
                same_note_runs += run_len
            run_len = 1
    if run_len > 3:
        same_note_runs += run_len
    same_note_penalty = min(same_note_runs / len(pitches), 1.0)

    # 9. 稀疏旋律惩罚
    sparsity_penalty = 0.0
    if len(pitches) <= 4:
        sparsity_penalty = 0.5
    elif len(pitches) <= 6:
        sparsity_penalty = 0.2

    # 10. 音程类型多样性（核心新指标）
    # 好旋律混合级进+小跳+偶尔大跳；CD交替只有1种音程
    interval_types = set()
    for iv in intervals:
        abs_iv = abs(iv)
        if abs_iv == 0:
            interval_types.add('unison')
        elif abs_iv <= 2:
            interval_types.add('step')
        elif abs_iv <= 5:
            interval_types.add('small_leap')
        elif abs_iv <= 7:
            interval_types.add('medium_leap')
        else:
            interval_types.add('large_leap')
    interval_variety = len(interval_types)  # 1-5

    # 10b. 同音重复比例（unison interval ratio）
    unison_ratio = sum(1 for iv in intervals if iv == 0) / len(intervals) if intervals else 0
    unison_penalty = 0.0
    if unison_ratio > 0.4:
        unison_penalty = 2.0  # 超过40%是同音重复=旋律差
    elif unison_ratio > 0.25:
        unison_penalty = 1.0

    # 11. 重复模式惩罚 — CD两音交替就是同一个2音pattern无限重复
    pattern_penalty = 0.0
    if len(pitches) >= 4:
        bigrams = [tuple(pitches[i:i+2]) for i in range(len(pitches)-1)]
        bg_counter = Counter(bigrams)
        most_common_bg = bg_counter.most_common(1)[0]
        most_common_bg_ratio = most_common_bg[1] / len(bigrams)
        # 如果超过70%都是同一个bigram，严重惩罚
        if most_common_bg_ratio > 0.8:
            pattern_penalty = 2.5
        elif most_common_bg_ratio > 0.6:
            pattern_penalty = 1.5
        elif most_common_bg_ratio > 0.4:
            pattern_penalty = 0.5

    # === 评分 ===
    # 音高多样性：需要至少5个不同音才像旋律
    if unique_pitches <= 2:
        diversity_mult = 0.0  # 1-2个音=不是旋律
    elif unique_pitches <= 3:
        diversity_mult = 0.15
    elif unique_pitches <= 4:
        diversity_mult = 0.4
    elif unique_pitches <= 6:
        diversity_mult = 0.7
    else:
        diversity_mult = 1.0

    # 音程多样性：至少2种类型才像旋律
    if interval_variety <= 1:
        variety_mult = 0.0  # 只有1种音程=不是旋律
    elif interval_variety == 2:
        variety_mult = 0.4
    elif interval_variety == 3:
        variety_mult = 0.75
    else:
        variety_mult = 1.0

    step_score = min(step_ratio / 0.6, 1.0) * 100
    leap_score = min(small_leap_ratio / 0.3, 1.0) * 50
    contour_score = min(contour_ratio / 0.5, 1.0) * 100
    # 音域：5-24半音为佳
    if pitch_range < 3:
        range_score = 0.0
    elif pitch_range < 5:
        range_score = (pitch_range / 5.0) * 30
    elif pitch_range <= 24:
        range_score = 30 + min((pitch_range - 5) / 19.0, 1.0) * 70
    else:
        range_score = 80  # 超大音域也给高分但封顶
    motif_score = min(motif_rate / 0.4, 1.0) * 100

    large_leap_pen = min(large_leap_ratio * 80, 25)   # 封顶25，避免琶音被过度惩罚
    extreme_pen = min(extreme_leap_ratio * 150, 25)    # 封顶25，同上
    repeat_pen = same_note_penalty * 100
    sparse_pen = sparsity_penalty * 80

    # 旋律质量评分：平衡多样性、音域和适度重复
    raw = (0.15 * step_score + 0.15 * leap_score + 0.25 * contour_score +
           0.20 * range_score + 0.10 * motif_score +
           0.15 * (min(interval_variety / 4.0, 1.0) * 100) -
           large_leap_pen - extreme_pen - repeat_pen - sparse_pen -
           pattern_penalty - unison_penalty)

    # 应用关键乘数
    raw *= diversity_mult * variety_mult

    # 熵指标
    interval_counter = Counter(intervals)
    total_iv = sum(interval_counter.values())
    entropy = 0.0
    if total_iv > 0:
        entropy = -sum((c / total_iv) * math.log2(c / total_iv) for c in interval_counter.values() if c > 0)

    score = max(0.0, min(100.0, raw))

    return MelodyResult(
        interval_diversity_entropy=round(entropy, 3),
        contour_change_ratio=round(contour_ratio, 3),
        pitch_range_semitones=pitch_range,
        motivic_repetition_rate=round(motif_rate, 3),
        melodic_points=points,
        score=round(score, 1),
    )
