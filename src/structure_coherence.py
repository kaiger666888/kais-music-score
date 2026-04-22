"""结构完整性分析 — 基于和弦变化检测段落，区分有意义AB和无脑重复"""
import math
from collections import Counter
from music21 import note, stream, chord
from .models import StructureResult


def analyze(score_obj) -> StructureResult:
    """分析结构完整性"""
    if not score_obj.parts:
        return StructureResult()

    part = score_obj.parts[0]

    # 提取所有音高（包括和弦分解）
    all_pitches = []
    for el in part.flatten().getElementsByClass([note.Note, chord.Chord]):
        if isinstance(el, note.Note):
            all_pitches.append(el.pitch.midi)
        elif isinstance(el, chord.Chord):
            if el.pitches:
                all_pitches.append(max(p.midi for p in el.pitches))

    if len(all_pitches) < 4:
        return StructureResult()

    # 1. 单音重复惩罚
    pitch_counter = Counter(all_pitches)
    most_common_ratio = pitch_counter.most_common(1)[0][1] / len(all_pitches)
    monotone_penalty = 1.0 if most_common_ratio > 0.9 else (0.5 if most_common_ratio > 0.7 else 0.0)

    # 2. 重复模式检测（4-gram）
    rep_coverage = 0.0
    if len(all_pitches) >= 8:
        window = 4
        patterns = [tuple(all_pitches[i:i + window]) for i in range(len(all_pitches) - window + 1)]
        pattern_counter = Counter(patterns)
        unique_patterns = len(set(patterns))
        repeated_notes = sum(c * window for c in pattern_counter.values() if c > 1)
        rep_coverage = repeated_notes / len(all_pitches) if all_pitches else 0.0

    # 3. 段落多样性 — 基于和弦根音变化（而非小节）
    chordified = score_obj.chordify()
    chord_events = list(chordified.recurse().getElementsByClass(chord.Chord))

    # 提取和弦根音序列
    chord_roots = []
    for c in chord_events:
        try:
            root = c.root().midi % 12 if c.root() else 0
            chord_roots.append(root)
        except Exception:
            chord_roots.append(-1)

    # 将和弦序列分成段落（每4个和弦一个段落）
    unique_sections = 1
    section_signatures = []
    if len(chord_roots) >= 2:
        chunk_size = max(2, len(chord_roots) // 4)  # 自适应段落大小
        chunk_size = min(chunk_size, 4)
        for i in range(0, len(chord_roots), chunk_size):
            section_signatures.append(tuple(chord_roots[i:i + chunk_size]))
        sig_counter = Counter(section_signatures)
        unique_sections = len(sig_counter)
    elif len(chord_roots) == 0:
        # 无和弦 — 用音高变化判断
        unique_pitch_patterns = len(set(tuple(all_pitches[i:i+2]) for i in range(len(all_pitches)-1)))
        unique_sections = max(1, min(unique_pitch_patterns, 5))

    # 曲式识别
    if unique_sections <= 1:
        detected_form = "AAAA"
    elif unique_sections == 2:
        detected_form = "AB"
    elif unique_sections == 3:
        detected_form = "ABA"
    else:
        detected_form = f"AB... ({unique_sections} sections)"

    # 段落边界
    boundaries = []
    prev_sig = None
    for i, sig in enumerate(section_signatures):
        if prev_sig is not None and sig != prev_sig:
            boundaries.append(i)
        prev_sig = sig

    # 4. 乐句对称性
    measures = list(part.getElementsByClass(stream.Measure)) if hasattr(part, 'getElementsByClass') else []
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

    # 5. 发展逻辑
    dev_score = min(rep_coverage * 100 + (1 - cv) * 30, 100) if cv <= 1 else 30

    # === 评分 ===
    # 段落多样性：2-4个不同段落最好
    if unique_sections <= 1:
        section_score = 10.0  # 无结构变化
    elif unique_sections == 2:
        section_score = 90.0
    elif unique_sections == 3:
        section_score = 95.0
    elif unique_sections <= 4:
        section_score = 85.0
    else:
        section_score = 60.0

    rep_norm = min(rep_coverage / 0.5, 1.0) * 80
    sym_norm = max(0, 1.0 - cv) * 100

    raw = (0.30 * section_score + 0.25 * rep_norm + 0.20 * sym_norm + 0.25 * dev_score)

    # 无脑重复惩罚
    raw -= monotone_penalty * 60

    # 稀疏惩罚 — 但只对真正稀疏的（单音重复那种），不惩罚和弦进行
    if len(all_pitches) <= 4:
        raw *= 0.3
    elif monotone_penalty > 0:
        raw *= 0.5

    score = max(0.0, min(100.0, raw))

    return StructureResult(
        repetition_coverage=round(rep_coverage, 3),
        detected_form=detected_form,
        phrase_symmetry_cv=round(cv, 3),
        development_logic_score=round(dev_score, 1),
        section_boundaries=boundaries,
        score=round(score, 1),
    )
