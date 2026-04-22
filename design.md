# kais-music-score 架构设计文档

> 音乐五维复杂度量化分析系统 — 从 MIDI/MusicXML 到交互式可视化报告

---

## 1. 目录结构

```
kais-music-score/
├── src/
│   ├── __init__.py
│   ├── cli.py                  # CLI 入口 (argparse)
│   ├── preprocess.py           # 音乐文件解析、分段、特征提取
│   ├── genre_detector.py       # 类型检测（古典/流行/爵士/电子/摇滚）
│   ├── harmony_complexity.py   # 维度1: 和声复杂度
│   ├── melody_diversity.py     # 维度2: 旋律多样性
│   ├── rhythm_innovation.py    # 维度3: 节奏创新性
│   ├── structure_coherence.py  # 维度4: 结构完整性
│   ├── expressiveness.py       # 维度5: 表现力
│   ├── music_scorer.py         # 类型感知评分引擎
│   ├── models.py               # 数据模型 (dataclass)
│   ├── export.py               # JSON/CSV 导出
│   └── render.py               # Jinja2 HTML 报告渲染
├── templates/
│   └── report.html.j2          # Plotly 交互式报告模板
├── requirements.txt
├── pyproject.toml
├── README.md
└── tests/
    ├── fixtures/               # 测试用 MIDI/XML 文件
    └── test_*.py
```

---

## 2. 数据模型 (`models.py`)

参考 story-score 的 `models.py`，用 dataclass 定义所有中间和最终数据结构：

```python
@dataclass
class PieceInfo:
    """乐曲基本信息"""
    source_file: str
    format: str                     # "midi" | "musicxml"
    total_measures: int
    total_duration_q: float         # quarterLength
    key: str                        # 如 "C major"
    time_signatures: list[str]      # 如 ["4/4"]
    tempo_marks: list[float]        # BPM 值列表
    part_count: int
    track_names: list[str]

@dataclass
class ChordEvent:
    """和弦事件"""
    measure: int
    beat: float
    name: str                       # 如 "C major", "Dm7"
    root: int                       # MIDI pitch
    pitches: list[int]

@dataclass
class MelodicPoint:
    """旋律分析单点"""
    measure: int
    beat: float
    pitch: int                      # MIDI pitch
    interval_from_prev: int         # 半音数
    direction: int                  # +1/-1/0

@dataclass
class RhythmicPoint:
    """节奏分析单点"""
    measure: int
    beat: float
    duration_q: float               # quarterLength
    beat_strength: float
    is_syncopated: bool

@dataclass
class HarmonyResult:
    chord_diversity_entropy: float
    modulation_count: int
    voice_leading_smoothness: float  # 平均半音距离
    root_motion_distribution: dict[str, float]  # interval_name -> ratio
    chord_events: list[ChordEvent]
    score: float                    # 0-100

@dataclass
class MelodyResult:
    interval_diversity_entropy: float
    contour_change_ratio: float
    pitch_range_semitones: int
    motivic_repetition_rate: float
    melodic_points: list[MelodicPoint]
    score: float

@dataclass
class RhythmResult:
    rhythmic_diversity_entropy: float
    syncopation_ratio: float
    notes_per_second: float
    polyrhythm_detected: bool
    rhythmic_points: list[RhythmicPoint]
    score: float

@dataclass
class StructureResult:
    repetition_coverage: float
    detected_form: str              # "ABA", "ABAC", "sonata", etc.
    phrase_symmetry_cv: float       # 变异系数
    development_logic_score: float
    section_boundaries: list[int]   # 小节号
    score: float

@dataclass
class ExpressivenessResult:
    dynamic_range: int              # velocity max-min
    dynamic_change_frequency: float # 次/分钟
    tempo_variation_range: float    # BPM max-min
    articulation_types: int
    articulation_details: list[str]
    score: float

@dataclass
class GenreDetection:
    detected_genre: str             # "classical"|"pop"|"jazz"|"electronic"|"rock"
    confidence: float               # 0-1
    genre_scores: dict[str, float]  # 各类型得分

@dataclass
class ScoreResult:
    """类型感知评分结果"""
    detected_genre: str
    genre_confidence: float
    genre_scores: dict[str, float]
    dimensions: dict[str, dict]     # dim_name -> {score, weight, label, ideal, actual}
    total: float                    # 0-100
    grade: str                      # A/B/C/D

@dataclass
class AnalysisReport:
    """完整分析报告"""
    piece: PieceInfo
    genre: GenreDetection
    harmony: HarmonyResult
    melody: MelodyResult
    rhythm: RhythmResult
    structure: StructureResult
    expressiveness: ExpressivenessResult
    score: Optional[ScoreResult] = None
```

---

## 3. 模块详细设计

### 3.1 `preprocess.py` — 音乐文件解析

**输入**: 文件路径 (.mid / .xml / .mxl)
**输出**: `PieceInfo` + `music21.stream.Score`

核心职责：
- `parse_file(path) -> stream.Score`: 用 `music21.converter.parse()` 加载，自动识别格式
- `extract_piece_info(score) -> PieceInfo`: 提取调性、拍号、BPM、声部数、时长等元信息
- `chordify(score) -> stream`: 合并声部为和弦流（用于和声分析）
- `extract_melody(score) -> list[note.Note]`: 提取主旋律声部（取音符数最多的 part，或 part[0]）
- `segment_by_measures(score, window=8) -> list[stream]`: 按小节窗口分段（用于结构分析）
- `normalize_durations(score) -> stream`: 量化时值到最近标准音符（三连音容差）

### 3.2 `genre_detector.py` — 类型检测

**输入**: `PieceInfo` + 五维原始指标
**输出**: `GenreDetection`

**检测逻辑**（多信号加权投票）：

| 信号 | 古典 | 流行 | 爵士 | 电子 | 摇滚 |
|------|------|------|------|------|------|
| 和声熵 H | 1.5-3.0 | 0.8-1.5 | 2.5-4.0 | 0.5-1.5 | 0.5-1.2 |
| 转调次数 | 2-5 | 0-1 | 2-8 | 0-1 | 0-1 |
| 切分比例 | 5-15% | 5-15% | 30-50% | 15-30% | 10-25% |
| 声部数 | 3-8 | 2-5 | 2-6 | 1-4 | 2-5 |
| 重复覆盖率 | 40-60% | 40-60% | 20-40% | 50-80% | 30-50% |
| 力度范围 | 50-127 | 30-80 | 30-70 | 20-60 | 60-127 |
| 速度变化 | 明显 | 无 | 中(swing) | 无 | 少量 |

**算法**:
1. 对每个信号，计算当前值与各类型理想区间的匹配度（0-1，在区间内=1，越远越低）
2. 各信号等权平均，得到每个类型的匹配得分
3. 取最高分为检测结果，归一化为置信度

### 3.3 `harmony_complexity.py` — 和声复杂度

**输入**: `stream.Score` (chordified)
**输出**: `HarmonyResult`

**核心算法**:

| 子指标 | 算法 | music21 API |
|--------|------|-------------|
| 和弦多样性熵 | 每拍/每小节取和弦 → 统计频率分布 → Shannon 熵 | `chordify()` + `chord.Chord.commonName` |
| 调性变化频率 | 每 8-16 小节分段 → `analyze('key')` → 统计调性中心变化 | `score.analyze('key')` |
| 声部进行质量 | 相邻和弦同声部半音距离 → 均值 | `voiceLeading.VoiceLeadingQuarterly` |
| 根音运动分布 | 相邻和弦根音音程 → 统计比例 | `chord.root()` + `interval.Interval` |

**评分公式**: `score = 0.35*entropy_norm + 0.25*modulation_norm + 0.25*voice_lead_norm + 0.15*root_motion_norm`

### 3.4 `melody_diversity.py` — 旋律多样性

**输入**: 旋律音符列表
**输出**: `MelodyResult`

**核心算法**:

| 子指标 | 算法 | music21 API |
|--------|------|-------------|
| 音程多样性熵 | 相邻音程类型频率 → Shannon 熵 | `interval.Interval` |
| 轮廓变化率 | 音高差分方向序列 → 方向变化次数/总音符 | `note.pitch.midi` 差分 |
| 音域范围 | max(midi) - min(midi) | `flatten().pitches` |
| 动机重复率 | n-gram 片段 → 编辑距离聚类 → 重复覆盖率 | 自定义 n-gram |

**评分公式**: `score = 0.30*interval_entropy_norm + 0.25*contour_norm + 0.20*range_norm + 0.25*motif_norm`

### 3.5 `rhythm_innovation.py` — 节奏创新性

**输入**: `stream.Score`
**输出**: `RhythmResult`

**核心算法**:

| 子指标 | 算法 | music21 API |
|--------|------|-------------|
| 节奏多样性熵 | 连续3音符时值组合 n-gram → Shannon 熵 | `note.duration.quarterLength` |
| 切分音比例 | `beatStrength < 0.5` 的音符数 / 总数 | `note.beatStrength` |
| 节奏密度 | 总音符数 / 总时长(秒) | `highestTime` + tempo |
| 复合节奏检测 | 各声部节奏型对比 → 非整数倍关系检测 | `parts` 分离 + 拍位对比 |

**评分公式**: `score = 0.30*rhythm_entropy_norm + 0.30*syncopation_norm + 0.20*density_norm + 0.20*poly_norm`

### 3.6 `structure_coherence.py` — 结构完整性

**输入**: `stream.Score` (分段后)
**输出**: `StructureResult`

**核心算法**:

| 子指标 | 算法 |
|--------|------|
| 重复模式覆盖率 | 旋律轮廓序列 → 滑动窗口匹配 → 重复片段/总时长 |
| 曲式识别 | 分段特征向量(和弦进行+旋律轮廓) → 聚类 → 推断曲式标签 |
| 乐句对称性 | 休止符/终止式检测乐句边界 → 长度变异系数 |
| 发展逻辑评分 | 呈示段 vs 发展段 vs 再现段特征相似度矩阵 |

**评分公式**: `score = 0.30*repetition_norm + 0.25*form_norm + 0.20*symmetry_norm + 0.25*development_norm`

### 3.7 `expressiveness.py` — 表现力

**输入**: `stream.Score`
**输出**: `ExpressivenessResult`

**核心算法**:

| 子指标 | 算法 | music21 API |
|--------|------|-------------|
| 力度变化幅度 | velocity max - min | `note.volume.velocity` |
| 力度变化频率 | velocity 差分超阈值次数 / 时长(分钟) | 同上 |
| 速度变化范围 | tempo 标记 max - min BPM | `tempo.MetronomeMark.number` |
| Articulation 多样性 | 不同 articulation 类型数 | `note.articulations` |

**评分公式**: `score = 0.30*dynamic_range_norm + 0.25*dynamic_freq_norm + 0.25*tempo_norm + 0.20*articulation_norm`

### 3.8 `music_scorer.py` — 类型感知评分

**输入**: `GenreDetection` + 五维 Result
**输出**: `ScoreResult`

核心思想：同一首爵士乐的和声复杂度 90 分，放在流行标准下可能是"过度复杂"。评分需参照类型理想区间。

**算法**:
1. 对每个维度，计算原始值与该类型理想区间的匹配度
2. 用类型专属权重加权求和
3. 映射到 0-100 + 字母等级

（详见第5节权重表）

### 3.9 `export.py` — 数据导出

**输入**: `AnalysisReport`
**输出**: report.json + csv/ 目录（6张CSV）

CSV 文件：
- `harmony.csv`: 小节, 和弦名, 根音, 音符数
- `melody.csv`: 小节, 音高, 音程, 方向
- `rhythm.csv`: 小节, 时值, 拍强度, 是否切分
- `structure.csv`: 段落, 类型标签, 小节范围, 重复来源
- `expressiveness.csv`: 小节, 平均velocity, 力度标记, articulation
- `summary.csv`: 五维得分汇总 + 类型检测 + 总分

### 3.10 `render.py` — HTML 报告渲染

**输入**: `AnalysisReport` + `ScoreResult`
**输出**: report.html

参考 story-score 的 Jinja2 + Plotly 模式：
- 6个 Plotly 图表（雷达图 + 5个维度时序/分布图）
- 钢琴卷帘 (piano roll) 可视化（可选，用 Plotly scatter）
- 类型检测面板
- 评分面板
- 深色主题

### 3.11 `cli.py` — 命令行入口

```
python -m src.cli --input song.mid --output-dir ./output [--format html|json|csv|all]
```

参考 story-score 的 cli.py 结构，argparse + `run_analysis()` 编排管线。

---

## 4. 数据流

```
[输入文件 .mid/.xml/.mxl]
        │
        ▼
   preprocess.parse_file()
        │
        ├─→ piece_info (元信息)
        │
        ├─→ chordified_stream ──→ harmony_complexity.analyze() ──→ HarmonyResult
        │
        ├─→ melody_notes ──────→ melody_diversity.analyze() ─────→ MelodyResult
        │
        ├─→ full_score ────────→ rhythm_innovation.analyze() ───→ RhythmResult
        │
        ├─→ segmented_score ───→ structure_coherence.analyze() ──→ StructureResult
        │
        └─→ full_score ────────→ expressiveness.analyze() ──────→ ExpressivenessResult
                                                                    │
        PieceInfo + 五维原始指标 ──→ genre_detector.detect() ──→ GenreDetection
                                                                    │
                                五维结果 + Genre ──→ music_scorer.score() ──→ ScoreResult
                                                                    │
                                                    Assembly ──→ AnalysisReport
                                                                    │
                                        ┌───────────────────────┼───────────────────────┐
                                        ▼                       ▼                       ▼
                                   export.to_json()       export.to_csv()        render.render_html()
                                        │                       │                       │
                                   report.json            csv/*.csv             report.html
```

---

## 5. 评分权重表

### 5.1 默认权重（未检测到类型时）

| 维度 | 权重 | 标签 |
|------|------|------|
| 和声复杂度 | 0.25 | Harmony |
| 旋律多样性 | 0.20 | Melody |
| 节奏创新性 | 0.20 | Rhythm |
| 结构完整性 | 0.20 | Structure |
| 表现力 | 0.15 | Expression |

### 5.2 类型感知权重

| 维度 | 古典 | 流行 | 爵士 | 电子 | 摇滚 |
|------|------|------|------|------|------|
| **和声复杂度** | 0.30 | 0.15 | **0.35** | 0.10 | 0.10 |
| **旋律多样性** | 0.25 | 0.25 | 0.25 | 0.15 | 0.20 |
| **节奏创新性** | 0.15 | 0.20 | **0.25** | 0.20 | 0.20 |
| **结构完整性** | **0.25** | 0.20 | 0.10 | 0.10 | 0.15 |
| **表现力** | 0.05 | 0.20 | 0.05 | 0.45 | **0.35** |

### 5.3 类型理想特征（评分校准基准）

| 指标 | 古典理想 | 流行理想 | 爵士理想 | 电子理想 | 摇滚理想 |
|------|---------|---------|---------|---------|---------|
| 和弦熵 H | 1.5-3.0 | 0.8-1.5 | 2.5-4.0 | 0.5-1.5 | 0.5-1.2 |
| 转调次数 | 2-5 | 0-1 | 2-8 | 0-1 | 0-1 |
| 声部进行距离 | <1.5 | 2-3 | 1-2 | N/A | 2-4 |
| 音程熵 H | 2.0-3.0 | 1.0-2.0 | 2.5-3.5 | 1.0-2.0 | 1.5-2.5 |
| 轮廓变化率 | 0.3-0.5 | 0.2-0.4 | 0.4-0.6 | 0.2-0.4 | 0.3-0.5 |
| 节奏熵 H | 1.5-2.5 | 1.0-2.0 | 2.0-3.5 | 0.5-1.5 | 0.8-1.5 |
| 切分比例 | 5-15% | 5-15% | 30-50% | 15-30% | 10-25% |
| 重复覆盖率 | 40-60% | 40-60% | 20-40% | 50-80% | 30-50% |
| 乐句对称CV | <0.1 | <0.15 | 0.1-0.3 | <0.1 | <0.2 |
| 力度范围 | 50-127 | 30-80 | 30-70 | 20-60 | 60-127 |
| 速度变化BPM | 10-30 | 0-5 | 5-20 | 0-3 | 3-15 |
| Articulation种类 | 3-5 | 0-2 | 1-3 | 0-1 | 0-2 |

**评分校准算法**: 对每个子指标，计算 `match_score = 1 - distance_to_ideal_range / max_distance`，clamp 到 [0,1]，再乘以维度内子指标权重得到维度分，最后乘以类型权重得到总分。

---

## 6. 类型检测详细逻辑

```
detect_genre(piece_info, harmony_result, rhythm_result, structure_result, expressiveness_result)
    │
    ├─ 提取特征向量:
    │   features = {
    │     "chord_entropy": harmony.chord_diversity_entropy,
    │     "modulation_count": harmony.modulation_count,
    │     "voice_lead": harmony.voice_leading_smoothness,
    │     "syncopation": rhythm.syncopation_ratio,
    │     "rhythm_entropy": rhythm.rhythmic_diversity_entropy,
    │     "repetition": structure.repetition_coverage,
    │     "part_count": piece_info.part_count,
    │     "dynamic_range": expressiveness.dynamic_range,
    │     "tempo_variation": expressiveness.tempo_variation_range,
    │   }
    │
    ├─ 对每种类型, 计算匹配度:
    │   for genre in [classical, pop, jazz, electronic, rock]:
    │       genre_scores[genre] = mean([
    │           range_match(features[key], IDEAL_RANGES[genre][key])
    │           for key in features
    │       ])
    │
    ├─ range_match(value, (lo, hi)):
    │   if lo <= value <= hi: return 1.0
    │   dist = min(abs(value-lo), abs(value-hi)) / range_width
    │   return max(0, 1 - dist)
    │
    ├─ 选最高分类型:
    │   detected = argmax(genre_scores)
    │   confidence = (top_score - second_score) / top_score  # 差距越大越确定
    │
    └─ 返回 GenreDetection(detected, confidence, genre_scores)
```

---

## 7. 依赖

```
# requirements.txt
music21>=9.1.0
numpy>=1.24.0
scipy>=1.10.0
plotly>=5.18.0
jinja2>=3.1.0
```

---

## 8. 与 story-score 的架构对比

| 方面 | story-score | music-score |
|------|------------|-------------|
| 输入 | .txt 文本 | .mid / .xml / .mxl |
| 预处理 | 分词 + 分段 + NLP | music21 解析 + 和弦化 + 旋律提取 |
| 维度 | 叙事弧线/情感深度/角色网络/节奏张力/文本质量 | 和声/旋律/节奏/结构/表现力 |
| 核心库 | NLTK/transformers | music21 |
| 类型感知 | 爽文/经典/悬疑/言情/史诗 | 古典/流行/爵士/电子/摇滚 |
| 输出 | report.html + report.json + 7 CSV | report.html + report.json + 6 CSV |
| 评分 | story_scorer.py | music_scorer.py |
| 渲染 | Jinja2 + Plotly (D3力导向图) | Jinja2 + Plotly (钢琴卷帘+雷达图) |

架构模式完全对齐：`preprocess → N个独立维度模块 → scorer → export + render`。
