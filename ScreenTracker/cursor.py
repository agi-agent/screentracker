import sys
import ctypes
import time
from datetime import datetime
from PIL import Image

class CursorOverlay:
    def __init__(self):
        self.platform = sys.platform
        self._init_platform()
    
    def _init_platform(self):
        if self.platform == 'win32':
            global win32gui, win32ui, win32con, win32api
            import win32gui
            import win32ui
            import win32con
            import win32api
            
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
            except:
                ctypes.windll.user32.SetProcessDPIAware()
    
    def screenshot_with_cursor(self):
        if self.platform == 'win32':
            return self._windows_screenshot()
        elif self.platform == 'darwin':
            return Image.new('RGB', (0,0)), 0, 0  # macOS空实现
        
    def _windows_screenshot(self):
        width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
        left = 0
        top = 0
        hdesktop = win32gui.GetDesktopWindow()
        desktop_dc = win32gui.GetWindowDC(hdesktop)
        mem_dc = win32ui.CreateDCFromHandle(desktop_dc)
        save_dc = mem_dc.CreateCompatibleDC()
        save_bitmap = win32ui.CreateBitmap()
        save_bitmap.CreateCompatibleBitmap(mem_dc, width, height)
        save_dc.SelectObject(save_bitmap)

        save_dc.BitBlt((0, 0), (width, height), mem_dc, (left, top), win32con.SRCCOPY)

        cursor_info = win32gui.GetCursorInfo()
        if cursor_info and cursor_info[1]:
            try:
                hcursor, x, y = cursor_info[1], cursor_info[2][0], cursor_info[2][1]
                icon_info = win32gui.GetIconInfo(hcursor)
                x -= icon_info[1]
                y -= icon_info[2]
                win32gui.DrawIconEx(
                    save_dc.GetSafeHdc(),
                    x - left,
                    y - top,
                    hcursor, 0, 0, 0, None, win32con.DI_NORMAL
                )
                if icon_info[0]: win32gui.DeleteObject(icon_info[0])
                if icon_info[1]: win32gui.DeleteObject(icon_info[1])
            except Exception: pass

        bmp_info = save_bitmap.GetInfo()
        bmp_str = save_bitmap.GetBitmapBits(True)
        image = Image.frombuffer(
            'RGB',
            (bmp_info['bmWidth'], bmp_info['bmHeight']),
            bmp_str, 'raw', 'BGRX', 0, 1
        )

        win32gui.DeleteObject(save_bitmap.GetHandle())
        save_dc.DeleteDC()
        mem_dc.DeleteDC()
        win32gui.ReleaseDC(hdesktop, desktop_dc)

        return image, width, height
