#!/usr/bin/env python
import sys
import threading
from pynput import mouse, keyboard
import pynput
import wx
import uuid
from PIL import ImageGrab, ImageDraw
import os
import time
import platform
from datetime import datetime
import signal
import sys

from sqlite import SqlitePool
from cursor import CursorOverlay
from collections import deque
# Ctrl+C 
#signal.signal(signal.SIGINT, lambda *_: None)
#pynput.keyboard.unbind('<ctrl>+<alt>+<del>')
def signal_handler(sig, frame):
    pass 
signal.signal(signal.SIGINT, signal_handler)

start_x = 0
start_y = 0
current_x = 0
current_y = 0

last_click_time = 0.0
double_click_inte = 0.5

str_mac_address = ''
path_cache = './_cache/'
db_path = './trackDB.db'

sql_conn = None
overlay = None

max_queue_size = 3
free_queue = deque()
screenshot_x = 900
screenshot_y = 900
thread_event = threading.Event()
rlock_key = threading.RLock()
rlock_click = threading.RLock()


def getcurfile(name):
    if getattr(sys,'frozen',False):
        return sys._MEIPASS+"/" + name
    return name
def getfile(name):
    return "/tmp/" + name

system = platform.system()
if system == "Darwin":
    path_cache = getfile("_cache/")
    db_path = getfile("trackDB.db")
    if not os.path.exists("/tmp/_cache/"):
        os.makedirs("/tmp/_cache/", exist_ok=True)
    if not os.path.isfile("/tmp/trackDB.db"):
        shutil.copy2(getcurfile("trackDB.db"), getfile("trackDB.db"))

def get_mac_address():
    # MAC 
    global str_mac_address
    mac_address = uuid.UUID(int=uuid.getnode()).hex[-12:].upper()
    mac_address = '-'.join([mac_address[i:i+2] for i in range(0, 11, 2)])
    str_mac_address = mac_address
    print(str_mac_address)
    logger.debug(f'mac_address:{str_mac_address}')

    
def check_path_or_files_missing(path):
    if not os.path.exists(path):
        return True
    if os.path.isfile(path):
        return False
    return len(os.listdir(path)) == 0

def get_5min_group(current_timestamp):
    dt = datetime.fromtimestamp(current_timestamp)
    adjusted_minute = (dt.minute // 5) * 5
    group_start = dt.replace(minute=adjusted_minute, second=0, microsecond=0)
    return group_start.strftime("%Y-%m-%d-%H-%M-00-000")


def on_click_event(data_day, time_stamp, time_group, str_mac_address, event, x, y, str_screenshot_id):
    global sql_conn, free_queue 
    if len(free_queue) <= 0: 
        logger.debug(f'len(free_queue):{len(free_queue)}')
        return
    our_task = next(iter(free_queue))
    img_path = path_cache + our_task["time"] + '.png'
    str_screenshot_id = our_task["time"]
    if check_path_or_files_missing(img_path):
        our_task["input"].save(img_path)
    logger.debug(f'on_click_event save img_path:{img_path}')
    conn = sql_conn.get_connection()
    conn.insert_click_track(data_day, time_stamp, time_group, str_mac_address, event, x, y, str_screenshot_id + '.png')
    sql_conn.release_connection(conn)
    
#on click envent
def on_click(x, y, button, pressed):
    with rlock_click:  
        global start_x, start_y, current_x, current_y, last_click_time, str_mac_address, double_click_inte
        event = 'click'
        clickdouble_event = ''
        #current_x = x
        #current_y = y
        
        current_time = time.time()
        str_group = get_5min_group(current_time)
        local_time = time.localtime(current_time)
        # data_head = time.strftime("%Y-%m-%d-%H:%M:%S", local_time)
        data_secs = (current_time - int(current_time)) * 1000
        # time_stamp = "%s:%03d" % (data_head, data_secs)
        data_day = time.strftime("%Y-%m-%d-%H", local_time)
        # str_track = "{} {} {}:{}, {}, {}, {}".format(str_mac_address, time_stamp, event, start_x, start_y, x, y)
        # print(str_track)
        data_head = time.strftime("%Y-%m-%d-%H-%M-%S", local_time)
        time_stamp = "%s-%03d" % (data_head, data_secs)

        if pressed and button == pynput.mouse.Button.left:
            (start_x, start_y) = (x, y)
            event = 'click_pressed'
            logger.debug(f'{event}:{x}, {y}')
                
        elif (not pressed) and (button == pynput.mouse.Button.left):
            event = 'click'
            if last_click_time and (current_time - last_click_time < double_click_inte):
                clickdouble_event = 'clickdouble'
                logger.debug(f'{clickdouble_event}:{start_x}, {start_y}, {x}, {y}')
            last_click_time = current_time
            logger.debug(f'{event}:{start_x}, {start_y}, {x}, {y}')
        elif pressed and button == pynput.mouse.Button.right:
            event = 'clickright_pressed'
            logger.debug(f'{event}:{x}, {y}')
        elif (not pressed) and (button == pynput.mouse.Button.right):
            event = 'clickright'
            logger.debug(f'{event}:{x}, {y}')
        elif pressed and button == pynput.mouse.Button.middle:
            event = 'clickmiddle'
            logger.debug(f'{event}:{x}, {y}')
        elif (not isinstance(button, str)):
            event = 'scroll' + f'_{button}_{pressed}'
            logger.debug(f'{event}:{x}, {y}')
        
        event = event.strip() 
        str_screenshot_id = "{}_{}_{}".format(str_mac_address, time_stamp, event)
        str_track_id = "{}_{}".format(str_mac_address, time.strftime("%Y-%m-%d-%H", local_time))
        time_group = get_5min_group(current_time)
        on_click_event(data_day, time_stamp, time_group, str_mac_address, event, x, y, str_screenshot_id)
        if not clickdouble_event == '':
            on_click_event(data_day, time_stamp, time_group, str_mac_address, clickdouble_event, x, y, str_screenshot_id) 

def on_key_event(data_day, time_stamp, time_group, str_mac_address, event, str_screenshot_id):
    global sql_conn, free_queue
    
    if len(free_queue) <= 0: 
        logger.debug(f'len(free_queue):{len(free_queue)}')
        return
        
    our_task = next(iter(free_queue))
    img_path = path_cache + our_task["time"] + '.png'
    str_screenshot_id = our_task["time"]
    if check_path_or_files_missing(img_path):
        our_task["input"].save(img_path)
    logger.debug(f'on_key_event save img_path:{img_path}')
    
    conn = sql_conn.get_connection()
    conn.insert_key_track(data_day, time_stamp, time_group, str_mac_address, event, str_screenshot_id + '.png')
    sql_conn.release_connection(conn)

#keyboard
def on_press(key):
    with rlock_key: 
        event = ''
        logger.debug(f'keyboardPress:{key}')
        try:
            char = key.char
            code = ord(char)
            event = f"keyboardPress_{code} "  
        except AttributeError:
            event = f"keyboardPress_{key} " 
        event = event.strip()    
            
        current_time = time.time()
        local_time = time.localtime(current_time)
        data_head = time.strftime("%Y-%m-%d-%H-%M-%S", local_time)
        data_secs = (current_time - int(current_time)) * 1000
        time_stamp = "%s-%03d" % (data_head, data_secs)
        data_day = time.strftime("%Y-%m-%d-%H", local_time)
        str_screenshot_id = "{}_{}_{}".format(str_mac_address, time_stamp, event)
        
        time_group = get_5min_group(current_time)
        on_key_event(data_day, time_stamp, time_group, str_mac_address, event, str_screenshot_id)

def on_release(key):
    event = ''
    logger.debug(f'keyboard:{key}')
    try:
        char = key.char
        code = ord(char)
        event = f"keyboard_{code} "  
    except AttributeError:
        event = f"keyboard_{key} " 
    event = event.strip()    
        
    current_time = time.time()
    local_time = time.localtime(current_time)
    data_head = time.strftime("%Y-%m-%d-%H-%M-%S", local_time)
    data_secs = (current_time - int(current_time)) * 1000
    time_stamp = "%s-%03d" % (data_head, data_secs)
    data_day = time.strftime("%Y-%m-%d-%H", local_time)
    str_screenshot_id = "{}_{}_{}".format(str_mac_address, time_stamp, event)
    
    time_group = get_5min_group(current_time)
    on_key_event(data_day, time_stamp, time_group, str_mac_address, event, str_screenshot_id)

class MainWindow(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Recorder Control Panel", size=(400, 250))
        self.CreateStatusBar()

        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Status display area
        self.status_text = wx.StaticText(panel, label="", style=wx.ALIGN_CENTER)
        main_sizer.Add(self.status_text, 0, wx.EXPAND | wx.ALL, 10)
        
        # Button area
        self.start_btn = wx.Button(panel, label="Start Recording")
        self.exit_btn = wx.Button(panel, label="End Recording")
        
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.Add(self.start_btn, 0, wx.RIGHT | wx.EXPAND, 10)
        btn_sizer.Add(self.exit_btn, 0, wx.LEFT | wx.EXPAND, 10)
        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(main_sizer)
        
        # Event bindings
        self.Bind(wx.EVT_BUTTON, self.OnStartListening, self.start_btn)
        self.Bind(wx.EVT_BUTTON, self.OnExit, self.exit_btn)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnExitDoubleClick, self.exit_btn)
        
        # Listener management
        self.mouse_listener = None
        self.keyboard_listener = None
        self.listening = False
        
        self.mouse_listener = mouse.Listener(on_click=self.OnClick, on_scroll=self.OnScroll)
        self.keyboard_listener = keyboard.Listener(on_press=self.OnKeyPress, on_release=self.OnKeyrelease)
        self.mouse_listener.start()
        self.keyboard_listener.start() 
        
        self.UpdateUI()
        
    def UpdateUI(self):
        if self.listening:
            self.status_text.SetLabel("Recording Started")
            self.start_btn.Disable()
            self.exit_btn.SetLabel("End Recording")
        else:
            self.status_text.SetLabel("")
            self.start_btn.Enable()
            self.exit_btn.SetLabel("End Recording")
    
    def OnStartListening(self, event):
        if not self.listening:
            self.listening = True
            # Start listener threads
            self.screenshot = threading.Thread(target=self.screenshot_task, args=('Thread1',))
            self.screenshot.daemon = True
            self.screenshot.start() 
            self.listening = True
            self.UpdateUI()
    
    def OnExit(self, event):
        self.OnExitAction()
    
    def OnExitDoubleClick(self, event):
        self.OnExitAction()
    
    def OnExitAction(self):
        # Confirmation dialog
        confirm = wx.MessageDialog(
            self, 
            "Are you sure you want to exit the program?", 
            "Exit Confirmation", 
            wx.YES_NO | wx.ICON_QUESTION
        )
        if confirm.ShowModal() == wx.ID_YES:
            if self.listening:
                # Stop listeners
                self.mouse_listener.stop()
                self.keyboard_listener.stop()
                self.listening = False
                self.UpdateUI()
            self.Destroy()
            sys.exit(0)
    
    def OnClick(self, x, y, button, pressed):
        #print("OnClick detected:", x, y)
        on_click(x, y, button, pressed)
        time.sleep(0)
    def OnScroll(self, x, y, dx, dy):
        on_click(x, y, dx, dy)
        #print("Scroll detected:", x, y, dx, dy)
        time.sleep(0)
        
    
    def OnKeyPress(self, key):
        on_press(key)
        time.sleep(0)
        
    def OnKeyrelease(self, key):
        on_release(key)
        time.sleep(0)
        
    def screenshot_task(self, name):
        print(name)
        global max_queue_size, free_queue, screenshot_x, screenshot_y, thread_event, current_x, current_y
        while(self.listening):
            #time.sleep(0.5)
            thread_event.wait(0.5)
            
            current_time = time.time()
            local_time = time.localtime(current_time)
            data_head = time.strftime("%Y-%m-%d-%H-%M-%S", local_time)
            data_secs = (current_time - int(current_time)) * 1000
            time_stamp = "%s-%03d" % (data_head, data_secs)
            str_screenshot_id = "{}_{}".format(str_mac_address, time_stamp)
            
            img = None
            try:
                #img = ImageGrab.grab()
                #width, height = img.size
                img, width, height  = overlay.screenshot_with_cursor()
                str_screenshot_id = "{}_{}_{}-{}".format(str_mac_address, time_stamp, width, height)
            except Exception as e:
                logger.debug(f'ImageGrab Error: {e}')
                continue
                
            our_task = {
                "input": img,
                "time": str_screenshot_id
                }
            free_queue.appendleft(our_task)
            queue_len = len(free_queue)
            if queue_len >= max_queue_size:
                free_queue.pop()
            logger.debug(f'queue append task, queue_size:{queue_len}')


import logging 
logger = logging.getLogger(__name__)
console_handler = logging.StreamHandler()
logging.basicConfig(filename='./client_lister_log.txt', 
                    format = '%(asctime)s.%(msecs)03d - %(message)s',
                    datefmt = '%Y-%m-%d %H:%M:%S',
                    level=logging.DEBUG, )

formatter = logging.Formatter('%(asctime)s.%(msecs)03d-%(name)s-%(filename)s-[line:%(lineno)d]'
                                  '-%(levelname)s-[log info]: %(message)s',
                                  datefmt='%Y-%m-%d,%H:%M:%S')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler) 


if __name__ == "__main__":
    app = wx.App(False)
    mac_address = get_mac_address()
    
    sql_conn = SqlitePool(db_path)
    overlay = CursorOverlay()
    
    frame = MainWindow()
    frame.Show()
    app.MainLoop()