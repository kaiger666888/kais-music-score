"""表现力分析 — 给无力度标记的MIDI合理默认值"""
from music21 import note, tempo, dynamics
from .models import ExpressivenessResult


def analyze(score_obj, all_notes: list, duration_seconds: float) -> ExpressivenessResult:
    """分析表现力"""
    velocities = []
    articulation_set = set()

    for n in all_notes:
        if hasattr(n, 'volume') and n.volume and n.volume.velocity is not None:
            velocities.append(n.volume.velocity)
        if hasattr(n, 'articulations') and n.articulations:
            for art in n.articulations:
                articulation_set.add(type(art).__name__)

    # 如果没有力度标记，使用合理的默认值
    # 实际音乐通常有力度变化，所以完全无标记稍微扣分
    has_velocity = len(velocities) > 0

    if not has_velocity:
        # 无力度标记时给一个中等范围，不加分也不大幅扣分
        velocities = [80] * min(len(all_notes), 10)
        # 实际上如果没有力度标记，给0范围
        velocities = []

    # 1. 力度范围
    dyn_range = max(velocities) - min(velocities) if velocities else 0

    # 2. 力度变化频率
    changes = 0
    if len(velocities) > 1:
        for i in range(1, len(velocities)):
            if abs(velocities[i] - velocities[i - 1]) > 15:
                changes += 1
    change_freq = changes / (duration_seconds / 60.0) if duration_seconds > 0 else 0.0

    # 3. 速度变化
    tempo_marks = [t.number for t in score_obj.flatten().getElementsByClass(tempo.MetronomeMark) if t.number]
    tempo_range = (max(tempo_marks) - min(tempo_marks)) if len(tempo_marks) >= 2 else 0.0

    # 4. Articulation 多样性
    art_types = len(articulation_set)
    art_details = sorted(articulation_set)

    # 评分 — 对无力度标记的MIDI给基线分而非0
    range_norm = min(dyn_range / 127.0, 1.0) * 100
    freq_norm = min(change_freq / 10.0, 1.0) * 100
    tempo_norm = min(tempo_range / 40.0, 1.0) * 100
    art_norm = min(art_types / 5.0, 1.0) * 100

    raw = 0.30 * range_norm + 0.25 * freq_norm + 0.25 * tempo_norm + 0.20 * art_norm

    # 如果没有任何表现力标记，给一个基线分（代表"中性"）
    if not has_velocity and tempo_range == 0 and art_types == 0:
        raw = 30.0  # 基线分，不惩罚也不奖励

    score = max(0.0, min(100.0, raw))

    return ExpressivenessResult(
        dynamic_range=dyn_range,
        dynamic_change_frequency=round(change_freq, 2),
        tempo_variation_range=round(tempo_range, 1),
        articulation_types=art_types,
        articulation_details=art_details,
        score=round(score, 1),
    )
