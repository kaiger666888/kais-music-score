"""CLI 主入口 — argparse + Jinja2 HTML 渲染"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from .models import AnalysisReport
from .preprocess import parse_file, extract_piece_info, chordify, extract_melody, extract_all_notes, get_duration_seconds
from .harmony_complexity import analyze as analyze_harmony
from .melody_diversity import analyze as analyze_melody
from .rhythm_innovation import analyze as analyze_rhythm
from .structure_coherence import analyze as analyze_structure
from .expressiveness import analyze as analyze_expressiveness
from .music_scorer import detect_genre, score_music
from .export import to_json, to_csv, _report_to_dict


def main():
    parser = argparse.ArgumentParser(description="kais-music-score: 音乐五维复杂度量化分析")
    parser.add_argument("--input", "-i", required=True, help="输入音乐文件路径 (.mid/.xml)")
    parser.add_argument("--output-dir", "-o", default="./output", help="输出目录")
    parser.add_argument("--format", "-f", choices=["html", "json", "csv", "all"], default="all", help="输出格式")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"错误：文件不存在: {args.input}", file=sys.stderr)
        sys.exit(1)

    # 解析
    print(f"🎼 加载文件: {args.input}")
    score_obj = parse_file(str(input_path))

    piece_info = extract_piece_info(score_obj, source_file=str(input_path))
    print(f"   调性: {piece_info.key}, 小节: {piece_info.total_measures}, 声部: {piece_info.part_count}")

    # 预处理
    chordified_stream = chordify(score_obj)
    melody_notes = extract_melody(score_obj)
    all_notes = extract_all_notes(score_obj)
    duration_sec = get_duration_seconds(score_obj)

    # 五维分析
    print("🔄 分析和声复杂度...")
    harmony = analyze_harmony(chordified_stream)
    print(f"   和弦熵: {harmony.chord_diversity_entropy}, 评分: {harmony.score}")

    print("🔄 分析旋律多样性...")
    melody = analyze_melody(melody_notes)
    print(f"   音程熵: {melody.interval_diversity_entropy}, 评分: {melody.score}")

    print("🔄 分析节奏创新性...")
    rhythm = analyze_rhythm(score_obj, all_notes, duration_sec)
    print(f"   切分比例: {rhythm.syncopation_ratio}, 评分: {rhythm.score}")

    print("🔄 分析结构完整性...")
    structure = analyze_structure(score_obj)
    print(f"   曲式: {structure.detected_form}, 评分: {structure.score}")

    print("🔄 分析表现力...")
    expressiveness = analyze_expressiveness(score_obj, all_notes, duration_sec)
    print(f"   力度范围: {expressiveness.dynamic_range}, 评分: {expressiveness.score}")

    # 类型检测 + 评分
    print("🔄 检测音乐类型...")
    genre = detect_genre(piece_info, harmony, rhythm, structure, expressiveness, melody)
    print(f"   类型: {genre.detected_genre} (置信度: {genre.confidence:.0%})")

    score_result = score_music(genre, harmony, melody, rhythm, structure, expressiveness)
    print(f"   总分: {score_result.total}/100  评级: {score_result.grade}")

    # 组装报告
    report = AnalysisReport(
        piece=piece_info,
        genre=genre,
        harmony=harmony,
        melody=melody,
        rhythm=rhythm,
        structure=structure,
        expressiveness=expressiveness,
        score=score_result,
    )

    # 输出
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    fmt = args.format

    if fmt in ("html", "all"):
        html_path = str(output_dir / "report.html")
        render_html(report, html_path)
        print(f"✅ HTML: {html_path}")

    if fmt in ("json", "all"):
        json_path = str(output_dir / "report.json")
        to_json(report, json_path)
        print(f"✅ JSON: {json_path}")

    if fmt in ("csv", "all"):
        csv_dir = str(output_dir / "csv")
        files = to_csv(report, csv_dir)
        print(f"✅ CSV: {csv_dir}/ ({len(files)} files)")


def render_html(report: AnalysisReport, output_path: str) -> None:
    from jinja2 import Environment, FileSystemLoader
    template_dir = Path(__file__).parent.parent / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)), autoescape=True)
    template = env.get_template("report.html.j2")

    report_data = _report_to_dict(report)
    # Add chart data
    report_data["melody_points"] = [
        {"pitch": p.pitch, "measure": p.measure} for p in report.melody.melodic_points
    ]
    report_data["rhythm_points"] = [
        {"beat_strength": p.beat_strength, "is_syncopated": p.is_syncopated} for p in report.rhythm.rhythmic_points
    ]
    report_data["harmony_events"] = [
        {"root": e.root, "measure": e.measure} for e in report.harmony.chord_events
    ]
    report_data["meta"]["expressiveness"] = {
        "dynamic_range": report.expressiveness.dynamic_range,
        "dynamic_change_frequency": report.expressiveness.dynamic_change_frequency,
        "tempo_variation_range": report.expressiveness.tempo_variation_range,
        "articulation_types": report.expressiveness.articulation_types,
    }

    html_content = template.render(
        report=report,
        report_data=json.dumps(report_data, ensure_ascii=False),
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    )
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)


if __name__ == "__main__":
    main()
