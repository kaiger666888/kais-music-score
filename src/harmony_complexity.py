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

    # === 和弦进行质量分析 ===
    # 策略：按小节聚合和弦，检测和弦进行模式
    # chordify产生大量事件（每拍一个），需要按小节聚合才能看清真正的进行
    
    root_pitch_classes = []
    for e in events:
        root_pitch_classes.append(e.root % 12)
    
    # 按小节聚合根音（取每个小节最常见的根音）
    measure_roots = {}  # measure -> most common root
    for e in events:
        m = e.measure
        if m not in measure_roots:
            measure_roots[m] = Counter()
        measure_roots[m][e.root % 12] += 1
    
    # 提取小节级和弦根音序列
    sorted_measures = sorted(measure_roots.keys())
    measure_root_seq = []
    for m in sorted_measures:
        most_common = measure_roots[m].most_common(1)[0][0]
        measure_root_seq.append(most_common)
    
    unique_roots = len(set(measure_root_seq)) if measure_root_seq else 0
    
    # 小节级bigram重复率
    measure_bigram_rep = 0.0
    if len(measure_root_seq) >= 4:
        bigrams = [tuple(measure_root_seq[i:i+2]) for i in range(len(measure_root_seq)-1)]
        bg_counter = Counter(bigrams)
        bg_repeated = sum(c for c in bg_counter.values() if c > 1)
        measure_bigram_rep = bg_repeated / len(bigrams) if bigrams else 0
    
    # 小节级trigram多样性
    measure_trigram_div = 1.0
    if len(measure_root_seq) >= 6:
        trigrams = [tuple(measure_root_seq[i:i+3]) for i in range(len(measure_root_seq)-2)]
        tg_counter = Counter(trigrams)
        measure_trigram_div = len(tg_counter) / len(trigrams) if trigrams else 1.0
    
    # 简单进行惩罚（基于小节级分析）
    simple_progression_penalty = 0.0
    
    # 检查根音集中度：如果少数几个根音占据大部分小节=简单进行
    root_counter = Counter(measure_root_seq)
    total_measures_count = len(measure_root_seq)
    top_roots = root_counter.most_common(3)
    top_roots_coverage = sum(count for _, count in top_roots) / total_measures_count if total_measures_count > 0 else 0
    
    # top3根音覆盖>60% = 和弦进行主要由2-3个和弦组成
    if top_roots_coverage > 0.6:
        simple_progression_penalty = 25.0
    elif top_roots_coverage > 0.5:
        simple_progression_penalty = 15.0
    
    # trigram多样性低 + 根音少 = 缺乏发展
    if measure_trigram_div < 0.25 and unique_roots <= 5:
        simple_progression_penalty = max(simple_progression_penalty, 30.0)
    elif measure_trigram_div < 0.35 and unique_roots <= 4:
        simple_progression_penalty = max(simple_progression_penalty, 15.0)
    
    # 根音太少 = 简单伴奏
    if unique_roots <= 2:
        simple_progression_penalty += 25.0
    elif unique_roots <= 3:
        simple_progression_penalty += 10.0

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

    raw = base_score + entropy_norm + mod_norm + vl_norm + rm_norm + size_variety_bonus - fake_chord_penalty - simple_progression_penalty

    score = max(0.0, min(100.0, raw))

    return HarmonyResult(
        chord_diversity_entropy=round(entropy, 3),
        modulation_count=mod_count,
        voice_leading_smoothness=round(vl_smoothness, 2),
        root_motion_distribution=root_motion,
        chord_events=events,
        score=round(score, 1),
    )
