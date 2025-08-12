#!/usr/bin/env python3
"""
Advanced Network Device Configuration Deployment GUI
Professional Network Management Tool with Modern UI
Author: Network Automation Team
Version: 3.0
"""

import sys
import os
import logging
import traceback
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from enum import Enum


# ================================================================================
# CONSTANTS AND CONFIGURATION
# ================================================================================

APP_NAME = "Network Deployment Suite"
APP_VERSION = "3.0"
APP_AUTHOR = "Network Automation Team"

# Configuration defaults
DEFAULT_CONFIG = {
    "logging": {
        "level": "INFO",
        "max_log_files": 30,
        "log_format": "%(asctime)s - [%(levelname)8s] - %(name)s - %(message)s",
        "date_format": "%Y-%m-%d %H:%M:%S"
    },
    "appearance": {
        "theme": "dark",
        "color_theme": "blue"
    },
    "paths": {
        "logs_dir": "logs",
        "config_dir": "config",
        "templates_dir": "templates",
        "exports_dir": "exports"
    }
}


# ================================================================================
# CUSTOM EXCEPTIONS
# ================================================================================

class NetworkDeploymentError(Exception):
    """Base exception for Network Deployment Suite"""
    pass


class DependencyError(NetworkDeploymentError):
    """Raised when required dependencies are missing"""
    pass


class ConfigurationError(NetworkDeploymentError):
    """Raised when configuration is invalid"""
    pass


class ModuleImportError(NetworkDeploymentError):
    """Raised when application modules cannot be imported"""
    pass


# ================================================================================
# LOGGER SETUP CLASS
# ================================================================================

class AppLogger:
    """Custom logger setup for the application"""
    
    def __init__(self, name: str = APP_NAME, config: Dict = None):
        """
        Initialize the application logger
        
        Args:
            name: Logger name
            config: Logger configuration dictionary
        """
        self.name = name
        self.config = config or DEFAULT_CONFIG["logging"]
        self.logger = None
        self.log_dir = None
        self.log_file = None
        
        self._setup_logger()
    
    def _setup_logger(self) -> None:
        """Set up the logger with file and console handlers"""
        try:
            # Create logs directory
            self.log_dir = Path(DEFAULT_CONFIG["paths"]["logs_dir"])
            self.log_dir.mkdir(exist_ok=True)
            
            # Create log filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.log_file = self.log_dir / f"network_deployment_{timestamp}.log"
            
            # Create logger
            self.logger = logging.getLogger(self.name)
            self.logger.setLevel(getattr(logging, self.config["level"]))
            
            # Clear existing handlers
            self.logger.handlers.clear()
            
            # Create formatters
            file_formatter = logging.Formatter(
                self.config["log_format"],
                datefmt=self.config["date_format"]
            )
            console_formatter = logging.Formatter(
                "%(levelname)s - %(message)s"
            )
            
            # File handler
            file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
            
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
            
            # Log initialization
            self.logger.info("=" * 70)
            self.logger.info(f"{APP_NAME} v{APP_VERSION} - Logger Initialized")
            self.logger.info(f"Log file: {self.log_file}")
            self.logger.info("=" * 70)
            
        except Exception as e:
            print(f"Failed to setup logger: {e}")
            sys.exit(1)
    
    def get_logger(self) -> logging.Logger:
        """Get the logger instance"""
        return self.logger
    
    def cleanup_old_logs(self, max_files: int = None) -> None:
        """
        Clean up old log files
        
        Args:
            max_files: Maximum number of log files to keep
        """
        max_files = max_files or self.config.get("max_log_files", 30)
        
        try:
            log_files = sorted(self.log_dir.glob("network_deployment_*.log"))
            if len(log_files) > max_files:
                for old_file in log_files[:-max_files]:
                    old_file.unlink()
                    self.logger.debug(f"Deleted old log file: {old_file}")
        except Exception as e:
            self.logger.warning(f"Failed to cleanup old logs: {e}")


# ================================================================================
# DEPENDENCY CHECKER CLASS
# ================================================================================

class DependencyChecker:
    """Check and validate application dependencies"""
    
    def __init__(self, logger: logging.Logger):
        """
        Initialize dependency checker
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
        self.required_packages = {
            'customtkinter': 'customtkinter',
            'pandas': 'pandas',
            'PIL': 'pillow',
            'numpy': 'numpy'
        }
        self.optional_packages = {
            'matplotlib': ('matplotlib', 'Charts and visualizations'),
            'netmiko': ('netmiko', 'Network device connectivity'),
            'paramiko': ('paramiko', 'SSH connections')
        }
        self.missing_required = []
        self.missing_optional = []
        self.feature_flags = {}
    
    def check_required(self) -> bool:
        """
        Check required dependencies
        
        Returns:
            True if all required dependencies are present
        """
        self.logger.info("Checking required dependencies...")
        
        for module, package in self.required_packages.items():
            try:
                __import__(module)
                self.logger.debug(f"✓ {package} is installed")
            except ImportError:
                self.missing_required.append(package)
                self.logger.error(f"✗ {package} is NOT installed (REQUIRED)")
        
        if self.missing_required:
            self.logger.error(f"Missing required packages: {', '.join(self.missing_required)}")
            return False
        
        self.logger.info("All required dependencies are installed ✓")
        return True
    
    def check_optional(self) -> Dict[str, bool]:
        """
        Check optional dependencies
        
        Returns:
            Dictionary of feature flags
        """
        self.logger.info("Checking optional dependencies...")
        
        for module, (package, feature) in self.optional_packages.items():
            try:
                if module == 'matplotlib':
                    import matplotlib
                    matplotlib.use('TkAgg')
                else:
                    __import__(module)
                self.feature_flags[module] = True
                self.logger.debug(f"✓ {package} is installed ({feature})")
            except ImportError:
                self.feature_flags[module] = False
                self.missing_optional.append((package, feature))
                self.logger.warning(f"⚠ {package} is not installed ({feature} will be disabled)")
        
        if self.missing_optional:
            self.logger.info("Optional features unavailable:")
            for package, feature in self.missing_optional:
                self.logger.info(f"  - {feature}: install {package}")
        
        return self.feature_flags
    
    def get_install_command(self) -> str:
        """Get pip install command for missing packages"""
        all_missing = self.missing_required + [pkg for pkg, _ in self.missing_optional]
        if all_missing:
            return f"pip install {' '.join(all_missing)}"
        return ""
    
    def print_dependency_report(self) -> None:
        """Print a formatted dependency report"""
        print("\n" + "=" * 70)
        print(f"{APP_NAME} - Dependency Report")
        print("=" * 70)
        
        if self.missing_required:
            print("\n❌ MISSING REQUIRED PACKAGES:")
            for package in self.missing_required:
                print(f"   - {package}")
            print(f"\n📦 Install with: pip install {' '.join(self.missing_required)}")
        else:
            print("\n✅ All required packages installed")
        
        if self.missing_optional:
            print("\n⚠️  OPTIONAL PACKAGES (for additional features):")
            for package, feature in self.missing_optional:
                print(f"   - {package}: {feature}")
        
        print("=" * 70 + "\n")


# ================================================================================
# CONFIGURATION MANAGER CLASS
# ================================================================================

class ConfigurationManager:
    """Manage application configuration"""
    
    def __init__(self, logger: logging.Logger):
        """
        Initialize configuration manager
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
        self.config_dir = Path(DEFAULT_CONFIG["paths"]["config_dir"])
        self.config_file = self.config_dir / "settings.json"
        self.config = DEFAULT_CONFIG.copy()
        
        self._setup_directories()
        self._load_config()
    
    def _setup_directories(self) -> None:
        """Create necessary directories"""
        directories = [
            self.config_dir,
            Path(DEFAULT_CONFIG["paths"]["logs_dir"]),
            Path(DEFAULT_CONFIG["paths"]["templates_dir"]),
            Path(DEFAULT_CONFIG["paths"]["exports_dir"])
        ]
        
        for directory in directories:
            try:
                directory.mkdir(exist_ok=True)
                self.logger.debug(f"Directory ensured: {directory}")
            except Exception as e:
                self.logger.warning(f"Failed to create directory {directory}: {e}")
    
    def _load_config(self) -> None:
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
                    self.logger.info(f"Configuration loaded from {self.config_file}")
            except Exception as e:
                self.logger.warning(f"Failed to load config: {e}, using defaults")
                self._save_config()
        else:
            self._save_config()
    
    def _save_config(self) -> None:
        """Save configuration to file"""
        try:
            self.config_dir.mkdir(exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
                self.logger.debug(f"Configuration saved to {self.config_file}")
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key: str, value) -> None:
        """Set configuration value"""
        self.config[key] = value
        self._save_config()


# ================================================================================
# APPLICATION LAUNCHER CLASS
# ================================================================================

class ApplicationLauncher:
    """Main application launcher with error handling"""
    
    def __init__(self):
        """Initialize the application launcher"""
        self.logger = None
        self.config_manager = None
        self.dependency_checker = None
        self.app = None
        self.feature_flags = {}
        
        # Setup components
        self._setup_logger()
        self._setup_config()
        self._check_dependencies()
    
    def _setup_logger(self) -> None:
        """Setup application logger"""
        app_logger = AppLogger()
        self.logger = app_logger.get_logger()
        app_logger.cleanup_old_logs()
    
    def _setup_config(self) -> None:
        """Setup configuration manager"""
        self.config_manager = ConfigurationManager(self.logger)
    
    def _check_dependencies(self) -> None:
        """Check and validate dependencies"""
        self.dependency_checker = DependencyChecker(self.logger)
        
        # Check required dependencies
        if not self.dependency_checker.check_required():
            self.dependency_checker.print_dependency_report()
            self._show_error(
                "Missing Required Dependencies",
                f"Please install: {self.dependency_checker.get_install_command()}"
            )
            sys.exit(1)
        
        # Check optional dependencies
        self.feature_flags = self.dependency_checker.check_optional()
        
        # Store feature flags globally
        os.environ['MATPLOTLIB_AVAILABLE'] = str(self.feature_flags.get('matplotlib', False))
        os.environ['NETMIKO_AVAILABLE'] = str(self.feature_flags.get('netmiko', False))
    
    def _configure_appearance(self) -> None:
        """Configure application appearance"""
        try:
            import customtkinter as ctk
            
            theme = self.config_manager.get("appearance", {}).get("theme", "dark")
            color_theme = self.config_manager.get("appearance", {}).get("color_theme", "blue")
            
            ctk.set_appearance_mode(theme)
            ctk.set_default_color_theme(color_theme)
            
            self.logger.info(f"Appearance configured: {theme} mode, {color_theme} theme")
            
        except Exception as e:
            self.logger.warning(f"Failed to configure appearance: {e}")
    
    def _import_modules(self) -> bool:
        """
        Import application modules
        
        Returns:
            True if all modules imported successfully
        """
        try:
            self.logger.info("Importing application modules...")
            
            global NetworkDeploymentGUI
            from modules.NetworkDeploymentGUI import NetworkDeploymentGUI
            
            # Import other modules for validation
            from modules.DeviceDialog import DeviceDialog
            from modules.DeviceModel import DeviceModel
            from modules.SettingsDialog import SettingsDialog
            
            self.logger.info("All modules imported successfully")
            return True
            
        except ImportError as e:
            self.logger.error(f"Failed to import modules: {e}")
            self.logger.error(traceback.format_exc())
            self._show_error(
                "Module Import Error",
                f"Failed to import application modules:\n{e}\n\n"
                "Please ensure all module files are in the 'modules' directory."
            )
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error importing modules: {e}")
            self.logger.error(traceback.format_exc())
            return False
    
    def _show_error(self, title: str, message: str) -> None:
        """
        Show error message to user
        
        Args:
            title: Error title
            message: Error message
        """
        try:
            import tkinter as tk
            from tkinter import messagebox
            
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(title, message)
            root.destroy()
        except:
            print(f"\n❌ ERROR: {title}")
            print(f"   {message}")
    
    def _show_info(self, title: str, message: str) -> None:
        """
        Show info message to user
        
        Args:
            title: Info title
            message: Info message
        """
        try:
            import tkinter as tk
            from tkinter import messagebox
            
            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo(title, message)
            root.destroy()
        except:
            print(f"\n📢 {title}")
            print(f"   {message}")
    
    def launch(self) -> int:
        """
        Launch the application
        
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            # Configure appearance
            self._configure_appearance()
            
            # Import modules
            if not self._import_modules():
                return 1
            
            # Log startup info
            self.logger.info("=" * 70)
            self.logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
            self.logger.info(f"Author: {APP_AUTHOR}")
            self.logger.info(f"Python: {sys.version}")
            self.logger.info(f"Platform: {sys.platform}")
            self.logger.info("Features:")
            self.logger.info(f"  • Charts: {'✓' if self.feature_flags.get('matplotlib') else '✗'}")
            self.logger.info(f"  • Network: {'✓' if self.feature_flags.get('netmiko') else '✗'}")
            self.logger.info("=" * 70)
            
            # Create and run application
            self.app = NetworkDeploymentGUI()
            self.logger.info("Application window created")
            
            # Start main loop
            self.app.mainloop()
            
            self.logger.info("Application closed normally")
            return 0
            
        except KeyboardInterrupt:
            self.logger.info("Application interrupted by user (Ctrl+C)")
            return 0
            
        except Exception as e:
            self.logger.critical(f"Fatal error: {e}")
            self.logger.critical(traceback.format_exc())
            
            self._show_error(
                "Application Error",
                f"A fatal error occurred:\n\n{e}\n\n"
                f"Please check the log file for details:\n"
                f"{self.logger.handlers[0].baseFilename if self.logger.handlers else 'logs/'}"
            )
            return 1
    
    def cleanup(self) -> None:
        """Cleanup resources before exit"""
        try:
            if self.app:
                self.app.quit()
            self.logger.info("Cleanup completed")
        except:
            pass


# ================================================================================
# MAIN ENTRY POINT
# ================================================================================

def main() -> int:
    """
    Main entry point for the application
    
    Returns:
        Exit code
    """
    launcher = None
    
    try:
        # Create and run application launcher
        launcher = ApplicationLauncher()
        return launcher.launch()
        
    except Exception as e:
        print(f"\n❌ Critical Error: {e}")
        print(traceback.format_exc())
        return 1
        
    finally:
        if launcher:
            launcher.cleanup()


if __name__ == "__main__":
    # Set exit code
    exit_code = main()
    
    # Exit with appropriate code
    sys.exit(exit_code)