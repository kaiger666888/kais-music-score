# kais-music-score 🎵

音乐五维复杂度量化分析工具。从 `.mid` / `.xml` (MusicXML) 音乐文件生成交互式 HTML 报告。

## 五维分析

| 维度 | 说明 |
|------|------|
| 🎹 和声复杂度 | 和弦多样性熵、调性变化频率、声部进行质量、根音运动分布 |
| 🎶 旋律多样性 | 音程多样性熵、旋律轮廓变化率、音域范围、动机重复率 |
| 🥁 节奏创新性 | 节奏多样性熵、切分音比例、节奏密度、复合节奏检测 |
| 🏗️ 结构完整性 | 重复模式覆盖率、曲式识别、乐句对称性、发展逻辑评分 |
| 💫 表现力 | 力度变化幅度/频率、速度变化范围、Articulation 多样性 |

## 类型感知评分

自动检测音乐类型（古典/流行/爵士/电子/摇滚），根据类型理想特征校准评分权重。

| 维度 | 古典 | 流行 | 爵士 | 电子 | 摇滚 |
|------|------|------|------|------|------|
| 和声复杂度 | 0.30 | 0.15 | 0.35 | 0.10 | 0.10 |
| 旋律多样性 | 0.25 | 0.25 | 0.25 | 0.15 | 0.20 |
| 节奏创新性 | 0.15 | 0.20 | 0.25 | 0.20 | 0.20 |
| 结构完整性 | 0.25 | 0.20 | 0.10 | 0.10 | 0.15 |
| 表现力 | 0.05 | 0.20 | 0.05 | 0.45 | 0.35 |

## 安装

```bash
pip install -r requirements.txt
```

## 使用

```bash
# 基本用法
python -m src.cli --input song.mid --output-dir ./output

# 指定输出格式
python -m src.cli --input song.mid --output-dir ./output --format all

# 仅导出 JSON
python -m src.cli --input song.mid --output-dir ./output --format json
```

### 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-i, --input` | 输入文件 (.mid / .xml / .mxl) | 必填 |
| `-o, --output-dir` | 输出目录 | `./output` |
| `-f, --format` | `html` / `json` / `csv` / `all` | `html` |

## 输出

- **report.html** — 交互式单文件报告（Plotly 雷达图 + 五维时序图，深色主题）
- **report.json** — 结构化分析数据（含五维评分、类型检测、子指标明细）
- **csv/** — 6 张分维度 CSV（harmony / melody / rhythm / structure / expressiveness / summary）

## 示例输出

```json
{
  "score": {
    "total": 43.3,
    "grade": "C",
    "detected_genre": "jazz",
    "genre_confidence": 0.72,
    "dimensions": {
      "harmony": { "score": 72.5, "weight": 0.35 },
      "melody": { "score": 77.1, "weight": 0.25 },
      "rhythm": { "score": 62.6, "weight": 0.25 },
      "structure": { "score": 51.8, "weight": 0.10 },
      "expressiveness": { "score": 25.0, "weight": 0.05 }
    }
  }
}
```

## 技术栈

- **Python 3.10+** — 分析引擎
- **music21** (MIT) — MIDI/MusicXML 解析与音乐学分析
- **numpy / scipy** — 数值计算
- **Jinja2** — HTML 模板
- **Plotly.js** — 交互式图表

## 架构

```
输入文件 (.mid/.xml)
    │
    ├─→ chordified ──→ harmony_complexity ──→ HarmonyResult
    ├─→ melody_notes ──→ melody_diversity ──→ MelodyResult
    ├─→ full_score ──→ rhythm_innovation ──→ RhythmResult
    ├─→ segmented ──→ structure_coherence ──→ StructureResult
    └─→ full_score ──→ expressiveness ──→ ExpressivenessResult
                                  │
              genre_detector ← PieceInfo + 五维原始指标
                                  │
              music_scorer ← 五维结果 + Genre
                                  │
                    ┌─────────┼─────────┐
                 JSON       CSV      HTML Report
```

## 已知局限

- 分析结果依赖 MIDI 文件编码质量
- MIDI velocity 在不同音源间含义不同，力度分析需谨慎
- 纯 MIDI 无法捕捉音色、混响、效果器等电子音乐核心元素
- 类型检测在低置信度时区分度有限

## 参考文献

1. Madsen & Widmer (2015) — "A complexity-based approach to melody track identification in MIDI files"
2. Conklin (2006) — "Melodic analysis with segment classes"
3. Cuthbert & Ariza (2010) — "Music21: A Toolkit for Computer-Aided Musicology"
