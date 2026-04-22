"""和声复杂度分析"""
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

    # 2. 调性变化（简单分段检测）
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

    # 3. 声部进行（相邻和弦根音半音距离）
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

    # 评分（0-100）
    entropy_norm = min(entropy / 4.0, 1.0) * 100
    mod_norm = min(mod_count / 5.0, 1.0) * 100
    vl_norm = max(0, 1.0 - vl_smoothness / 5.0) * 100
    rm_norm = min(len(interval_counter) / 7.0, 1.0) * 100

    score = 0.35 * entropy_norm + 0.25 * mod_norm + 0.25 * vl_norm + 0.15 * rm_norm

    return HarmonyResult(
        chord_diversity_entropy=round(entropy, 3),
        modulation_count=mod_count,
        voice_leading_smoothness=round(vl_smoothness, 2),
        root_motion_distribution=root_motion,
        chord_events=events,
        score=round(score, 1),
    )
