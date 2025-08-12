
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

class SettingsDialog(ctk.CTkToplevel):
    """Settings dialog"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.title("Settings")
        self.geometry("500x400")
        self.resizable(False, False)
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create settings widgets"""
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="Application Settings",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=20)
        
        # Settings notebook
        notebook = ctk.CTkTabview(self)
        notebook.pack(padx=20, pady=10, fill="both", expand=True)
        
        # Add tabs
        notebook.add("General")
        notebook.add("Connection")
        notebook.add("Advanced")
        
        # General settings
        general_frame = notebook.tab("General")
        
        ctk.CTkLabel(general_frame, text="Theme:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        theme_combo = ctk.CTkComboBox(
            general_frame,
            values=["Dark", "Light", "System"],
            width=200
        )
        theme_combo.grid(row=0, column=1, padx=10, pady=5)
        theme_combo.set("Dark")
        
        ctk.CTkLabel(general_frame, text="Log Level:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        log_combo = ctk.CTkComboBox(
            general_frame,
            values=["DEBUG", "INFO", "WARNING", "ERROR"],
            width=200
        )
        log_combo.grid(row=1, column=1, padx=10, pady=5)
        log_combo.set("INFO")
        
        # Connection settings
        conn_frame = notebook.tab("Connection")
        
        ctk.CTkLabel(conn_frame, text="Timeout (seconds):").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        timeout_entry = ctk.CTkEntry(conn_frame, width=200)
        timeout_entry.grid(row=0, column=1, padx=10, pady=5)
        timeout_entry.insert(0, "30")
        
        ctk.CTkLabel(conn_frame, text="Max Threads:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        threads_entry = ctk.CTkEntry(conn_frame, width=200)
        threads_entry.grid(row=1, column=1, padx=10, pady=5)
        threads_entry.insert(0, "10")
        
        ctk.CTkLabel(conn_frame, text="Retry Attempts:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        retry_entry = ctk.CTkEntry(conn_frame, width=200)
        retry_entry.grid(row=2, column=1, padx=10, pady=5)
        retry_entry.insert(0, "3")
        
        # Advanced settings
        adv_frame = notebook.tab("Advanced")
        
        auto_save = ctk.CTkCheckBox(adv_frame, text="Auto-save configuration")
        auto_save.pack(padx=10, pady=5, anchor="w")
        
        verify_ssl = ctk.CTkCheckBox(adv_frame, text="Verify SSL certificates")
        verify_ssl.pack(padx=10, pady=5, anchor="w")
        
        debug_mode = ctk.CTkCheckBox(adv_frame, text="Enable debug mode")
        debug_mode.pack(padx=10, pady=5, anchor="w")
        
        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(pady=20)
        
        save_btn = ctk.CTkButton(
            button_frame,
            text="Save",
            command=self.save_settings,
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
    
    def save_settings(self):
        """Save settings"""
        # In a real application, save settings to file or database
        messagebox.showinfo("Settings", "Settings saved successfully!")
        self.destroy()
