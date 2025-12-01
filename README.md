Python 运行库管理器 (PyLibManager) / Python Library Manager
<img width="2232" height="1578" alt="image" src="https://github.com/user-attachments/assets/836dc796-c5e6-4e56-82ac-083ec487b924" />


中文 | English

<a id="中文说明"></a>中文说明

📖 项目简介

PyLibManager 是一个基于 Tkinter 开发的轻量级、专业的 Python 库管理 GUI 工具。

与传统的命令行 pip 不同，它提供了一个直观的图形界面来查看、安装、卸载和管理 Python 包。其核心亮点在于环境隔离探测机制 (Probe Mechanism)：无论你是直接运行源码，还是将其打包成 EXE 文件运行，它都能通过“探针”脚本精准管理外部的目标 Python 环境，而不会局限于管理自身的运行环境。

✨ 核心功能

多环境支持：可以手动选择并管理电脑上任意位置的 Python 解释器（虚拟环境 venv、Conda 环境或系统 Python）。

探针扫描技术：采用独立的子进程执行探针脚本，完美解决打包成 EXE 后无法扫描外部库的问题。

详细信息展示：列出已安装库的名称、版本，并计算占用空间大小和安装时间。

在线简介获取：点击库名，自动从 PyPI 官网异步获取作者、主页和功能简介。

一键管理：支持安装新库、卸载选中库以及一键升级 pip。

搜索与排序：支持按包名实时过滤，点击表头可按名称、版本、大小或时间排序。

🚀 如何运行

1. 源码运行

确保你的电脑已安装 Python 3.x。此脚本仅依赖 Python 标准库（tkinter, subprocess, json, urllib, threading 等），无需安装额外第三方库。

python "Pipgui Management.py"


2. 打包为 EXE

此工具专门为打包优化。你可以使用 PyInstaller 将其打包为独立可执行文件，打包后依然可以管理外部 Python 环境。

pyinstaller -F -w "Pipgui Management.py"


🛠️ 使用指南

启动软件：打开软件后，它会自动尝试检测当前的 Python 环境。

选择环境：如果显示的路径不是你想管理的环境，点击顶部的 “浏览...” 按钮，选择目标环境的 python.exe 文件。

刷新列表：点击 “重新加载”，软件会扫描该环境下的所有库。

安装库：在输入框输入包名（如 requests），点击 “安装包”。

查看详情：点击列表中的任意一行，底部面板将加载该库的 PyPI 在线信息。

<a id="english-description"></a>English Description

📖 Introduction

PyLibManager is a lightweight, professional GUI tool for managing Python libraries, built with Tkinter.

Unlike the traditional command-line pip, it provides an intuitive graphical interface to view, install, uninstall, and manage Python packages. Its core highlight is the Environment Isolation Probe Mechanism: Whether you run it from source code or compiled as an EXE, it uses a "probe" script to accurately manage external target Python environments, avoiding the common issue where packaged apps can only manage their own internal libraries.

✨ Key Features

Multi-Environment Support: Manually select and manage any Python interpreter on your computer (Virtual Environments, Conda, or System Python).

Probe Scanning Technology: Uses a separate subprocess to execute a probe script, perfectly solving the issue of scanning external libraries after packaging to EXE.

Detailed Metrics: Lists installed packages with names, versions, calculated disk usage size, and installation date.

Online Metadata: Click on a package to asynchronously fetch the author, homepage, and summary from PyPI.

One-Click Management: Supports installing new packages, uninstalling selected ones, and upgrading pip with a single click.

Search & Sort: Real-time filtering by package name; sortable columns (Name, Version, Size, Date).

🚀 How to Run

1. Run from Source

Ensure Python 3.x is installed. This script relies only on the Python Standard Library (tkinter, subprocess, json, urllib, threading, etc.), so no pip install is required.

python "Pipgui Management.py"


2. Build as EXE

This tool is optimized for packaging. You can use PyInstaller to compile it into a standalone executable. It will still function correctly to manage external environments.

pyinstaller -F -w "Pipgui Management.py"


🛠️ User Guide

Launch: Open the application. It will attempt to auto-detect the current Python environment.

Select Environment: If the displayed path is not the target environment, click the "Browse..." (浏览...) button at the top and select the target python.exe.

Refresh: Click "Reload" (重新加载) to scan all libraries in that environment.

Install: Enter a package name (e.g., numpy) in the text box and click "Install Package" (安装包).

View Details: Click on any row in the list to load online PyPI information in the bottom panel.

📝 License

This project is open-source and available under the MIT License.
