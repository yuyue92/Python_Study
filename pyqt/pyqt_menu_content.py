#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QMenuBar, QStatusBar, QListWidget, 
                             QStackedWidget, QLabel, QPushButton, QTextEdit,
                             QTreeWidget, QTreeWidgetItem, QSplitter, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon


class SideMenu(QFrame):
    """左侧菜单组件"""
    menu_clicked = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        self.setFixedWidth(200)
        self.setFrameStyle(QFrame.StyledPanel)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # 菜单标题
        title = QLabel("功能菜单")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 菜单树
        self.menu_tree = QTreeWidget()
        self.menu_tree.setHeaderHidden(True)
        self.menu_tree.itemClicked.connect(self.on_item_clicked)
        
        # 添加菜单项
        self.setup_menu_items()
        
        layout.addWidget(self.menu_tree)
        self.setLayout(layout)
        
        # 设置样式
        self.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border-right: 1px solid #d0d0d0;
            }
            QTreeWidget {
                background-color: white;
                border: 1px solid #d0d0d0;
                border-radius: 3px;
            }
            QTreeWidget::item {
                padding: 5px;
                border-bottom: 1px solid #e0e0e0;
            }
            QTreeWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QTreeWidget::item:hover {
                background-color: #ecf0f1;
            }
        """)
    
    def setup_menu_items(self):
        """设置菜单项"""
        # 首页
        home_item = QTreeWidgetItem(["首页"])
        self.menu_tree.addTopLevelItem(home_item)
        
        # 数据管理
        data_item = QTreeWidgetItem(["数据管理"])
        data_item.addChild(QTreeWidgetItem(["数据录入"]))
        data_item.addChild(QTreeWidgetItem(["数据查询"]))
        data_item.addChild(QTreeWidgetItem(["数据统计"]))
        self.menu_tree.addTopLevelItem(data_item)
        
        # 系统设置
        settings_item = QTreeWidgetItem(["系统设置"])
        settings_item.addChild(QTreeWidgetItem(["用户管理"]))
        settings_item.addChild(QTreeWidgetItem(["权限设置"]))
        settings_item.addChild(QTreeWidgetItem(["系统配置"]))
        self.menu_tree.addTopLevelItem(settings_item)
        
        # 帮助中心
        help_item = QTreeWidgetItem(["帮助中心"])
        help_item.addChild(QTreeWidgetItem(["使用指南"]))
        help_item.addChild(QTreeWidgetItem(["关于软件"]))
        self.menu_tree.addTopLevelItem(help_item)
        
        # 展开所有项
        self.menu_tree.expandAll()
    
    def on_item_clicked(self, item, column):
        """菜单项点击事件"""
        item_text = item.text(0)
        self.menu_clicked.emit(item_text)


class ContentArea(QStackedWidget):
    """右侧内容区域"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        # 创建不同的页面
        self.create_home_page()
        self.create_data_entry_page()
        self.create_data_query_page()
        self.create_data_stats_page()
        self.create_user_management_page()
        self.create_permissions_page()
        self.create_system_config_page()
        self.create_user_guide_page()
        self.create_about_page()
        
        # 默认显示首页
        self.setCurrentIndex(0)
    
    def create_home_page(self):
        """创建首页"""
        page = QWidget()
        layout = QVBoxLayout()
        
        # 欢迎标题
        welcome_label = QLabel("欢迎使用桌面管理系统")
        welcome_label.setFont(QFont("Arial", 16, QFont.Bold))
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet("color: #2c3e50; margin: 20px;")
        
        # 系统介绍
        intro_text = QTextEdit()
        intro_text.setPlainText("""
系统功能概览：

1. 数据管理
   - 支持数据的录入、查询和统计分析
   - 提供直观的数据展示界面

2. 系统设置
   - 用户管理和权限控制
   - 灵活的系统配置选项

3. 帮助支持
   - 详细的使用指南
   - 完善的技术支持

请从左侧菜单选择您需要使用的功能模块。
        """)
        intro_text.setReadOnly(True)
        intro_text.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                padding: 10px;
                font-size: 12px;
            }
        """)
        
        layout.addWidget(welcome_label)
        layout.addWidget(intro_text)
        page.setLayout(layout)
        self.addWidget(page)
    
    def create_data_entry_page(self):
        """创建数据录入页面"""
        page = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("数据录入")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        
        content = QLabel("这里是数据录入功能界面...")
        content.setStyleSheet("padding: 20px; background-color: white; border: 1px solid #d0d0d0;")
        
        layout.addWidget(title)
        layout.addWidget(content)
        layout.addStretch()
        page.setLayout(layout)
        self.addWidget(page)
    
    def create_data_query_page(self):
        """创建数据查询页面"""
        page = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("数据查询")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        
        content = QLabel("这里是数据查询功能界面...")
        content.setStyleSheet("padding: 20px; background-color: white; border: 1px solid #d0d0d0;")
        
        layout.addWidget(title)
        layout.addWidget(content)
        layout.addStretch()
        page.setLayout(layout)
        self.addWidget(page)
    
    def create_data_stats_page(self):
        """创建数据统计页面"""
        page = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("数据统计")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        
        content = QLabel("这里是数据统计功能界面...")
        content.setStyleSheet("padding: 20px; background-color: white; border: 1px solid #d0d0d0;")
        
        layout.addWidget(title)
        layout.addWidget(content)
        layout.addStretch()
        page.setLayout(layout)
        self.addWidget(page)
    
    def create_user_management_page(self):
        """创建用户管理页面"""
        page = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("用户管理")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        
        content = QLabel("这里是用户管理功能界面...")
        content.setStyleSheet("padding: 20px; background-color: white; border: 1px solid #d0d0d0;")
        
        layout.addWidget(title)
        layout.addWidget(content)
        layout.addStretch()
        page.setLayout(layout)
        self.addWidget(page)
    
    def create_permissions_page(self):
        """创建权限设置页面"""
        page = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("权限设置")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        
        content = QLabel("这里是权限设置功能界面...")
        content.setStyleSheet("padding: 20px; background-color: white; border: 1px solid #d0d0d0;")
        
        layout.addWidget(title)
        layout.addWidget(content)
        layout.addStretch()
        page.setLayout(layout)
        self.addWidget(page)
    
    def create_system_config_page(self):
        """创建系统配置页面"""
        page = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("系统配置")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        
        content = QLabel("这里是系统配置功能界面...")
        content.setStyleSheet("padding: 20px; background-color: white; border: 1px solid #d0d0d0;")
        
        layout.addWidget(title)
        layout.addWidget(content)
        layout.addStretch()
        page.setLayout(layout)
        self.addWidget(page)
    
    def create_user_guide_page(self):
        """创建使用指南页面"""
        page = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("使用指南")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        
        guide_text = QTextEdit()
        guide_text.setPlainText("""
使用指南

1. 系统登录
   - 使用管理员账号登录系统
   - 首次使用请联系系统管理员获取账号

2. 功能模块
   - 数据管理：用于处理各类业务数据
   - 系统设置：管理用户和系统配置
   - 帮助中心：获取使用帮助和技术支持

3. 操作流程
   - 从左侧菜单选择功能模块
   - 在右侧内容区域进行具体操作
   - 使用顶部菜单栏访问全局功能

4. 技术支持
   - 如遇问题请查看帮助文档
   - 或联系技术支持团队
        """)
        for i in range(33):
            guide_text.append('item-{}'.format(i))
            
        guide_text.setReadOnly(True)
        guide_text.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                padding: 10px;
                font-size: 12px;
            }
        """)
        
        layout.addWidget(title)
        layout.addWidget(guide_text)
        page.setLayout(layout)
        self.addWidget(page)
    
    def create_about_page(self):
        """创建关于软件页面"""
        page = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("关于软件")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        
        about_text = QTextEdit()
        about_text.setPlainText("""
桌面管理系统 v1.0

开发信息：
- 开发语言：Python 3.8
- 界面框架：PyQt5
- 开发时间：2025年

功能特点：
- 模块化设计，易于扩展
- 友好的用户界面
- 完善的权限管理
- 数据安全可靠

版权信息：
本软件受版权法保护，未经授权不得复制或传播。

技术支持：
如有问题或建议，请联系开发团队。
        """)
        about_text.setReadOnly(True)
        about_text.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                padding: 10px;
                font-size: 12px;
            }
        """)
        
        layout.addWidget(title)
        layout.addWidget(about_text)
        page.setLayout(layout)
        self.addWidget(page)
    
    def show_page(self, page_name):
        """根据页面名称显示对应页面"""
        page_mapping = {
            "首页": 0,
            "数据录入": 1,
            "数据查询": 2,
            "数据统计": 3,
            "用户管理": 4,
            "权限设置": 5,
            "系统配置": 6,
            "使用指南": 7,
            "关于软件": 8
        }
        
        page_index = page_mapping.get(page_name, 0)
        self.setCurrentIndex(page_index)


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("桌面管理系统")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建状态栏
        self.create_status_bar()
        
        # 创建主要布局
        self.create_main_layout()
        
        # 设置应用样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ecf0f1;
            }
        """)
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件(&F)')
        file_menu.addAction('新建', self.on_new_file, 'Ctrl+N')
        file_menu.addAction('打开', self.on_open_file, 'Ctrl+O')
        file_menu.addAction('保存', self.on_save_file, 'Ctrl+S')
        file_menu.addSeparator()
        file_menu.addAction('退出', self.close, 'Ctrl+Q')
        
        # 编辑菜单
        edit_menu = menubar.addMenu('编辑(&E)')
        edit_menu.addAction('撤销', self.on_undo, 'Ctrl+Z')
        edit_menu.addAction('重做', self.on_redo, 'Ctrl+Y')
        edit_menu.addSeparator()
        edit_menu.addAction('复制', self.on_copy, 'Ctrl+C')
        edit_menu.addAction('粘贴', self.on_paste, 'Ctrl+V')
        
        # 视图菜单
        view_menu = menubar.addMenu('视图(&V)')
        view_menu.addAction('刷新', self.on_refresh, 'F5')
        view_menu.addAction('全屏', self.on_fullscreen, 'F11')
        
        # 工具菜单
        tools_menu = menubar.addMenu('工具(&T)')
        tools_menu.addAction('选项', self.on_options)
        tools_menu.addAction('导入数据', self.on_import_data)
        tools_menu.addAction('导出数据', self.on_export_data)
        
        # 帮助菜单
        help_menu = menubar.addMenu('帮助(&H)')
        help_menu.addAction('使用帮助', self.on_help, 'F1')
        help_menu.addAction('关于', self.on_about)
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("就绪")
        
        # 添加永久状态信息
        self.status_bar.addPermanentWidget(QLabel("用户：管理员"))
        self.status_bar.addPermanentWidget(QLabel("版本：v1.0"))
    
    def create_main_layout(self):
        """创建主要布局"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 创建左侧菜单
        self.side_menu = SideMenu()
        self.side_menu.menu_clicked.connect(self.on_menu_clicked)
        
        # 创建右侧内容区域
        self.content_area = ContentArea()
        
        # 添加到分割器
        splitter.addWidget(self.side_menu)
        splitter.addWidget(self.content_area)
        
        # 设置分割器比例
        splitter.setSizes([200, 1000])
        
        # 主布局
        main_layout = QHBoxLayout()
        main_layout.addWidget(splitter)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        central_widget.setLayout(main_layout)
    
    def on_menu_clicked(self, menu_item):
        """菜单项点击处理"""
        self.status_bar.showMessage(f"当前页面：{menu_item}")
        self.content_area.show_page(menu_item)
    
    # 菜单栏事件处理函数
    def on_new_file(self):
        self.status_bar.showMessage("新建文件")
    
    def on_open_file(self):
        self.status_bar.showMessage("打开文件")
    
    def on_save_file(self):
        self.status_bar.showMessage("保存文件")
    
    def on_undo(self):
        self.status_bar.showMessage("撤销操作")
    
    def on_redo(self):
        self.status_bar.showMessage("重做操作")
    
    def on_copy(self):
        self.status_bar.showMessage("复制")
    
    def on_paste(self):
        self.status_bar.showMessage("粘贴")
    
    def on_refresh(self):
        self.status_bar.showMessage("刷新页面")
    
    def on_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
    
    def on_options(self):
        self.status_bar.showMessage("打开选项设置")
    
    def on_import_data(self):
        self.status_bar.showMessage("导入数据")
    
    def on_export_data(self):
        self.status_bar.showMessage("导出数据")
    
    def on_help(self):
        self.content_area.show_page("使用指南")
        self.status_bar.showMessage("显示帮助信息")
    
    def on_about(self):
        self.content_area.show_page("关于软件")
        self.status_bar.showMessage("关于软件")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("桌面管理系统")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("软件开发团队")
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
