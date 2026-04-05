import sys
import os
import json
import random
import winreg
from datetime import datetime

from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QMenu, QAction, 
                             QSystemTrayIcon, QMessageBox, QWidget, QHBoxLayout, 
                             QVBoxLayout, QPushButton, QSlider, QFrame, QDialog)
from PyQt5.QtCore import (Qt, QTimer, QUrl, QSize, QPoint, QRect, QRectF, QPropertyAnimation, QEasingCurve)
from PyQt5.QtGui import (QMovie, QIcon, QCursor, QPainter, QPixmap, QImage, 
                         QPainterPath, QColor, QFont, QBrush, QPen)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

def resource_path(relative_path):
    """获取资源文件的绝对路径，支持开发环境和PyInstaller打包后的环境"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 打包后的临时目录
        return os.path.join(sys._MEIPASS, relative_path)
    # 开发环境：使用脚本所在目录
    return os.path.join(os.path.abspath("."), relative_path)

# --- 进度条自定义按钮 ---
class OptionButton(QPushButton):
    def __init__(self, text, is_timeout_target=False, duration=5000, parent=None):
        super().__init__(text, parent)
        self.is_timeout_target = is_timeout_target
        self.duration = duration
        self.start_time = None
        self.progress = 1.0  # 1.0 到 0.0
        self.setFixedHeight(40)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: black;
                border: 2px solid #333;
                border-radius: 10px;
                font-family: 'Microsoft YaHei';
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
                border-color: #FF69B4;
                color: #FF69B4;
            }
        """)

    def set_progress(self, p):
        self.progress = p
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.is_timeout_target and self.progress > 0:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 绘制底部进度条 (从两端向中间收缩)
            bar_height = 4
            w = self.width()
            h = self.height()
            
            # 当前宽度
            bar_width = w * self.progress
            x = (w - bar_width) / 2
            y = h - bar_height - 2
            
            painter.setBrush(QBrush(QColor("#FF69B4"))) # HotPink
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(QRect(int(x), int(y), int(bar_width), int(bar_height)), 2, 2)


# --- 漫画气泡风格事件对话框 ---
class EventDialog(QDialog):
    def __init__(self, event, parent=None, scale_factor=0.8):
        super().__init__(parent)
        self.event = event
        self.selected_option = None
        self.scale_factor = scale_factor
        self.timeout_index = event.get("timeout_option_index", -1)
        
        # 窗口设置
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 动态调整大小
        base_w, base_h = 350, 140  # 降低基础高度
        self.setFixedSize(int(base_w * scale_factor), int(base_h * scale_factor))
        
        self.init_ui()
        
        # 倒计时设置
        self.remaining_time = 5000 # 5秒
        self.timer_interval = 20
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(self.timer_interval)

    def init_ui(self):
        # 根据缩放调整字体和布局
        scale = self.scale_factor
        
        # 主布局
        layout = QVBoxLayout()
        layout.setContentsMargins(int(15*scale), int(15*scale), int(15*scale), int(15*scale))
        layout.setSpacing(int(10*scale))

        # 标题 (左上角小字)
        title_label = QLabel("事件") 
        title_font_size = max(8, int(10 * scale))
        title_label.setStyleSheet(f"color: #666; font-size: {title_font_size}px; font-family: 'Microsoft YaHei'; font-weight: bold;")
        layout.addWidget(title_label)

        # 对话内容 (气泡中央)
        content_label = QLabel(self.event.get("dialogue", ""))
        content_label.setWordWrap(True)
        content_label.setAlignment(Qt.AlignCenter)
        content_font_size = max(10, int(14 * scale))
        content_label.setStyleSheet(f"color: #333; font-size: {content_font_size}px; font-family: 'Microsoft YaHei'; font-weight: bold;")
        layout.addWidget(content_label)
        
        layout.addStretch()

        # 选项按钮容器
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(int(10*scale))
        
        self.option_buttons = []
        options = self.event.get("options", [])
        
        btn_h = int(40 * scale)
        btn_font_size = max(8, int(10 * scale))
        
        for i, option in enumerate(options):
            is_target = (i == self.timeout_index)
            btn = OptionButton(option.get("text", ""), is_timeout_target=is_target)
            btn.setFixedHeight(btn_h)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: white;
                    color: black;
                    border: 1px solid #333;
                    border-radius: {int(10*scale)}px;
                    font-family: 'Microsoft YaHei';
                    font-size: {btn_font_size}px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: #f0f0f0;
                    border-color: #FF69B4;
                    color: #FF69B4;
                }}
            """)
            btn.clicked.connect(lambda checked, opt=option: self.select_option(opt))
            btn_layout.addWidget(btn)
            self.option_buttons.append(btn)
            
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制气泡背景
        path = QPainterPath()
        rect = QRect(5, 5, self.width()-10, self.height()-10)
        radius = 20
        # 必须显式转换为 QRectF，否则可能导致 crash 或绘制异常
        path.addRoundedRect(QRectF(rect), radius, radius)
        
        # 阴影效果 (通过绘制多次半透明层模拟)
        painter.setPen(Qt.NoPen)
        for i in range(5):
             color = QColor(0, 0, 0, 10 - i*2)
             painter.setBrush(color)
             painter.drawPath(path.translated(float(i), float(i)))

        # 白色背景
        painter.setBrush(Qt.white)
        painter.setPen(QPen(QColor("#333"), 3)) # 深色描边
        painter.drawPath(path)

    def update_timer(self):
        self.remaining_time -= self.timer_interval
        
        # 更新进度条
        progress = max(0.0, self.remaining_time / 5000.0)
        for btn in self.option_buttons:
            if btn.is_timeout_target:
                btn.set_progress(progress)
        
        # 超时处理
        if self.remaining_time <= 0:
            self.timer.stop()
            if self.timeout_index >= 0 and self.timeout_index < len(self.event.get("options", [])):
                default_option = self.event["options"][self.timeout_index]
                self.select_option(default_option)
            else:
                self.reject()

    def select_option(self, option):
        self.timer.stop()
        self.selected_option = option
        self.accept()

# --- 浮动好感度反馈 ---
class FavorabilityFeedback(QWidget):
    def __init__(self, content, parent=None, is_special=False):
        super().__init__(None) # 设为顶级窗口以防被裁剪
        
        self.is_special = is_special
        self.numeric_mode = False
        
        if isinstance(content, int):
            self.text = f"{'+' if content > 0 else ''}{content}"
            self.numeric_mode = True
        else:
            self.text = str(content)
            
        # 设置为无边框、透明背景、置顶、且不接受鼠标事件
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_DeleteOnClose)  # 动画结束后自动销毁对象释放内存
        
        if is_special:
            self.setFixedSize(300, 100)
        else:
            self.setFixedSize(120, 60)
        
        # 动画
        self.opacity = 1.0
        # self.y_offset = 0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(20) # 50fps
        
        self.lifetime = 1500 # 1.5秒

    def animate(self):
        self.lifetime -= 20
        self.move(self.x(), self.y() - 1)
        
        if self.lifetime < 500:
            self.opacity = self.lifetime / 500.0 # 淡出
            
        if self.lifetime <= 0:
            self.timer.stop()
            self.close()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setOpacity(self.opacity)
        
        if self.is_special:
            painter.setPen(QColor("#FF1493")) # DeepPink
            painter.setFont(QFont("Microsoft YaHei", 20, QFont.Bold))
            painter.drawText(self.rect(), Qt.AlignCenter, self.text)
        elif self.numeric_mode:
            # 图标
            path = QPainterPath()

            _w, _h = 40, 30
            path.moveTo(_w / 2, _h * 0.35)
            path.cubicTo(_w * 0.15, _h * 0.05, _w * 0.05, _h * 0.5, _w / 2, _h * 0.9)
            path.cubicTo(_w * 0.95, _h * 0.5, _w * 0.85, _h * 0.05, _w / 2, _h * 0.35)
            
            painter.translate(10, 15)
            
            painter.setBrush(QBrush(QColor("#FF69B4")))
            painter.setPen(Qt.NoPen)
            painter.drawPath(path)
            
            # 数值
            painter.setPen(QColor("#FF69B4") if '+' in self.text else QColor("gray"))
            painter.setFont(QFont("Arial", 16, QFont.Bold))
            painter.drawText(35, 20, self.text)


# --- 好感度爱心控件 ---
class HeartWidget(QWidget):
    def __init__(self, value, parent=None):
        super().__init__(parent)
        self.value = value
        self.setFixedSize(26, 22)  # 图标大小
        self.setToolTip(f"当前好感度: {self.value}/100")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. 绘制粉色爱心
        path = QPainterPath()
        # 爱心绘制逻辑 (基于 32x32 画布)
        w, h = self.width(), self.height()
        path.moveTo(w / 2, h * 0.35)
        path.cubicTo(w * 0.15, h * 0.05, w * 0.05, h * 0.5, w / 2, h * 0.9)
        path.cubicTo(w * 0.95, h * 0.5, w * 0.85, h * 0.05, w / 2, h * 0.35)
        
        painter.setBrush(QBrush(QColor("#FF69B4")))  # HotPink
        painter.setPen(Qt.NoPen)
        painter.drawPath(path)

        # 2. 绘制中间的数值
        painter.setPen(Qt.white)
        font = QFont("Arial", 9, QFont.Bold)
        painter.setFont(font)
        text = str(self.value)
        
        # 计算文字居中位置 (稍微向上偏移一点以适应心形重心)
        metrics = painter.fontMetrics()
        text_w = metrics.width(text)
        text_h = metrics.height()
        x = (w - text_w) // 2
        y = (h + text_h // 2) // 2 + 2 
        
        painter.drawText(x, y, text)

# --- 平滑渲染 Label (保持原样) ---
class SmoothMovieLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScaledContents(False) 
        self._movie = None
        self._cache = {}
        self._smoothing_enabled = False 

    def setSmoothing(self, enabled):
        if self._smoothing_enabled != enabled:
            self._smoothing_enabled = enabled
            self._cache.clear()
            self.repaint()

    def setMovie(self, movie):
        if self._movie:
            self._movie.frameChanged.disconnect(self.repaint)
        self._cache = {}
        super().setMovie(movie)
        self._movie = movie
        if self._movie:
            self._movie.frameChanged.connect(self.repaint)

    def process_frame(self, pixmap):
        if pixmap.isNull(): return pixmap
        img = pixmap.toImage().convertToFormat(QImage.Format_ARGB32_Premultiplied)
        if img.isNull(): return pixmap
        w, h = img.width(), img.height()
        if w < 2 or h < 2: return pixmap

        alpha_channel = QImage(w, h, QImage.Format_ARGB32_Premultiplied)
        alpha_channel.fill(Qt.transparent)
        p_a = QPainter(alpha_channel)
        p_a.drawImage(0, 0, img)
        p_a.setCompositionMode(QPainter.CompositionMode_SourceIn)
        p_a.fillRect(alpha_channel.rect(), Qt.white)
        p_a.end()
        
        blurred_alpha = alpha_channel.scaled(w // 8, h // 8, Qt.IgnoreAspectRatio, Qt.SmoothTransformation) \
                                     .scaled(w, h, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

        result = QImage(w, h, QImage.Format_ARGB32_Premultiplied)
        result.fill(Qt.transparent)
        p = QPainter(result)
        offsets = [(-1, -1), (1, -1), (-1, 1), (1, 1), (0, -1), (0, 1), (-1, 0), (1, 0)]
        for ox, oy in offsets:
             p.drawImage(ox, oy, img)
        p.drawImage(0, 0, img)
        p.setCompositionMode(QPainter.CompositionMode_DestinationIn)
        p.drawImage(0, 0, blurred_alpha)
        p.end()

        return QPixmap.fromImage(result)

    def paintEvent(self, event):
        if self._movie and self._movie.isValid():
            raw_pixmap = self._movie.currentPixmap()
            final_pixmap = None
            
            if not self._smoothing_enabled:
                final_pixmap = raw_pixmap
            else:
                fid = self._movie.currentFrameNumber()
                if fid in self._cache:
                    final_pixmap = self._cache[fid]
                else:
                    if not raw_pixmap.isNull():
                        processed = self.process_frame(raw_pixmap)
                        self._cache[fid] = processed
                        final_pixmap = processed
                    else:
                        final_pixmap = raw_pixmap

            if final_pixmap and not final_pixmap.isNull():
                painter = QPainter(self)
                painter.setRenderHint(QPainter.SmoothPixmapTransform)
                painter.setRenderHint(QPainter.Antialiasing)
                target_size = final_pixmap.size().scaled(self.size(), Qt.KeepAspectRatio)
                x = (self.width() - target_size.width()) // 2
                y = (self.height() - target_size.height()) // 2
                target_rect = QRect(x, y, target_size.width(), target_size.height())
                painter.drawPixmap(target_rect, final_pixmap)
                return
        super().paintEvent(event)

# --- 工具条 (修改版) ---
class FloatingToolbar(QWidget):
    def __init__(self, parent=None, pet_ref=None):
        super().__init__(parent)
        self.pet = pet_ref
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        bg_frame = QFrame()
        bg_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 180);
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 50);
            }
        """)
        bg_layout = QHBoxLayout(bg_frame)
        bg_layout.setContentsMargins(10, 5, 10, 5)
        bg_layout.setSpacing(10)
        
        btn_style = """
            QPushButton {
                background-color: transparent;
                color: white;
                font-size: 16px;
                border: none;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #FFD700;
                font-size: 18px;
            }
        """

        # --- 新增：好感度显示 ---
        self.heart_widget = HeartWidget(self.pet.favorability)
        
        self.btn_settings = QPushButton("⚙️")
        self.btn_settings.setToolTip("设置")
        self.btn_settings.setStyleSheet(btn_style)
        self.btn_settings.clicked.connect(self.show_settings_menu)
        
        self.btn_music = QPushButton("🎵")
        self.btn_music.setToolTip("战歌")
        self.update_music_icon()
        self.btn_music.setStyleSheet(btn_style)
        self.btn_music.clicked.connect(self.toggle_music)

        self.btn_zoom = QPushButton("🔍")
        self.btn_zoom.setToolTip("缩放")
        self.btn_zoom.setStyleSheet(btn_style)
        self.btn_zoom.clicked.connect(self.show_zoom_slider)

        self.btn_info = QPushButton("🫖")
        # 原本使用ℹ️，此处用茶壶emoji后我这里没显示
        self.btn_info.setToolTip("关于")
        self.btn_info.setStyleSheet(btn_style)
        self.btn_info.clicked.connect(self.pet.show_about)

        self.btn_exit = QPushButton("🚪")
        self.btn_exit.setToolTip("退出")
        self.btn_exit.setStyleSheet(btn_style)
        self.btn_exit.clicked.connect(QApplication.instance().quit)

        # 添加顺序：好感度放在最左侧，然后是其他按钮
        bg_layout.addWidget(self.heart_widget) 
        bg_layout.addWidget(self.btn_settings)
        bg_layout.addWidget(self.btn_music)
        bg_layout.addWidget(self.btn_zoom)
        bg_layout.addWidget(self.btn_info)
        bg_layout.addWidget(self.btn_exit)

        layout.addWidget(bg_frame)
        self.setLayout(layout)

    def update_music_icon(self):
        state = self.pet.music_player.state()
        self.btn_music.setText("⏸️" if state == QMediaPlayer.PlayingState else "🎵")

    def toggle_music(self):
        self.pet.toggle_music()
        self.update_music_icon()

    def show_settings_menu(self):
        menu = QMenu(self)
        top_action = QAction("置于顶层", self, checkable=True)
        top_action.setChecked(bool(self.pet.windowFlags() & Qt.WindowStaysOnTopHint))
        top_action.triggered.connect(self.pet.toggle_top_most)
        menu.addAction(top_action)
        
        boot_action = QAction("开机自启", self, checkable=True)
        boot_action.setChecked(self.pet.check_startup())
        boot_action.triggered.connect(self.pet.toggle_startup)
        menu.addAction(boot_action)

        edge_action = QAction("边缘优化 (去锯齿)", self, checkable=True)
        edge_action.setChecked(self.pet.image_label._smoothing_enabled)
        edge_action.triggered.connect(self.pet.toggle_edge_smoothing)
        menu.addAction(edge_action)

        menu.exec_(QCursor.pos())

    def show_zoom_slider(self):
        self.slider_popup = QWidget(None, Qt.Popup | Qt.FramelessWindowHint)
        self.slider_popup.setAttribute(Qt.WA_TranslucentBackground)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        bg = QFrame()
        bg.setStyleSheet("QFrame { background-color: rgba(0,0,0,180); border-radius: 5px; }")
        l = QVBoxLayout(bg)
        l.setContentsMargins(10, 10, 10, 10)
        
        slider = QSlider(Qt.Horizontal)
        slider.setRange(50, 250) 
        slider.setValue(int(self.pet.scale_factor * 100))
        slider.setFixedWidth(150)
        slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 4px; background: grey; border-radius: 2px; }
            QSlider::handle:horizontal { background: #FFD700; width: 16px; margin: -6px 0; border-radius: 8px; }
        """)
        slider.valueChanged.connect(self.on_slider_change)
        
        l.addWidget(slider)
        layout.addWidget(bg)
        self.slider_popup.setLayout(layout)
        
        pos = QCursor.pos()
        self.slider_popup.move(pos.x() - 85, pos.y() + 20)
        self.slider_popup.show()

    def on_slider_change(self, value):
        factor = value / 100.0
        self.pet.update_scale(factor)

# --- 主程序 ---
class WisdelPet(QMainWindow):
    # 常量定义
    MAX_FAVORABILITY = 100
    EVENT_MIN_DELAY = 30000
    EVENT_MAX_DELAY = 120000

    def __init__(self):
        super().__init__()


        self.setWindowTitle("ew本体")
        self.icon_path = resource_path("ew_desktop.ico")
        self.setWindowIcon(QIcon(self.icon_path))
        
        self.STATE_NORMAL = "normal"
        self.STATE_DRAG = "drag"
        self.STATE_SPEAKING = "speaking"
        self.STATE_LAUGH = "laugh"
        self.STATE_WAITING = "waiting"
        
        self.current_state = self.STATE_NORMAL
        self.click_count = 0
        self.favorability = 0  # --- 新增：好感度初始值 ---
        
        self.BASE_WIDTH = 400 
        self.scale_factor = 0.0 
        
        self.is_left_pressed = False
        self.is_really_dragging = False
        self.drag_start_pos = QPoint()
        self.drag_window_start_pos = QPoint()
        self.manual_audio_stop = False 
        
        # --- 新增：事件系统 ---
        self.events = {}
        self.current_event_chain = None  # 用于追踪事件链（如换大盏->倒酒）
        self.toolbar = None # 初始化工具栏引用，防止未打开时访问报错
        
        # --- 新增：好感度反馈窗口列表，防止被垃圾回收 ---
        self.active_feedbacks = []

        self.init_ui()
        self.load_assets()
        self.load_events()
        self.setup_audio()
        self.setup_timers()
        self.setup_tray()
        
        self.change_state(self.STATE_NORMAL)
        self.update_scale(1.5)
        QTimer.singleShot(100, self.center_window)

    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.image_label = SmoothMovieLabel(self)
        self.setCentralWidget(self.image_label)

    def center_window(self):
        screen = QApplication.primaryScreen().availableGeometry()
        geo = self.geometry()
        x = (screen.width() - geo.width()) // 2
        y = (screen.height() - geo.height()) // 2
        self.move(x, y)

    def restore_defaults(self):
        self.update_scale(1.5)
        self.center_window()
        self.show()

    def update_scale(self, factor):
        if factor < 0.5: factor = 0.5
        if factor > 2.5: factor = 2.5

        if abs(factor - self.scale_factor) < 0.0001:
            return

        click_geo = self.geometry()
        current_center_x = click_geo.x() + click_geo.width() / 2.0
        current_center_y = click_geo.y() + click_geo.height() / 2.0
        
        self.scale_factor = factor
        new_w = int(round(self.BASE_WIDTH * self.scale_factor))
        if hasattr(self, 'ASPECT_RATIO'):
            new_h = int(round(new_w * self.ASPECT_RATIO))
        else:
            new_h = int(round(new_w * 9 / 16))
        
        new_x = int(round(current_center_x - new_w / 2.0))
        new_y = int(round(current_center_y - new_h / 2.0))
        
        self.setGeometry(new_x, new_y, new_w, new_h)
        self.setFixedSize(new_w, new_h)

    def load_assets(self):
        self.movies = {}
        anim_path = resource_path("assets/animation")
        
        # 检查动画目录是否存在
        if not os.path.exists(anim_path):
            QMessageBox.critical(
                None, 
                "资源加载错误",
                f"找不到动画资源目录！\n\n路径: {anim_path}\n\n"
                f"请确保资源文件夹 'assets' 与程序在同一目录下。\n"
                f"当前工作目录: {os.getcwd()}"
            )
            sys.exit(1)
        
        files = {
            self.STATE_NORMAL: "ew_normal.gif",
            self.STATE_DRAG: "ew_dragging.gif", 
            self.STATE_SPEAKING: "ew_speaking.gif",
            self.STATE_LAUGH: "ew_laugh.gif",
            self.STATE_WAITING: "ew_waiting.gif"
        }
        
        missing_files = []
        invalid_files = []
        for state, filename in files.items():
            path = os.path.join(anim_path, filename)
            if os.path.exists(path):
                movie = QMovie(path)
                if movie.isValid() and movie.frameCount() > 0:
                    # movie.setCacheMode(QMovie.CacheAll) # 移除全帧缓存以降低内存占用
                    self.movies[state] = movie
                else:
                    invalid_files.append(filename)
                    print(f"警告: GIF文件无法加载或已损坏: {path}")
            else:
                missing_files.append(filename)
        
        # 检查是否缺少核心动画文件
        if self.STATE_NORMAL not in self.movies:
            error_files = missing_files + invalid_files
            QMessageBox.critical(
                None,
                "资源加载错误",
                f"找不到核心动画文件: ew_normal.gif\n\n"
                f"路径: {os.path.join(anim_path, 'ew_normal.gif')}\n\n"
                f"缺失/损坏文件: {', '.join(error_files)}\n\n"
                f"请检查资源文件是否完整！"
            )
            sys.exit(1)
        
        # 警告缺失或损坏的非核心动画文件
        all_problem_files = []
        if missing_files:
            all_problem_files.extend([f"{f} (缺失)" for f in missing_files])
        if invalid_files:
            all_problem_files.extend([f"{f} (损坏/不支持)" for f in invalid_files])
        
        if all_problem_files:
            QMessageBox.warning(
                None,
                "动画文件问题",
                f"以下动画文件存在问题，部分功能可能受影响：\n\n{chr(10).join(all_problem_files)}\n\n"
                f"程序将继续运行，但某些动画效果可能无法显示。"
            )
        
        if self.STATE_NORMAL in self.movies:
            rect = self.movies[self.STATE_NORMAL].frameRect()
            if not rect.isNull():
                self.BASE_WIDTH = rect.width()
                self.BASE_HEIGHT = rect.height()
                self.ASPECT_RATIO = self.BASE_HEIGHT / self.BASE_WIDTH
            else:
                self.BASE_HEIGHT = int(self.BASE_WIDTH * 9 / 16)
                self.ASPECT_RATIO = 9/16
        else:
            self.BASE_HEIGHT = int(self.BASE_WIDTH * 9 / 16)
            self.ASPECT_RATIO = 9/16

        self.audio_files = []
        audio_root = resource_path("assets/audio")
        if os.path.exists(audio_root):
            try:
                for f in os.listdir(audio_root):
                    full = os.path.join(audio_root, f)
                    if os.path.isfile(full) and f.lower().endswith(".mp3"):
                        self.audio_files.append(full)
            except Exception as e:
                print(f"读取音频目录时出错: {str(e)}")
        else:
            print(f"警告: 音频目录不存在: {audio_root}")
        
        # 检查关键音频文件
        self.path_laugh = resource_path("assets/audio/specified/izwisdel_Laugh.mp3")
        self.path_song = resource_path("assets/audio/specified/izwisdel_song.mp3")
        self.path_hourly = resource_path("assets/audio/hourly")
        
        missing_audio = []
        if not os.path.exists(self.path_laugh):
            missing_audio.append("笑声音效 (izwisdel_Laugh.mp3)")
        if not os.path.exists(self.path_song):
            missing_audio.append("战歌 (izwisdel_song.mp3)")
        if not os.path.exists(self.path_hourly):
            missing_audio.append("整点报时目录 (hourly/)")
        
        if missing_audio:
            QMessageBox.warning(
                None,
                "音频文件缺失",
                f"以下音频资源缺失，相关功能将无法使用：\n\n" +
                "\n".join(f"• {item}" for item in missing_audio) +
                "\n\n程序将继续运行。"
            )

    # --- 新增：加载事件配置 ---
    def load_events(self):
        events_path = resource_path("events.json")
        try:
            with open(events_path, 'r', encoding='utf-8') as f:
                events_data = json.load(f)
                self.events = events_data.get("events", {})
        except FileNotFoundError:
            QMessageBox.warning(
                None,
                "配置文件缺失",
                f"找不到事件配置文件！\n\n路径: {events_path}\n\n程序将以基础功能运行（无事件系统）。"
            )
            self.events = {}
        except json.JSONDecodeError as e:
            QMessageBox.critical(
                None,
                "配置文件错误",
                f"事件配置文件格式错误！\n\n错误: {str(e)}\n\n程序将以基础功能运行（无事件系统）。"
            )
            self.events = {}
        except Exception as e:
            QMessageBox.critical(
                None,
                "加载错误",
                f"加载事件配置时发生未知错误！\n\n错误: {str(e)}\n\n程序将以基础功能运行（无事件系统）。"
            )
            self.events = {}

    def setup_audio(self):
        self.voice_player = QMediaPlayer()
        self.voice_player.setVolume(100)
        self.music_player = QMediaPlayer()
        self.music_player.setVolume(50)
        self.voice_player.stateChanged.connect(self.on_voice_finished)
        
        # 添加音频播放错误处理
        self.voice_player.error.connect(self.on_audio_error)
        self.music_player.error.connect(self.on_audio_error)
    
    def on_audio_error(self, error):
        """音频播放错误处理"""
        if error != QMediaPlayer.NoError:
            player = self.sender()
            error_msg = player.errorString()
            print(f"音频播放错误: {error_msg}")
            # 对于严重错误，显示提示框
            if error == QMediaPlayer.ResourceError or error == QMediaPlayer.FormatError:
                QMessageBox.warning(
                    self,
                    "音频播放错误",
                    f"音频文件无法播放！\n\n错误: {error_msg}\n\n请检查音频文件格式是否正确。"
                )

    def setup_timers(self):
        self.idle_timer = QTimer(self)
        self.idle_timer.setInterval(15000)
        self.idle_timer.timeout.connect(self.enter_waiting_sequence)
        self.idle_timer.start()

        self.waiting_duration_timer = QTimer(self)
        self.waiting_duration_timer.setSingleShot(True)
        self.waiting_duration_timer.setInterval(4000)
        self.waiting_duration_timer.timeout.connect(self.end_waiting_sequence)

        self.hourly_timer = QTimer(self)
        self.hourly_timer.timeout.connect(self.check_hourly_chime)
        self.hourly_timer.start(1000)

        self.restore_timer = QTimer(self)
        self.restore_timer.setSingleShot(True)
        self.restore_timer.timeout.connect(self.check_restore_state)

        # --- 新增：事件触发定时器 ---
        self.event_trigger_timer = QTimer(self)
        self.event_trigger_timer.setSingleShot(True)
        self.event_trigger_timer.timeout.connect(self.trigger_random_event)
        self.schedule_next_event()  # 启动事件触发调度

    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(self.icon_path))
        tray_menu = QMenu()
        
        restore_action = QAction("恢复默认大小位置", self)
        restore_action.triggered.connect(self.restore_defaults)
        
        show_action = QAction("显示/隐藏", self)
        show_action.triggered.connect(self.toggle_visibility)
        
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        
        tray_menu.addAction(restore_action)
        tray_menu.addSeparator()
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()

    def reset_interaction(self):
        self.idle_timer.start()
        if self.waiting_duration_timer.isActive() or self.current_state == self.STATE_WAITING:
            self.waiting_duration_timer.stop()
            if not self.is_left_pressed:
                self.change_state(self.STATE_NORMAL)
        # --- 新增：重新计划事件 ---
        if self.current_event_chain is None:
            self.event_trigger_timer.stop()
            self.schedule_next_event()

    def change_state(self, state_name):
        if state_name not in self.movies:
            print(f"警告: 动画状态 '{state_name}' 对应的文件不存在，跳过切换")
            return
        if self.current_state == self.STATE_LAUGH and state_name == self.STATE_SPEAKING:
            return

        self.current_state = state_name
        
        if self.image_label.movie():
            self.image_label.movie().stop()
        
        movie = self.movies[state_name]
        self.image_label.setMovie(movie)
        movie.start()

    def enter_waiting_sequence(self):
        if self.current_state == self.STATE_NORMAL:
            self.change_state(self.STATE_WAITING)
            self.waiting_duration_timer.start()

    def end_waiting_sequence(self):
        if self.current_state == self.STATE_WAITING:
            self.change_state(self.STATE_NORMAL)

    def play_audio(self, file_path, fallback_timeout, show_error=False):
        try:
            if os.path.exists(file_path):
                self.manual_audio_stop = True 
                self.voice_player.stop()
                self.manual_audio_stop = False
                self.voice_player.setVolume(100)
                self.voice_player.setMedia(QMediaContent(QUrl.fromLocalFile(os.path.abspath(file_path))))
                self.voice_player.play()
                self.restore_timer.start(fallback_timeout + 3000) 
            else:
                error_msg = f"音频文件不存在: {file_path}"
                print(error_msg)
                if show_error:
                    QMessageBox.warning(
                        self,
                        "音频文件缺失",
                        f"找不到音频文件！\n\n{file_path}\n\n该功能暂时无法使用。"
                    )
                self.restore_timer.start(1000)
        except Exception as e:
            error_msg = f"播放音频时出错: {str(e)}"
            print(error_msg)
            if show_error:
                QMessageBox.warning(
                    self,
                    "音频播放失败",
                    f"播放音频时发生错误！\n\n{error_msg}"
                )
            self.restore_timer.start(1000)

    def check_restore_state(self):
        if self.is_left_pressed and self.is_really_dragging:
            self.change_state(self.STATE_DRAG)
        else:
            self.change_state(self.STATE_NORMAL)

    def on_voice_finished(self, state):
        if self.manual_audio_stop:
            return
        if state == QMediaPlayer.StoppedState:
            if self.current_state in [self.STATE_SPEAKING, self.STATE_LAUGH]:
                self.check_restore_state()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_left_pressed = True
            self.is_really_dragging = False
            self.drag_start_pos = event.globalPos()
            self.drag_window_start_pos = self.frameGeometry().topLeft()
            self.reset_interaction()
            event.accept()
        elif event.button() == Qt.RightButton:
            self.show_toolbar(event.globalPos())

    def mouseMoveEvent(self, event):
        if self.is_left_pressed:
            delta = event.globalPos() - self.drag_start_pos
            if not self.is_really_dragging and delta.manhattanLength() > 5:
                self.is_really_dragging = True
                if self.current_state not in [self.STATE_SPEAKING, self.STATE_LAUGH]:
                    self.change_state(self.STATE_DRAG)
            
            if self.is_really_dragging:
                self.move(self.drag_window_start_pos + delta)
                self.reset_interaction()
                event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_left_pressed = False
            if self.is_really_dragging:
                if self.current_state == self.STATE_DRAG:
                    self.change_state(self.STATE_NORMAL)
            else:
                self.handle_click_interaction()
            event.accept()

    def wheelEvent(self, event):
        angle = event.angleDelta().y()
        step = 0.1
        if angle > 0:
            new_scale = self.scale_factor + step
        else:
            new_scale = self.scale_factor - step
        
        self.update_scale(new_scale)
        self.reset_interaction()
        event.accept()

    def handle_click_interaction(self):
        self.click_count += 1
        
        # 好感度增加
        self.update_favorability(1)

        if self.click_count % 5 == 0:
            self.trigger_laugh()
        else:
            self.trigger_speak()

    # --- 统一更新好感度 ---
    def update_favorability(self, change):
        if change == 0: return
        
        old_val = self.favorability
        self.favorability += change
        
        if self.favorability < 0: 
            self.favorability = 0
        if self.favorability > self.MAX_FAVORABILITY: 
            self.favorability = self.MAX_FAVORABILITY
            
        # 触发庆祝逻辑: 之前没满，现在满了
        if old_val < self.MAX_FAVORABILITY and self.favorability >= self.MAX_FAVORABILITY:
            self.trigger_overflow_celebration()
        else:
            self.show_favorability_feedback(change)
            
    def trigger_overflow_celebration(self):
        self.show_favorability_feedback(f"好感度已达{self.MAX_FAVORABILITY}~", is_special=True)
        # 播放歌曲
        if os.path.exists(self.path_song):
            # if self.music_player.state() != QMediaPlayer.PlayingState:
            self.music_player.setMedia(QMediaContent(QUrl.fromLocalFile(os.path.abspath(self.path_song))))
            self.music_player.play()
            if self.toolbar:
                self.toolbar.update_music_icon() # 更新图标状态
        else:
            print(f"战歌文件不存在，无法播放庆祝音乐: {self.path_song}")

    # --- 显示好感度反馈 ---
    def show_favorability_feedback(self, content, is_special=False):
        feedback = FavorabilityFeedback(content, parent=None, is_special=is_special)
        
        # 监听销毁事件，从列表中移除
        self.active_feedbacks.append(feedback)
        feedback.destroyed.connect(lambda: self.cleanup_feedback(feedback))

        # 获取当前鼠标位置或者窗口右上角
        geo = self.geometry()
        # 基础位置
        base_x = geo.x() + geo.width() - 80
        base_y = geo.y() + 40
        
        # 随机偏移 (随机性让画面更生动)
        offset_x = random.randint(-30, 30)
        offset_y = random.randint(-20, 10)
        
        feedback.move(int(base_x + offset_x), int(base_y + offset_y)) 
        feedback.show()
        
    def cleanup_feedback(self, feedback):
        if feedback in self.active_feedbacks:
            self.active_feedbacks.remove(feedback)

    def trigger_laugh(self):
        self.change_state(self.STATE_LAUGH)
        if os.path.exists(self.path_laugh):
            self.play_audio(self.path_laugh, 5000)
        else:
            # 如果笑声文件不存在，只播放动画
            self.restore_timer.start(2000)

    def trigger_speak(self):
        if self.current_state != self.STATE_LAUGH:
            self.change_state(self.STATE_SPEAKING)
            if self.audio_files:
                self.play_audio(random.choice(self.audio_files), 2000)
            else:
                print("警告: 没有可用的语音音频文件")
                self.restore_timer.start(1500)

    def show_toolbar(self, pos):
        # 每次右键都会创建新的 Toolbar，自动获取最新的 favorability
        self.toolbar = FloatingToolbar(parent=None, pet_ref=self)
        self.toolbar.move(pos.x() + 10, pos.y() - 25)
        self.toolbar.show()

    def toggle_top_most(self, checked):
        if checked:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        self.show()

    def toggle_edge_smoothing(self, checked):
        self.image_label.setSmoothing(checked)
        
    def toggle_music(self):
        if self.music_player.state() == QMediaPlayer.PlayingState:
            self.music_player.stop()
        else:
            if os.path.exists(self.path_song):
                self.music_player.setMedia(QMediaContent(QUrl.fromLocalFile(os.path.abspath(self.path_song))))
                self.music_player.play()
            else:
                QMessageBox.warning(
                    self,
                    "战歌文件缺失",
                    f"找不到战歌文件！\n\n{self.path_song}\n\n请确保音频文件存在。"
                )

    def show_about(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("作者")
        msg.setTextFormat(Qt.RichText)
        msg.setText("<h3>原作者：<a href='https://space.bilibili.com/6297797' style='color:blue;'>@依然匹萨吧</a></h3>"
            "<h3>ew版：<a href='https://space.bilibili.com/20868284' style='color:blue;'>@酱酱酱酱油_</a></h3>"
            f"<p>声明：本软件免费，禁止商用贩卖。</p>"
            "<p>形象版权归鹰角网络所有。</p>"
            "<p>使用本软件的一切后果自行负责。</p>")
        msg.exec_()

    # --- 新增：事件系统方法 ---
    def schedule_next_event(self):
        """计划下一个随机事件"""
        if self.current_event_chain is None:  # 只有在没有事件链时才触发随机事件
            delay = random.randint(self.EVENT_MIN_DELAY, self.EVENT_MAX_DELAY)
            self.event_trigger_timer.start(delay)

    def trigger_random_event(self):
        """触发随机事件"""
        if self.current_state == self.STATE_NORMAL and self.current_event_chain is None:
            # 获取所有可以随机触发的事件
            random_events = [
                event for event in self.events.values()
                if event.get("trigger") == "random_idle"
            ]
            if random_events:
                event = random.choice(random_events)
                self.show_event_dialog(event)

    def show_event_dialog(self, event):
        """显示事件对话框"""
        try:
            # 播放事件开始音效
            audio_start = event.get("audio_start")
            if audio_start:
                audio_path = resource_path(audio_start)
                if os.path.exists(audio_path):
                    # 不打断背景音乐，使用 voice player
                    self.change_state(self.STATE_SPEAKING) # 配合口型
                    self.play_audio(audio_path, 2000)
                else:
                    print(f"事件音频缺失: {audio_start}")

            # 传入当前缩放比例
            current_scale = self.scale_factor
            # 限制最小缩放，避免对话框太小看不清
            display_scale = max(0.8, current_scale)
            
            dialog = EventDialog(event, self, scale_factor=display_scale)
            # 将对话框移动到窗口中心附近
            geo = self.geometry()
            x = geo.x() + (geo.width() - dialog.width()) // 2
            y = geo.y() + geo.height() - int(50 * display_scale) # 略微偏下
            dialog.move(x, y)
            
            if dialog.exec_() == QDialog.Accepted and dialog.selected_option:
                self.handle_event_option(event, dialog.selected_option)
        except Exception as e:
            QMessageBox.warning(
                self,
                "事件显示错误",
                f"显示事件对话框时出错！\n\n错误: {str(e)}"
            )
        finally:
            self.schedule_next_event()

    def handle_event_option(self, event, option):
        """处理事件选项的结果"""
        try:
            result = option.get("result", {})
            result_type = result.get("type", "")
            favorability_change = result.get("favorability_change", 0)

            # 更新好感度
            self.update_favorability(favorability_change)
                
            # 根据结果类型处理
            if result_type == "trigger_event":
                target_event_id = result.get("target_event")
                if target_event_id in self.events:
                    self.current_event_chain = target_event_id
                    self.show_event_dialog(self.events[target_event_id])
                    self.current_event_chain = None
                else:
                    print(f"未找到目标事件: {target_event_id}")

            elif result_type == "audio":
                audio_file = result.get("audio_file", "")
                if audio_file:
                    audio_path = resource_path(audio_file)
                    if os.path.exists(audio_path):
                        self.change_state(self.STATE_SPEAKING)
                        self.play_audio(audio_path, 3000)
                    else:
                        print(f"事件结果音频缺失: {audio_file}")

            elif result_type == "laugh":
                self.change_state(self.STATE_LAUGH)
                if os.path.exists(self.path_laugh):
                    self.play_audio(self.path_laugh, 5000)
                else:
                    self.restore_timer.start(2000)
        except Exception as e:
            print(f"处理事件选项时出错: {str(e)}")
            QMessageBox.warning(
                self,
                "事件处理错误",
                f"处理事件结果时出错！\n\n错误: {str(e)}"
            )

    def check_hourly_chime(self):
        now = datetime.now()
        if now.minute == 0 and now.second == 0:
            h = 12 if now.hour % 12 == 0 else now.hour % 12
            path = os.path.join(self.path_hourly, f"hour{h}.mp3")
            if os.path.exists(path):
                self.change_state(self.STATE_SPEAKING)
                self.play_audio(path, 3000)
            else:
                print(f"整点报时音频缺失: {path}")

    # --- 自启 ---
    def get_reg_path(self): return r"Software\Microsoft\Windows\CurrentVersion\Run"
    def check_startup(self):
        try:
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.get_reg_path(), 0, winreg.KEY_READ)
            winreg.QueryValueEx(k, "ewDesktop")
            winreg.CloseKey(k)
            return True
        except: return False
    def toggle_startup(self, checked):
        if not sys.executable.endswith(".exe"): 
            QMessageBox.information(
                self,
                "提示",
                "开机自启功能仅在打包后的.exe程序中可用。"
            )
            return
        try:
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.get_reg_path(), 0, winreg.KEY_WRITE)
            if checked: 
                winreg.SetValueEx(k, "ewDesktop", 0, winreg.REG_SZ, sys.executable)
            else: 
                try: 
                    winreg.DeleteValue(k, "ewDesktop")
                except: 
                    pass
            winreg.CloseKey(k)
        except Exception as e:
            QMessageBox.warning(
                self,
                "设置失败",
                f"设置开机自启失败！\n\n错误: {str(e)}\n\n可能需要管理员权限。"
            )

if __name__ == "__main__":
    try:
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        app = QApplication(sys.argv)
        pet = WisdelPet()
        pet.show()
        sys.exit(app.exec_())
    except Exception as e:
        # 全局异常捕获
        error_msg = f"程序运行时发生严重错误！\n\n错误类型: {type(e).__name__}\n错误信息: {str(e)}\n\n请截图此信息并联系开发者。"
        try:
            QMessageBox.critical(None, "程序错误", error_msg)
        except:
            # 如果连消息框都无法显示，至少打印到控制台
            print(error_msg)
            import traceback
            traceback.print_exc()
        sys.exit(1)