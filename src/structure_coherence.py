"""结构完整性分析 — 基于和弦变化+音高变化检测段落"""
import math
from collections import Counter
from music21 import note, stream, chord
from .models import StructureResult


def analyze(score_obj) -> StructureResult:
    """分析结构完整性"""
    if not score_obj.parts:
        return StructureResult()

    part = score_obj.parts[0]

    # 提取所有音高
    all_pitches = []
    for el in part.flatten().getElementsByClass([note.Note, chord.Chord]):
        if isinstance(el, note.Note):
            all_pitches.append(el.pitch.midi)
        elif isinstance(el, chord.Chord):
            if el.pitches:
                all_pitches.append(max(p.midi for p in el.pitches))

    if len(all_pitches) < 4:
        return StructureResult()

    # === 音高丰富度门控 ===
    unique_pitches = len(set(all_pitches))
    if unique_pitches <= 2:
        pitch_richness_factor = 0.05
    elif unique_pitches <= 3:
        pitch_richness_factor = 0.2
    elif unique_pitches <= 5:
        pitch_richness_factor = 0.5
    else:
        pitch_richness_factor = 1.0

    # 1. 单音重复惩罚
    pitch_counter = Counter(all_pitches)
    most_common_ratio = pitch_counter.most_common(1)[0][1] / len(all_pitches)
    monotone_penalty = 1.0 if most_common_ratio > 0.9 else (0.5 if most_common_ratio > 0.7 else 0.0)

    # 2. 音高重复模式检测（4-gram）
    pitch_rep_coverage = 0.0
    if len(all_pitches) >= 8:
        window = 4
        patterns = [tuple(all_pitches[i:i + window]) for i in range(len(all_pitches) - window + 1)]
        pattern_counter = Counter(patterns)
        repeated_notes = sum(c * window for c in pattern_counter.values() if c > 1)
        pitch_rep_coverage = repeated_notes / len(all_pitches) if all_pitches else 0.0

    # === 和弦进行分析（对结构检测至关重要）===
    chordified = score_obj.chordify()
    chord_events = list(chordified.recurse().getElementsByClass(chord.Chord))

    chord_roots = []
    for c in chord_events:
        try:
            root = c.root().midi % 12 if c.root() else 0
            chord_roots.append(root)
        except Exception:
            chord_roots.append(-1)

    # 和弦bigram重复（和声节奏模式）
    chord_pattern_score = 0.0
    if len(chord_roots) >= 4:
        chord_bigrams = [tuple(chord_roots[i:i+2]) for i in range(len(chord_roots)-1)]
        cb_counter = Counter(chord_bigrams)
        cb_repeated = sum(c for c in cb_counter.values() if c > 1)
        chord_pattern_score = cb_repeated / len(chord_bigrams) if chord_bigrams else 0

    # 段落多样性
    unique_sections = 1
    section_signatures = []
    if len(chord_roots) >= 2:
        chunk_size = max(2, len(chord_roots) // 4)
        chunk_size = min(chunk_size, 4)
        for i in range(0, len(chord_roots), chunk_size):
            section_signatures.append(tuple(chord_roots[i:i + chunk_size]))
        sig_counter = Counter(section_signatures)
        unique_sections = len(sig_counter)
    elif len(chord_roots) == 0:
        unique_pitch_patterns = len(set(tuple(all_pitches[i:i+2]) for i in range(len(all_pitches)-1)))
        unique_sections = max(1, min(unique_pitch_patterns, 5))

    if unique_sections <= 1:
        detected_form = "AAAA"
    elif unique_sections == 2:
        detected_form = "AB"
    elif unique_sections == 3:
        detected_form = "ABA"
    else:
        detected_form = f"AB... ({unique_sections} sections)"

    boundaries = []
    prev_sig = None
    for i, sig in enumerate(section_signatures):
        if prev_sig is not None and sig != prev_sig:
            boundaries.append(i)
        prev_sig = sig

    # 4. 乐句对称性
    rests = list(part.flatten().getElementsByClass(note.Rest))
    phrase_lengths = []
    if rests:
        prev_pos = 0.0
        for r in rests:
            pos = r.offset
            if pos - prev_pos > 2.0:
                phrase_lengths.append(pos - prev_pos)
            prev_pos = pos
        if part.highestTime > 0:
            phrase_lengths.append(part.highestTime - prev_pos)
    else:
        phrase_lengths.append(part.highestTime if part.highestTime > 0 else 1.0)

    if phrase_lengths:
        mean_pl = sum(phrase_lengths) / len(phrase_lengths)
        std_pl = math.sqrt(sum((l - mean_pl) ** 2 for l in phrase_lengths) / len(phrase_lengths))
        cv = std_pl / mean_pl if mean_pl > 0 else 0.0
    else:
        cv = 0.0

    # === 评分 ===
    # 段落多样性
    if unique_sections <= 1:
        section_score = 10.0
    elif unique_sections == 2:
        section_score = 88.0
    elif unique_sections == 3:
        section_score = 93.0
    elif unique_sections <= 5:
        section_score = 82.0
    elif unique_sections <= 7:
        section_score = 75.0  # 更多段落仍然合理
    else:
        section_score = 50.0

    # 重复模式：同时考虑音高重复和和弦重复
    combined_rep = max(pitch_rep_coverage, chord_pattern_score)
    rep_norm = min(combined_rep / 0.5, 1.0) * 75
    
    sym_norm = max(0, 1.0 - cv) * 80
    
    # 发展逻辑：基于组合重复率
    dev_score = min(combined_rep * 100 + (1 - cv) * 30, 100) if cv <= 1 else 30

    raw = (0.30 * section_score + 0.25 * rep_norm + 0.20 * sym_norm + 0.25 * dev_score)
    raw -= monotone_penalty * 50
    raw *= pitch_richness_factor

    if len(all_pitches) <= 4:
        raw *= 0.3

    score = max(0.0, min(100.0, raw))

    return StructureResult(
        repetition_coverage=round(combined_rep, 3),
        detected_form=detected_form,
        phrase_symmetry_cv=round(cv, 3),
        development_logic_score=round(dev_score, 1),
        section_boundaries=boundaries,
        score=round(score, 1),
    )
