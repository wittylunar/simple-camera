"""
Simple Camera Module

A Python module for capturing photos and recording videos using OpenCV.
"""

import cv2
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


class Camera:
    """A simple camera class for photo and video capture."""

    def __init__(self, camera_id: int = 0):
        """
        Initialize the camera.

        Args:
            camera_id: The camera device ID (0 for default camera)
        """
        self.camera_id = camera_id
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_recording = False
        self.output_dir = Path("./captures")
        self.output_dir.mkdir(exist_ok=True)

        # Default settings
        self.settings: Dict[str, Any] = {
            "resolution": (1280, 720),
            "fps": 30,
            "photo_format": "png",
            "video_format": "avi",
            "video_codec": "XVID",
            "brightness": -1,  # -1 means default
            "contrast": -1,
            "saturation": -1,
        }

    def open(self) -> bool:
        """
        Open the camera device.

        Returns:
            True if camera opened successfully, False otherwise
        """
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            return False

        # Apply settings
        self._apply_settings()
        return True

    def close(self):
        """Close the camera device."""
        if self.cap:
            self.cap.release()
            self.cap = None

    def _apply_settings(self):
        """Apply current settings to the camera."""
        if not self.cap:
            return

        width, height = self.settings["resolution"]
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, self.settings["fps"])

        # Apply image adjustments if set
        if self.settings["brightness"] != -1:
            self.cap.set(cv2.CAP_PROP_BRIGHTNESS, self.settings["brightness"])
        if self.settings["contrast"] != -1:
            self.cap.set(cv2.CAP_PROP_CONTRAST, self.settings["contrast"])
        if self.settings["saturation"] != -1:
            self.cap.set(cv2.CAP_PROP_SATURATION, self.settings["saturation"])

    def capture_photo(self, filename: Optional[str] = None) -> Optional[str]:
        """
        Capture a photo.

        Args:
            filename: Optional filename for the photo. If not provided,
                      a timestamp-based name will be generated.

        Returns:
            The path to the saved photo, or None if capture failed
        """
        if not self.cap or not self.cap.isOpened():
            print("Error: Camera is not open")
            return None

        ret, frame = self.cap.read()
        if not ret:
            print("Error: Failed to capture frame")
            return None

        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"photo_{timestamp}.{self.settings['photo_format']}"

        # Ensure file has correct extension
        ext = self.settings["photo_format"]
        if not filename.endswith(f".{ext}"):
            filename = f"{filename}.{ext}"

        filepath = self.output_dir / filename

        # Save the photo
        cv2.imwrite(str(filepath), frame)
        print(f"Photo saved: {filepath}")
        return str(filepath)

    def start_recording(self, filename: Optional[str] = None) -> bool:
        """
        Start recording a video.

        Args:
            filename: Optional filename for the video. If not provided,
                      a timestamp-based name will be generated.

        Returns:
            True if recording started successfully, False otherwise
        """
        if not self.cap or not self.cap.isOpened():
            print("Error: Camera is not open")
            return False

        if self.is_recording:
            print("Error: Already recording")
            return False

        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"video_{timestamp}.mp4"

        # Ensure file has .mp4 extension
        if not filename.endswith(".mp4"):
            filename = f"{filename}.mp4"

        filepath = self.output_dir / filename

        # Get actual resolution from camera
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = self.settings["fps"]
        
        # Ensure resolution is valid
        if width <= 0 or height <= 0:
            width, height = 1280, 720
        if fps <= 0:
            fps = 30

        # Create video writer - try H264 first (best quality/size)
        fourcc = cv2.VideoWriter_fourcc(*'avc1')
        self.video_writer = cv2.VideoWriter(
            str(filepath), fourcc, fps, (width, height)
        )

        if not self.video_writer.isOpened():
            print("Error: Failed to create video writer with avc1")
            # Try mp4v as fallback
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.video_writer = cv2.VideoWriter(
                str(filepath), fourcc, fps, (width, height)
            )
            if not self.video_writer.isOpened():
                print("Error: Failed to create video writer with mp4v")
                # Try MJPG as last resort
                fourcc = cv2.VideoWriter_fourcc(*'MJPG')
                filepath = filepath.with_suffix('.avi')
                self.video_writer = cv2.VideoWriter(
                    str(filepath), fourcc, fps, (width, height)
                )
                if not self.video_writer.isOpened():
                    print("Error: Failed to create video writer with MJPG too")
                    return False
                print(f"Recording started with MJPG codec: {filepath}")
            else:
                print(f"Recording started with mp4v codec: {filepath}")
        else:
            print(f"Recording started with avc1 (H.264) codec: {filepath}")

        self.recording_filename = filepath
        self.is_recording = True
        return True

    def stop_recording(self) -> Optional[str]:
        """
        Stop recording a video.

        Returns:
            The path to the saved video, or None if not recording
        """
        if not self.is_recording:
            print("Error: Not recording")
            return None

        self.is_recording = False
        self.video_writer.release()
        self.video_writer = None

        filepath = self.recording_filename
        print(f"Recording saved: {filepath}")
        return str(filepath)

    def record_video(self, duration: float, filename: Optional[str] = None) -> Optional[str]:
        """
        Record a video for a specified duration.

        Args:
            duration: Duration in seconds
            filename: Optional filename for the video

        Returns:
            The path to the saved video, or None if recording failed
        """
        if not self.start_recording(filename):
            return None

        import time
        start_time = time.time()
        fps = self.settings["fps"]
        frame_delay = 1.0 / fps

        print(f"Recording for {duration} seconds... Press Ctrl+C to stop early")

        try:
            while time.time() - start_time < duration:
                frame_start = time.time()

                ret, frame = self.cap.read()
                if not ret:
                    print("Warning: Failed to capture frame")
                    continue

                self.video_writer.write(frame)

                # Maintain frame rate
                elapsed = time.time() - frame_start
                if elapsed < frame_delay:
                    time.sleep(frame_delay - elapsed)

                # Show progress
                elapsed_time = time.time() - start_time
                print(f"\rRecording: {elapsed_time:.1f}s / {duration}s", end="", flush=True)

        except KeyboardInterrupt:
            print("\nRecording interrupted")

        print()  # New line after progress
        return self.stop_recording()

    def preview(self, duration: float = 5):
        """
        Preview the camera feed in a window.

        Args:
            duration: Duration in seconds to show preview (0 for infinite)
        """
        if not self.cap or not self.cap.isOpened():
            print("Error: Camera is not open")
            return

        print(f"Preview window opened. Press 'q' to quit or wait {duration}s")

        import time
        start_time = time.time()

        cv2.namedWindow("Camera Preview", cv2.WINDOW_NORMAL)

        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Warning: Failed to capture frame")
                continue

            cv2.imshow("Camera Preview", frame)

            # Check for quit key
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # Check duration limit
            if duration > 0 and time.time() - start_time > duration:
                break

        cv2.destroyWindow("Camera Preview")

    def get_settings(self) -> Dict[str, Any]:
        """Get current camera settings."""
        return self.settings.copy()

    def update_settings(self, **kwargs) -> Dict[str, Any]:
        """
        Update camera settings.

        Args:
            **kwargs: Settings to update (resolution, fps, photo_format, etc.)

        Returns:
            Updated settings
        """
        valid_keys = self.settings.keys()
        for key, value in kwargs.items():
            if key in valid_keys:
                self.settings[key] = value
            else:
                print(f"Warning: Unknown setting '{key}'")

        # Re-apply settings if camera is open
        if self.cap and self.cap.isOpened():
            self._apply_settings()

        return self.settings.copy()

    def save_settings(self, filepath: str = "camera_settings.json"):
        """Save current settings to a JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.settings, f, indent=2)
        print(f"Settings saved to {filepath}")

    def load_settings(self, filepath: str = "camera_settings.json") -> bool:
        """
        Load settings from a JSON file.

        Args:
            filepath: Path to the settings file

        Returns:
            True if loaded successfully, False otherwise
        """
        if not os.path.exists(filepath):
            print(f"Settings file not found: {filepath}")
            return False

        with open(filepath, 'r') as f:
            loaded_settings = json.load(f)

        # Update only valid settings
        for key, value in loaded_settings.items():
            if key in self.settings:
                self.settings[key] = value

        # Re-apply settings if camera is open
        if self.cap and self.cap.isOpened():
            self._apply_settings()

        print(f"Settings loaded from {filepath}")
        return True

    def list_cameras(self) -> list:
        """
        List available camera devices.

        Returns:
            List of available camera IDs
        """
        available = []
        # Check first 10 camera IDs
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available.append(i)
                cap.release()
        return available

    def __enter__(self):
        """Context manager entry."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
