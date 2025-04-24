#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  @Time    : 2025-01-17 21:30
#  @Author  : yanmin
#  @Site    :
#  @File    : .py
#  @Software: vscode
import wx
import sys
import os
import csv
import uuid
import sqlite3
import wx.grid as gridlib
from PIL import Image
import pillow_avif
import zipfile
import platform
from pathlib import Path
from images_plugin import ThumbnailFrame

path_cache = './_cache/'
TABLE_NAME = "TRACK"
db_path = "./trackDB.db"

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

class SQLiteBrowser(wx.Frame):
    def __init__(self, *args, **kw):
        super(SQLiteBrowser, self).__init__(*args, **kw)

        self.InitUI()
        self.conn = None

    def InitUI(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_open = wx.Button(panel, label="Load exist track:")
        self.btn_open.Bind(wx.EVT_BUTTON, self.OnOpen)
        hbox1.Add(self.btn_open, flag=wx.LEFT, border=10)
        vbox.Add(hbox1, flag=wx.EXPAND | wx.TOP | wx.BOTTOM, border=10)

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.listbox1 = wx.ListBox(panel)
        self.listbox1.Bind(wx.EVT_LISTBOX, self.OnTableSelected)
        hbox2.Add(self.listbox1, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
        
        self.listbox2 = wx.ListBox(panel, style = wx.LB_HSCROLL|wx.LB_ALWAYS_SB)
        #self.listbox2 = wx.ListBox(panel, style = wx.LB_MULTIPLE|wx.LB_HSCROLL|wx.LB_ALWAYS_SB)
        self.listbox2.Bind(wx.EVT_LISTBOX, self.OnColumnSelected)
        hbox2.Add(self.listbox2, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)

        vbox.Add(hbox2, proportion=1, flag=wx.EXPAND)

        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        #self.text_ctrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE)
        #hbox3.Add(self.text_ctrl, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
        self.btn_exec = wx.Button(panel, label="Delete select track")
        self.btn_exec.Bind(wx.EVT_BUTTON, self.OnExecuteSQL)
        hbox3.Add(self.btn_exec, flag=wx.LEFT, border=10)
        vbox.Add(hbox3, proportion=1, flag=wx.EXPAND)

        hbox4 = wx.BoxSizer(wx.HORIZONTAL)
        
        self.grid = gridlib.Grid(panel)
        self.grid.CreateGrid(5, 6)
        hbox4.Add(self.grid, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
        vbox.Add(hbox4, proportion=3, flag=wx.EXPAND)
        
        
        hbox5 = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_Next = wx.Button(panel, label="Export select track")
        self.btn_Next.Bind(wx.EVT_BUTTON, self.OnNext)
        hbox5.Add(self.btn_Next, flag=wx.LEFT, border=10)
        vbox.Add(hbox5, proportion=3, flag=wx.EXPAND)
        
        panel.SetSizer(vbox)   
        
        self.SetTitle('Track Browser')
        self.SetSize((800, 600))
        self.Centre()
        
    def get_mac_address(self):
        """Cross-platform MAC address retrieval"""
        try:
            #mac = hex(uuid.getnode()).replace('0x', '').upper()
            mac = uuid.UUID(int=uuid.getnode()).hex[-12:].upper()
            return '-'.join([mac[i:i+2] for i in range(0, 11, 2)])
        except Exception as e:
            wx.MessageBox(f"MAC retrieval failed: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
            return "00-00-00-00-00-00"
            
    def create_zip(self, output_zip: str, files_to_zip: list) -> None:
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in files_to_zip:
                file_path = Path(file)
                try:
                    zipf.write(file_path, arcname=file_path.name)
                except Exception as e:
                    print(f"zip : {e}")
                    continue
                    #return 0

    def OnOpen(self, event):
        self.conn = sqlite3.connect(db_path, uri=True, timeout=10, check_same_thread=False)
        self.LoadTables()
    def LoadTables(self):
        if self.conn:
            cursor = self.conn.cursor()
            #cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            #cursor.execute("SELECT * FROM TRACK;")
            cursor.execute("SELECT TIME FROM TRACK;")
            tables = [row[0] for row in cursor.fetchall()]
            _set = set(tables)
            new_tables = sorted(_set, key=tables.index)
            self.listbox1.Set(new_tables)

    def OnTableSelected(self, event):
        table_name = self.listbox1.GetStringSelection()
        if self.conn:
            cursor = self.conn.cursor()
            #cursor.execute(f"PRAGMA table_info({table_name})")
            #select_sql= "SELECT TIMESTEMP FROM TRACK where TIME= \"{}\";".format(table_name)
            select_sql= "SELECT TIMEGROUP FROM TRACK where TIME= \"{}\";".format(table_name)
            cursor.execute(select_sql)
            #cursor.execute("SELECT TIMESTEMP FROM TRACK where TIME={table_name};")
            columns1 = [row[0] for row in cursor.fetchall()]
            #columns2 = [row[5] for row in cursor.fetchall()]
            _set = set(columns1)
            new_tables = sorted(_set, key=columns1.index)
            self.listbox2.Set(new_tables)

    def OnColumnSelected(self, event):
        column_name = self.listbox2.GetStringSelection()
        column_day = column_name[:16]
        sql_query= "SELECT IMG_PATH FROM TRACK where TIMEGROUP BETWEEN \"{}\" AND \"{}\";".format(column_day, column_name)
        results = []
        if self.conn and sql_query.strip():
            cursor = self.conn.cursor()
            try:
                cursor.execute(sql_query)
                results = cursor.fetchall()
                self.DisplayResults(results)
            except sqlite3.Error as e:
                wx.MessageBox(f"An error occurred: {e}", "Error", wx.OK | wx.ICON_ERROR)
        frame = ThumbnailFrame(None, "Time rangs:[" + column_day + "] Images", results, path_cache)
        frame.Show()
        

    def OnExecuteSQL(self, event):
        column_name = self.listbox2.GetStringSelection()
        column_day = column_name[:16]
        #sql_query= "delete from TRACK where TIMESTEMP= \"{}\";".format(column_name)
        sql_query= "delete from TRACK where TIMEGROUP BETWEEN \"{}\" AND \"{}\";".format(column_day, column_name)
        if self.conn and sql_query.strip():
            cursor = self.conn.cursor()
            try:
                cursor.execute(sql_query)
                self.conn.commit()
                self.grid.ClearGrid()
                #results = cursor.fetchall()
                #self.DisplayResults(results)
                #self.OnColumnSelected(None)
            except sqlite3.Error as e:
                wx.MessageBox(f"An error occurred: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def OnNext(self, event):
        selected_dir = "./_cache/"
        dialog = wx.DirDialog(self, "please select Dir", style=wx.DD_DEFAULT_STYLE)
        if dialog.ShowModal() == wx.ID_OK:
            selected_dir = dialog.GetPath()
            wx.MessageBox(f"select Dir:\n{selected_dir}\n  Compressing files... \n Please wait for a few minutes", "Tips", wx.OK)
        dialog.Destroy()
        self.Waiting()

        all_items = self.listbox2.GetItems()

        for selection in all_items:
            list_urls = []
            list_upload = []
            csv_name = path_cache + self.get_mac_address() + "_" + selection + '.csv'
            cursor = self.conn.cursor()
            select_sql= "SELECT * FROM TRACK where TIMEGROUP= \"{}\";".format(selection)
            cursor.execute(select_sql)
            #cursor.execute("SELECT TIMESTEMP FROM TRACK where TIME={table_name};")
            rows = cursor.fetchall()
            with open(csv_name, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(rows)
                
            list_urls = [row[5] for row in rows]
            _set = set(list_urls)
            new_list_urls = sorted(_set, key=list_urls.index)
            #cursor.close()
            try:
                for i in new_list_urls:
                    img_name = path_cache + i
                    JPGimg = Image.open(path_cache + i)
                    JPGimg.save(img_name.replace("png",'avif'),'AVIF')
                    list_upload.append(img_name.replace("png",'avif'))
                list_upload.append(csv_name)
                list_upload.append('ID.txt')
            except Exception as e:
                self.Waited()
                wx.MessageBox(f"An error occurred: {e}", "Error", wx.OK | wx.ICON_ERROR)
                return
            
            flag = 1
            flag = self.create_zip(selected_dir + "/" + self.get_mac_address() + "_" + selection + ".zip", list_upload)
            if (flag==False):
                toastone = wx.MessageDialog(None, "Compressing files failed! \n {}".format(i), "zip", wx.YES_DEFAULT | wx.ICON_QUESTION)
                if toastone.ShowModal() == wx.ID_YES:  
                    toastone.Destroy()  
                self.Waited()
                return 
        for selection in all_items:
            sql_query= "delete from TRACK where TIMEGROUP= \"{}\";".format(selection)
            if sql_query.strip():
                cursor = self.conn.cursor()
                try:
                    cursor.execute(sql_query)
                    self.conn.commit()
                    cursor.close()
                except sqlite3.Error as e:
                    wx.MessageBox(f"An error occurred: {e}", "Error", wx.OK | wx.ICON_ERROR)
                    cursor.close()
                    self.Waited()
                    return

        self.grid.ClearGrid()
        self.Waited()
        wx.MessageBox(f"Dir:\n{selected_dir}\n  Compressing files successfully！", "Tips", wx.OK)
        
    def DisplayResults(self, results):
        self.grid.ClearGrid()
        if results:
            rows = len(results)
            cols = len(results[0])
            #self.grid.ClearGrid()
            if rows > self.grid.GetNumberRows():
                self.grid.AppendRows(rows - self.grid.GetNumberRows())
            if cols > self.grid.GetNumberCols():
                self.grid.AppendCols(cols - self.grid.GetNumberCols())

            for i, row in enumerate(results):
                for j, value in enumerate(row):
                    self.grid.SetCellValue(i, j, str(value))
                    
    def Waiting(self):
        self.btn_open.Disable()
        self.btn_exec.Disable()
        self.btn_Next.Disable()
        self.listbox1.Disable()
        self.listbox2.Disable()
        self.grid.Disable()

    def Waited(self):
        self.btn_open.Enable()
        self.btn_exec.Enable()
        self.btn_Next.Enable()
        self.listbox1.Enable()
        self.listbox2.Enable()
        self.grid.Enable()

if __name__ == '__main__':
    app = wx.App(False)
    frame = SQLiteBrowser(None)
    frame.Show(True)
    app.MainLoop()
