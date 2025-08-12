
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from modules.device_models_db import DEVICE_MODELS  

class DeviceDialog(ctk.CTkToplevel):
    """Dialog for adding/editing devices"""
    
    def __init__(self, parent, title="Device", device=None, model=None):
        super().__init__(parent)
        
        self.title(title)
        self.geometry("400x500")
        self.resizable(False, False)
        
        self.result = None
        self.device = device or {}
        self.model = model
        
        self.create_widgets()
        
        # Load existing values if editing
        if device:
            self.load_device_data()
    
    def create_widgets(self):
        """Create dialog widgets"""
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="Device Configuration",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=20)
        
        # Form frame
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(padx=20, pady=10, fill="both", expand=True)
        
        # IP Address
        ctk.CTkLabel(form_frame, text="IP Address:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.ip_entry = ctk.CTkEntry(form_frame, width=200)
        self.ip_entry.grid(row=0, column=1, padx=10, pady=5)
        
        # Hostname
        ctk.CTkLabel(form_frame, text="Hostname:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.hostname_entry = ctk.CTkEntry(form_frame, width=200)
        self.hostname_entry.grid(row=1, column=1, padx=10, pady=5)
        
        # Model
        ctk.CTkLabel(form_frame, text="Model:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.model_var = ctk.StringVar()
        self.model_combo = ctk.CTkComboBox(
            form_frame,
            values=list(DEVICE_MODELS.keys()),
            variable=self.model_var,
            width=200
        )
        self.model_combo.grid(row=2, column=1, padx=10, pady=5)
        
        # Username
        ctk.CTkLabel(form_frame, text="Username:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.username_entry = ctk.CTkEntry(form_frame, width=200)
        self.username_entry.grid(row=3, column=1, padx=10, pady=5)
        
        # Password
        ctk.CTkLabel(form_frame, text="Password:").grid(row=4, column=0, sticky="w", padx=10, pady=5)
        self.password_entry = ctk.CTkEntry(form_frame, width=200, show="*")
        self.password_entry.grid(row=4, column=1, padx=10, pady=5)
        
        # Enable Password (for Cisco)
        ctk.CTkLabel(form_frame, text="Enable Password:").grid(row=5, column=0, sticky="w", padx=10, pady=5)
        self.enable_entry = ctk.CTkEntry(form_frame, width=200, show="*")
        self.enable_entry.grid(row=5, column=1, padx=10, pady=5)
        
        # Port
        ctk.CTkLabel(form_frame, text="Port:").grid(row=6, column=0, sticky="w", padx=10, pady=5)
        self.port_entry = ctk.CTkEntry(form_frame, width=200)
        self.port_entry.grid(row=6, column=1, padx=10, pady=5)
        self.port_entry.insert(0, "22")
        
        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(pady=20)
        
        save_btn = ctk.CTkButton(
            button_frame,
            text="Save",
            command=self.save_device,
            width=100
        )
        save_btn.pack(side="left", padx=5)
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.destroy,
            width=100,
            fg_color="gray"
        )
        cancel_btn.pack(side="left", padx=5)
    
    def load_device_data(self):
        """Load existing device data"""
        self.ip_entry.insert(0, self.device.get('ip', ''))
        self.hostname_entry.insert(0, self.device.get('hostname', ''))
        self.model_var.set(self.device.get('model', ''))
        self.username_entry.insert(0, self.device.get('username', ''))
        self.password_entry.insert(0, self.device.get('password', ''))
        self.enable_entry.insert(0, self.device.get('enable', ''))
        self.port_entry.delete(0, tk.END)
        self.port_entry.insert(0, self.device.get('port', '22'))
    
    def save_device(self):
        """Save device configuration"""
        self.result = {
            'ip': self.ip_entry.get(),
            'hostname': self.hostname_entry.get(),
            'model': self.model_var.get(),
            'username': self.username_entry.get(),
            'password': self.password_entry.get(),
            'enable': self.enable_entry.get(),
            'port': self.port_entry.get()
        }
        
        # Validate
        if not self.result['ip']:
            messagebox.showwarning("Validation Error", "IP address is required")
            return
        
        if not self.result['hostname']:
            self.result['hostname'] = f"Device_{self.result['ip'].replace('.', '_')}"
        
        self.destroy()
