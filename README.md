# AI Diary

一个自动化的AI日记生成器，通过定期截屏并使用AI分析来记录你的日常活动。

## 功能特点

- 每小时自动截屏
- 使用OpenAI的GPT-4 Vision模型分析图片内容
- 生成优美的日记内容
- 自动保存截图和日记内容

## 安装要求

- Python 3.8+
- OpenAI API密钥

## 安装步骤

1. 克隆此仓库：
```bash
git clone [repository-url]
cd ai-diary
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 创建 `.env` 文件并添加你的OpenAI API密钥：
```
OPENAI_API_KEY=your-api-key-here
```

## 使用方法

运行主程序：
```bash
python ai_diary.py
```

程序会自动：
- 创建 `screenshots` 和 `diaries` 目录
- 每小时整点进行截屏
- 分析图片内容
- 生成日记
- 保存所有内容

## 文件结构

- `screenshots/`: 存储所有截屏图片
- `diaries/`: 存储生成的日记内容
- `ai_diary.py`: 主程序文件
- `requirements.txt`: 项目依赖
- `.env`: 环境变量配置文件

## 注意事项

- 确保你的电脑在运行程序时保持开机状态
- 需要有稳定的网络连接以使用OpenAI API
- 建议在运行程序时保持屏幕解锁状态 