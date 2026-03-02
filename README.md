# Perle 数据统计面板使用说明

本项目是一个用于统计和展示 Perle NFT 徽章持有数据的 Web 面板。它包含了前端展示页面和后端数据采集脚本，能够实时读取 Solana 链上数据并生成历史趋势图表。

## 📂 目录结构

```
Perle数据统计面板/
├── index.html              # 主页（展示面板）
├── css/
│   └── style.css           # 样式文件
├── js/
│   └── script.js           # 前端逻辑（图表渲染、数据加载）
├── update_stats.py         # [核心] 日常数据更新脚本
├── reconstruct_history.py  # [工具] 历史数据重构脚本
├── verify_core_counts.py   # [工具] 简单验证脚本
├── badge_stats.json        # 数据文件（存储历史记录）
└── README.md               # 说明文档
```

## 🚀 快速开始

### 1. 环境准备

确保您的电脑上已安装 Python 3.x。
本项目使用 Python 标准库，**无需安装任何额外的 pip 包**。

### 2. 启动面板

直接在浏览器中打开 `index.html` 文件即可查看统计面板。

## 🛠️ 脚本命令说明

### 1. 日常数据更新 (Daily Update)

**用途**：每天运行一次，用于获取当天的最新链上数据并记录到历史文件中。建议在每天固定时间（如北京时间 00:00 后）运行。

**命令**：
```bash
python update_stats.py
```

**功能**：
- 自动查询 Newcomer, Researcher, Scholar 三种徽章的当前持有量。
- 将数据追加到 `badge_stats.json` 中。
- 如果当天已经运行过，它会更新当天的记录（不会重复添加）。

### 2. 历史数据重构 (Historical Reconstruction)

**用途**：如果您漏掉了几天的 `update_stats.py` 运行（导致数据断档），或者丢失了 `badge_stats.json` 文件，可以使用此脚本来修复和补全数据。

**命令**：
```bash
python reconstruct_history.py
```

**功能**：
- 扫描链上过去 45 天的交易记录。
- 基于当前的持有量，反向推导过去每一天的持有量，自动补全缺失的日期。
- **警告**：此脚本运行时间较长（取决于交易量），并且会覆盖现有的 `badge_stats.json` 文件。

### 3. 数据验证 (Verification)

**用途**：用于快速检查当前的链上数据是否能正常读取，不进行文件写入。

**命令**：
```bash
python verify_core_counts.py
```

## 📊 数据文件说明

脚本会自动更新以下两个文件：

1.  `badge_stats.json`: 原始数据文件（JSON格式）。
2.  `js/badge_data.js`: 前端专用数据文件（JS格式），用于解决本地打开网页时的跨域问题。

数据格式示例：
```json
[
  {
    "date": "2026-01-13",
    "timestamp": 1768233600000,
    "newcomer": 2873,
    "researcher": 1205,
    "scholar": 150
  },
  ...
]
```

- **date**: 北京时间日期 (YYYY-MM-DD)
- **newcomer/researcher/scholar**: 对应徽章的持有数量

## ⚠️ 注意事项

1. **网络连接**：脚本需要访问 Solana RPC 节点 (`https://mainnet.helius-rpc.com`)，请确保网络通畅。
2. **RPC 限制**：如果运行脚本时出现连接错误或超时，可能是触发了 RPC 的速率限制，请稍后重试。
3. **数据准确性**：`reconstruct_history.py` 是基于交易记录反推的，虽然精度很高，但极端情况下（如复杂的批量转账或燃烧操作）可能会有微小误差。`update_stats.py` 记录的是当时的精确快照。
