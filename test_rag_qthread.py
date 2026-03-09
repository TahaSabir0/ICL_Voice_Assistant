import os
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
from PySide6.QtCore import QThread, Signal, QObject, QCoreApplication
import sys

class Worker(QObject):
    finished = Signal()
    def __init__(self):
        super().__init__()
    def run(self):
        print('Worker starting')
        try:
            from src.rag.retriever import Retriever
            print('Retriever imported')
            r = Retriever()
            print('Retriever initialized')
            res = r.get_context('what is ICL?')
            print('Result:', len(res))
        except Exception as e:
            print('Error:', e)
        self.finished.emit()

app = QCoreApplication(sys.argv)
thread = QThread()
worker = Worker()
worker.moveToThread(thread)
thread.started.connect(worker.run)
worker.finished.connect(thread.quit)
thread.finished.connect(app.quit)
thread.start()
app.exec()
