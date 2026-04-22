"""和声复杂度分析 — 多维度评估和声质量"""
import math
from collections import Counter
from music21 import chord, interval, note, stream
from .models import HarmonyResult, ChordEvent


def _shannon_entropy(counter: Counter) -> float:
    total = sum(counter.values())
    if total == 0:
        return 0.0
    return -sum((c / total) * math.log2(c / total) for c in counter.values() if c > 0)


def analyze(chordified: stream.Stream) -> HarmonyResult:
    """分析和弦复杂度"""
    chord_objs = list(chordified.recurse().getElementsByClass(chord.Chord))
    events = []
    chord_names = []

    for c in chord_objs:
        try:
            name = c.commonName or c.pitchedCommonName or str(c.pitches[0].name) if c.pitches else "N/A"
        except Exception:
            name = "N/A"
        root_midi = c.root().midi if c.root() else 60
        events.append(ChordEvent(
            measure=c.measureNumber or 0,
            beat=c.beat or 0.0,
            name=name,
            root=root_midi,
            pitches=[p.midi for p in c.pitches],
        ))
        chord_names.append(name)

    # 1. 和弦多样性熵
    name_counter = Counter(chord_names)
    entropy = _shannon_entropy(name_counter)

    # 1b. 真实和弦比例 — 识别为三和弦/七和弦的比例
    # music21 commonName 会对非标准"和弦"返回None或原始音名
    real_chord_count = 0
    for c in chord_objs:
        cn = c.commonName
        if cn and ('major' in cn or 'minor' in cn or 'dominant' in cn or 
                  'diminished' in cn or 'augmented' in cn or 'half-diminished' in cn or
                  'minor-major' in cn or 'major-seventh' in cn or 'minor-seventh' in cn or
                  'dominant-seventh' in cn):
            real_chord_count += 1
    real_ratio = real_chord_count / len(chord_objs) if chord_objs else 0
    fake_chord_penalty = (1.0 - real_ratio) * 60  # 非真实和弦多→大幅扣分

    # 2. 调性变化
    mod_count = 0
    try:
        if len(chordified.parts) > 0:
            measures = chordified.parts[0].getElementsByClass(stream.Measure)
            prev_key = None
            segment_measures = []
            for m in measures:
                segment_measures.append(m)
                if len(segment_measures) >= 8:
                    seg = stream.Stream(segment_measures)
                    try:
                        k = seg.analyze('key')
                        cur_key = f"{k.tonic.name}{k.mode}"
                        if prev_key and cur_key != prev_key:
                            mod_count += 1
                        prev_key = cur_key
                    except Exception:
                        pass
                    segment_measures = []
    except Exception:
        pass

    # 3. 声部进行
    distances = []
    for i in range(1, len(events)):
        d = abs(events[i].root - events[i - 1].root) % 12
        distances.append(d)
    vl_smoothness = sum(distances) / len(distances) if distances else 2.0

    # 4. 根音运动分布
    interval_counter = Counter()
    for i in range(1, len(events)):
        d = abs(events[i].root - events[i - 1].root) % 12
        interval_counter[d] += 1
    root_motion = {str(k): v / sum(interval_counter.values()) if interval_counter else 0
                   for k, v in sorted(interval_counter.items())}

    # 5. 和弦数量（基础分指标）
    chord_count = len(events)
    
    # 6. 和弦音程丰富度（三和弦vs七和弦vs更多）
    chord_size_diversity = set()
    for c in chord_objs:
        chord_size_diversity.add(len(c.pitches))

    # === 评分 ===
    # 基础分：有和弦变化就给基线
    if chord_count <= 1:
        base_score = 5.0
    elif chord_count <= 3:
        base_score = 15.0
    else:
        base_score = 25.0

    entropy_norm = min(entropy / 3.5, 1.0) * 35
    mod_norm = min(mod_count / 3.0, 1.0) * 20
    vl_norm = max(0, 1.0 - vl_smoothness / 4.5) * 25
    rm_norm = min(len(interval_counter) / 6.0, 1.0) * 15
    
    # 和弦大小多样性奖励（有3音、4音、5音和弦=好）
    size_variety_bonus = min(len(chord_size_diversity) / 3.0, 1.0) * 10

    raw = base_score + entropy_norm + mod_norm + vl_norm + rm_norm + size_variety_bonus - fake_chord_penalty

    score = max(0.0, min(100.0, raw))

    return HarmonyResult(
        chord_diversity_entropy=round(entropy, 3),
        modulation_count=mod_count,
        voice_leading_smoothness=round(vl_smoothness, 2),
        root_motion_distribution=root_motion,
        chord_events=events,
        score=round(score, 1),
    )
