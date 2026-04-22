"""表现力分析"""
from music21 import note, tempo, dynamics
from .models import ExpressivenessResult


def analyze(score_obj, all_notes: list, duration_seconds: float) -> ExpressivenessResult:
    """分析表现力"""
    velocities = []
    articulation_set = set()

    for n in all_notes:
        # velocity
        if hasattr(n, 'volume') and n.volume and n.volume.velocity is not None:
            velocities.append(n.volume.velocity)
        # articulations
        if hasattr(n, 'articulations') and n.articulations:
            for art in n.articulations:
                articulation_set.add(type(art).__name__)

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

    # 评分
    range_norm = min(dyn_range / 127.0, 1.0) * 100
    freq_norm = min(change_freq / 10.0, 1.0) * 100
    tempo_norm = min(tempo_range / 40.0, 1.0) * 100
    art_norm = min(art_types / 5.0, 1.0) * 100

    score = 0.30 * range_norm + 0.25 * freq_norm + 0.25 * tempo_norm + 0.20 * art_norm

    return ExpressivenessResult(
        dynamic_range=dyn_range,
        dynamic_change_frequency=round(change_freq, 2),
        tempo_variation_range=round(tempo_range, 1),
        articulation_types=art_types,
        articulation_details=art_details,
        score=round(score, 1),
    )
