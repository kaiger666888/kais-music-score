# docs_done.md

## 创建的文件

| 文件 | 说明 |
|------|------|
| `README.md` | 项目介绍、五维说明、安装、使用方法、类型感知权重表、示例输出、架构图 |
| `SKILL.md` | OpenClaw skill 格式，触发词、参数说明、输出格式、五维+类型权重 |
| `.gitignore` | Python + 输出目录忽略 |

## GitHub 仓库

**https://github.com/kaiger666888/kais-music-score**

## 项目摘要

- **五维**: 和声复杂度 / 旋律多样性 / 节奏创新性 / 结构完整性 / 表现力
- **输入**: MIDI (.mid) / MusicXML (.xml / .mxl)
- **输出**: report.html (Plotly 交互式) + report.json + 6 张 CSV
- **类型感知**: 古典/流行/爵士/电子/摇滚，各类型有独立权重和理想特征基准
- **技术栈**: Python 3.10+ / music21 / numpy / scipy / Jinja2 / Plotly
