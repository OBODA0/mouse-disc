"""Daemon mode for instant Mouse Disc show - keeps QApplication warm"""
import os
import sys
import socket
import threading
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSocketNotifier, pyqtSignal, QObject

# Unix socket path
SOCKET_PATH = "/tmp/mouse-disc.sock"


class SignalHandler(QObject):
    """Handle signals from client processes"""
    show_requested = pyqtSignal(int, int)  # cursor_x, cursor_y

    def __init__(self):
        super().__init__()
        self.socket_path = Path(SOCKET_PATH)
        self.server = None
        self.notifier = None
        self._setup_socket()

    def _setup_socket(self):
        """Setup Unix socket server"""
        # Remove old socket
        if self.socket_path.exists():
            self.socket_path.unlink()

        self.server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server.bind(str(self.socket_path))
        self.server.listen(5)
        self.server.setblocking(False)

        # Use QSocketNotifier for Qt integration
        self.notifier = QSocketNotifier(
            self.server.fileno(),
            QSocketNotifier.Type.Read
        )
        self.notifier.activated.connect(self._handle_connection)

    def _handle_connection(self):
        """Handle incoming connection"""
        try:
            conn, _ = self.server.accept()
            data = conn.recv(32).decode().strip()
            conn.close()

            if data.startswith("show,"):
                # Parse "show,cursor_x,cursor_y"
                parts = data.split(",")
                if len(parts) == 3:
                    cursor_x = int(parts[1])
                    cursor_y = int(parts[2])
                    self.show_requested.emit(cursor_x, cursor_y)
        except Exception:
            pass

    def cleanup(self):
        """Cleanup socket"""
        if self.notifier:
            self.notifier.setEnabled(False)
        if self.server:
            self.server.close()
        if self.socket_path.exists():
            self.socket_path.unlink()


def send_show_signal(cursor_x: int, cursor_y: int) -> bool:
    """Send show signal to daemon. Returns True if daemon is running."""
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(0.1)
        sock.connect(SOCKET_PATH)
        sock.send(f"show,{cursor_x},{cursor_y}".encode())
        sock.close()
        return True
    except (FileNotFoundError, ConnectionRefusedError, socket.timeout):
        return False
