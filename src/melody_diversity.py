"""旋律多样性分析 — 奖励级进运动，惩罚随机大跳"""
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

    # 1. 级进比例 (stepwise motion: |interval| <= 2) — 好旋律的核心特征
    step_count = sum(1 for iv in intervals if abs(iv) <= 2)
    step_ratio = step_count / len(intervals)

    # 2. 小跳比例 (small leaps: 3 <= |interval| <= 5) — 适度跳跃是好的
    small_leap_count = sum(1 for iv in intervals if 3 <= abs(iv) <= 5)
    small_leap_ratio = small_leap_count / len(intervals)

    # 3. 大跳惩罚 (large leaps: |interval| > 7, > octave) — 随机音乐特征
    large_leap_count = sum(1 for iv in intervals if abs(iv) > 7)
    large_leap_ratio = large_leap_count / len(intervals)
    extreme_leap_count = sum(1 for iv in intervals if abs(iv) > 12)
    extreme_leap_ratio = extreme_leap_count / len(intervals)

    # 4. 轮廓变化率 — 好旋律有方向变化
    changes = sum(1 for i in range(1, len(directions)) if directions[i] != directions[i - 1])
    contour_ratio = changes / len(directions) if directions else 0.0

    # 5. 音域
    pitch_range = max(pitches) - min(pitches) if pitches else 0

    # 6. 动机重复率（3-gram）— 好旋律有主题重复
    motif_rate = 0.0
    if len(pitches) >= 6:
        trigrams = [tuple(pitches[i:i + 3]) for i in range(len(pitches) - 2)]
        tg_counter = Counter(trigrams)
        repeated = sum(c for c in tg_counter.values() if c > 1)
        motif_rate = repeated / len(trigrams) if trigrams else 0.0

    # 7. 单音重复惩罚 — 同一音连续重复超过3次
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
    same_note_penalty = min(same_note_runs / len(pitches), 1.0) if pitches else 0.0

    # 7. 稀疏旋律惩罚 — 太少音符说明旋律太简单
    sparsity_penalty = 0.0
    if len(pitches) <= 4:
        sparsity_penalty = 0.5
    elif len(pitches) <= 6:
        sparsity_penalty = 0.2

    # 8. 音高多样性惩罚 — 唯一音过少=旋律贫乏
    unique_pitches = len(set(pitches)) if pitches else 0
    diversity_penalty = 0.0
    if unique_pitches <= 2:
        diversity_penalty = 2.5  # 只有1-2个音=几乎无旋律
    elif unique_pitches <= 3:
        diversity_penalty = 1.5
    elif unique_pitches <= 4:
        diversity_penalty = 0.8

    # === 评分 ===
    # 好旋律 = 高级进比例 + 适度小跳 + 低大跳 + 有方向变化 + 有动机重复 + 不单调重复
    step_score = min(step_ratio / 0.6, 1.0) * 100      # 级进多 → 高分
    leap_score = min(small_leap_ratio / 0.3, 1.0) * 50  # 适度跳跃加分
    contour_score = min(contour_ratio / 0.5, 1.0) * 100  # 方向变化多 → 高分
    range_score = min(pitch_range / 24.0, 1.0) * 100 if pitch_range >= 5 else (pitch_range / 5.0) * 50  # 适度音域
    motif_score = min(motif_rate / 0.4, 1.0) * 100      # 动机重复 → 高分

    # 惩罚项
    large_leap_penalty = large_leap_ratio * 80            # 大跳惩罚
    extreme_penalty = extreme_leap_ratio * 150            # 超大跳严重惩罚
    repeat_penalty = same_note_penalty * 100              # 单音重复惩罚
    sparse_penalty = sparsity_penalty * 80                # 稀疏旋律惩罚

    raw = (0.30 * step_score + 0.15 * leap_score + 0.20 * contour_score +
           0.15 * range_score + 0.20 * motif_score -
           large_leap_penalty - extreme_penalty - repeat_penalty - sparse_penalty - diversity_penalty)

    # 熵指标保留用于类型检测
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
