import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import sys
import threading
import json
import urllib.request
import os
import shutil
from concurrent.futures import ThreadPoolExecutor

# 探针脚本：这段代码会被发送到目标Python解释器执行，用于获取真实的库列表
PROBE_SCRIPT = """
import importlib.metadata
import os
import datetime
import json
import sys

def get_size_and_date(dist):
    try:
        files = dist.files
        if not files:
            return "N/A", "N/A", 0
        
        base_path = None
        p = dist.locate_file(files[0])
        if os.path.exists(p):
            base_path = os.path.dirname(str(p))
            
        if not base_path or not os.path.exists(base_path):
            return "未知", "未知", 0
            
        total_size = 0
        latest_time = 0
        
        # 限制遍历深度防止卡顿
        for dirpath, _, filenames in os.walk(base_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    stat = os.stat(fp)
                    total_size += stat.st_size
                    if stat.st_mtime > latest_time:
                        latest_time = stat.st_mtime
                except: pass
                
        size_str = f"{total_size / (1024*1024):.2f} MB"
        if latest_time > 0:
            date_str = datetime.datetime.fromtimestamp(latest_time).strftime('%Y-%m-%d %H:%M')
        else:
            date_str = "未知"
        return size_str, date_str, total_size
    except:
        return "错误", "错误", 0

data = []
try:
    dists = list(importlib.metadata.distributions())
    for dist in dists:
        name = dist.metadata['Name']
        version = dist.version
        size, date, raw_size = get_size_and_date(dist)
        data.append({
            "name": name,
            "version": version,
            "size": size,
            "date": date,
            "raw_size": raw_size
        })
except Exception as e:
    # 兼容低版本Python或环境异常
    data = [{"error": str(e)}]

print(json.dumps(data))
"""

class LibraryManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PyLib Manager")
        self.root.geometry("1100x750")
        
        self.style = ttk.Style()
        try:
            self.style.theme_use('clam')
        except: pass
        
        # 变量
        self.target_python = tk.StringVar()
        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar(value="就绪")
        
        self.installed_packages = []
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # 1. 自动检测目标 Python
        self._detect_initial_python()
        
        # 2. 构建界面
        self.create_widgets()
        
        # 3. 初始加载
        self.root.after(500, self.refresh_packages)

    def _detect_initial_python(self):
        """核心逻辑：区分开发环境和打包环境"""
        if getattr(sys, 'frozen', False):
            # 如果是exe运行，尝试找系统的python
            path = shutil.which("python")
            if path:
                self.target_python.set(path)
            else:
                self.target_python.set("未找到Python，请手动选择")
        else:
            # 如果是源码运行，默认管理自己
            self.target_python.set(sys.executable)

    def create_widgets(self):
        # === 顶部：环境选择区 ===
        env_frame = ttk.LabelFrame(self.root, text="目标环境设置", padding=5)
        env_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        ttk.Label(env_frame, text="Python解释器路径:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(env_frame, textvariable=self.target_python, width=60).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(env_frame, text="浏览...", command=self.select_python).pack(side=tk.LEFT, padx=5)
        ttk.Button(env_frame, text="重新加载", command=self.refresh_packages).pack(side=tk.LEFT, padx=5)

        # === 操作区 ===
        control_frame = ttk.Frame(self.root, padding="5")
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10)
        
        self.package_entry = ttk.Entry(control_frame, width=20)
        self.package_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.package_entry.bind('<Return>', lambda e: self.install_package())
        
        ttk.Button(control_frame, text="安装包", command=self.install_package).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="卸载选中", command=self.uninstall_package).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="升级pip", command=self.upgrade_pip).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(control_frame, text="搜索:").pack(side=tk.LEFT, padx=(20, 5))
        self.search_var.trace('w', self.filter_packages)
        ttk.Entry(control_frame, textvariable=self.search_var, width=15).pack(side=tk.LEFT)

        # === 主列表 ===
        paned = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        tree_frame = ttk.Frame(paned)
        paned.add(tree_frame, weight=3)
        
        cols = ("name", "version", "size", "date")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")
        
        self.tree.heading("name", text="库名", command=lambda: self.sort_tree("name", False))
        self.tree.heading("version", text="版本", command=lambda: self.sort_tree("version", False))
        self.tree.heading("size", text="预估大小", command=lambda: self.sort_tree("raw_size", False))
        self.tree.heading("date", text="安装时间", command=lambda: self.sort_tree("date", False))
        
        self.tree.column("name", width=250)
        self.tree.column("version", width=120)
        self.tree.column("size", width=100)
        self.tree.column("date", width=150)
        
        sb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=sb.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<<TreeviewSelect>>", self.on_item_select)

        # === 底部详情 ===
        detail_frame = ttk.LabelFrame(paned, text="PyPI 在线简介", padding="5")
        paned.add(detail_frame, weight=1)
        
        self.detail_text = tk.Text(detail_frame, height=6, state=tk.DISABLED, bg="#f9f9f9", font=("Consolas", 10))
        self.detail_text.pack(fill=tk.BOTH, expand=True)

        # === 状态栏 ===
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    # === 逻辑功能 ===
    
    def select_python(self):
        f = filedialog.askopenfilename(title="选择Python解释器", filetypes=[("Python", "python.exe"), ("All", "*.*")])
        if f:
            self.target_python.set(f)
            self.refresh_packages()

    def set_status(self, msg):
        self.status_var.set(msg)
        self.root.update_idletasks()

    def refresh_packages(self):
        py_path = self.target_python.get()
        if not py_path or not os.path.exists(py_path):
            messagebox.showerror("错误", "无效的Python路径！")
            return
            
        # 清空列表
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.set_status(f"正在扫描环境: {py_path} ...")
        
        # 后台线程扫描
        threading.Thread(target=self._scan_thread, args=(py_path,), daemon=True).start()

    def _scan_thread(self, py_path):
        try:
            # 关键：使用 subprocess 调用目标 python 执行探针脚本
            # 这样可以完全隔离 EXE 环境和目标环境
            cmd = [py_path, "-c", PROBE_SCRIPT]
            
            # Windows下隐藏窗口
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                encoding='utf-8', 
                errors='ignore',
                startupinfo=startupinfo
            )
            
            if result.returncode != 0:
                raise Exception(f"执行失败: {result.stderr}")
            
            raw_json = result.stdout.strip()
            if not raw_json:
                raise Exception("未返回数据")
                
            data = json.loads(raw_json)
            
            # 检查是否有探针错误
            if data and "error" in data[0]:
                raise Exception(f"探针错误: {data[0]['error']}")
            
            # 排序
            data.sort(key=lambda x: x['name'].lower())
            
            # 更新UI
            self.root.after(0, lambda: self._update_ui_list(data))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("扫描失败", str(e)))
            self.root.after(0, lambda: self.set_status("扫描失败"))

    def _update_ui_list(self, data):
        self.installed_packages = data
        self.filter_packages()
        self.set_status(f"就绪。共找到 {len(data)} 个库。")

    def filter_packages(self, *args):
        query = self.search_var.get().lower()
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for pkg in self.installed_packages:
            if query in pkg['name'].lower():
                # 存储 raw_size 以便排序
                self.tree.insert("", tk.END, values=(pkg['name'], pkg['version'], pkg['size'], pkg['date']), tags=(str(pkg['raw_size']),))

    def on_item_select(self, event):
        sel = self.tree.selection()
        if not sel: return
        name = self.tree.item(sel[0])['values'][0]
        self.detail_text.config(state=tk.NORMAL)
        self.detail_text.delete(1.0, tk.END)
        self.detail_text.insert(tk.END, "Loading...")
        self.detail_text.config(state=tk.DISABLED)
        self.executor.submit(self._fetch_pypi, name)

    def _fetch_pypi(self, name):
        text = "获取失败"
        try:
            url = f"https://pypi.org/pypi/{name}/json"
            with urllib.request.urlopen(url, timeout=3) as res:
                if res.status == 200:
                    info = json.loads(res.read().decode())['info']
                    text = f"名称: {info.get('name')}\n"
                    text += f"作者: {info.get('author')}\n"
                    text += f"主页: {info.get('home_page')}\n"
                    text += f"简介: {info.get('summary')}\n"
        except: pass
        self.root.after(0, lambda: self._update_detail(text))

    def _update_detail(self, text):
        self.detail_text.config(state=tk.NORMAL)
        self.detail_text.delete(1.0, tk.END)
        self.detail_text.insert(tk.END, text)
        self.detail_text.config(state=tk.DISABLED)

    # === 安装/卸载/管理 ===
    
    def install_package(self):
        name = self.package_entry.get().strip()
        if not name: return
        self._run_pip(["install", name], f"安装 {name}")

    def uninstall_package(self):
        sel = self.tree.selection()
        if not sel: return
        name = self.tree.item(sel[0])['values'][0]
        if messagebox.askyesno("确认", f"确定卸载 {name}?"):
            self._run_pip(["uninstall", name, "-y"], f"卸载 {name}")

    def upgrade_pip(self):
        self._run_pip(["install", "--upgrade", "pip"], "升级 pip")

    def _run_pip(self, args, op_name):
        py_path = self.target_python.get()
        if not os.path.exists(py_path): return
        
        self.set_status(f"正在执行: {op_name} ...")
        
        def _thread():
            try:
                # 使用目标Python调用pip模块
                cmd = [py_path, "-m", "pip"] + args
                
                startupinfo = None
                if os.name == 'nt':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8', # 尝试utf-8，如果失败可能需要gbk
                    errors='replace',
                    startupinfo=startupinfo
                )
                
                is_ok = proc.returncode == 0
                msg = f"{op_name} {'成功' if is_ok else '失败'}"
                detail = proc.stdout + "\n" + proc.stderr
                
                self.root.after(0, lambda: self._on_pip_done(is_ok, msg, detail))
            except Exception as e:
                self.root.after(0, lambda: self._on_pip_done(False, str(e), str(e)))
        
        threading.Thread(target=_thread, daemon=True).start()

    def _on_pip_done(self, ok, msg, detail):
        self.set_status(msg)
        if ok:
            messagebox.showinfo("成功", msg)
            self.package_entry.delete(0, tk.END)
            self.refresh_packages() # 刷新列表
        else:
            messagebox.showerror("失败", f"{msg}\n{detail}")

    def sort_tree(self, col, reverse):
        # 获取所有项
        l = []
        for k in self.tree.get_children(''):
            val = self.tree.set(k, col)
            # 如果是size列，我们需要用隐藏的tag（真实字节数）来排序，而不是字符串 "xx MB"
            if col == "raw_size":
                # 获取tags里的第一个值（我们在filter_packages里存了raw_size）
                tags = self.tree.item(k, 'tags')
                if tags:
                    val = float(tags[0])
                else:
                    val = 0
            l.append((val, k))

        l.sort(key=lambda x: x[0], reverse=reverse)

        for index, (_, k) in enumerate(l):
            self.tree.move(k, '', index)

        # 切换排序方向
        self.tree.heading(col, command=lambda: self.sort_tree(col, not reverse))

if __name__ == "__main__":
    root = tk.Tk()
    app = LibraryManagerApp(root)
    root.mainloop()