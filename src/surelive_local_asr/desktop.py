"""Private desktop model manager; Tk owns UI and a Windows tray owns visibility."""
import json, os, queue, threading, time
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pystray
from PIL import Image, ImageDraw, ImageTk
from session_state import atomic_json, sessions, request_exit

COPY = {
 'title': ('本机字幕助手', 'Local subtitle helper'),
 'subtitle': ('为本地影院准备模型，让识别留在电脑上。', 'Prepare models for your cinema. Speech recognition stays on your PC.'),
 'hardware': ('运行设备', 'PROCESSING DEVICE'),
 'gpu': ('NVIDIA 加速可用 · 无需安装 CUDA 工具包', 'NVIDIA acceleration ready · no CUDA toolkit needed'),
 'cpu': ('CPU 模式 · 无需独立显卡', 'CPU mode · no dedicated graphics card required'),
 'gpu_checking': ('正在检测显卡与兼容运行库…', 'Checking GPU and compatible libraries…'),
 'gpu_needed': ('检测到 NVIDIA · 首次识别时按需准备加速组件', 'NVIDIA detected · acceleration components will be prepared on first use'),
 'gpu_system': ('NVIDIA 加速可用 · 复用本机兼容环境', 'NVIDIA ready · reusing compatible local libraries'),
 'gpu_downloaded': ('NVIDIA 加速可用 · 使用已准备组件', 'NVIDIA ready · using downloaded components'),
 'gpu_failed': ('加速暂不可用 · 可重试，识别仍可使用 CPU', 'Acceleration unavailable · retry or continue on CPU'),
 'gpu_prepare': ('准备 / 重试 NVIDIA 加速', 'Prepare / retry NVIDIA acceleration'),
 'gpu_hint': ('缺少组件时从 NVIDIA 官方下载约 1.11 GB；可取消、续传。', 'Missing components: about 1.11 GB from NVIDIA. Cancel and resume supported.'),
 'cpu_only': ('仅用 CPU，不下载加速组件', 'Use CPU only; do not download acceleration components'),
 'nvidia': ('NVIDIA 官方', 'NVIDIA official'),
 'gpu-connecting': ('正在连接 NVIDIA 下载源', 'Connecting to NVIDIA'),
 'gpu-downloading': ('正在下载加速组件', 'Downloading acceleration components'),
 'gpu-verifying': ('正在校验加速组件', 'Verifying acceleration components'),
 'gpu-extracting': ('正在解压并检查加速组件', 'Extracting and checking acceleration components'),
 'gpu-waiting': ('等待另一影院准备加速组件', 'Waiting for another cinema to prepare acceleration'),
 'connected': ('影院已连接', 'Cinema connected'), 'standby': ('等待影院连接', 'Waiting for cinema'),
 'models': ('选择识别模型', 'Choose a speech model'),
 'small': ('轻量优先', 'Lightweight'), 'large': ('大模型', 'Larger model'),
 'small_detail': ('下载较小，适合 CPU 或快速识别', 'Smaller download; suitable for CPU and quick runs'),
 'large_detail': ('适合有显卡的电脑，资源占用更高', 'Best with a GPU; uses more memory'),
 'languages': ('种识别语言', 'speech languages'),
 'source_language': ('视频原语言请在影院中选择；支持自动检测。', 'Choose the video language in the cinema, or use auto-detection.'),
 'sense': ('SenseVoice 在浏览器中运行：中 / 英 / 粤 / 日 / 韩。', 'SenseVoice runs in your browser: Chinese, English, Cantonese, Japanese, Korean.'),
 'download': ('下载 / 继续准备', 'Download / resume'), 'ready': ('模型已就绪', 'Model ready'),
 'import': ('使用已有模型…', 'Use existing model…'), 'cancel': ('取消准备', 'Cancel preparation'),
 'idle': ('准备就绪', 'Ready when you are'),
 'idle_hint': ('在影院点击“连接助手”或“生成字幕”开始使用。', 'In the cinema, click “Connect helper” or “Generate subtitles”.'),
 'preparing': ('正在准备模型', 'Preparing model'), 'uploading': ('正在接收音轨', 'Receiving media'),
 'extracting': ('正在读取音轨', 'Reading audio'), 'loading': ('正在加载模型', 'Loading model'),
 'recognizing': ('正在识别字幕', 'Recognizing speech'), 'cpu-fallback': ('正在切换到 CPU', 'Switching to CPU'),
 'complete': ('任务已完成', 'Task complete'), 'cancelled': ('已取消，可重新开始', 'Cancelled; ready to retry'),
 'error': ('任务未完成', 'Task could not finish'),
 'connecting': ('正在连接下载源', 'Connecting to download source'),
 'downloading': ('正在下载模型', 'Downloading model'), 'importing': ('正在复制已有模型', 'Copying existing model'),
 'verifying': ('正在校验文件', 'Verifying files'),
 'auto': ('自动：官方源失败后切换镜像', 'Auto: official, then mirror on failure'),
 'official': ('Hugging Face 官方源', 'Hugging Face official'), 'mirror': ('HF-Mirror 国内镜像（第三方）', 'HF-Mirror China mirror (third-party)'),
 'local': ('本地文件', 'Local files'),
 'source': ('下载来源', 'Download source'),
 'source_hint': ('所有来源均校验固定版本。镜像不接收账号或视频。', 'Every source uses pinned checksums. No account or media is sent to the mirror.'),
 'settings': ('设置', 'Settings'), 'storage': ('模型存储位置', 'Model storage'), 'change': ('更改…', 'Change…'),
 'storage_hint': ('更改位置不搬迁旧模型。导入会校验并复制到当前目录。', 'Changing the location does not move old models. Import verifies and copies here.'),
 'folder_title': ('选择包含 model.bin 的完整 CTranslate2 模型文件夹', 'Select the complete CTranslate2 model folder containing model.bin'),
 'tray': ('收起到托盘', 'Hide to tray'), 'open': ('打开助手', 'Open helper'),
 'exit': ('退出助手', 'Quit helper'), 'exit_confirm': ('有任务正在运行。退出将停止模型准备和已连接影院的识别，是否继续？', 'Tasks are running. Quitting stops model preparation and connected cinema recognition. Continue?'),
 'footer': ('关闭窗口会收起到右下角托盘；右键托盘图标可退出。', 'Closing this window hides it to the system tray. Right-click the tray icon to quit.'),
 'busy': ('请先完成或取消任务，再更改模型设置。', 'Finish or cancel active tasks before changing model settings.'),
 'notice': ('隔离试用 · Small 99 / Large-v3 100 种语言，识别结果需核对。', 'Private preview · Small 99 / Large-v3 100 languages. Review generated subtitles.'),
 'details': ('查看详情', 'Details'), 'tray_error': ('托盘不可用，窗口保持打开。', 'Tray unavailable; keeping the window open.'),
}

def run_gui(host, test_driver=None):
    import msvcrt
    guard = (host.DATA / 'desktop.lock').open('a+b'); guard.seek(0); guard.write(b'0'); guard.flush(); guard.seek(0)
    try: msvcrt.locking(guard.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        (host.DATA / 'show.request').touch(); guard.close(); return
    app = tk.Tk(); app.withdraw()
    # A launcher may be started hidden; explicitly show the real UI after initialization.
    app.title('SureLive · ' + COPY['title'][0]); app.geometry('820x700'); app.minsize(780, 650)
    bg, card, line, text, muted, accent = '#101722', '#1a2636', '#34465d', '#eef4fc', '#a6b7cd', '#77b9ff'
    app.configure(bg=bg)
    language = host.settings.get('uiLanguage', 'zh'); selected = host.settings.get('selectedModel', 'small')
    if selected not in host.catalog: selected = 'small'
    expanded, quitting = False, False
    events = queue.Queue(); tray = None; shown_request = 0; previous_tray = ''
    widgets, cards = {}, {}
    def tr(key): return COPY.get(key, (key,key))[language == 'en']
    def save(**values):
        try: current = json.loads(host.settings_file.read_text(encoding='utf-8'))
        except (OSError, ValueError): current = {}
        current.update(values); host.settings.update(current); atomic_json(host.settings_file, current)
    def remote(): return [s for s in sessions(host.DATA) if s['kind'] == 'native']
    def busy(): return any(bool(j) and not j.get('finished', False) for j in host.jobs.values()) or any(bool(s.get('job')) and not s['job'].get('finished', False) for s in remote())
    def label(parent, value='', size=11, color=text, bold=False, **kwargs):
        return tk.Label(parent, text=value, bg=parent['bg'], fg=color, font=('Segoe UI', size, 'bold' if bold else 'normal'), **kwargs)
    def button(parent, value, command, primary=False):
        return tk.Button(parent, text=value, command=command, bg=accent if primary else '#26364b', fg='#102139' if primary else text,
                         activebackground='#98cbff' if primary else '#344b66', activeforeground='#102139' if primary else text,
                         relief='flat', bd=0, padx=16, pady=9, cursor='hand2', font=('Segoe UI', 10, 'bold'),
                         disabledforeground='#6c829c', highlightthickness=0)
    style = ttk.Style(app); style.theme_use('clam')
    style.configure('SL.TCombobox', fieldbackground='#26364b', background='#26364b', foreground=text, arrowcolor=text, padding=7)
    style.map('SL.TCombobox', fieldbackground=[('readonly','#26364b')], foreground=[('readonly',text)], selectbackground=[('readonly','#26364b')])
    style.configure('SL.Horizontal.TProgressbar', troughcolor='#26364b', background=accent, bordercolor=card, lightcolor=accent, darkcolor=accent)
    style.configure('SL.Vertical.TScrollbar',troughcolor=bg,background='#34465d',bordercolor=bg,arrowcolor=muted)
    icon_image = Image.new('RGBA',(64,64),bg)
    draw = ImageDraw.Draw(icon_image); draw.rounded_rectangle((3,3,61,61),radius=15,fill=accent)
    draw.polygon([(23,16),(46,32),(23,48)],fill='#102139')
    app_icon = ImageTk.PhotoImage(icon_image); app.iconphoto(True,app_icon)

    def select_model(value):
        nonlocal selected
        if busy(): return
        selected = value; save(selectedModel=value); update()
    def set_language(event=None):
        nonlocal language
        language = 'en' if widgets['language'].get() == 'English' else 'zh'
        save(uiLanguage=language); render()
        if tray: tray.update_menu()
    def start(import_dir=None):
        if busy(): messagebox.showinfo(tr('title'),tr('busy'),parent=app); return
        try:
            _, job = host.begin(selected, prepare_only=True, import_dir=import_dir)
            threading.Thread(target=host.run,args=(job,),daemon=True).start()
        except Exception as error: messagebox.showerror(tr('title'),str(error),parent=app)
    def import_model():
        directory = filedialog.askdirectory(title=tr('folder_title'),parent=app)
        if directory: start(directory)
    def prepare_gpu():
        if busy(): return
        try:
            _, job = host.begin(selected, prepare_only=True)
            job['gpuOnly'] = True
            threading.Thread(target=host.run,args=(job,),daemon=True).start()
        except Exception as error: messagebox.showerror(tr('title'),str(error),parent=app)
    def cpu_mode():
        save(accelerationMode='cpu' if widgets['cpu_var'].get() else 'auto'); update()
    def change_directory():
        if busy(): messagebox.showinfo(tr('title'),tr('busy'),parent=app); return
        directory = filedialog.askdirectory(title=tr('storage'),parent=app)
        if directory:
            host.models.root = Path(directory); save(modelDirectory=directory); render()
    def change_source(event=None):
        if busy(): return
        save(downloadSource=('auto','official','mirror')[widgets['source'].current()])
    def toggle_settings():
        nonlocal expanded
        expanded = not expanded; render()
    def show():
        app.deiconify(); app.update_idletasks()
        # The hidden launcher must not leave the interactive window hidden on Windows.
        import ctypes
        from ctypes import wintypes
        user32=ctypes.windll.user32;user32.GetParent.restype=wintypes.HWND
        window=user32.GetParent(app.winfo_id())
        user32.ShowWindow.argtypes=[wintypes.HWND,ctypes.c_int]
        user32.ShowWindow(window,5)
        dark=ctypes.c_int(1)
        try:ctypes.windll.dwmapi.DwmSetWindowAttribute(wintypes.HWND(window),20,ctypes.byref(dark),ctypes.sizeof(dark))
        except OSError:pass
        app.lift(); app.focus_force()
    def hide():
        if tray and tray.visible: app.withdraw()
        else: messagebox.showinfo(tr('title'),tr('tray_error'),parent=app)
    def quit_app():
        nonlocal quitting
        if busy() and not messagebox.askyesno(tr('exit'),tr('exit_confirm'),parent=app): return
        quitting = True
        for job in list(host.jobs.values()): host.stop(job)
        for state in remote(): request_exit(host.DATA,state['id'])
        if tray: tray.stop()
        app.destroy()
    def on_unmap(event):
        if event.widget is app and app.state() == 'iconic': app.after(0,hide)
    app.protocol('WM_DELETE_WINDOW',hide); app.bind('<Unmap>',on_unmap)

    def render():
        for child in app.winfo_children(): child.destroy()
        widgets.clear(); cards.clear(); app.title('SureLive · ' + tr('title'))
        canvas=tk.Canvas(app,bg=bg,highlightthickness=0,yscrollincrement=20)
        scroll=ttk.Scrollbar(app,orient='vertical',command=canvas.yview,style='SL.Vertical.TScrollbar')
        canvas.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');canvas.pack(side='left',fill='both',expand=True)
        shell = tk.Frame(canvas,bg=bg,padx=26,pady=22); content=canvas.create_window((0,0),window=shell,anchor='nw')
        shell.bind('<Configure>',lambda event:canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>',lambda event:canvas.itemconfigure(content,width=event.width))
        widgets['canvas']=canvas
        app.bind('<MouseWheel>',lambda event:canvas.yview_scroll(-int(event.delta/120),'units'))
        head = tk.Frame(shell,bg=bg); head.pack(fill='x')
        label(head,'SureLive',24,bold=True).pack(side='left')
        lang = ttk.Combobox(head,values=['简体中文','English'],state='readonly',width=10,style='SL.TCombobox')
        lang.set('English' if language == 'en' else '简体中文'); lang.pack(side='right'); lang.bind('<<ComboboxSelected>>',set_language); widgets['language']=lang
        label(shell,tr('title'),14,color=accent,bold=True).pack(anchor='w',pady=(2,3))
        label(shell,tr('subtitle'),10,color=muted).pack(anchor='w')
        hardware = tk.Frame(shell,bg=card,padx=17,pady=12); hardware.pack(fill='x',pady=(16,18))
        label(hardware,tr('hardware'),9,color=muted).pack(anchor='w')
        widgets['hardware']=label(hardware,'',11,bold=True,wraplength=700,justify='left');widgets['hardware'].pack(anchor='w',pady=(4,3))
        widgets['connection']=label(hardware,'',10,color=accent); widgets['connection'].pack(anchor='w')
        widgets['gpu_prepare']=button(hardware,tr('gpu_prepare'),prepare_gpu);widgets['gpu_prepare'].pack(anchor='w',pady=(6,0))
        widgets['gpu_hint']=label(hardware,tr('gpu_hint'),9,color=muted,wraplength=700,justify='left');widgets['gpu_hint'].pack(anchor='w')
        widgets['cpu_var']=tk.BooleanVar(value=host.settings.get('accelerationMode')=='cpu')
        widgets['cpu_only']=tk.Checkbutton(hardware,text=tr('cpu_only'),variable=widgets['cpu_var'],command=cpu_mode,
            bg=card,fg=text,selectcolor=card,activebackground=card,activeforeground=text,highlightthickness=0,font=('Segoe UI',10))
        widgets['cpu_only'].pack(anchor='w',pady=(4,0))
        label(shell,tr('models'),12,bold=True).pack(anchor='w',pady=(0,9))
        row = tk.Frame(shell,bg=bg); row.pack(fill='x'); row.grid_columnconfigure((0,1),weight=1,uniform='models')
        for i, key in enumerate(('small','large-v3')):
            frame=tk.Frame(row,bg=card,padx=15,pady=12,highlightthickness=1,highlightbackground=line)
            frame.grid(row=0,column=i,sticky='nsew',padx=(0,6) if i==0 else (6,0))
            choose=button(frame,'Small' if i==0 else 'Large-v3',lambda k=key:select_model(k)); choose.pack(anchor='w')
            label(frame,tr('small' if i==0 else 'large'),10,color=accent).pack(anchor='w',pady=(7,4))
            gb=sum(f['size'] for f in host.catalog[key]['files'])/1024**3
            label(frame,f'{gb:.2f} GB  ·  {len(host.catalog[key]["languages"])} '+tr('languages'),10,color=muted).pack(anchor='w')
            label(frame,tr('small_detail' if i==0 else 'large_detail'),9,color=muted,wraplength=330,justify='left').pack(anchor='w',pady=(4,0))
            cards[key]=(frame,choose)
        label(shell,tr('source_language'),10,color=muted).pack(anchor='w',pady=(10,2))
        label(shell,tr('sense'),9,color=muted).pack(anchor='w')
        actions=tk.Frame(shell,bg=bg); actions.pack(fill='x',pady=(14,12))
        widgets['download']=button(actions,tr('download'),start,True);widgets['download'].pack(side='left',padx=(0,9))
        widgets['import']=button(actions,tr('import'),import_model);widgets['import'].pack(side='left')
        widgets['cancel']=button(actions,tr('cancel'),lambda:[host.stop(j) for j in list(host.jobs.values())]);widgets['cancel'].pack(side='right')
        task=tk.Frame(shell,bg=card,padx=16,pady=11);task.pack(fill='x')
        widgets['status']=label(task,'',11,bold=True);widgets['status'].pack(anchor='w')
        widgets['progress']=ttk.Progressbar(task,style='SL.Horizontal.TProgressbar',maximum=100);widgets['progress'].pack(fill='x',pady=8)
        widgets['detail']=label(task,'',9,color=muted,wraplength=700,justify='left');widgets['detail'].pack(anchor='w')
        tools=tk.Frame(shell,bg=bg);tools.pack(fill='x',pady=(12,0))
        button(tools,('▾ ' if expanded else '▸ ')+tr('settings'),toggle_settings).pack(side='left')
        button(tools,tr('tray'),hide).pack(side='right')
        if expanded:
            config=tk.Frame(shell,bg=card,padx=15,pady=10);config.pack(fill='x',pady=8)
            label(config,tr('source'),10,bold=True).grid(row=0,column=0,sticky='w')
            source=ttk.Combobox(config,values=[tr(k) for k in ('auto','official','mirror')],state='readonly',width=46,style='SL.TCombobox')
            source.current(('auto','official','mirror').index(host.settings.get('downloadSource','auto')));source.grid(row=0,column=1,sticky='ew',padx=(12,0));source.bind('<<ComboboxSelected>>',change_source);widgets['source']=source
            label(config,tr('source_hint'),9,color=muted).grid(row=1,column=0,columnspan=2,sticky='w',pady=6)
            label(config,tr('storage'),10,bold=True).grid(row=2,column=0,sticky='w')
            widgets['directory']=button(config,tr('change'),change_directory);widgets['directory'].grid(row=2,column=1,sticky='e')
            label(config,str(host.models.root),9,color=accent,wraplength=680,justify='left').grid(row=3,column=0,columnspan=2,sticky='w')
            label(config,tr('storage_hint'),9,color=muted,wraplength=680,justify='left').grid(row=4,column=0,columnspan=2,sticky='w',pady=(5,0))
            app.after_idle(lambda:canvas.yview_moveto(1))
        app.geometry('820x760')
        label(shell,tr('footer'),9,color=muted,wraplength=730,justify='left').pack(anchor='w',pady=(12,0))
        label(shell,tr('notice'),9,color=muted,wraplength=730,justify='left').pack(anchor='w',pady=(5,0))
        update()

    def update():
        nonlocal previous_tray
        states=remote(); local_job=next(iter(host.jobs.values()),{})
        active_remote=next((s.get('job',{}) for s in states if bool(s.get('job')) and not s['job'].get('finished',False)),{})
        job=local_job if local_job and not local_job.get('finished',False) else (active_remote or local_job)
        occupied=busy(); ready=host.models.ready(selected)
        hw=next((s['hardware'] for s in states if s.get('hardware',{}).get('state') in ('ready','preparing')),host.gpu.status)
        mode='cpu' if host.settings.get('accelerationMode')=='cpu' else (
            {'checking':'gpu_checking','needed':'gpu_needed','failed':'gpu_failed','preparing':'gpu-downloading'}.get(hw.get('state'),
             'gpu_'+hw['source'] if hw.get('source') in ('system','downloaded') else 'gpu' if hw.get('preferred')=='cuda' else 'cpu'))
        widgets['hardware'].config(text=tr(mode))
        widgets['gpu_prepare'].config(state='normal' if not occupied and hw.get('state') in ('needed','failed') else 'disabled')
        widgets['gpu_hint'].config(text=tr('gpu_hint') if hw.get('cudaDevices') and hw.get('state')!='ready' else '')
        widgets['cpu_only'].config(state='disabled' if occupied else 'normal')
        widgets['connection'].config(text=(tr('connected')+f' · {len(states)}') if states else tr('standby'))
        for key,(frame,choose) in cards.items():
            frame.config(highlightbackground=accent if key==selected else line)
            choose.config(text=('✓  ' if key==selected else '')+('Small' if key=='small' else 'Large-v3'),state='disabled' if occupied else 'normal')
        widgets['download'].config(text=tr('ready') if ready else tr('download'),state='disabled' if occupied or ready else 'normal')
        widgets['import'].config(state='disabled' if occupied else 'normal')
        widgets['cancel'].config(state='normal' if local_job and not local_job.get('finished',False) else 'disabled')
        if 'source' in widgets:widgets['source'].config(state='disabled' if occupied else 'readonly');widgets['directory'].config(state='disabled' if occupied else 'normal')
        stage=job.get('stage','idle'); detail=job.get('download',{}) if stage=='preparing' else {}
        widgets['status'].config(text=tr(detail.get('phase',stage))+(' · '+job['model'] if job.get('model') else '')+(f" · {job['chunk']}/{job['chunks']}" if stage=='recognizing' and job.get('chunks') else ''))
        widgets['progress']['value']=job.get('percent',0) if stage in ('preparing','recognizing') else (100 if stage=='complete' else 0)
        message=tr('idle_hint')
        if detail:
            message=tr(detail['source'])+f"  ·  {detail.get('received',0)/1024**2:.1f} / {detail.get('total',0)/1024**2:.1f} MB"
            if detail.get('speed'):message+=f"  ·  {detail['speed']/1024**2:.1f} MB/s"
            message+='  ·  '+detail.get('file','')
        if job.get('warning'): message=job['warning'] if language=='zh' else job['warning'].split(' / ')[-1]
        if job.get('error'):
            message=job['error'];message=message if language=='zh' else message.split(' / ')[-1]
        widgets['detail'].config(text=message[:450],fg='#ffb4a8' if stage=='error' else muted)
        title='SureLive · '+tr(stage if occupied else 'standby')
        if tray and title!=previous_tray:tray.title=title;tray.update_menu();previous_tray=title

    def tick():
        nonlocal shown_request, expanded
        if quitting:return
        while not events.empty():
            event=events.get_nowait()
            if event=='show':show()
            elif event=='settings':expanded=True;render();show()
            elif event=='quit':quit_app()
            if quitting:return
        try:
            modified=(host.DATA/'show.request').stat().st_mtime_ns
            if modified>shown_request:shown_request=modified;show()
        except OSError:pass
        update();app.after(500,tick)
    render()
    try:
        tray=pystray.Icon('SureLiveASRPreview',icon_image,'SureLive',menu=pystray.Menu(
            pystray.MenuItem(lambda item:tr('open'),lambda:events.put('show'),default=True),
            pystray.MenuItem(lambda item:tr('settings'),lambda:events.put('settings')),
            pystray.Menu.SEPARATOR,pystray.MenuItem(lambda item:tr('exit'),lambda:events.put('quit'))))
        tray.run_detached()
    except Exception:tray=None
    try:
        show();tick()
        if test_driver:
            app.after(500,lambda:test_driver(app,{'widgets':widgets,'cards':cards,'select':select_model,
                'language':set_language,'settings':toggle_settings,'source':change_source,'hide':hide,
                'show':show,'quit':quit_app,'update':update,'tray':tray}))
        app.mainloop()
    finally:
        if tray:tray.stop()
        guard.seek(0);msvcrt.locking(guard.fileno(),msvcrt.LK_UNLCK,1);guard.close()
