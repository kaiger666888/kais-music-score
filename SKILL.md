---
name: kais-music-score
description: 音乐五维复杂度量化分析（和声复杂度/旋律多样性/节奏创新性/结构完整性/表现力）。从 MIDI/MusicXML 生成交互式 Plotly HTML 报告，支持类型感知评分（古典/流行/爵士/电子/摇滚）。
---

# kais-music-score — 音乐五维可视化分析

## 触发词
音乐分析、music score、MIDI分析、和声分析、旋律分析、节奏分析、音乐评分、music analysis、complexity analysis、音乐可视化、music visualization、曲式分析、genre detection

## 使用方法

```bash
# 基本用法
python skills/kais-music-score/src/cli.py --input song.mid --output-dir ./output

# 指定输出格式
python skills/kais-music-score/src/cli.py --input song.mid --output-dir ./output --format all

# 仅导出 JSON
python skills/kais-music-score/src/cli.py --input song.mid --output-dir ./output --format json
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--input` | 输入文件路径 (.mid / .xml / .mxl) | 必填 |
| `--output-dir` | 输出目录 | `./output` |
| `--format` | 输出格式：`html`(默认)、`json`、`csv`、`all` | `html` |

## 输出格式

- **report.html** — 交互式单文件 HTML 报告（Plotly 雷达图 + 五维时序/分布图，深色主题）
- **report.json** — 结构化分析数据（五维评分、类型检测、子指标明细）
- **csv/** — 6 张分维度 CSV（harmony / melody / rhythm / structure / expressiveness / summary）

## 五维分析维度

1. **和声复杂度** — 和弦多样性熵(Shannon)、调性变化频率、声部进行质量(平均半音距离)、根音运动分布
2. **旋律多样性** — 音程多样性熵、旋律轮廓变化率、音域范围(半音)、动机重复与变化率
3. **节奏创新性** — 节奏多样性熵(n-gram)、切分音比例、节奏密度(音符/秒)、复合节奏检测
4. **结构完整性** — 重复模式覆盖率、曲式识别(ABA/sonata等)、乐句对称性(变异系数)、发展逻辑评分
5. **表现力** — 力度变化幅度/频率、速度变化范围(BPM)、Articulation 多样性

## 类型感知评分

自动检测 5 种音乐类型，根据类型理想特征校准各维度权重：

| 类型 | 和声权重 | 旋律权重 | 节奏权重 | 结构权重 | 表现力权重 |
|------|---------|---------|---------|---------|-----------|
| 古典 | 0.30 | 0.25 | 0.15 | 0.25 | 0.05 |
| 流行 | 0.15 | 0.25 | 0.20 | 0.20 | 0.20 |
| 爵士 | 0.35 | 0.25 | 0.25 | 0.10 | 0.05 |
| 电子 | 0.10 | 0.15 | 0.20 | 0.10 | 0.45 |
| 摇滚 | 0.10 | 0.20 | 0.20 | 0.15 | 0.35 |

## 依赖

```bash
pip install -r skills/kais-music-score/requirements.txt
```
