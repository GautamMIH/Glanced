import tkinter as tk
from tkinter import Menu, scrolledtext, ttk, Toplevel, Checkbutton, BooleanVar, Frame, Label, Button
import time
import os 

# --- LibreHardwareMonitor Initialization ---
LHM_AVAILABLE = False
LHM_COMPUTER_INSTANCE = None
LHM_HARDWARE_ENUMS = None 
LHM_HARDWARE_ITEMS_CACHE = [] 

def initialize_lhm():
    global LHM_AVAILABLE, LHM_COMPUTER_INSTANCE, LHM_HARDWARE_ENUMS, LHM_HARDWARE_ITEMS_CACHE
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        dll_path = os.path.join(script_dir, "LibreHardwareMonitorLib.dll")
        hidsharp_dll_path = os.path.join(script_dir, "HidSharp.dll")

        if not os.path.exists(dll_path):
            print(f"Info: LibreHardwareMonitorLib.dll not found at {dll_path}.")
            if not os.path.exists(hidsharp_dll_path):
                 print(f"Info: HidSharp.dll also not found at {hidsharp_dll_path} (LHM dependency).")
            print("LHM support disabled.")
            LHM_AVAILABLE = False
            return
        
        if not os.path.exists(hidsharp_dll_path):
            print(f"Info: HidSharp.dll not found at {hidsharp_dll_path} (LHM dependency). LHM might fail or be unstable.")

        import clr 
        clr.AddReference(dll_path) 
        
        from LibreHardwareMonitor.Hardware import Computer, HardwareType, SensorType
        
        LHM_HARDWARE_ENUMS = {'HardwareType': HardwareType, 'SensorType': SensorType}

        computer = Computer()
        computer.IsCpuEnabled = True
        computer.IsGpuEnabled = True
        computer.IsMemoryEnabled = True 
        computer.IsMotherboardEnabled = True 
        computer.IsControllerEnabled = True 
        computer.IsStorageEnabled = True
        computer.IsNetworkEnabled = True
        computer.Open()
        LHM_COMPUTER_INSTANCE = computer
        
        if LHM_COMPUTER_INSTANCE:
            LHM_HARDWARE_ITEMS_CACHE.clear() 
            for hw_item in LHM_COMPUTER_INSTANCE.Hardware:
                LHM_HARDWARE_ITEMS_CACHE.append(hw_item)
        
        LHM_AVAILABLE = True
        print("Info: LibreHardwareMonitor initialized successfully.")
    except Exception as e:
        print(f"Error initializing LibreHardwareMonitor: {e}. LHM support disabled.")
        LHM_AVAILABLE = False


def close_lhm():
    global LHM_COMPUTER_INSTANCE
    if LHM_COMPUTER_INSTANCE:
        try:
            LHM_COMPUTER_INSTANCE.Close()
            print("Info: LibreHardwareMonitor closed.")
        except Exception as e:
            print(f"Error closing LibreHardwareMonitor: {e}")

initialize_lhm()

# --- Enhanced UI Configuration ---
UPDATE_INTERVAL_MS = 2000 
WINDOW_WIDTH = 850 # Slightly wider for better spacing
WINDOW_HEIGHT = 650 # Slightly taller
WINDOW_BG_COLOR = "#2B2B2B" # Main background
FRAME_BG_COLOR = "#3C3C3C"  # Background for frames within the window
NAV_BG_COLOR = "#252525"    # Navigation pane background
NAV_BUTTON_BG_COLOR = "#3A3A3A"
NAV_BUTTON_FG_COLOR = "#E0E0E0"
NAV_BUTTON_ACTIVE_BG_COLOR = "#007ACC" # Accent color for active/hover
NAV_BUTTON_ACTIVE_FG_COLOR = "#FFFFFF"
TEXT_COLOR = "#DCDCDC" # Main text color
TEXT_AREA_BG_COLOR = "#1E1E1E" # Darker for text areas
LABEL_FRAME_TEXT_COLOR = "#FFFFFF" # For LabelFrame titles
VALUE_COLOR = "#FFFFFF" # For sensor values
SEPARATOR_COLOR = "#4A4A4A"

FONT_FAMILY_UI = "Segoe UI" 
FONT_FAMILY_MONO = "Consolas" 
FONT_SIZE_NORMAL = 10
FONT_SIZE_HEADER = 12 
FONT_SIZE_SUB_HEADER = 10
FONT_SIZE_NAV = 9
FONT_SIZE_SMALL = 8 
FONT_SIZE_VALUE = 11 
SELECTIVE_SECTION_BG = "#333333" # Background for individual hardware sections in selective view
MIN_SELECTIVE_SECTION_WIDTH = 300 
RESIZE_DEBOUNCE_MS = 300 

class SystemStatsApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("System Monitor Pro") 
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+100+100") 
        self.configure(bg=WINDOW_BG_COLOR)
        self.protocol("WM_DELETE_WINDOW", self.exit_app)

        # Style for ttk widgets
        style = ttk.Style(self)
        style.theme_use('clam') # Using 'clam' or 'alt' or 'default' can give a base for ttk styling
        style.configure("TPanedwindow", background=WINDOW_BG_COLOR)
        style.configure("Vertical.TScrollbar", troughcolor=FRAME_BG_COLOR, bordercolor=FRAME_BG_COLOR, background=NAV_BUTTON_BG_COLOR, arrowcolor=TEXT_COLOR)
        style.map("Vertical.TScrollbar",
            background=[('active', NAV_BUTTON_ACTIVE_BG_COLOR)],
            arrowcolor=[('pressed', NAV_BUTTON_ACTIVE_FG_COLOR), ('active', NAV_BUTTON_ACTIVE_FG_COLOR)]
        )


        self.selected_hardware_id_list_view = None 
        self.nav_buttons_list_view = {} 
        self.current_view_mode = tk.StringVar(value="Selective View") 
        
        self.selective_view_config = {} 
        self.resize_job_id = None 
        self.last_known_width = self.winfo_width() 

        # --- Menu Bar ---
        menubar = Menu(self, bg=WINDOW_BG_COLOR, fg=TEXT_COLOR, activebackground=NAV_BUTTON_ACTIVE_BG_COLOR, activeforeground=NAV_BUTTON_ACTIVE_FG_COLOR)
        filemenu = Menu(menubar, tearoff=0, bg=FRAME_BG_COLOR, fg=TEXT_COLOR, activebackground=NAV_BUTTON_ACTIVE_BG_COLOR, activeforeground=NAV_BUTTON_ACTIVE_FG_COLOR)
        filemenu.add_command(label="Exit", command=self.exit_app, font=(FONT_FAMILY_UI, FONT_SIZE_NORMAL))
        menubar.add_cascade(label="File", menu=filemenu, font=(FONT_FAMILY_UI, FONT_SIZE_NORMAL))
        
        viewmenu = Menu(menubar, tearoff=0, bg=FRAME_BG_COLOR, fg=TEXT_COLOR, activebackground=NAV_BUTTON_ACTIVE_BG_COLOR, activeforeground=NAV_BUTTON_ACTIVE_FG_COLOR)
        viewmenu.add_radiobutton(label="Selective Dashboard", variable=self.current_view_mode, value="Selective View", command=self.switch_view, font=(FONT_FAMILY_UI, FONT_SIZE_NORMAL))
        viewmenu.add_radiobutton(label="Detailed Sensor List", variable=self.current_view_mode, value="List View", command=self.switch_view, font=(FONT_FAMILY_UI, FONT_SIZE_NORMAL))
        viewmenu.add_separator()
        viewmenu.add_command(label="Configure Dashboard...", command=self.open_selective_view_config_dialog, font=(FONT_FAMILY_UI, FONT_SIZE_NORMAL))
        menubar.add_cascade(label="View", menu=viewmenu, font=(FONT_FAMILY_UI, FONT_SIZE_NORMAL))
        self.config(menu=menubar)

        # --- Main content area ---
        self.main_display_frame = tk.Frame(self, bg=WINDOW_BG_COLOR)
        self.main_display_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15) # Increased padding

        # --- List View components ---
        self.list_view_paned_window = ttk.PanedWindow(self.main_display_frame, orient=tk.HORIZONTAL, style="TPanedwindow")
        self.nav_frame_list_view = tk.Frame(self.list_view_paned_window, bg=NAV_BG_COLOR, width=250, padx=5, pady=5) # Increased width and padding
        self.list_view_paned_window.add(self.nav_frame_list_view, weight=1)
        self.content_frame_list_view = tk.Frame(self.list_view_paned_window, bg=FRAME_BG_COLOR, padx=5, pady=5) # Use FRAME_BG_COLOR
        self.list_view_paned_window.add(self.content_frame_list_view, weight=3)
        self.sensor_text_area_list_view = scrolledtext.ScrolledText(
            self.content_frame_list_view, wrap=tk.WORD, font=(FONT_FAMILY_MONO, FONT_SIZE_NORMAL), # Use MONO font
            bg=TEXT_AREA_BG_COLOR, fg=TEXT_COLOR, relief=tk.FLAT, bd=0, state=tk.DISABLED,
            padx=10, pady=10
        )
        self.sensor_text_area_list_view.pack(fill=tk.BOTH, expand=True)
        
        # --- Selective View components ---
        self.selective_canvas = tk.Canvas(self.main_display_frame, bg=WINDOW_BG_COLOR, highlightthickness=0) # Use WINDOW_BG for canvas
        self.selective_scrollbar = ttk.Scrollbar(self.main_display_frame, orient="vertical", command=self.selective_canvas.yview, style="Vertical.TScrollbar")
        self.selective_scrollable_frame = tk.Frame(self.selective_canvas, bg=WINDOW_BG_COLOR) # Match canvas bg
        self.selective_scrollable_frame.bind("<Configure>", lambda e: self.selective_canvas.configure(scrollregion=self.selective_canvas.bbox("all")))
        self.selective_canvas.create_window((0, 0), window=self.selective_scrollable_frame, anchor="nw")
        self.selective_canvas.configure(yscrollcommand=self.selective_scrollbar.set)
        self.selective_canvas.bind("<MouseWheel>", self._on_selective_mousewheel) 
        self.selective_canvas.bind("<Button-4>", self._on_selective_mousewheel) 
        self.selective_canvas.bind("<Button-5>", self._on_selective_mousewheel)

        self.selective_view_hw_frames = {} 
        self.selective_view_hw_labels = {} 
        
        # --- Status Bar ---
        self.status_bar = tk.Label(self, text="Initializing...", font=(FONT_FAMILY_UI, FONT_SIZE_SMALL), 
                                   fg=TEXT_COLOR, bg=NAV_BG_COLOR, relief=tk.FLAT, anchor="w", bd=0, padx=10) # Styled status bar
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self._populate_initial_selective_view_config() 
        self.populate_navigation_list_view() 

        self.bind("<Configure>", self.on_window_resize) 
        self.switch_view() 
        self.update_stats_loop()
        self.update_status_bar() # Initial status bar update

    def update_status_bar(self):
        lhm_status = "LHM Active" if LHM_AVAILABLE else "LHM N/A - Run as Admin?"
        self.status_bar.config(text=f"Status: {lhm_status}  |  Last Update: {time.strftime('%H:%M:%S')}")

    def _populate_initial_selective_view_config(self):
        # ... (Logic remains the same, ensure it uses new FONT and COLOR constants if applicable within dialogs)
        if not LHM_HARDWARE_ITEMS_CACHE or not LHM_HARDWARE_ENUMS:
            return
        
        HardwareType = LHM_HARDWARE_ENUMS['HardwareType']
        SensorType = LHM_HARDWARE_ENUMS['SensorType']
        self.selective_view_config.clear()

        for hw_item in LHM_HARDWARE_ITEMS_CACHE:
            hw_id = hw_item.Identifier.ToString()
            if hw_id in self.selective_view_config: continue

            self.selective_view_config[hw_id] = {
                'show_hw': BooleanVar(value=False), 
                'name': hw_item.Name,
                'lhm_item': hw_item, 
                'sensors': {}
            }
            
            is_first_gpu_selected = any(self.selective_view_config[prev_id]['show_hw'].get() 
                                        for prev_id in self.selective_view_config 
                                        if prev_id != hw_id and 
                                           self.selective_view_config[prev_id]['lhm_item'].HardwareType in [HardwareType.GpuNvidia, HardwareType.GpuAmd, HardwareType.GpuIntel])

            if hw_item.HardwareType == HardwareType.Cpu:
                self.selective_view_config[hw_id]['show_hw'].set(True)
            elif hw_item.HardwareType in [HardwareType.GpuNvidia, HardwareType.GpuAmd, HardwareType.GpuIntel] and not is_first_gpu_selected:
                self.selective_view_config[hw_id]['show_hw'].set(True)


            key_cpu_sensors = {"Temperature": ["package", "core", "tctl", "tdie"], "CPU Fan": ["cpu fan", "cpu_fan1"], "System Fan": ["system fan", "sys_fan"], "Load": ["cpu total"]}
            key_gpu_sensors = {"Temperature": ["core", "edge"], "Hot Spot Temp": ["hot spot", "hotspot", "junction"], "Fan Speed": ["gpu fan", "fan"], "Load": ["gpu core", "core"]}
            
            all_sensors_for_hw = []
            def collect_sensors(item, path_prefix=""):
                for sensor in item.Sensors:
                    all_sensors_for_hw.append({'lhm_sensor': sensor, 'path': path_prefix + sensor.Name})
                for sub_item in item.SubHardware:
                    sub_item.Update() 
                    collect_sensors(sub_item, path_prefix + sub_item.Name + " / ")
            collect_sensors(hw_item)

            for sensor_info in all_sensors_for_hw:
                sensor = sensor_info['lhm_sensor']
                sensor_id = sensor.Identifier.ToString()
                sensor_display_name = sensor_info['path'] 
                should_show_sensor_by_default = False
                if self.selective_view_config[hw_id]['show_hw'].get(): 
                    current_key_sensors = {}
                    if hw_item.HardwareType == HardwareType.Cpu: current_key_sensors = key_cpu_sensors
                    elif hw_item.HardwareType in [HardwareType.GpuNvidia, HardwareType.GpuAmd, HardwareType.GpuIntel]: current_key_sensors = key_gpu_sensors
                    for display_key, keywords in current_key_sensors.items():
                        target_sensor_type_name = display_key.split(" ")[-1] if display_key != "Hot Spot Temp" else "Temperature"
                        if display_key in ["CPU Fan", "System Fan", "Fan Speed"]: target_sensor_type_name = "Fan"
                        actual_sensor_type_enum = getattr(SensorType, target_sensor_type_name, None)
                        if sensor.SensorType == actual_sensor_type_enum and any(kw.lower() in sensor.Name.lower() for kw in keywords):
                            should_show_sensor_by_default = True; break
                self.selective_view_config[hw_id]['sensors'][sensor_id] = {
                    'show_sensor': BooleanVar(value=should_show_sensor_by_default),
                    'name': sensor_display_name, 'type': sensor.SensorType, 'lhm_sensor': sensor }
        self.apply_selective_view_config()


    def on_window_resize(self, event):
        if event.widget == self:
            current_width = self.winfo_width()
            if current_width != self.last_known_width:
                self.last_known_width = current_width
                if self.current_view_mode.get() == "Selective View":
                    if self.resize_job_id: self.after_cancel(self.resize_job_id)
                    self.resize_job_id = self.after(RESIZE_DEBOUNCE_MS, self.build_selective_view_ui)

    def _on_selective_mousewheel(self, event):
        if self.current_view_mode.get() == "Selective View" and self.selective_canvas.winfo_ismapped():
            if hasattr(event, 'delta') and event.delta: self.selective_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            elif hasattr(event, 'num'): 
                if event.num == 4: self.selective_canvas.yview_scroll(-1, "units")
                elif event.num == 5: self.selective_canvas.yview_scroll(1, "units")

    def open_selective_view_config_dialog(self):
        # ... (Dialog styling will inherit some from parent, but can be further enhanced)
        config_dialog = Toplevel(self)
        config_dialog.title("Configure Dashboard View")
        config_dialog.geometry("600x500") 
        config_dialog.configure(bg=FRAME_BG_COLOR) # Use FRAME_BG_COLOR
        config_dialog.transient(self)
        config_dialog.grab_set()

        Label(config_dialog, text="Select hardware and their sensors for Dashboard:",
              font=(FONT_FAMILY_UI, FONT_SIZE_HEADER), bg=FRAME_BG_COLOR, fg=TEXT_COLOR).pack(pady=10, padx=10)

        hw_config_canvas = tk.Canvas(config_dialog, bg=FRAME_BG_COLOR, highlightthickness=0)
        hw_config_scrollbar = ttk.Scrollbar(config_dialog, orient="vertical", command=hw_config_canvas.yview, style="Vertical.TScrollbar")
        hw_config_scrollable_frame = tk.Frame(hw_config_canvas, bg=FRAME_BG_COLOR)
        hw_config_scrollable_frame.bind("<Configure>", lambda e: hw_config_canvas.configure(scrollregion=hw_config_canvas.bbox("all")))
        hw_config_canvas.create_window((0,0), window=hw_config_scrollable_frame, anchor="nw")
        hw_config_canvas.configure(yscrollcommand=hw_config_scrollbar.set)
        
        hw_config_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10,0), pady=5)
        hw_config_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0,10), pady=5)

        if LHM_HARDWARE_ITEMS_CACHE:
            for hw_item_cache_obj in LHM_HARDWARE_ITEMS_CACHE: 
                hw_id = hw_item_cache_obj.Identifier.ToString()
                if hw_id not in self.selective_view_config: # Should be populated
                    self.selective_view_config[hw_id] = {'show_hw': BooleanVar(value=False), 'name': hw_item_cache_obj.Name, 'lhm_item': hw_item_cache_obj, 'sensors': {}}

                entry_frame = Frame(hw_config_scrollable_frame, bg=FRAME_BG_COLOR)
                entry_frame.pack(fill=tk.X, pady=3, padx=5)

                cb = Checkbutton(entry_frame, text=self.selective_view_config[hw_id]['name'], 
                                 variable=self.selective_view_config[hw_id]['show_hw'],
                                 bg=FRAME_BG_COLOR, fg=TEXT_COLOR, selectcolor=SELECTIVE_SECTION_BG, 
                                 activebackground=FRAME_BG_COLOR, activeforeground=TEXT_COLOR,
                                 font=(FONT_FAMILY_UI, FONT_SIZE_NORMAL), anchor="w")
                cb.pack(side=tk.LEFT, padx=5)

                edit_button = Button(entry_frame, text="Edit Sensors", 
                                     command=lambda current_hw_id=hw_id: self.open_sensor_selection_dialog(current_hw_id, config_dialog),
                                     bg=NAV_BUTTON_BG_COLOR, fg=NAV_BUTTON_FG_COLOR, relief=tk.FLAT, bd=2, 
                                     activebackground=NAV_BUTTON_ACTIVE_BG_COLOR, activeforeground=NAV_BUTTON_ACTIVE_FG_COLOR,
                                     font=(FONT_FAMILY_UI, FONT_SIZE_SMALL), padx=5)
                edit_button.pack(side=tk.RIGHT, padx=5)
        else:
            Label(hw_config_scrollable_frame, text="No hardware found by LHM.", bg=FRAME_BG_COLOR, fg=TEXT_COLOR).pack()

        button_frame = Frame(config_dialog, bg=FRAME_BG_COLOR) # Use FRAME_BG_COLOR
        button_frame.pack(pady=15, side=tk.BOTTOM, fill=tk.X)
        
        ok_button = Button(button_frame, text="Apply & Close", width=15, command=lambda: [self.apply_selective_view_config(), config_dialog.destroy()],
                           bg=NAV_BUTTON_BG_COLOR, fg=NAV_BUTTON_FG_COLOR, relief=tk.FLAT, bd=2, activebackground=NAV_BUTTON_ACTIVE_BG_COLOR, activeforeground=NAV_BUTTON_ACTIVE_FG_COLOR, font=(FONT_FAMILY_UI, FONT_SIZE_NORMAL))
        ok_button.pack(side=tk.RIGHT, padx=10)

    def open_sensor_selection_dialog(self, hw_id, parent_dialog):
        # ... (Dialog styling can also be enhanced here)
        sensor_dialog = Toplevel(parent_dialog) 
        hw_name = self.selective_view_config[hw_id]['name']
        sensor_dialog.title(f"Sensors: {hw_name[:30]}") # Shorter title
        sensor_dialog.geometry("600x450") # Slightly wider
        sensor_dialog.configure(bg=FRAME_BG_COLOR)
        sensor_dialog.transient(parent_dialog)
        sensor_dialog.grab_set()

        Label(sensor_dialog, text=f"Choose sensors for {hw_name}:",
              font=(FONT_FAMILY_UI, FONT_SIZE_HEADER), bg=FRAME_BG_COLOR, fg=TEXT_COLOR).pack(pady=10, padx=10)

        sensor_list_canvas = tk.Canvas(sensor_dialog, bg=FRAME_BG_COLOR, highlightthickness=0)
        sensor_list_scrollbar = ttk.Scrollbar(sensor_dialog, orient="vertical", command=sensor_list_canvas.yview, style="Vertical.TScrollbar")
        sensor_list_scrollable_frame = tk.Frame(sensor_list_canvas, bg=FRAME_BG_COLOR)
        sensor_list_scrollable_frame.bind("<Configure>", lambda e: sensor_list_canvas.configure(scrollregion=sensor_list_canvas.bbox("all")))
        sensor_list_canvas.create_window((0,0), window=sensor_list_scrollable_frame, anchor="nw")
        sensor_list_canvas.configure(yscrollcommand=sensor_list_scrollbar.set)
        sensor_list_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10,0), pady=5)
        sensor_list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0,10), pady=5)

        hw_config_entry = self.selective_view_config[hw_id]
        lhm_hardware_item = hw_config_entry['lhm_item'] 
        
        all_sensors_for_this_hw = []
        def _collect_sensors_recursive(item, path_prefix=""):
            for sensor in item.Sensors:
                all_sensors_for_this_hw.append({'lhm_sensor': sensor, 'display_name': path_prefix + sensor.Name})
            for sub_item in item.SubHardware:
                sub_item.Update()
                _collect_sensors_recursive(sub_item, path_prefix + sub_item.Name + " / ")
        lhm_hardware_item.Update() 
        _collect_sensors_recursive(lhm_hardware_item)

        for sensor_info in all_sensors_for_this_hw:
            sensor_obj = sensor_info['lhm_sensor']
            sensor_id = sensor_obj.Identifier.ToString()
            sensor_display_name = sensor_info['display_name'] 
            if sensor_id not in hw_config_entry['sensors']:
                hw_config_entry['sensors'][sensor_id] = {
                    'show_sensor': BooleanVar(value=False), 'name': sensor_display_name, 
                    'type': sensor_obj.SensorType, 'lhm_sensor': sensor_obj }
            cb = Checkbutton(sensor_list_scrollable_frame, text=sensor_display_name, 
                             variable=hw_config_entry['sensors'][sensor_id]['show_sensor'],
                             bg=FRAME_BG_COLOR, fg=TEXT_COLOR, selectcolor=SELECTIVE_SECTION_BG, 
                             activebackground=FRAME_BG_COLOR, activeforeground=TEXT_COLOR,
                             font=(FONT_FAMILY_UI, FONT_SIZE_NAV), anchor="w")
            cb.pack(fill=tk.X, padx=5, pady=1)

        ok_button = Button(sensor_dialog, text="OK", width=10, command=sensor_dialog.destroy,
                           bg=NAV_BUTTON_BG_COLOR, fg=NAV_BUTTON_FG_COLOR, relief=tk.FLAT, bd=2, activebackground=NAV_BUTTON_ACTIVE_BG_COLOR, activeforeground=NAV_BUTTON_ACTIVE_FG_COLOR, font=(FONT_FAMILY_UI, FONT_SIZE_NORMAL))
        ok_button.pack(pady=10, side=tk.BOTTOM)

    def apply_selective_view_config(self):
        self.build_selective_view_ui() 

    def build_selective_view_ui(self):
        for widget in self.selective_scrollable_frame.winfo_children(): widget.destroy()
        self.selective_view_hw_frames.clear(); self.selective_view_hw_labels.clear()
        available_width = self.selective_canvas.winfo_width()
        if available_width <= 1: available_width = self.winfo_width() - (self.selective_scrollbar.winfo_width() if self.selective_scrollbar.winfo_ismapped() else 0) - 40 # Adjusted padding
        num_columns = max(1, available_width // MIN_SELECTIVE_SECTION_WIDTH)
        prev_cols = self.selective_scrollable_frame.grid_size()[0]
        for i in range(prev_cols): self.selective_scrollable_frame.columnconfigure(i, weight=0, uniform=None) 
        for i in range(num_columns): self.selective_scrollable_frame.columnconfigure(i, weight=1, uniform="sel_hw_group_dyn")

        current_row, current_col = 0, 0
        if LHM_AVAILABLE and LHM_HARDWARE_ENUMS: 
            for hw_id, hw_conf in self.selective_view_config.items():
                if hw_conf['show_hw'].get(): 
                    hw_name_display = hw_conf['name']
                    frame = tk.LabelFrame(self.selective_scrollable_frame, text=hw_name_display,
                                          font=(FONT_FAMILY_UI, FONT_SIZE_HEADER, "bold"),
                                          fg=LABEL_FRAME_TEXT_COLOR, bg=SELECTIVE_SECTION_BG, padx=10, pady=10, relief=tk.GROOVE, bd=1) # Added relief
                    frame.grid(row=current_row, column=current_col, sticky="nsew", padx=10, pady=10) # Increased padding
                    self.selective_scrollable_frame.rowconfigure(current_row, weight=0) 
                    self.selective_view_hw_frames[hw_id] = frame
                    self.selective_view_hw_labels[hw_id] = {} 
                    sensor_row_idx = 0
                    for sensor_id, sensor_conf_detail in hw_conf['sensors'].items(): 
                        if sensor_conf_detail['show_sensor'].get(): 
                            sensor_display_name_short = sensor_conf_detail['lhm_sensor'].Name 
                            tk.Label(frame, text=f"{sensor_display_name_short}:", font=(FONT_FAMILY_UI, FONT_SIZE_NORMAL), 
                                     fg=TEXT_COLOR, bg=SELECTIVE_SECTION_BG).grid(row=sensor_row_idx, column=0, sticky="w", pady=2, padx=5)
                            value_label = tk.Label(frame, text="N/A", font=(FONT_FAMILY_UI, FONT_SIZE_VALUE, "bold"), 
                                                   fg=VALUE_COLOR, bg=SELECTIVE_SECTION_BG) # Use VALUE_COLOR
                            value_label.grid(row=sensor_row_idx, column=1, sticky="e", padx=5, pady=2)
                            self.selective_view_hw_labels[hw_id][sensor_id] = value_label 
                            sensor_row_idx +=1
                    frame.columnconfigure(1, weight=1)
                    current_col += 1
                    if current_col >= num_columns: current_col = 0; current_row += 1
        self.selective_scrollable_frame.update_idletasks()
        self.selective_canvas.config(scrollregion=self.selective_canvas.bbox("all"))
        self.refresh_selective_view_sensors() 

    def switch_view(self):
        mode = self.current_view_mode.get()
        if mode == "List View":
            self.selective_canvas.pack_forget(); self.selective_scrollbar.pack_forget()
            self.list_view_paned_window.pack(fill=tk.BOTH, expand=True)
            if LHM_HARDWARE_ITEMS_CACHE and not self.selected_hardware_id_list_view and self.nav_buttons_list_view: 
                first_hw_id = LHM_HARDWARE_ITEMS_CACHE[0].Identifier.ToString()
                self.select_hardware_list_view(first_hw_id)
            elif self.selected_hardware_id_list_view: self.refresh_selected_hardware_sensors_list_view()
        elif mode == "Selective View":
            self.list_view_paned_window.pack_forget()
            self.selective_canvas.pack(side=tk.LEFT, fill="both", expand=True); self.selective_scrollbar.pack(side="right", fill="y")
            self.build_selective_view_ui() 

    def populate_navigation_list_view(self):
        for widget in self.nav_frame_list_view.winfo_children(): widget.destroy()
        self.nav_buttons_list_view.clear()
        if not LHM_AVAILABLE or not LHM_HARDWARE_ITEMS_CACHE:
            tk.Label(self.nav_frame_list_view, text="No Hardware", bg=NAV_BG_COLOR, fg=TEXT_COLOR, font=(FONT_FAMILY_UI, FONT_SIZE_NAV)).pack(pady=10, padx=5)
            return
        for hw_item in LHM_HARDWARE_ITEMS_CACHE:
            hw_id = hw_item.Identifier.ToString()
            btn_text = f"{hw_item.Name}\n({hw_item.HardwareType.ToString()})"
            btn = tk.Button(self.nav_frame_list_view, text=btn_text, font=(FONT_FAMILY_UI, FONT_SIZE_NAV),
                            bg=NAV_BUTTON_BG_COLOR, fg=NAV_BUTTON_FG_COLOR, activebackground=NAV_BUTTON_ACTIVE_BG_COLOR, activeforeground=NAV_BUTTON_ACTIVE_FG_COLOR,
                            relief=tk.FLAT, anchor="w", justify=tk.LEFT, padx=10, pady=3, bd=0,
                            command=lambda hid=hw_id: self.select_hardware_list_view(hid))
            btn.pack(fill=tk.X, pady=1)
            self.nav_buttons_list_view[hw_id] = btn
            
    def select_hardware_list_view(self, hw_id):
        self.selected_hardware_id_list_view = hw_id
        for item_id, button in self.nav_buttons_list_view.items():
            is_selected = (item_id == hw_id)
            button.config(relief=tk.SUNKEN if is_selected else tk.FLAT, 
                          bg=NAV_BUTTON_ACTIVE_BG_COLOR if is_selected else NAV_BUTTON_BG_COLOR,
                          fg=NAV_BUTTON_ACTIVE_FG_COLOR if is_selected else NAV_BUTTON_FG_COLOR)
        self.refresh_selected_hardware_sensors_list_view()

    def refresh_selected_hardware_sensors_list_view(self):
        if self.selected_hardware_id_list_view and LHM_AVAILABLE and LHM_COMPUTER_INSTANCE:
            selected_hw_item = next((item for item in LHM_HARDWARE_ITEMS_CACHE if item.Identifier.ToString() == self.selected_hardware_id_list_view), None)
            if selected_hw_item:
                selected_hw_item.Update() 
                sensor_data_lines = self.format_sensors_for_hardware_item_recursive(selected_hw_item)
                self.update_text_area(self.sensor_text_area_list_view, sensor_data_lines)

    def refresh_selective_view_sensors(self):
        if not LHM_AVAILABLE or not LHM_HARDWARE_ENUMS:
            for hw_id_labels in self.selective_view_hw_labels.values():
                for label in hw_id_labels.values(): label.config(text="LHM N/A")
            return
        SensorType = LHM_HARDWARE_ENUMS['SensorType']
        for hw_id, hw_conf in self.selective_view_config.items():
            if hw_conf['show_hw'].get() and hw_id in self.selective_view_hw_labels:
                lhm_hardware_item = hw_conf['lhm_item']
                lhm_hardware_item.Update() 
                for sensor_id, sensor_config_details in hw_conf['sensors'].items():
                    if sensor_config_details['show_sensor'].get() and sensor_id in self.selective_view_hw_labels[hw_id]:
                        current_sensor_value = "N/A"
                        def find_sensor_recursively(item_to_search, target_sensor_id):
                            for s_obj in item_to_search.Sensors: 
                                if s_obj.Identifier.ToString() == target_sensor_id: return s_obj
                            for sub_item in item_to_search.SubHardware:
                                found_s = find_sensor_recursively(sub_item, target_sensor_id)
                                if found_s: return found_s
                            return None
                        actual_sensor = find_sensor_recursively(lhm_hardware_item, sensor_id)
                        if actual_sensor and actual_sensor.Value is not None:
                            s_val, s_type = actual_sensor.Value, actual_sensor.SensorType 
                            unit, formatted_val = "", f"{s_val}"
                            if s_type == SensorType.Temperature: unit = "°C"; formatted_val = f"{s_val:.1f}"
                            elif s_type == SensorType.Fan: unit = "RPM"; formatted_val = f"{s_val:.0f}"
                            elif s_type == SensorType.Load: unit = "%"; formatted_val = f"{s_val:.1f}"
                            elif s_type == SensorType.Power: unit = "W"; formatted_val = f"{s_val:.1f}"
                            elif s_type == SensorType.Voltage: unit = "V"; formatted_val = f"{s_val:.3f}"
                            elif s_type == SensorType.Clock: unit = "MHz"; formatted_val = f"{s_val:.0f}"
                            elif s_type == SensorType.Control: unit = "%"; formatted_val = f"{s_val:.0f}" 
                            elif s_type == SensorType.Factor: unit = ""; formatted_val = f"{s_val:.2f}" 
                            elif s_type == SensorType.Data: unit = "GB"; formatted_val = f"{s_val:.2f}" 
                            elif s_type == SensorType.SmallData: unit = "MB"; formatted_val = f"{s_val:.0f}" 
                            elif s_type == SensorType.Throughput: unit = "B/s"; formatted_val = f"{s_val:.0f}" 
                            elif s_type == SensorType.Level: unit = "%"; formatted_val = f"{s_val:.0f}"
                            current_sensor_value = f"{formatted_val}{unit if unit else ''}"
                        self.selective_view_hw_labels[hw_id][sensor_id].config(text=current_sensor_value)

    def format_sensors_for_hardware_item_recursive(self, hardware_item, indentation_level=0):
        data_lines = []
        if not LHM_HARDWARE_ENUMS: return data_lines 
        SensorType = LHM_HARDWARE_ENUMS['SensorType']
        indent, sensor_indent = "  " * indentation_level, "  " * (indentation_level + 1)
        direct_sensors_found, sub_hardware_had_sensors = False, False
        for sensor in hardware_item.Sensors:
            if sensor.Value is None: continue
            s_type, s_name, s_val = sensor.SensorType, sensor.Name, sensor.Value
            if s_type in [SensorType.Temperature, SensorType.Fan, SensorType.Load, SensorType.Power, SensorType.Voltage, SensorType.Clock, SensorType.Control, SensorType.Factor, SensorType.Data, SensorType.SmallData, SensorType.Throughput, SensorType.Level]:
                unit, formatted_val = "", f"{s_val}"
                if s_type == SensorType.Temperature: unit = "°C"; formatted_val = f"{s_val:.1f}"
                elif s_type == SensorType.Fan: unit = "RPM"; formatted_val = f"{s_val:.0f}"
                elif s_type == SensorType.Load: unit = "%"; formatted_val = f"{s_val:.1f}"
                elif s_type == SensorType.Power: unit = "W"; formatted_val = f"{s_val:.1f}"
                elif s_type == SensorType.Voltage: unit = "V"; formatted_val = f"{s_val:.3f}"
                elif s_type == SensorType.Clock: unit = "MHz"; formatted_val = f"{s_val:.0f}"
                elif s_type == SensorType.Control: unit = "%"; formatted_val = f"{s_val:.0f}" 
                elif s_type == SensorType.Factor: unit = ""; formatted_val = f"{s_val:.2f}" 
                elif s_type == SensorType.Data: unit = "GB"; formatted_val = f"{s_val:.2f}" 
                elif s_type == SensorType.SmallData: unit = "MB"; formatted_val = f"{s_val:.0f}" 
                elif s_type == SensorType.Throughput: unit = "B/s"; formatted_val = f"{s_val:.0f}" 
                elif s_type == SensorType.Level: unit = "%"; formatted_val = f"{s_val:.0f}" 
                data_lines.append(f"{sensor_indent}{s_name[:30].ljust(30)}: {formatted_val.rjust(8)} {unit}")
                direct_sensors_found = True
        for sub_hw_item in hardware_item.SubHardware:
            sub_hw_item.Update() 
            data_lines.append(f"{indent}  -- {sub_hw_item.Name} ({sub_hw_item.HardwareType.ToString()}) --")
            sub_data_lines = self.format_sensors_for_hardware_item_recursive(sub_hw_item, indentation_level + 1)
            if sub_data_lines:
                meaningful_sub_data = [line for line in sub_data_lines if "(No relevant sensors" not in line.strip()]
                if meaningful_sub_data:
                    data_lines.extend(meaningful_sub_data); sub_hardware_had_sensors = True
                elif not direct_sensors_found and not sub_hardware_had_sensors and indentation_level == 0:
                    data_lines.append(f"{indent}    (No relevant sensors for this sub-component)")
        if not direct_sensors_found and not sub_hardware_had_sensors and indentation_level == 0 and not any(hardware_item.SubHardware):
            data_lines.append(f"{indent}  (No relevant sensors of interest found for this component)")
        return data_lines

    def update_text_area(self, text_area, new_data_lines):
        try:
            current_yview_top_fraction = text_area.yview()[0]
            text_area.config(state=tk.NORMAL) 
            text_area.delete(1.0, tk.END) 
            if new_data_lines:
                for line in new_data_lines: text_area.insert(tk.END, line + "\n")
            else: text_area.insert(tk.END, "No sensor data to display.\n")
            text_area.yview_moveto(current_yview_top_fraction)
            text_area.config(state=tk.DISABLED) 
        except tk.TclError: pass
        except Exception as e: print(f"Error updating text area: {e}")

    def update_stats_loop(self):
        try:
            if self.current_view_mode.get() == "List View":
                self.refresh_selected_hardware_sensors_list_view()
            elif self.current_view_mode.get() == "Selective View":
                self.refresh_selective_view_sensors()
            self.update_status_bar() # Update status bar in each loop
        except Exception as e:
            print(f"Error during main stats update loop: {e}")
        self.after(UPDATE_INTERVAL_MS, self.update_stats_loop)

    def exit_app(self):
        close_lhm() 
        self.destroy()

if __name__ == "__main__":
    app = SystemStatsApp()
    app.mainloop()
