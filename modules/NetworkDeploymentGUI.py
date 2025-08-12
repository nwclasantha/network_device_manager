"""
Network Deployment GUI - Fixed Layout Version
All buttons visible and properly aligned
"""

import os
import json
import csv
import threading
import queue
import time
import random
import platform
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

# GUI imports
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import customtkinter as ctk

# Data processing
import pandas as pd
import numpy as np

# Try to import matplotlib for charts
try:
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    import matplotlib.animation as animation
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# Try to import netmiko for real device connectivity
try:
    from netmiko import ConnectHandler
    from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
    NETMIKO_AVAILABLE = True
except ImportError:
    NETMIKO_AVAILABLE = False

# Import other modules
from modules.DeviceDialog import DeviceDialog
from modules.SettingsDialog import SettingsDialog
from modules.device_models_db import DEVICE_MODELS  


class NetworkDeploymentGUI(ctk.CTk):
    """Main GUI Application Class with Fixed Layout"""
    
    def __init__(self):
        super().__init__()
        
        # Window configuration - LARGER DEFAULT SIZE
        self.title("🌐 Advanced Network Deployment Suite v3.0")
        self.geometry("1600x950")  # Increased size
        self.minsize(1400, 800)    # Larger minimum
        
        # Center window on screen
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
        
        # Variables
        self.selected_model = None
        self.config_file_path = None
        self.inventory_file_path = None
        self.deployment_thread = None
        self.deployment_queue = queue.Queue()
        self.devices = []
        self.deployment_results = []
        self.deployment_running = False
        self.demo_mode = not NETMIKO_AVAILABLE
        
        # Statistics
        self.stats = {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'pending': 0,
            'in_progress': 0
        }
        
        # Configure grid weights FIRST
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)  # Sidebar - fixed width
        self.grid_columnconfigure(1, weight=1)  # Main content - expandable
        
        # Create UI
        self.setup_ui()
        self.create_menu_bar()
        self.update_dashboard()
        
        # Check deployment mode
        self.check_deployment_mode()
        
        # Start queue processor
        self.process_queue()
    
    def check_deployment_mode(self):
        """Check and notify user about deployment mode"""
        if self.demo_mode:
            self.log_message("⚠️ DEMO MODE ACTIVE - Install netmiko for real deployments", "WARNING")
            self.log_message("To install: pip install netmiko paramiko", "INFO")
        else:
            self.log_message("✅ Real deployment mode active", "INFO")
        
    def setup_ui(self):
        """Setup the main UI layout with proper spacing"""
        # Create main containers
        self.create_sidebar()
        self.create_main_content()
        self.create_status_bar()
        
    def create_menu_bar(self):
        """Create application menu bar"""
        self.menubar = tk.Menu(self, bg='#2b2b2b', fg='white', relief=tk.FLAT)
        self.config(menu=self.menubar)
        
        # File menu
        file_menu = tk.Menu(self.menubar, tearoff=0, bg='#2b2b2b', fg='white')
        self.menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Inventory", command=self.load_inventory)
        file_menu.add_command(label="Load Config", command=self.load_config)
        file_menu.add_separator()
        file_menu.add_command(label="Export Results", command=self.export_results)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        
        # Tools menu
        tools_menu = tk.Menu(self.menubar, tearoff=0, bg='#2b2b2b', fg='white')
        self.menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Test Connectivity", command=self.test_connectivity)
        tools_menu.add_command(label="Validate Config", command=self.validate_config)
        tools_menu.add_separator()
        tools_menu.add_command(label="Toggle Demo Mode", command=self.toggle_demo_mode)
        tools_menu.add_separator()
        tools_menu.add_command(label="Settings", command=self.open_settings)
        
        # Help menu
        help_menu = tk.Menu(self.menubar, tearoff=0, bg='#2b2b2b', fg='white')
        self.menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.show_documentation)
        help_menu.add_command(label="About", command=self.show_about)
        
    def create_sidebar(self):
        """Create left sidebar with fixed width and proper spacing"""
        # Sidebar frame with fixed width
        self.sidebar = ctk.CTkScrollableFrame(self, width=320, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 2))
        # REMOVED: self.sidebar.grid_propagate(False)  # This line causes the error
        # The width is already maintained by the width=320 parameter
        
        # Logo and Title Frame
        logo_frame = ctk.CTkFrame(self.sidebar, height=120)
        logo_frame.pack(fill="x", padx=15, pady=(15, 10))
        logo_frame.pack_propagate(False)
        
        # Network icon
        icon_label = ctk.CTkLabel(
            logo_frame,
            text="🌐",
            font=ctk.CTkFont(size=36)
        )
        icon_label.pack(pady=(10, 5))
        
        title_label = ctk.CTkLabel(
            logo_frame,
            text="Network Deployment",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack()
        
        # Mode indicator
        self.mode_label = ctk.CTkLabel(
            logo_frame,
            text="DEMO MODE" if self.demo_mode else "REAL MODE",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="yellow" if self.demo_mode else "green"
        )
        self.mode_label.pack(pady=(5, 10))
        
        # Separator
        separator1 = ctk.CTkFrame(self.sidebar, height=2, fg_color="gray30")
        separator1.pack(fill="x", padx=15, pady=5)
        
        # Device Model Section
        model_section = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        model_section.pack(fill="x", padx=15, pady=10)
        
        model_label = ctk.CTkLabel(
            model_section,
            text="Device Model",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        model_label.pack(fill="x", pady=(0, 8))
        
        self.model_var = ctk.StringVar()
        self.model_dropdown = ctk.CTkComboBox(
            model_section,
            values=list(DEVICE_MODELS.keys()),
            variable=self.model_var,
            command=self.on_model_selected,
            width=280,
            height=32
        )
        self.model_dropdown.pack(fill="x")
        self.model_dropdown.set("Select a model...")
        
        # Device Info Display
        self.device_info_frame = ctk.CTkFrame(model_section, height=80)
        self.device_info_frame.pack(fill="x", pady=(10, 0))
        
        # Separator
        separator2 = ctk.CTkFrame(self.sidebar, height=2, fg_color="gray30")
        separator2.pack(fill="x", padx=15, pady=5)
        
        # Credentials Section
        cred_section = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        cred_section.pack(fill="x", padx=15, pady=10)
        
        cred_label = ctk.CTkLabel(
            cred_section,
            text="Default Credentials",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        cred_label.pack(fill="x", pady=(0, 8))
        
        # Username
        self.username_entry = ctk.CTkEntry(
            cred_section,
            placeholder_text="Username",
            width=280,
            height=32
        )
        self.username_entry.pack(fill="x", pady=(0, 8))
        
        # Password
        self.password_entry = ctk.CTkEntry(
            cred_section,
            placeholder_text="Password",
            show="*",
            width=280,
            height=32
        )
        self.password_entry.pack(fill="x")
        
        # Separator
        separator3 = ctk.CTkFrame(self.sidebar, height=2, fg_color="gray30")
        separator3.pack(fill="x", padx=15, pady=5)
        
        # File Operations Section
        file_section = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        file_section.pack(fill="x", padx=15, pady=10)
        
        file_label = ctk.CTkLabel(
            file_section,
            text="Configuration Files",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        file_label.pack(fill="x", pady=(0, 8))
        
        # Load Config Button
        self.load_config_btn = ctk.CTkButton(
            file_section,
            text="📁 Load Config File",
            command=self.load_config,
            width=280,
            height=36,
            font=ctk.CTkFont(size=13)
        )
        self.load_config_btn.pack(fill="x", pady=(0, 8))
        
        # Load Inventory Button
        self.load_inventory_btn = ctk.CTkButton(
            file_section,
            text="📋 Load Inventory",
            command=self.load_inventory,
            width=280,
            height=36,
            font=ctk.CTkFont(size=13)
        )
        self.load_inventory_btn.pack(fill="x")
        
        # Separator
        separator4 = ctk.CTkFrame(self.sidebar, height=2, fg_color="gray30")
        separator4.pack(fill="x", padx=15, pady=10)
        
        # Action Buttons Section
        action_section = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        action_section.pack(fill="x", padx=15, pady=10)
        
        # Deploy Button
        self.deploy_btn = ctk.CTkButton(
            action_section,
            text="🚀 START DEPLOYMENT",
            command=self.start_deployment,
            width=280,
            height=45,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="green",
            hover_color="darkgreen"
        )
        self.deploy_btn.pack(fill="x", pady=(0, 10))
        
        # Stop Button
        self.stop_btn = ctk.CTkButton(
            action_section,
            text="⏹ STOP",
            command=self.stop_deployment,
            width=280,
            height=38,
            font=ctk.CTkFont(size=13),
            fg_color="red",
            hover_color="darkred",
            state="disabled"
        )
        self.stop_btn.pack(fill="x")
        
        # Add some bottom padding
        bottom_spacer = ctk.CTkFrame(self.sidebar, height=20, fg_color="transparent")
        bottom_spacer.pack(fill="x")
        
    def create_main_content(self):
        """Create main content area with proper sizing"""
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=(2, 5), pady=5)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Create Tabview with proper sizing
        self.tabview = ctk.CTkTabview(self.main_frame, width=1200, height=800)
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Configure tab button height
        self.tabview._segmented_button.configure(height=35)
        
        # Add tabs
        self.tabview.add("📊 Dashboard")
        self.tabview.add("📝 Configuration")
        self.tabview.add("🖥️ Devices")
        self.tabview.add("📈 Deployment")
        self.tabview.add("📋 Logs")
        
        # Create tab contents
        self.create_dashboard_tab()
        self.create_config_tab()
        self.create_devices_tab()
        self.create_deployment_tab()
        self.create_logs_tab()
        
    def create_dashboard_tab(self):
        """Create dashboard with proper grid weights"""
        dashboard_frame = self.tabview.tab("📊 Dashboard")
        dashboard_frame.grid_columnconfigure(0, weight=1)
        dashboard_frame.grid_rowconfigure(0, weight=0)  # Stats - fixed height
        dashboard_frame.grid_rowconfigure(1, weight=1)  # Charts - expandable
        
        # Statistics Cards Frame
        stats_frame = ctk.CTkFrame(dashboard_frame, height=120)
        stats_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        stats_frame.grid_propagate(False)
        
        # Create inner frame for cards
        cards_container = ctk.CTkFrame(stats_frame, fg_color="transparent")
        cards_container.pack(expand=True)
        
        # Create stat cards in a grid
        self.stat_cards = {}
        stats_config = [
            ("Total Devices", "total", "#3498db", "📱"),
            ("Successful", "successful", "#2ecc71", "✅"),
            ("Failed", "failed", "#e74c3c", "❌"),
            ("In Progress", "in_progress", "#f39c12", "⏳")
        ]
        
        for i, (label, key, color, icon) in enumerate(stats_config):
            card = self.create_stat_card(cards_container, label, "0", color, icon)
            card.grid(row=0, column=i, padx=10, pady=10)
            self.stat_cards[key] = card
        
        # Charts Frame with proper grid
        charts_frame = ctk.CTkFrame(dashboard_frame)
        charts_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        charts_frame.grid_columnconfigure((0, 1), weight=1, uniform="charts")
        charts_frame.grid_rowconfigure(0, weight=1)
        
        # Create charts
        self.create_pie_chart(charts_frame)
        self.create_progress_chart(charts_frame)
        
    def create_stat_card(self, parent, title, value, color, icon):
        """Create a statistics card with fixed size"""
        card = ctk.CTkFrame(parent, width=200, height=100)
        card.grid_propagate(False)
        
        # Icon
        icon_label = ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=28))
        icon_label.pack(pady=(10, 5))
        
        # Value
        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=color
        )
        value_label.pack()
        
        # Title
        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        title_label.pack(pady=(0, 10))
        
        # Store value label for updates
        card.value_label = value_label
        
        return card
    
    def create_pie_chart(self, parent):
        """Create pie chart with proper sizing"""
        self.pie_frame = ctk.CTkFrame(parent)
        self.pie_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        if MATPLOTLIB_AVAILABLE:
            self.pie_fig = Figure(figsize=(6, 5), dpi=80, facecolor='#212121')
            self.pie_ax = self.pie_fig.add_subplot(111)
            
            self.pie_canvas = FigureCanvasTkAgg(self.pie_fig, master=self.pie_frame)
            self.pie_canvas.get_tk_widget().pack(fill="both", expand=True)
            
            self.update_pie_chart()
        else:
            self.pie_label = ctk.CTkLabel(
                self.pie_frame,
                text="📊 Charts unavailable\n(Install matplotlib)",
                font=ctk.CTkFont(size=14),
                text_color="gray"
            )
            self.pie_label.pack(expand=True)
        
    def create_progress_chart(self, parent):
        """Create progress chart with proper sizing"""
        self.progress_frame = ctk.CTkFrame(parent)
        self.progress_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        if MATPLOTLIB_AVAILABLE:
            self.prog_fig = Figure(figsize=(6, 5), dpi=80, facecolor='#212121')
            self.prog_ax = self.prog_fig.add_subplot(111)
            
            self.prog_canvas = FigureCanvasTkAgg(self.prog_fig, master=self.progress_frame)
            self.prog_canvas.get_tk_widget().pack(fill="both", expand=True)
            
            self.update_progress_chart()
        else:
            self.prog_label = ctk.CTkLabel(
                self.progress_frame,
                text="📈 Progress: 0%",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            self.prog_label.pack(expand=True)
        
    def create_config_tab(self):
        """Create configuration tab with proper layout"""
        config_frame = self.tabview.tab("📝 Configuration")
        config_frame.grid_columnconfigure(0, weight=1)
        config_frame.grid_rowconfigure(0, weight=0)  # Toolbar
        config_frame.grid_rowconfigure(1, weight=1)  # Editor
        
        # Toolbar
        toolbar = ctk.CTkFrame(config_frame, height=50)
        toolbar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        toolbar.grid_propagate(False)
        
        # Toolbar buttons container
        btn_container = ctk.CTkFrame(toolbar, fg_color="transparent")
        btn_container.pack(side="left", padx=10, pady=8)
        
        # Buttons
        ctk.CTkButton(
            btn_container,
            text="📁 Open",
            command=self.load_config,
            width=90,
            height=32
        ).pack(side="left", padx=(0, 5))
        
        ctk.CTkButton(
            btn_container,
            text="💾 Save",
            command=self.save_config,
            width=90,
            height=32
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_container,
            text="✅ Validate",
            command=self.validate_config,
            width=90,
            height=32
        ).pack(side="left", padx=5)
        
        # Config editor
        self.config_editor = ctk.CTkTextbox(
            config_frame,
            font=ctk.CTkFont(family="Consolas" if platform.system() == "Windows" else "Courier", size=12),
            wrap="none"
        )
        self.config_editor.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
    def create_devices_tab(self):
        """Create devices tab with proper layout"""
        devices_frame = self.tabview.tab("🖥️ Devices")
        devices_frame.grid_columnconfigure(0, weight=1)
        devices_frame.grid_rowconfigure(0, weight=0)  # Toolbar
        devices_frame.grid_rowconfigure(1, weight=1)  # Tree
        
        # Toolbar
        toolbar = ctk.CTkFrame(devices_frame, height=50)
        toolbar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        toolbar.grid_propagate(False)
        
        # Toolbar content
        toolbar_content = ctk.CTkFrame(toolbar, fg_color="transparent")
        toolbar_content.pack(side="left", padx=10, pady=8)
        
        # Search
        self.device_search = ctk.CTkEntry(
            toolbar_content,
            placeholder_text="🔍 Search devices...",
            width=250,
            height=32
        )
        self.device_search.pack(side="left", padx=(0, 10))
        
        # Buttons
        btn_frame = ctk.CTkFrame(toolbar_content, fg_color="transparent")
        btn_frame.pack(side="left")
        
        buttons = [
            ("➕ Add", self.add_device),
            ("✏️ Edit", self.edit_device),
            ("🗑️ Delete", self.delete_device),
            ("🔌 Test", self.test_selected_device)
        ]
        
        for text, command in buttons:
            ctk.CTkButton(
                btn_frame,
                text=text,
                command=command,
                width=75,
                height=32
            ).pack(side="left", padx=2)
        
        # Devices TreeView Frame
        tree_frame = ctk.CTkFrame(devices_frame)
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Style configuration for treeview
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", 
                       background="#2b2b2b",
                       foreground="white",
                       rowheight=25,
                       fieldbackground="#2b2b2b")
        style.map('Treeview', background=[('selected', '#4a4a4a')])
        style.configure("Treeview.Heading",
                       background="#3c3c3c",
                       foreground="white",
                       relief="flat")
        
        # Create Treeview
        self.devices_tree = ttk.Treeview(
            tree_frame,
            columns=("IP", "Hostname", "Model", "Status", "Username"),
            show="tree headings",
            selectmode="extended",
            height=20
        )
        
        # Configure columns
        self.devices_tree.heading("#0", text="ID")
        self.devices_tree.heading("IP", text="IP Address")
        self.devices_tree.heading("Hostname", text="Hostname")
        self.devices_tree.heading("Model", text="Model")
        self.devices_tree.heading("Status", text="Status")
        self.devices_tree.heading("Username", text="Username")
        
        # Column widths
        self.devices_tree.column("#0", width=50, minwidth=50)
        self.devices_tree.column("IP", width=150, minwidth=100)
        self.devices_tree.column("Hostname", width=200, minwidth=150)
        self.devices_tree.column("Model", width=180, minwidth=120)
        self.devices_tree.column("Status", width=100, minwidth=80)
        self.devices_tree.column("Username", width=120, minwidth=80)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.devices_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.devices_tree.xview)
        self.devices_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout
        self.devices_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
    def create_deployment_tab(self):
        """Create deployment tab with proper layout"""
        deploy_frame = self.tabview.tab("📈 Deployment")
        deploy_frame.grid_columnconfigure(0, weight=1)
        deploy_frame.grid_rowconfigure(0, weight=0)  # Progress
        deploy_frame.grid_rowconfigure(1, weight=1)  # Results
        
        # Progress Section
        progress_frame = ctk.CTkFrame(deploy_frame, height=100)
        progress_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        progress_frame.grid_propagate(False)
        
        # Progress content
        progress_content = ctk.CTkFrame(progress_frame, fg_color="transparent")
        progress_content.pack(expand=True)
        
        # Overall Progress Label
        self.overall_progress_label = ctk.CTkLabel(
            progress_content,
            text="Overall Progress: 0%",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.overall_progress_label.pack(pady=(10, 5))
        
        # Progress Bar
        self.overall_progress = ctk.CTkProgressBar(progress_content, width=700, height=22)
        self.overall_progress.pack(pady=(5, 10))
        self.overall_progress.set(0)
        
        # Results Section
        results_frame = ctk.CTkFrame(deploy_frame)
        results_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)
        
        # Results TreeView
        self.results_tree = ttk.Treeview(
            results_frame,
            columns=("Device", "IP", "Status", "Time", "Message"),
            show="tree headings",
            selectmode="browse",
            height=20
        )
        
        # Configure columns
        self.results_tree.heading("#0", text="")
        self.results_tree.heading("Device", text="Device")
        self.results_tree.heading("IP", text="IP Address")
        self.results_tree.heading("Status", text="Status")
        self.results_tree.heading("Time", text="Time")
        self.results_tree.heading("Message", text="Message")
        
        # Column widths
        self.results_tree.column("#0", width=0, stretch=False)
        self.results_tree.column("Device", width=200, minwidth=150)
        self.results_tree.column("IP", width=150, minwidth=100)
        self.results_tree.column("Status", width=100, minwidth=80)
        self.results_tree.column("Time", width=180, minwidth=150)
        self.results_tree.column("Message", width=350, minwidth=200)
        
        # Scrollbar
        vsb = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=vsb.set)
        
        # Grid
        self.results_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        
    def create_logs_tab(self):
        """Create logs tab with proper layout"""
        logs_frame = self.tabview.tab("📋 Logs")
        logs_frame.grid_columnconfigure(0, weight=1)
        logs_frame.grid_rowconfigure(0, weight=0)  # Controls
        logs_frame.grid_rowconfigure(1, weight=1)  # Log viewer
        
        # Log controls
        controls_frame = ctk.CTkFrame(logs_frame, height=50)
        controls_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        controls_frame.grid_propagate(False)
        
        # Controls content
        controls_content = ctk.CTkFrame(controls_frame, fg_color="transparent")
        controls_content.pack(side="left", padx=10, pady=8)
        
        # Log level
        ctk.CTkLabel(controls_content, text="Log Level:").pack(side="left", padx=(0, 5))
        
        self.log_level_var = ctk.StringVar(value="INFO")
        log_level_menu = ctk.CTkComboBox(
            controls_content,
            values=["DEBUG", "INFO", "WARNING", "ERROR"],
            variable=self.log_level_var,
            width=100,
            height=32
        )
        log_level_menu.pack(side="left", padx=(0, 10))
        
        # Buttons
        ctk.CTkButton(
            controls_content,
            text="🗑️ Clear",
            command=self.clear_logs,
            width=80,
            height=32
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            controls_content,
            text="💾 Export",
            command=self.export_logs,
            width=80,
            height=32
        ).pack(side="left", padx=2)
        
        # Log viewer
        self.log_viewer = ctk.CTkTextbox(
            logs_frame,
            font=ctk.CTkFont(family="Consolas" if platform.system() == "Windows" else "Courier", size=10),
            wrap="word"
        )
        self.log_viewer.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
    def create_status_bar(self):
        """Create status bar at bottom"""
        self.status_bar = ctk.CTkFrame(self, height=30, corner_radius=0)
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        
        # Status text
        self.status_text = ctk.CTkLabel(
            self.status_bar,
            text="Ready",
            font=ctk.CTkFont(size=11),
            anchor="w"
        )
        self.status_text.pack(side="left", padx=15)
        
        # Connection indicator
        self.connection_indicator = ctk.CTkLabel(
            self.status_bar,
            text="● Idle",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="e"
        )
        self.connection_indicator.pack(side="right", padx=15)
    
    # ============================================================================
    # All the functional methods remain the same as before...
    # (Including all methods from toggle_demo_mode onwards)
    # ============================================================================
    
    def toggle_demo_mode(self):
        """Toggle between demo and real deployment mode"""
        if not NETMIKO_AVAILABLE:
            messagebox.showwarning(
                "Netmiko Not Installed",
                "Cannot switch to real mode without netmiko.\n\n"
                "Install with: pip install netmiko paramiko"
            )
            return
        
        self.demo_mode = not self.demo_mode
        mode = "DEMO MODE" if self.demo_mode else "REAL MODE"
        color = "yellow" if self.demo_mode else "green"
        
        self.mode_label.configure(text=mode, text_color=color)
        self.log_message(f"Switched to {mode}", "INFO")
        
        if self.demo_mode:
            self.log_message("⚠️ Deployments will be simulated", "WARNING")
        else:
            self.log_message("✅ Real device deployments enabled", "INFO")
        
    def on_model_selected(self, choice):
        """Handle device model selection"""
        if choice in DEVICE_MODELS:
            self.selected_model = DEVICE_MODELS[choice]
            
            # Update credentials
            self.username_entry.delete(0, tk.END)
            self.username_entry.insert(0, self.selected_model.default_username)
            self.password_entry.delete(0, tk.END)
            self.password_entry.insert(0, self.selected_model.default_password)
            
            # Update device info display
            self.update_device_info()
            self.log_message(f"Selected model: {choice}", "INFO")
            
    def update_device_info(self):
        """Update device information display"""
        # Clear existing info
        for widget in self.device_info_frame.winfo_children():
            widget.destroy()
        
        if self.selected_model:
            # Model icon and name
            header = ctk.CTkLabel(
                self.device_info_frame,
                text=f"{self.selected_model.icon} {self.selected_model.model}",
                font=ctk.CTkFont(size=13, weight="bold")
            )
            header.pack(pady=(5, 3))
            
            # Vendor
            vendor = ctk.CTkLabel(
                self.device_info_frame,
                text=f"Vendor: {self.selected_model.vendor}",
                font=ctk.CTkFont(size=11),
                text_color="gray"
            )
            vendor.pack(pady=2)
            
            # Capabilities
            if self.selected_model.capabilities:
                cap_text = "Features: " + ", ".join(self.selected_model.capabilities[:3])
                if len(self.selected_model.capabilities) > 3:
                    cap_text += "..."
                capabilities = ctk.CTkLabel(
                    self.device_info_frame,
                    text=cap_text,
                    font=ctk.CTkFont(size=10),
                    text_color="lightblue",
                    wraplength=260
                )
                capabilities.pack(pady=(2, 5))
    
    def load_config(self):
        """Load configuration file"""
        file_path = filedialog.askopenfilename(
            title="Select Configuration File",
            filetypes=[
                ("Text files", "*.txt"),
                ("Config files", "*.cfg *.conf"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    config_content = f.read()
                
                self.config_file_path = file_path
                self.config_editor.delete("1.0", tk.END)
                self.config_editor.insert("1.0", config_content)
                
                self.log_message(f"Loaded configuration: {os.path.basename(file_path)}", "INFO")
                self.update_status(f"Config loaded: {os.path.basename(file_path)}")
                
                # Switch to config tab
                self.tabview.set("📝 Configuration")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load config: {str(e)}")
                self.log_message(f"Error loading config: {str(e)}", "ERROR")
    
    def save_config(self):
        """Save configuration file"""
        if self.config_file_path:
            file_path = self.config_file_path
        else:
            file_path = filedialog.asksaveasfilename(
                title="Save Configuration File",
                defaultextension=".txt",
                filetypes=[
                    ("Text files", "*.txt"),
                    ("Config files", "*.cfg"),
                    ("All files", "*.*")
                ]
            )
        
        if file_path:
            try:
                config_content = self.config_editor.get("1.0", tk.END)
                with open(file_path, 'w') as f:
                    f.write(config_content)
                
                self.config_file_path = file_path
                self.log_message(f"Saved configuration: {os.path.basename(file_path)}", "INFO")
                self.update_status(f"Config saved: {os.path.basename(file_path)}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save config: {str(e)}")
                self.log_message(f"Error saving config: {str(e)}", "ERROR")
    
    def load_inventory(self):
        """Load device inventory file"""
        file_path = filedialog.askopenfilename(
            title="Select Inventory File",
            filetypes=[
                ("CSV files", "*.csv"),
                ("Excel files", "*.xlsx *.xls"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                # Load based on file type
                if file_path.endswith('.csv'):
                    df = pd.read_csv(file_path)
                else:
                    df = pd.read_excel(file_path)
                
                # Clear existing devices
                self.devices = []
                for item in self.devices_tree.get_children():
                    self.devices_tree.delete(item)
                
                # Add devices to tree
                for idx, row in df.iterrows():
                    device = {
                        'id': idx + 1,
                        'ip': row.get('ip', ''),
                        'hostname': row.get('hostname', f'Device_{idx+1}'),
                        'model': row.get('model', self.model_var.get()),
                        'username': row.get('username', self.username_entry.get()),
                        'password': row.get('password', self.password_entry.get()),
                        'status': 'Ready'
                    }
                    
                    self.devices.append(device)
                    
                    # Add to treeview
                    self.devices_tree.insert(
                        "",
                        "end",
                        text=str(device['id']),
                        values=(
                            device['ip'],
                            device['hostname'],
                            device['model'],
                            device['status'],
                            device['username']
                        )
                    )
                
                self.inventory_file_path = file_path
                self.stats['total'] = len(self.devices)
                self.stats['pending'] = len(self.devices)
                self.update_dashboard()
                
                self.log_message(f"Loaded {len(self.devices)} devices from inventory", "INFO")
                self.update_status(f"Loaded {len(self.devices)} devices")
                
                # Switch to devices tab
                self.tabview.set("🖥️ Devices")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load inventory: {str(e)}")
                self.log_message(f"Error loading inventory: {str(e)}", "ERROR")
    
    def add_device(self):
        """Add a new device manually"""
        dialog = DeviceDialog(self, title="Add Device", model=self.selected_model)
        self.wait_window(dialog)
        
        if dialog.result:
            device = dialog.result
            device['id'] = len(self.devices) + 1
            device['status'] = 'Ready'
            
            self.devices.append(device)
            
            # Add to treeview
            self.devices_tree.insert(
                "",
                "end",
                text=str(device['id']),
                values=(
                    device['ip'],
                    device['hostname'],
                    device['model'],
                    device['status'],
                    device['username']
                )
            )
            
            self.stats['total'] = len(self.devices)
            self.stats['pending'] = len(self.devices)
            self.update_dashboard()
            
            self.log_message(f"Added device: {device['hostname']} ({device['ip']})", "INFO")
    
    def edit_device(self):
        """Edit selected device"""
        selection = self.devices_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a device to edit")
            return
        
        item = selection[0]
        device_id = int(self.devices_tree.item(item)['text'])
        device = self.devices[device_id - 1]
        
        dialog = DeviceDialog(self, title="Edit Device", device=device, model=self.selected_model)
        self.wait_window(dialog)
        
        if dialog.result:
            # Update device
            self.devices[device_id - 1].update(dialog.result)
            
            # Update treeview
            self.devices_tree.item(
                item,
                values=(
                    dialog.result['ip'],
                    dialog.result['hostname'],
                    dialog.result['model'],
                    device['status'],
                    dialog.result['username']
                )
            )
            
            self.log_message(f"Updated device: {dialog.result['hostname']}", "INFO")
    
    def delete_device(self):
        """Delete selected devices"""
        selection = self.devices_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select device(s) to delete")
            return
        
        if messagebox.askyesno("Confirm Delete", f"Delete {len(selection)} device(s)?"):
            for item in selection:
                self.devices_tree.delete(item)
            
            # Rebuild devices list
            self.devices = []
            for item in self.devices_tree.get_children():
                values = self.devices_tree.item(item)['values']
                self.devices.append({
                    'id': len(self.devices) + 1,
                    'ip': values[0],
                    'hostname': values[1],
                    'model': values[2],
                    'status': values[3],
                    'username': values[4],
                    'password': self.password_entry.get()
                })
            
            self.stats['total'] = len(self.devices)
            self.update_dashboard()
            
            self.log_message(f"Deleted {len(selection)} device(s)", "INFO")
    
    def test_selected_device(self):
        """Test connectivity to selected device"""
        selection = self.devices_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a device to test")
            return
        
        item = selection[0]
        device_id = int(self.devices_tree.item(item)['text'])
        device = self.devices[device_id - 1]
        
        self.test_device_connectivity(device)
    
    def test_device_connectivity(self, device):
        """Test connectivity to a specific device"""
        self.update_status(f"Testing connectivity to {device['hostname']}...")
        self.log_message(f"Testing connectivity to {device['ip']}...", "INFO")
        
        # Run test in thread
        thread = threading.Thread(target=self._test_connectivity_thread, args=(device,))
        thread.daemon = True
        thread.start()
    
    def _test_connectivity_thread(self, device):
        """Test connectivity in background thread"""
        try:
            # First try actual SSH connectivity if netmiko is available and not in demo mode
            if NETMIKO_AVAILABLE and not self.demo_mode:
                try:
                    self.after(0, self.log_message, f"🔌 Testing SSH connectivity to {device['ip']}...", "INFO")
                    
                    connection_params = {
                        'device_type': 'autodetect',
                        'host': device['ip'],
                        'username': device.get('username', 'admin'),
                        'password': device.get('password', ''),
                        'port': device.get('port', 22),
                        'timeout': 10,
                        'global_delay_factor': 1,
                    }
                    
                    # Test connection
                    connection = ConnectHandler(**connection_params)
                    connection.disconnect()
                    
                    self.after(0, self.log_message, f"✅ SSH to {device['hostname']} successful", "INFO")
                    self.after(0, self.update_status, f"Device {device['hostname']} is reachable via SSH")
                    return
                    
                except NetmikoTimeoutException:
                    self.after(0, self.log_message, f"⏱️ SSH timeout to {device['hostname']}", "WARNING")
                except NetmikoAuthenticationException:
                    self.after(0, self.log_message, f"🔐 SSH auth failed for {device['hostname']}", "WARNING")
                except Exception as e:
                    self.after(0, self.log_message, f"SSH test failed: {str(e)}", "DEBUG")
            
            # Fallback to ping test
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            command = ['ping', param, '1', device['ip']]
            result = subprocess.run(command, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                self.after(0, self.log_message, f"✅ Ping to {device['hostname']} successful", "INFO")
                self.after(0, self.update_status, f"Device {device['hostname']} is reachable (ping only)")
            else:
                self.after(0, self.log_message, f"❌ {device['hostname']} is not reachable", "WARNING")
                self.after(0, self.update_status, f"Device {device['hostname']} is not reachable")
                
        except Exception as e:
            self.after(0, self.log_message, f"Error testing {device['hostname']}: {str(e)}", "ERROR")
            self.after(0, self.update_status, "Connectivity test failed")
    
    def test_connectivity(self):
        """Test connectivity to all devices"""
        if not self.devices:
            messagebox.showwarning("No Devices", "Please load device inventory first")
            return
        
        self.log_message("Starting connectivity test for all devices...", "INFO")
        
        for device in self.devices:
            self.test_device_connectivity(device)
    
    def validate_config(self):
        """Validate configuration syntax"""
        config_content = self.config_editor.get("1.0", tk.END).strip()
        
        if not config_content:
            messagebox.showwarning("No Configuration", "Please load or enter a configuration first")
            return
        
        # Basic validation checks
        errors = []
        warnings = []
        
        lines = config_content.split('\n')
        
        # Check for required elements
        has_hostname = any('hostname' in line.lower() for line in lines)
        if not has_hostname:
            warnings.append("No hostname configuration found")
        
        # Check for common syntax errors
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if line and not line.startswith('!'):
                # Check for unclosed quotes
                if line.count('"') % 2 != 0:
                    errors.append(f"Line {i}: Unclosed quotes")
                
                # Check for tabs (should use spaces)
                if '\t' in line:
                    warnings.append(f"Line {i}: Contains tabs (use spaces instead)")
        
        # Show results
        if errors:
            message = "Configuration has errors:\n\n" + "\n".join(errors)
            messagebox.showerror("Validation Failed", message)
            self.log_message("Configuration validation failed", "ERROR")
        elif warnings:
            message = "Configuration has warnings:\n\n" + "\n".join(warnings)
            messagebox.showwarning("Validation Warnings", message)
            self.log_message("Configuration validated with warnings", "WARNING")
        else:
            messagebox.showinfo("Validation Successful", "Configuration is valid!")
            self.log_message("Configuration validated successfully", "INFO")
    
    def start_deployment(self):
        """Start deployment process"""
        # Validate inputs
        if not self.selected_model:
            messagebox.showwarning("No Model", "Please select a device model")
            return
        
        if not self.devices:
            messagebox.showwarning("No Devices", "Please load device inventory")
            return
        
        config_content = self.config_editor.get("1.0", tk.END).strip()
        if not config_content:
            messagebox.showwarning("No Configuration", "Please load configuration")
            return
        
        # Show warning if in demo mode
        mode_msg = ""
        if self.demo_mode:
            mode_msg = "\n\n⚠️ DEMO MODE: Deployments will be simulated"
        
        # Confirm deployment
        if not messagebox.askyesno(
            "Confirm Deployment",
            f"Deploy configuration to {len(self.devices)} devices?\n\n"
            f"Model: {self.selected_model.model}\n"
            f"Username: {self.username_entry.get()}"
            f"{mode_msg}"
        ):
            return
        
        # Reset statistics
        self.stats = {
            'total': len(self.devices),
            'successful': 0,
            'failed': 0,
            'pending': len(self.devices),
            'in_progress': 0
        }
        
        # Clear previous results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # Update UI
        self.deployment_running = True
        self.deploy_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.overall_progress.set(0)
        
        # Switch to deployment tab
        self.tabview.set("📈 Deployment")
        
        # Start deployment thread
        self.deployment_thread = threading.Thread(target=self._deployment_worker)
        self.deployment_thread.daemon = True
        self.deployment_thread.start()
        
        self.log_message(f"Deployment started in {'DEMO' if self.demo_mode else 'REAL'} mode", "INFO")
        self.update_status("Deployment in progress...")
        self.connection_indicator.configure(text="● Deploying", text_color="green")
    
    def _deployment_worker(self):
        """Worker thread for deployment"""
        config_content = self.config_editor.get("1.0", tk.END).strip()
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        for i, device in enumerate(self.devices):
            if not self.deployment_running:
                break
            
            # Update progress
            self.stats['in_progress'] = 1
            self.stats['pending'] -= 1
            self.after(0, self.update_dashboard)
            
            # Deploy to device
            result = self.deploy_to_device(device, config_content, username, password)
            
            # Update statistics
            if result['status'] == 'Success':
                self.stats['successful'] += 1
            else:
                self.stats['failed'] += 1
            self.stats['in_progress'] = 0
            
            # Add result to tree
            self.after(0, self._add_deployment_result, result)
            
            # Update progress
            progress = (i + 1) / len(self.devices)
            self.after(0, self.overall_progress.set, progress)
            self.after(0, self.overall_progress_label.configure, 
                      {'text': f"Overall Progress: {int(progress * 100)}%"})
            self.after(0, self.update_dashboard)
            
            # Small delay between devices
            time.sleep(0.5)
        
        # Deployment complete
        self.after(0, self._deployment_complete)
    
    def deploy_to_device(self, device, config, username, password):
        """Deploy configuration to a single device"""
        result = {
            'device': device['hostname'],
            'ip': device['ip'],
            'status': 'Failed',
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'message': ''
        }
        
        try:
            # Check if we're in demo mode or netmiko is not available
            if self.demo_mode or not NETMIKO_AVAILABLE:
                # DEMO MODE - Simulated deployment
                self.log_message(f"🎮 DEMO: Simulating deployment to {device['hostname']}", "INFO")
                time.sleep(random.uniform(1, 3))
                
                # Random success/failure for demo
                if random.random() > 0.1:  # 90% success rate
                    result['status'] = 'Success'
                    result['message'] = 'Configuration deployed successfully (DEMO)'
                else:
                    result['status'] = 'Failed'
                    result['message'] = 'Connection timeout (DEMO)'
            else:
                # REAL DEPLOYMENT using Netmiko
                self.log_message(f"🔌 Connecting to {device['hostname']} ({device['ip']})...", "INFO")
                
                # Build connection parameters
                connection_params = {
                    'device_type': self.selected_model.device_type if self.selected_model else 'cisco_ios',
                    'host': device['ip'],
                    'username': username or device.get('username', 'admin'),
                    'password': password or device.get('password', ''),
                    'port': device.get('port', 22),
                    'timeout': 30,
                    'global_delay_factor': 2,
                }
                
                # Add enable password if needed
                if self.selected_model and self.selected_model.default_enable:
                    connection_params['secret'] = self.selected_model.default_enable
                
                # Establish connection
                self.log_message(f"Establishing SSH connection to {device['ip']}...", "DEBUG")
                connection = ConnectHandler(**connection_params)
                
                # Enter enable mode if required
                if not connection.check_enable_mode():
                    connection.enable()
                
                # Send configuration
                self.log_message(f"Sending configuration to {device['hostname']}...", "INFO")
                
                # Split config into lines and send
                config_lines = [line.strip() for line in config.split('\n') 
                               if line.strip() and not line.strip().startswith('!')]
                
                if config_lines:
                    output = connection.send_config_set(config_lines)
                    
                    # Save configuration
                    save_commands = {
                        'cisco_ios': 'write memory',
                        'cisco_xe': 'write memory',
                        'cisco_xr': 'commit',
                        'cisco_nxos': 'copy running-config startup-config',
                        'aruba_osswitch': 'write memory',
                        'juniper_junos': 'commit',
                        'huawei': 'save',
                        'fortinet': 'end\nconfig system global\nset cfg-save automatic\nend'
                    }
                    
                    save_cmd = save_commands.get(connection_params['device_type'], 'write memory')
                    connection.send_command(save_cmd)
                    
                    # Disconnect
                    connection.disconnect()
                    
                    # Success
                    result['status'] = 'Success'
                    result['message'] = 'Configuration deployed and saved successfully'
                    self.log_message(f"✅ Successfully deployed to {device['hostname']}", "INFO")
                else:
                    result['status'] = 'Failed'
                    result['message'] = 'No valid configuration lines to deploy'
                    self.log_message(f"❌ No valid config for {device['hostname']}", "WARNING")
                    
        except Exception as e:
            # Handle specific netmiko exceptions if available
            if NETMIKO_AVAILABLE:
                try:
                    if isinstance(e, NetmikoTimeoutException):
                        result['message'] = 'Connection timeout - Device unreachable'
                        self.log_message(f"❌ Timeout connecting to {device['hostname']}", "ERROR")
                    elif isinstance(e, NetmikoAuthenticationException):
                        result['message'] = 'Authentication failed - Check credentials'
                        self.log_message(f"❌ Authentication failed for {device['hostname']}", "ERROR")
                    else:
                        result['message'] = f'Error: {str(e)}'
                        self.log_message(f"❌ Error deploying to {device['hostname']}: {str(e)}", "ERROR")
                except:
                    result['message'] = f'Error: {str(e)}'
                    self.log_message(f"❌ Error deploying to {device['hostname']}: {str(e)}", "ERROR")
            else:
                result['message'] = f'Error: {str(e)}'
                self.log_message(f"❌ Error deploying to {device['hostname']}: {str(e)}", "ERROR")
        
        return result
    
    def _add_deployment_result(self, result):
        """Add deployment result to tree"""
        # Determine tag for coloring
        tag = "success" if result['status'] == 'Success' else "failed"
        
        # Add to tree
        self.results_tree.insert(
            "",
            "end",
            values=(
                result['device'],
                result['ip'],
                result['status'],
                result['time'],
                result['message']
            ),
            tags=(tag,)
        )
        
        # Configure tags
        self.results_tree.tag_configure("success", foreground="green")
        self.results_tree.tag_configure("failed", foreground="red")
        
        # Auto-scroll to latest
        self.results_tree.yview_moveto(1)
    
    def _deployment_complete(self):
        """Handle deployment completion"""
        self.deployment_running = False
        self.deploy_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        
        # Show summary
        mode_text = " (DEMO)" if self.demo_mode else ""
        message = (
            f"Deployment Complete{mode_text}!\n\n"
            f"Total: {self.stats['total']}\n"
            f"Successful: {self.stats['successful']}\n"
            f"Failed: {self.stats['failed']}"
        )
        
        messagebox.showinfo("Deployment Complete", message)
        
        self.log_message(f"Deployment complete: {self.stats['successful']} successful, {self.stats['failed']} failed", "INFO")
        self.update_status("Deployment complete")
        self.connection_indicator.configure(text="● Idle", text_color="gray")
    
    def stop_deployment(self):
        """Stop deployment process"""
        if messagebox.askyesno("Confirm Stop", "Stop the deployment process?"):
            self.deployment_running = False
            self.log_message("Deployment stopped by user", "WARNING")
            self.update_status("Deployment stopped")
    
    def update_dashboard(self):
        """Update dashboard statistics and charts"""
        # Update stat cards
        for key, card in self.stat_cards.items():
            if key in self.stats:
                card.value_label.configure(text=str(self.stats[key]))
        
        # Update charts
        self.update_pie_chart()
        self.update_progress_chart()
    
    def update_pie_chart(self):
        """Update pie chart"""
        if not MATPLOTLIB_AVAILABLE:
            return
            
        self.pie_ax.clear()
        
        # Data
        sizes = []
        labels = []
        colors = []
        
        if self.stats['successful'] > 0:
            sizes.append(self.stats['successful'])
            labels.append('Successful')
            colors.append('#2ecc71')
        
        if self.stats['failed'] > 0:
            sizes.append(self.stats['failed'])
            labels.append('Failed')
            colors.append('#e74c3c')
        
        if self.stats['pending'] > 0:
            sizes.append(self.stats['pending'])
            labels.append('Pending')
            colors.append('#95a5a6')
        
        if self.stats['in_progress'] > 0:
            sizes.append(self.stats['in_progress'])
            labels.append('In Progress')
            colors.append('#f39c12')
        
        if sizes:
            self.pie_ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                           startangle=90, textprops={'color': 'white'})
        else:
            # No data
            self.pie_ax.text(0.5, 0.5, 'No Data', ha='center', va='center',
                           transform=self.pie_ax.transAxes, color='white', size=16)
        
        self.pie_ax.set_title('Deployment Status', color='white', pad=20)
        self.pie_fig.patch.set_facecolor('#212121')
        self.pie_ax.set_facecolor('#212121')
        
        # Only draw if canvas exists
        if hasattr(self, 'pie_canvas'):
            self.pie_canvas.draw()
    
    def update_progress_chart(self):
        """Update progress chart"""
        if not MATPLOTLIB_AVAILABLE:
            # Update fallback label if it exists
            if hasattr(self, 'prog_label'):
                if self.stats['total'] > 0:
                    completed = self.stats['successful'] + self.stats['failed']
                    progress = (completed / self.stats['total']) * 100
                    self.prog_label.configure(text=f"📈 Progress: {progress:.1f}%")
            return
            
        self.prog_ax.clear()
        
        # Calculate progress
        if self.stats['total'] > 0:
            completed = self.stats['successful'] + self.stats['failed']
            progress = (completed / self.stats['total']) * 100
        else:
            progress = 0
        
        # Create horizontal bar
        self.prog_ax.barh(['Progress'], [progress], color='#3498db', height=0.5)
        self.prog_ax.barh(['Progress'], [100 - progress], left=[progress], 
                         color='#34495e', height=0.5)
        
        self.prog_ax.set_xlim(0, 100)
        self.prog_ax.set_xlabel('Percentage Complete', color='white')
        self.prog_ax.set_title('Deployment Progress', color='white', pad=20)
        self.prog_ax.tick_params(colors='white')
        
        # Add percentage text
        self.prog_ax.text(50, 0, f'{progress:.1f}%', ha='center', va='center',
                         color='white', fontsize=16, fontweight='bold')
        
        self.prog_fig.patch.set_facecolor('#212121')
        self.prog_ax.set_facecolor('#212121')
        
        # Only draw if canvas exists
        if hasattr(self, 'prog_canvas'):
            self.prog_canvas.draw()
    
    def export_results(self):
        """Export deployment results"""
        if not self.deployment_results and not self.results_tree.get_children():
            messagebox.showwarning("No Results", "No deployment results to export")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Export Results",
            defaultextension=".csv",
            filetypes=[
                ("CSV files", "*.csv"),
                ("Excel files", "*.xlsx"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                # Collect results from tree
                results = []
                for item in self.results_tree.get_children():
                    values = self.results_tree.item(item)['values']
                    results.append({
                        'Device': values[0],
                        'IP': values[1],
                        'Status': values[2],
                        'Time': values[3],
                        'Message': values[4]
                    })
                
                # Save based on file type
                df = pd.DataFrame(results)
                if file_path.endswith('.csv'):
                    df.to_csv(file_path, index=False)
                else:
                    df.to_excel(file_path, index=False)
                
                self.log_message(f"Exported results to {os.path.basename(file_path)}", "INFO")
                messagebox.showinfo("Export Successful", f"Results exported to {os.path.basename(file_path)}")
                
            except Exception as e:
                messagebox.showerror("Export Failed", f"Failed to export results: {str(e)}")
                self.log_message(f"Export failed: {str(e)}", "ERROR")
    
    def clear_logs(self):
        """Clear log viewer"""
        self.log_viewer.delete("1.0", tk.END)
        self.log_message("Logs cleared", "INFO")
    
    def export_logs(self):
        """Export logs to file"""
        file_path = filedialog.asksaveasfilename(
            title="Export Logs",
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("Log files", "*.log"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                log_content = self.log_viewer.get("1.0", tk.END)
                with open(file_path, 'w') as f:
                    f.write(log_content)
                
                messagebox.showinfo("Export Successful", f"Logs exported to {os.path.basename(file_path)}")
                
            except Exception as e:
                messagebox.showerror("Export Failed", f"Failed to export logs: {str(e)}")
    
    def open_settings(self):
        """Open settings dialog"""
        dialog = SettingsDialog(self)
        self.wait_window(dialog)
    
    def show_documentation(self):
        """Show documentation"""
        messagebox.showinfo(
            "Documentation",
            "Network Deployment Suite v3.0\n\n"
            "Quick Start:\n"
            "1. Select device model from sidebar\n"
            "2. Load device inventory (CSV/Excel)\n"
            "3. Load configuration template\n"
            "4. Review and edit as needed\n"
            "5. Click 'Start Deployment'\n\n"
            "For detailed documentation, visit:\n"
            "https://docs.example.com/network-deployment"
        )
    
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About",
            "Network Deployment Suite v3.0\n\n"
            "Professional Network Configuration Tool\n"
            "© 2024 Network Automation Team\n\n"
            "Built with Python and CustomTkinter\n"
            "Supports multiple vendor devices"
        )
    
    def log_message(self, message, level="INFO"):
        """Add message to log viewer"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        self.log_viewer.insert(tk.END, log_entry)
        self.log_viewer.see(tk.END)
        
        # Also log to file
        logging.log(getattr(logging, level), message)
    
    def update_status(self, message):
        """Update status bar"""
        self.status_text.configure(text=message)
    
    def process_queue(self):
        """Process messages from deployment queue"""
        try:
            while True:
                message = self.deployment_queue.get_nowait()
                # Process message
                if message['type'] == 'log':
                    self.log_message(message['text'], message.get('level', 'INFO'))
                elif message['type'] == 'status':
                    self.update_status(message['text'])
                elif message['type'] == 'progress':
                    self.overall_progress.set(message['value'])
        except queue.Empty:
            pass
        
        # Schedule next check
        self.after(100, self.process_queue)