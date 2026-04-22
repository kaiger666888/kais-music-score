"""音乐文件预处理 — MIDI/MusicXML 解析 → 统一内部格式"""
from typing import Optional
from music21 import converter, note, stream, tempo, meter, key as m21key
from .models import PieceInfo


def parse_file(path: str) -> stream.Score:
    """加载音乐文件"""
    return converter.parse(path)


def extract_piece_info(score: stream.Score, source_file: str = "") -> PieceInfo:
    """提取乐曲元信息"""
    fmt = "midi" if source_file.endswith(".mid") else "musicxml"
    measures = score.parts[0].getElementsByClass(stream.Measure) if score.parts else []
    total_measures = len(measures)
    total_duration_q = score.flatten().highestTime

    # 调性
    try:
        k = score.analyze('key')
        key_str = f"{k.tonic.name} {k.mode}"
    except Exception:
        key_str = "Unknown"

    # 拍号
    ts_list = list(score.flatten().getElementsByClass(meter.TimeSignature))
    time_sigs = list(set(str(ts.ratioString) for ts in ts_list)) if ts_list else ["4/4"]

    # 速度
    tempo_list = [t.number for t in score.flatten().getElementsByClass(tempo.MetronomeMark) if t.number]
    avg_tempo = sum(tempo_list) / len(tempo_list) if tempo_list else 120.0

    # 声部
    part_count = len(score.parts)
    track_names = [p.partName or f"Part {i}" for i, p in enumerate(score.parts)]

    return PieceInfo(
        source_file=source_file,
        format=fmt,
        total_measures=total_measures,
        total_duration_q=total_duration_q,
        key=key_str,
        time_signatures=time_sigs,
        tempo_marks=[avg_tempo],
        part_count=part_count,
        track_names=track_names,
    )


def chordify(score: stream.Score) -> stream.Stream:
    """合并声部为和弦流"""
    return score.chordify()


def extract_melody(score: stream.Score) -> list:
    """提取主旋律声部（音符数最多的 part）"""
    if not score.parts:
        return []
    # 选音符最多的 part
    best_part = max(score.parts, key=lambda p: len(list(p.flatten().getElementsByClass(note.Note))))
    return list(best_part.flatten().getElementsByClass(note.Note))


def extract_all_notes(score: stream.Score) -> list:
    """提取所有音符"""
    return list(score.flatten().getElementsByClass(note.Note))


def get_duration_seconds(score: stream.Score) -> float:
    """估算总时长（秒）"""
    tempo_marks = [t.number for t in score.flatten().getElementsByClass(tempo.MetronomeMark) if t.number]
    bpm = tempo_marks[0] if tempo_marks else 120.0
    q = score.flatten().highestTime or 1.0
    # quarterLength to seconds: at bpm, 1 quarter = 60/bpm seconds
    return q * 60.0 / bpm
