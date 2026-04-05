# ewDesktop
## 作者：@酱酱酱酱油_(https://space.bilibili.com/20868284)
**使用说明**详见匹萨老师的新三关羽，我真的要开始干活了555

本项目仅供学习交流使用，禁止商用；形象版权归鹰角网络所有

——————————————————————————————————
# 原作
# 关羽桌面伴侣 (GuanyuDesktop)

## 作者：[@依然匹萨吧](https://space.bilibili.com/6297797)

## 功能介绍

**[介绍视频](https://www.bilibili.com/video/BV1iafwBLE36)**

**关羽桌面伴侣** 是一款基于 PyQt5 开发的桌面宠物应用。它能在你的桌面上显示一个可爱的关羽形象，陪伴你的工作和学习。

- ### 1. 基础操作

  - **移动关羽**：鼠标左键按住关羽拖动
  - **互动**：点击关羽触发语音和动画
  - **缩放大小**：鼠标滚轮上下滚动或右键打开工具栏，点击 🔍 图标使用缩放滑块
  - **打开菜单**：鼠标右键点击关羽

  ### 2. 工具栏功能

  右键点击关羽会弹出浮动工具栏，从左到右依次为：

  - **好感度 ❤️**：显示当前好感度值（0-100）
  - **设置 ⚙️**：
    - 置于顶层：让关羽始终显示在最前面
    - 开机自启：随系统启动自动运行
    - 边缘优化：启用抗锯齿平滑处理
  - **战歌 🎵**：播放/暂停背景音乐
  - **缩放 🔍**：打开缩放滑块调整大小（50%-250%）
  - **关于 ℹ️**：查看作者信息和声明
  - **退出 🚪**：关闭程序

  ### 3. 好感度系统

  - 每次点击关羽增加 1 点好感度
  - 事件选项会影响好感度增减
  - 好感度达到 100 时触发满值庆祝效果

  ### 4. 事件系统

  - 程序会在 30-120 秒内随机触发事件
  - 部分选项有 5 秒倒计时，超时自动选择默认选项
  - 选择不同选项会有不同的好感度变化和后续事件

  ### 5. 整点报时

  - 每小时整点时，关羽会播放对应时间的报时语音
  - 报时音频文件位于 `assets/audio/hourly/` 目录

  ### 6. 系统托盘

  - 程序运行时会在系统托盘显示图标，右键托盘图标可：
    - 恢复默认大小位置
    - 显示/隐藏窗口
    - 退出程序

## 文件说明

```
├── main.py                    # 主程序入口
├── main.spec                  # PyInstaller 打包配置
├── events.json                # 事件配置文件
├── requirements.txt           # Python 依赖列表
├── run.bat                    # Windows 快速启动脚本
├── guanyu_desktop.ico         # 程序图标
├── assets/                    # 资源文件目录
│   ├── animation/             # 动画 GIF 文件
│   │   ├── guanyu_normal.gif      # 正常状态
│   │   ├── guanyu_dragging.gif    # 拖拽状态
│   │   ├── guanyu_speaking.gif    # 说话状态
│   │   ├── guanyu_laugh.gif       # 大笑状态
│   │   └── guanyu_waiting.gif     # 等待状态
│   └── audio/                 # 音频文件目录
│       ├── hourly/            # 整点报时音频
│       └── specified/         # 特定音频
│           ├── guanyu_laugh.mp3   # 大笑音效
│           └── guanyu_song.mp3    # 战歌
└── LICENSE                    # 许可证文件
```

## 环境要求

- **操作系统**: Windows 7/10/11（推荐 Windows 10/11）
- **Python**: 3.10 或更高版本
- **硬件**: 
  - 扬声器（用于播放音效和语音）
  - 建议屏幕分辨率 1920x1080 或更高

## 快速开始

### 运行发布版本（EXE）

下载最新版本的 `.exe` 文件，双击运行即可

### 从源码运行

方法一：

   在 Windows 上双击 [`run.bat`](run.bat)

方法二：

1. **克隆项目**
   
   ```bash
   git clone https://github.com/PizzaDark/GuanyuDesktop.git
   cd GuanyuDesktop
   ```
   
2. **安装依赖**
   ```bash
   # 推荐python3.10
   python -m venv .venv
.venv\Scripts\activate #Windows
   source .venv/bin/activate #macOS/Linux
   
   pip install -r requirements.txt
   ```

3. **运行程序**
   
   ```bash
   python main.py
   ```
   

## 事件配置

`events.json` 文件用于配置随机事件，格式如下：

```json
{
  "event_id": {
    "dialogue": "事件对话内容",
    "options": [
      {
        "text": "选项1文字",
        "favorability_change": 5,
        "next_event": "下一个事件ID（可选）"
      },
      {
        "text": "选项2文字",
        "favorability_change": -3
      }
    ],
    "timeout_option_index": 0
  }
}
```

- `dialogue`: 事件对话内容
- `options`: 选项数组
  - `text`: 选项显示文字
  - `favorability_change`: 好感度变化（可正可负）
  - `next_event`: 选择该选项后触发的下一个事件ID（可选）
- `timeout_option_index`: 超时时自动选择的选项索引（-1 表示无超时）

## 常见问题

**Q: 程序启动后看/听不到关羽？**  
A: 资源文件缺失或是不支持在你的设备上使用；或者检查是否被其他窗口遮挡，可以在系统托盘右键选择"恢复默认大小位置"。

**Q: 动画显示有锯齿？**  
A: 右键打开工具栏，点击设置 ⚙️，勾选"边缘优化 (去锯齿)"选项。

**Q: 事件对话框没有出现？**  
A: 检查 `events.json` 文件是否存在且格式正确，程序启动时会在控制台输出加载结果。

**Q: 如何调整默认大小？**  
A: 修改代码中的 `self.update_scale(1.5)` 参数，或在程序运行时调整大小后，该大小会保持到下次启动。

**Q: 好感度有什么用？**  
A: 好感度达到 100 时会触发满值庆祝效果，未来版本可能会根据好感度解锁更多内容。

**Q: 开机自启动不生效？**  
A: 此功能仅在打包成 EXE 后可用，源码运行模式下会提示"仅打包版本支持"。

## 构建可执行文件

使用 PyInstaller 进行打包：

```bash
pyinstaller main.spec
```

打包文件将生成在 `dist/` 目录下。请确保将以下文件/文件夹与生成的 EXE 放在一起：
- `assets/` 文件夹
- `events.json`
- `guanyu_desktop.ico`

**注意**：PyInstaller 会自动将资源文件打包到临时目录，但建议仍将 assets 文件夹与 EXE 放在一起，方便用户自定义内容。

## 依赖库

| 依赖包 | 用途 |
|--------|------|
| PyQt5 | 图形界面框架 |
| PyQt5-Qt5 | Qt5 运行时 |
| PyQt5-sip | PyQt5 支持库 |

## 开源许可证

本项目采用 **[知识共享 署名 - 非商业性使用 - 相同方式共享 4.0 国际许可证 (CC BY-NC-SA 4.0)](LICENSE)** 授权。

### 核心条款说明

1. **允许的行为**：你可以自由复制、修改、分发本项目的代码 / 程序，前提是满足以下条件；
2. **禁止的行为**：严禁将本项目（包括修改后的衍生版本）用于任何商业目的（如出售、付费分发、商业运营等）；
3. **必须遵守**：
   - **署名**：必须保留原作者信息（[@依然匹萨吧](https://space.bilibili.com/6297797)）；
   - **相同方式共享**：若你修改 / 衍生本项目，必须采用与本协议相同的许可证发布。

### 协议完整文本

请查看官方协议全文：https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.zh-hans

本项目仅供学习交流使用，禁止商用贩卖；形象版权归新三国所有；使用本软件的一切后果自行负责
