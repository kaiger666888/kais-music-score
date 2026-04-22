"""结构完整性分析"""
import math
from collections import Counter
from music21 import note, stream, chord
from .models import StructureResult


def analyze(score_obj) -> StructureResult:
    """分析结构完整性"""
    if not score_obj.parts:
        return StructureResult()

    part = score_obj.parts[0]
    measures = list(part.getElementsByClass(stream.Measure))
    if not measures:
        return StructureResult()

    # 1. 重复模式检测（旋律轮廓 4-gram 匹配）
    melody_notes = list(part.flatten().getElementsByClass(note.Note))
    pitches = [n.pitch.midi for n in melody_notes if hasattr(n, 'pitch') and n.pitch]
    rep_coverage = 0.0

    if len(pitches) >= 8:
        window = 4
        total_windows = len(pitches) - window + 1
        patterns = [tuple(pitches[i:i + window]) for i in range(total_windows)]
        pattern_counter = Counter(patterns)
        repeated_notes = sum(c * window for c in pattern_counter.values() if c > 1)
        rep_coverage = repeated_notes / len(pitches) if len(pitches) > 0 else 0.0

    # 2. 曲式识别（简化：基于和弦重复模式）
    chordified = score_obj.chordify()
    chords_per_measure = {}
    for c in chordified.recurse().getElementsByClass(chord.Chord):
        m = c.measureNumber or 0
        try:
            name = c.commonName or str(c.root().name)
        except Exception:
            name = "N/A"
        chords_per_measure.setdefault(m, []).append(name)

    # 每 4 小节为一个段落的签名
    section_signatures = []
    for i in range(0, len(measures), 4):
        sig = []
        for j in range(i, min(i + 4, len(measures))):
            m_num = measures[j].number
            sig.extend(chords_per_measure.get(m_num, [""]))
        section_signatures.append(tuple(sig))

    # 聚类判断曲式
    sig_counter = Counter(section_signatures)
    unique_sections = len(sig_counter)
    total_sections = len(section_signatures)

    if unique_sections <= 1:
        detected_form = "AAAA"
    elif unique_sections == 2:
        a_sig, _ = sig_counter.most_common(1)[0]
        if section_signatures == [a_sig, a_sig]:
            detected_form = "AA"
        elif section_signatures[0] == section_signatures[-1]:
            detected_form = "ABA"
        else:
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
            boundaries.append(i * 4)
        prev_sig = sig

    # 3. 乐句对称性（休止符分割乐句长度）
    rests = list(part.flatten().getElementsByClass(note.Rest))
    phrase_lengths = []
    if rests:
        prev_pos = 0.0
        for r in rests:
            pos = r.offset
            if pos - prev_pos > 2.0:  # 至少 2 拍才算一个乐句
                phrase_lengths.append(pos - prev_pos)
            prev_pos = pos
        phrase_lengths.append(part.highestTime - prev_pos)
    else:
        phrase_lengths.append(part.highestTime)

    if phrase_lengths:
        mean_pl = sum(phrase_lengths) / len(phrase_lengths)
        std_pl = math.sqrt(sum((l - mean_pl) ** 2 for l in phrase_lengths) / len(phrase_lengths))
        cv = std_pl / mean_pl if mean_pl > 0 else 0.0
    else:
        cv = 0.0

    # 4. 发展逻辑评分（简化：基于重复+变化比例）
    dev_score = min(rep_coverage * 100 + (1 - cv) * 30, 100) if cv <= 1 else 30

    # 评分
    rep_norm = min(rep_coverage / 0.6, 1.0) * 100
    form_norm = min(unique_sections / 4.0, 1.0) * 100
    sym_norm = max(0, 1.0 - cv) * 100
    dev_norm = min(dev_score, 100)

    score = 0.30 * rep_norm + 0.25 * form_norm + 0.20 * sym_norm + 0.25 * dev_norm

    return StructureResult(
        repetition_coverage=round(rep_coverage, 3),
        detected_form=detected_form,
        phrase_symmetry_cv=round(cv, 3),
        development_logic_score=round(dev_score, 1),
        section_boundaries=boundaries,
        score=round(score, 1),
    )
