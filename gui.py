#!/usr/bin/env python3
"""
Simple Camera GUI

Graphical user interface for the simple camera application using tkinter and OpenCV.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import cv2
from PIL import Image, ImageTk
import threading
import os
import sys
from datetime import datetime
from pathlib import Path
from camera import Camera
import pyaudio
import wave


class CameraGUI:
    """GUI application for the simple camera."""

    def __init__(self, root):
        """Initialize the GUI."""
        self.root = root
        self.root.title("Simple Camera")
        
        # Get screen size and set window (not maximized)
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        width = int(screen_width * 0.8)
        height = int(screen_height * 0.75)
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.minsize(1200, 800)

        # Camera instance
        self.camera = None
        self.is_preview_running = False
        self.is_recording = False
        self.preview_thread = None
        self.stop_preview = threading.Event()

        # Output directory
        self.output_dir = Path("./captures")
        self.output_dir.mkdir(exist_ok=True)

        # Settings
        self.resolution_var = tk.StringVar(value="1280x720")
        self.fps_var = tk.StringVar(value="30")
        self.photo_format_var = tk.StringVar(value="png")
        self.video_format_var = tk.StringVar(value="avi")
        self.camera_id_var = tk.IntVar(value=0)
        
        # Audio settings
        self.mic_enabled_var = tk.BooleanVar(value=False)
        self.mic_device_var = tk.StringVar(value="Default")
        self.available_mics = []
        self._refresh_mic_devices()

        # Recording state
        self.recording_start_time = None
        self.audio_recording = None
        self.audio_frames = []
        self.is_recording_audio = False
        self.audio_stream = None
        self.audio_thread = None
        self.current_video_file = None

        # Setup UI
        self._setup_ui()

        # Bind cleanup on close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _refresh_mic_devices(self):
        """Refresh available microphone devices."""
        try:
            import pyaudio
            p = pyaudio.PyAudio()
            self.available_mics = ["Default"]
            for i in range(p.get_device_count()):
                try:
                    info = p.get_device_info_by_index(i)
                    if info.get('maxInputChannels', 0) > 0:
                        name = info.get('name', f'Device {i}')
                        self.available_mics.append(f"{i}: {name[:40]}")
                except:
                    pass
            p.terminate()
        except Exception as e:
            self.available_mics = ["Default", "No audio devices found"]

    def _setup_ui(self):
        """Setup the user interface."""
        # Main container using PanedWindow for better layout control
        self.main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel - Video preview
        left_panel = ttk.Frame(self.main_pane)
        self.main_pane.add(left_panel, weight=3)

        # Video label with fixed aspect ratio container
        self.video_frame = ttk.Frame(left_panel, relief=tk.SUNKEN, borderwidth=2)
        self.video_frame.pack(fill=tk.BOTH, expand=True)
        
        self.video_label = ttk.Label(self.video_frame, background="black")
        self.video_label.pack(fill=tk.BOTH, expand=True)

        # Status bar
        self.status_var = tk.StringVar(value="Ready - Click 'Start Camera' to begin")
        status_bar = ttk.Label(
            left_panel, textvariable=self.status_var,
            relief=tk.SUNKEN, anchor=tk.W
        )
        status_bar.pack(fill=tk.X, pady=(5, 0))

        # Right panel - Controls (fixed width)
        right_panel = ttk.Frame(self.main_pane, width=380)
        self.main_pane.add(right_panel, weight=1)

        # Camera selection
        camera_frame = ttk.LabelFrame(right_panel, text="Camera", padding=15)
        camera_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(camera_frame, text="Camera ID:").pack(anchor=tk.W)
        camera_spinbox = ttk.Spinbox(
            camera_frame, from_=0, to=10, width=10,
            textvariable=self.camera_id_var
        )
        camera_spinbox.pack(anchor=tk.W, pady=(5, 0))

        self.start_camera_btn = ttk.Button(
            camera_frame, text="📹 Start Camera", command=self._start_camera
        )
        self.start_camera_btn.pack(fill=tk.X, pady=(15, 5))

        self.stop_camera_btn = ttk.Button(
            camera_frame, text="⏹ Stop Camera", command=self._stop_camera,
            state=tk.DISABLED
        )
        self.stop_camera_btn.pack(fill=tk.X, pady=(5, 0))
        
        # Microphone controls
        mic_frame = ttk.LabelFrame(right_panel, text="Microphone", padding=15)
        mic_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(mic_frame, text="Device:").pack(anchor=tk.W)
        self.mic_combo = ttk.Combobox(
            mic_frame, textvariable=self.mic_device_var,
            values=self.available_mics, width=35, state="readonly"
        )
        self.mic_combo.pack(anchor=tk.W, pady=(5, 0))
        self.mic_combo.set("Default" if self.available_mics else "No devices")
        
        self.mic_toggle_btn = ttk.Checkbutton(
            mic_frame, text="🎤 Enable Microphone",
            variable=self.mic_enabled_var
        )
        self.mic_toggle_btn.pack(fill=tk.X, pady=(15, 0))

        # Photo controls
        photo_frame = ttk.LabelFrame(right_panel, text="Photo", padding=15)
        photo_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(photo_frame, text="Format:").pack(anchor=tk.W)
        format_combo = ttk.Combobox(
            photo_frame, textvariable=self.photo_format_var,
            values=["png", "jpg", "bmp"], width=10, state="readonly"
        )
        format_combo.pack(anchor=tk.W, pady=(5, 0))

        self.photo_btn = ttk.Button(
            photo_frame, text="📷 Take Photo", command=self._take_photo,
            state=tk.DISABLED
        )
        self.photo_btn.pack(fill=tk.X, pady=(15, 0))

        # Video controls
        video_frame = ttk.LabelFrame(right_panel, text="Video", padding=15)
        video_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(video_frame, text="FPS:").pack(anchor=tk.W)
        fps_spinbox = ttk.Spinbox(
            video_frame, from_=15, to=60, width=10,
            textvariable=self.fps_var
        )
        fps_spinbox.pack(anchor=tk.W, pady=(5, 0))
        
        ttk.Label(video_frame, text="Format: MP4 (H.264)", foreground="gray").pack(anchor=tk.W, pady=(10, 0))

        self.record_btn = ttk.Button(
            video_frame, text="🔴 Start Recording", command=self._toggle_recording,
            state=tk.DISABLED
        )
        self.record_btn.pack(fill=tk.X, pady=(15, 0))
        
        self.play_video_btn = ttk.Button(
            video_frame, text="▶ Play Last Video", command=self._play_last_video,
            state=tk.DISABLED
        )
        self.play_video_btn.pack(fill=tk.X, pady=(5, 0))

        self.recording_time_var = tk.StringVar(value="")
        self.recording_label = ttk.Label(
            video_frame, textvariable=self.recording_time_var,
            foreground="red"
        )
        self.recording_label.pack(pady=(5, 0))

        # Settings
        settings_frame = ttk.LabelFrame(right_panel, text="Settings", padding=15)
        settings_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(settings_frame, text="Resolution:").pack(anchor=tk.W)
        resolution_combo = ttk.Combobox(
            settings_frame, textvariable=self.resolution_var,
            values=["640x480", "1280x720", "1920x1080", "1280x960"],
            width=15, state="readonly"
        )
        resolution_combo.pack(anchor=tk.W, pady=(5, 0))

        ttk.Button(
            settings_frame, text="Save Settings",
            command=self._save_settings
        ).pack(fill=tk.X, pady=(15, 5))

        ttk.Button(
            settings_frame, text="Load Settings",
            command=self._load_settings
        ).pack(fill=tk.X, pady=(5, 0))

        # Output directory
        output_frame = ttk.LabelFrame(right_panel, text="Output", padding=15)
        output_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(
            output_frame, text="Open Output Folder",
            command=self._open_output_folder
        ).pack(fill=tk.X)
        
        # Keyboard shortcuts
        self.root.bind('<F1>', lambda e: self._take_photo())
        self.root.bind('<F2>', lambda e: self._toggle_recording())
        self.root.bind('<F3>', lambda e: self._toggle_camera())
        
        # Style
        style = ttk.Style()
        style.configure("Recording.TButton", foreground="red")

    def _start_camera(self):
        """Start the camera preview."""
        camera_id = self.camera_id_var.get()
        self.camera = Camera(camera_id)

        if not self.camera.open():
            messagebox.showerror("Error", "Could not open camera")
            return

        # Apply settings
        width, height = map(int, self.resolution_var.get().split('x'))
        self.camera.update_settings(
            resolution=(width, height),
            fps=int(self.fps_var.get()),
            photo_format=self.photo_format_var.get(),
            video_format=self.video_format_var.get()
        )

        self.is_preview_running = True
        self.stop_preview.clear()

        # Update buttons
        self.start_camera_btn.config(state=tk.DISABLED)
        self.stop_camera_btn.config(state=tk.NORMAL)
        self.photo_btn.config(state=tk.NORMAL)
        self.record_btn.config(state=tk.NORMAL)

        self.status_var.set(f"Camera {camera_id} started - {self.resolution_var.get()}")

        # Start preview thread
        self.preview_thread = threading.Thread(target=self._preview_loop, daemon=True)
        self.preview_thread.start()

    def _stop_camera(self):
        """Stop the camera preview."""
        if self.is_recording:
            self._toggle_recording()

        self.is_preview_running = False
        self.stop_preview.set()

        if self.camera:
            self.camera.close()
            self.camera = None

        # Clear video display
        self.video_label.configure(image="")

        # Update buttons
        self.start_camera_btn.config(state=tk.NORMAL)
        self.stop_camera_btn.config(state=tk.DISABLED)
        self.photo_btn.config(state=tk.DISABLED)
        self.record_btn.config(state=tk.DISABLED)

        self.status_var.set("Camera stopped")

    def _toggle_camera(self):
        """Toggle camera on/off."""
        if self.camera and self.camera.cap and self.camera.cap.isOpened():
            self._stop_camera()
        else:
            self._start_camera()

    def _preview_loop(self):
        """Main preview loop running in a separate thread."""
        while self.is_preview_running and not self.stop_preview.is_set():
            if self.camera and self.camera.cap and self.camera.cap.isOpened():
                ret, frame = self.camera.cap.read()
                if ret:
                    # Write frame to video if recording
                    if self.is_recording and self.camera.is_recording and self.camera.video_writer:
                        self.camera.video_writer.write(frame)
                    
                    self._update_preview(frame)

    def _update_preview(self, frame):
        """Update the preview label with a new frame."""
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Resize to fit the label
        label_width = self.video_label.winfo_width()
        label_height = self.video_label.winfo_height()

        if label_width > 1 and label_height > 1:
            frame_rgb = cv2.resize(frame_rgb, (label_width, label_height))

        # Convert to ImageTk format
        img = Image.fromarray(frame_rgb)
        img_tk = ImageTk.PhotoImage(image=img)

        # Update label
        self.video_label.configure(image=img_tk)
        self.video_label.image = img_tk  # Keep reference

    def _take_photo(self):
        """Take a photo."""
        if not self.camera:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"photo_{timestamp}.{self.photo_format_var.get()}"

        filepath = self.camera.capture_photo(filename)
        if filepath:
            self.status_var.set(f"Photo saved: {filepath}")
            messagebox.showinfo("Photo Taken", f"Saved to:\n{filepath}")
        else:
            self.status_var.set("Failed to take photo")
            messagebox.showerror("Error", "Failed to capture photo")

    def _toggle_recording(self):
        """Toggle video recording."""
        if not self.camera:
            return

        if self.is_recording:
            # Stop recording
            filepath = self.camera.stop_recording()
            self.is_recording = False
            self.record_btn.config(text="🔴 Start Recording")
            self.record_btn.style = ttk.Style()
            self.recording_time_var.set("")
            self.play_video_btn.config(state=tk.NORMAL)
            self.current_video_file = filepath

            if filepath:
                self.status_var.set(f"Video saved: {filepath}")
                messagebox.showinfo("Recording Stopped", f"Saved to:\n{filepath}\n\nClick 'Play Last Video' to watch")
        else:
            # Start recording
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"video_{timestamp}.mp4"

            if self.camera.start_recording(filename):
                self.is_recording = True
                self.recording_start_time = datetime.now()
                self.record_btn.config(text="⏹ Stop Recording")
                self.play_video_btn.config(state=tk.DISABLED)
                self.status_var.set("Recording...")
                self.current_video_file = None

                # Start recording timer
                self._update_recording_time()

    def _play_last_video(self):
        """Play the last recorded video."""
        if not self.current_video_file or not os.path.exists(self.current_video_file):
            messagebox.showwarning("No Video", "No video file found to play")
            return
        
        # Try to play video using system default player
        try:
            if os.name == 'nt':  # Windows
                os.startfile(self.current_video_file)
            elif sys.platform == 'darwin':  # macOS
                os.system(f'open "{self.current_video_file}"')
            else:  # Linux
                os.system(f'xdg-open "{self.current_video_file}" &')
            self.status_var.set(f"Playing: {os.path.basename(self.current_video_file)}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not play video: {e}")

    def _update_recording_time(self):
        """Update the recording time display."""
        if self.is_recording:
            elapsed = datetime.now() - self.recording_start_time
            elapsed_str = str(elapsed).split('.')[0]  # Remove microseconds
            self.recording_time_var.set(f"⏺ Recording: {elapsed_str}")
            self.root.after(1000, self._update_recording_time)

    def _save_settings(self):
        """Save current settings to file."""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            title="Save Settings"
        )
        if filepath:
            settings = {
                "resolution": self.resolution_var.get(),
                "fps": self.fps_var.get(),
                "photo_format": self.photo_format_var.get(),
                "video_format": self.video_format_var.get(),
                "camera_id": self.camera_id_var.get()
            }
            import json
            with open(filepath, 'w') as f:
                json.dump(settings, f, indent=2)
            self.status_var.set(f"Settings saved to {filepath}")

    def _load_settings(self):
        """Load settings from file."""
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")],
            title="Load Settings"
        )
        if filepath:
            import json
            try:
                with open(filepath, 'r') as f:
                    settings = json.load(f)

                if "resolution" in settings:
                    self.resolution_var.set(settings["resolution"])
                if "fps" in settings:
                    self.fps_var.set(settings["fps"])
                if "photo_format" in settings:
                    self.photo_format_var.set(settings["photo_format"])
                if "video_format" in settings:
                    self.video_format_var.set(settings["video_format"])
                if "camera_id" in settings:
                    self.camera_id_var.set(settings["camera_id"])

                self.status_var.set(f"Settings loaded from {filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load settings: {e}")

    def _open_output_folder(self):
        """Open the output folder in file manager."""
        os.startfile(str(self.output_dir.absolute())) if os.name == 'nt' \
            else os.system(f"xdg-open '{self.output_dir.absolute()}'")

    def _on_closing(self):
        """Handle window close event."""
        self._stop_camera()
        self.root.destroy()


def main():
    """Main entry point."""
    root = tk.Tk()
    app = CameraGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
