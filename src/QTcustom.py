from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import QThread, QObject
from PySide6.QtWidgets import QVBoxLayout, QTextEdit, QPushButton

import sys
import subprocess
import requests

from .QTstyle import styleSheet

# custom threads
class DownloadAndReportToQTThread(QThread):
    """
    Downloads a file while reporting the actual bytes downloaded
    """

    finished = QtCore.Signal()
    progress = QtCore.Signal(int)

    def __init__(self, link, downloadLocation, parent=None):
        super().__init__(parent)
        self.link = link
        self.downloadLocation = downloadLocation

    def run(self):
        response = requests.get(
            self.link,
            stream=True,
        )
        totalByteSize = int(response.headers["Content-Length"])
        totalSize = 0
        with open(self.downloadLocation, "wb") as f:
            chunk_size = 128
            for chunk in response.iter_content(chunk_size=chunk_size):
                f.write(chunk)
                totalSize += chunk_size
                size = totalSize / totalByteSize * 100
                self.progress.emit(size)
        self.finished.emit()

class SubprocessThread(QThread):
    output = QtCore.Signal(str)

    def __init__(self, command):
        super().__init__()
        self.command = command

    def run(self):
        process = subprocess.Popen(
            self.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        for line in iter(process.stdout.readline, ''):
            self.output.emit(line.strip())
        
        process.stdout.close()
        return_code = process.wait()
        self.output.emit(f"Process finished with return code {return_code}")



# Custom Widgets
class DownloadProgressPopup(QtWidgets.QProgressDialog):
    """
    Runs a download of a file in a thread while reporitng progress to a qt progressbar popup.
    This wont start up in a new process, rather it will just take over the current process
    """

    def __init__(self, link: str, downloadLocation: str, title: str = None):
        super().__init__()
        self.link = link
        self.downloadLocation = downloadLocation
        self.setWindowTitle(title)
        self.setStyleSheet(styleSheet())
        self.setRange(0, 100)
        self.setMinimumSize(300, 100)
        self.setMaximumSize(300, 100)
        customProgressBar = QtWidgets.QProgressBar()
        customProgressBar.setTextVisible(False)
        self.setAttribute(QtCore.Qt.WA_QuitOnClose)
        customProgressBar.setAlignment(QtCore.Qt.AlignCenter)
        self.setBar(customProgressBar)
        self.startDownload()
        self.exec()
        self.workerThread.wait()

    """
    Initializes all threading bs
    """

    def startDownload(self):
        self.workerThread = DownloadAndReportToQTThread(
            link=self.link, downloadLocation=self.downloadLocation
        )
        self.workerThread.progress.connect(self.setProgress)
        self.workerThread.finished.connect(self.close)
        self.workerThread.finished.connect(self.workerThread.deleteLater)
        self.workerThread.finished.connect(self.workerThread.quit)
        self.workerThread.finished.connect(
            self.workerThread.wait
        )  # need quit and wait to allow process to exit safely
        self.canceled.connect(self.cancel_process)

        self.workerThread.start()

    def cancel_process(self):
        QtWidgets.QApplication.quit()
        sys.exit()

    def setProgress(self, value):
        if self.wasCanceled():
            exit()
        self.setValue(value + 10)


class DisplayCommandOutputPopup(QtWidgets.QProgressDialog):
    """
    Runs a download of a file in a thread while reporitng progress to a qt progressbar popup.
    This wont start up in a new process, rather it will just take over the current process
    """

    def __init__(self, command:str, title:str="Running Command"):
        super().__init__()
        self.command = command
        self.setWindowTitle(title)
        self.setStyleSheet(styleSheet())
        self.setRange(0, 100)
        self.setMinimumSize(300, 100)
        self.setMaximumSize(300, 100)
        customProgressBar = QtWidgets.QProgressBar()
        customProgressBar.setTextVisible(False)
        self.setAttribute(QtCore.Qt.WA_QuitOnClose)
        customProgressBar.setAlignment(QtCore.Qt.AlignCenter)
        self.setBar(customProgressBar)
        self.startDownload()
        self.exec()
        self.workerThread.wait()

    """
    Initializes all threading bs
    """

    def startDownload(self):
        self.workerThread = SubprocessThread(
            command=self.command
        )
        self.workerThread.output.connect(self.setProgress)
        self.workerThread.finished.connect(self.close)
        self.workerThread.finished.connect(self.workerThread.deleteLater)
        self.workerThread.finished.connect(self.workerThread.quit)
        self.workerThread.finished.connect(
            self.workerThread.wait
        )  # need quit and wait to allow process to exit safely

        self.workerThread.start()

    def setProgress(self, value):
        
        print(value)


if __name__ == "__main__":
    DownloadProgressPopup(
        link="https://github.com/TNTwise/Rife-Vulkan-Models/releases/download/models/ffmpeg",
        downloadLocation="ffmpeg",
        title="Downloading Python",
    )
