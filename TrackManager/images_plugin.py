#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  @Time    : 2025-01-17 21:30
#  @Author  : yanmin
#  @Site    :
#  @File    : .py
#  @Software: vscode
#!/usr/bin/env python
import os
from PIL import Image
import io
import wx

class ThumbnailFrame(wx.Frame):
    def __init__(self, parent, title, image_folder, image_path):
        super().__init__(parent, title=title, size=(800, 600))
        
        self.panel = wx.ScrolledWindow(self)
        self.panel.SetScrollbars(1, 1, 1, 1)
        
        self.grid_sizer = wx.GridSizer(rows=0, cols=1, hgap=10, vgap=10)
        self.panel.SetSizer(self.grid_sizer)
        
        # load image
        self.load_images(image_folder, image_path)
        #self.image_path = image_path
        
    def load_images_folder(self, folder_path):
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                image_path = os.path.join(folder_path, filename)
                try:
                    with Image.open(image_path) as img:
                        img.thumbnail((150, 150))
                        # change images wx.Bitmap
                        width, height = img.size
                        img_data = io.BytesIO()
                        img.save(img_data, format='PNG')
                        img_data = img_data.getvalue()
                        wx_image = wx.Image(io.BytesIO(img_data))
                        bitmap = wx_image.ConvertToBitmap()
                        
                        img_button = wx.BitmapButton(self.panel, bitmap=bitmap)
                        img_button.SetToolTip(filename)
                        
                        self.grid_sizer.Add(img_button, 0, wx.ALL, 5)
                except Exception as e:
                    print(f"Error loading image {filename}: {str(e)}")
        
        self.panel.Layout()
        
    def load_images(self, filename_list, image_cache_path):
        for filename in filename_list:
            #if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            #    image_path = filename
            if filename[0].lower().endswith(('.png', '.jpg', '.jpeg')):
                image_path = filename[0]
                #image_path = "./_cache/" + image_path
                image_path = image_cache_path + image_path
                
                try:
                    with Image.open(image_path) as img:
                        img.thumbnail((750, 500))
                        # wx.Bitmap
                        width, height = img.size
                        img_data = io.BytesIO()
                        img.save(img_data, format='PNG')
                        img_data = img_data.getvalue()
                        wx_image = wx.Image(io.BytesIO(img_data))
                        bitmap = wx_image.ConvertToBitmap()
                        
                        img_button = wx.BitmapButton(self.panel, bitmap=bitmap)
                        #img_button.SetToolTip(filename)
                        self.grid_sizer.Add(img_button, 0, wx.ALL, 5)
                except Exception as e:
                    print(f"Error loading image {filename}: {str(e)}")
        
        self.panel.Layout()
