import csv
import logging
import os
import tkinter as tk
from typing import List, Optional
import webbrowser
from queue import Queue
from tkinter.filedialog import askdirectory, asksaveasfilename, askopenfile

from getpaper.GUI.main_frame import MainFrame
from getpaper.config import RESULT_LIST_EN, PROJECT_URL
from getpaper.download import SciHubDownloader
from getpaper.utils import startThread, MyThread

log = logging.getLogger("GetPaper")

class MenuBar(tk.Menu):
    def __init__(self, app):
        """
        Application's MenuBar
        Args:
            app: This application, inherit ttkbootstrap.Style
        """

        super().__init__(app.master)
        self.main_frame: MainFrame = app.main_frame    # for calling main_frame's function
        self.tip = self.main_frame.tip
        self.add_command(label = "数据导出", command = self.saveToFile)
        self.add_command(label = "全部下载", command = self.downloadAll)
        self.add_command(label = "通过DOI下载", command = self.downloadByDoiFile)
        self.add_command(label = "使用说明", command = self.help)

    @startThread("Save_File")
    def saveToFile(self) -> None:
        """
        Save search result to csv file
        Args:
            filename: Name of csv file to save
        """

        if not hasattr(self.main_frame, "result"):
            # ensure searching has been done 
            self.tip.setTip("无搜索结果")
            return

        if filename := asksaveasfilename(defaultextension = ".csv", filetypes = [("csv", ".csv")]): 
            filename = os.path.abspath(filename)
            log.info(f"Save file to file: {filename}")
            try:
                with open(filename, "w", newline = "", encoding = "utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow([s.strip(":\n") for s in RESULT_LIST_EN])
                    writer.writerows(self.main_frame.result)
                self.tip.setTip("保存成功")
            except Exception as e:
                log.error(f"Save {filename} failed: ", e)
                self.tip.setTip("保存失败")

    @startThread("DownloadPapers")
    def downloadAll(self, details:Optional[List[str]] = None) -> None:
        """
        Using SciHubDownloader to get PDFs of all results to specified directory
        Args:
            details: Contain download infomations. (title, *_, doi, _)
        """

        if not details:
            # if no details was set, use main_frame.result
            if not hasattr(self.main_frame, "result"):
                # ensure searching has been done
                self.tip.setTip("无搜索结果")
                return
            details = self.main_frame.result

        if target_dir := askdirectory():
            log.info(f"Downloading all paper to dictory: {os.path.abspath(target_dir)}")
            
            self.tip.setTip("准备下载中...")

            try:
                # create a queue for monitor progress of download
                monitor_queue = Queue(len(details))
                downloader = SciHubDownloader(self.main_frame.scihub_url.get())
                MyThread(tip_set = self.tip.setTip,
                        target = downloader.multiDownload,
                        args = (details, monitor_queue, target_dir),
                        name = "Multi-Download").start()

                self.main_frame.monitor(monitor_queue, len(details))

            finally:
                self.tip.setTip("下载结束")
                self.tip.bar.stop()

    def downloadByDoiFile(self) -> None:
        """
        Using SciHubDownloader to get PDFs from a txt file, each line represent a doi in this file.
        A detail list is uesed to call SciHubDownloader.multiDownload():
            detail[0] is paper's title (as save filename), default to doi
            detail[-2] is doi for download
        """

        if file := askopenfile(filetypes = [("文本文件", ".txt")]):
            dois = file.readlines()
            details = []
            log.info(f"Open file: {file.name}\nNumber of lines:{len(dois)}")
            
            for doi in dois:
                if not doi.startswith("10."):
                    # all valid doi start with "10."
                    continue
                doi = doi.strip()
                # create a detail list, detail[0] = title(as filename), detail[-2] = doi
                details.append([doi.strip(), None, doi.strip(), None])

            log.info(f"Number of loaded doi: {len(details)}")
            self.downloadAll(details)

    def help(self) -> None:
        webbrowser.open_new_tab(PROJECT_URL)
