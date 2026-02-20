#!/usr/bin/env python3
"""
Simple Camera CLI

Command-line interface for the simple camera application.
"""

import argparse
import sys
import time
from camera import Camera


def cmd_photo(args):
    """Capture a photo."""
    with Camera(args.camera_id) as cam:
        if not cam.cap or not cam.cap.isOpened():
            print("Error: Could not open camera")
            sys.exit(1)

        # Apply any settings from args
        if args.resolution:
            width, height = map(int, args.resolution.split('x'))
            cam.update_settings(resolution=(width, height))
        if args.format:
            cam.update_settings(photo_format=args.format)

        # Capture photo(s)
        if args.count > 1:
            for i in range(args.count):
                filename = f"{args.name}_{i+1}" if args.name else None
                cam.capture_photo(filename)
                if i < args.count - 1:
                    time.sleep(args.interval)
        else:
            cam.capture_photo(args.name)


def cmd_video(args):
    """Record a video."""
    with Camera(args.camera_id) as cam:
        if not cam.cap or not cam.cap.isOpened():
            print("Error: Could not open camera")
            sys.exit(1)

        # Apply settings
        if args.resolution:
            width, height = map(int, args.resolution.split('x'))
            cam.update_settings(resolution=(width, height))
        if args.fps:
            cam.update_settings(fps=args.fps)
        if args.format:
            cam.update_settings(video_format=args.format)

        if args.duration:
            # Timed recording
            cam.record_video(args.duration, args.name)
        else:
            # Manual recording
            print("Press Enter to start recording, then Enter again to stop")
            input()
            cam.start_recording(args.name)
            print("Recording... Press Enter to stop")
            input()
            cam.stop_recording()


def cmd_preview(args):
    """Preview camera feed."""
    with Camera(args.camera_id) as cam:
        if not cam.cap or not cam.isOpened():
            print("Error: Could not open camera")
            sys.exit(1)
        cam.preview(args.duration if args.duration else 0)


def cmd_settings(args):
    """Manage camera settings."""
    cam = Camera(args.camera_id)

    if args.save:
        cam.save_settings(args.save)
    elif args.load:
        if cam.load_settings(args.load):
            print("Current settings:", cam.get_settings())
    elif args.show:
        print("Current settings:", cam.get_settings())
    elif args.reset:
        # Reset to defaults
        cam.settings = {
            "resolution": (1280, 720),
            "fps": 30,
            "photo_format": "png",
            "video_format": "mp4",
            "video_codec": "mp4v",
            "brightness": -1,
            "contrast": -1,
            "saturation": -1,
        }
        cam.save_settings()
        print("Settings reset to defaults")
    else:
        # Show current settings
        print("Current settings:", cam.get_settings())


def cmd_list(args):
    """List available cameras."""
    cam = Camera()
    cameras = cam.list_cameras()
    if cameras:
        print("Available cameras:")
        for i in cameras:
            print(f"  - Camera ID: {i}")
    else:
        print("No cameras found")


def main():
    parser = argparse.ArgumentParser(
        description="Simple Camera - Capture photos and videos from your camera"
    )
    parser.add_argument(
        "--camera-id", "-c", type=int, default=0,
        help="Camera device ID (default: 0)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Photo command
    photo_parser = subparsers.add_parser("photo", help="Capture a photo")
    photo_parser.add_argument("--name", "-n", help="Output filename")
    photo_parser.add_argument(
        "--count", "-N", type=int, default=1,
        help="Number of photos to capture"
    )
    photo_parser.add_argument(
        "--interval", "-i", type=float, default=1.0,
        help="Interval between photos (seconds)"
    )
    photo_parser.add_argument(
        "--resolution", "-r", help="Resolution (e.g., 1280x720)"
    )
    photo_parser.add_argument(
        "--format", "-f", choices=["png", "jpg", "bmp"],
        help="Photo format"
    )
    photo_parser.set_defaults(func=cmd_photo)

    # Video command
    video_parser = subparsers.add_parser("video", help="Record a video")
    video_parser.add_argument("--name", "-n", help="Output filename")
    video_parser.add_argument(
        "--duration", "-d", type=float,
        help="Recording duration in seconds"
    )
    video_parser.add_argument(
        "--resolution", "-r", help="Resolution (e.g., 1920x1080)"
    )
    video_parser.add_argument(
        "--fps", type=int, help="Frames per second"
    )
    video_parser.add_argument(
        "--format", "-f", choices=["mp4", "avi", "mkv"],
        help="Video format"
    )
    video_parser.set_defaults(func=cmd_video)

    # Preview command
    preview_parser = subparsers.add_parser("preview", help="Preview camera feed")
    preview_parser.add_argument(
        "--duration", "-d", type=int, default=5,
        help="Preview duration in seconds (0 for infinite)"
    )
    preview_parser.set_defaults(func=cmd_preview)

    # Settings command
    settings_parser = subparsers.add_parser("settings", help="Manage settings")
    settings_parser.add_argument("--save", help="Save settings to file")
    settings_parser.add_argument("--load", help="Load settings from file")
    settings_parser.add_argument(
        "--show", action="store_true", help="Show current settings"
    )
    settings_parser.add_argument(
        "--reset", action="store_true", help="Reset to default settings"
    )
    settings_parser.set_defaults(func=cmd_settings)

    # List command
    list_parser = subparsers.add_parser("list", help="List available cameras")
    list_parser.set_defaults(func=cmd_list)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
