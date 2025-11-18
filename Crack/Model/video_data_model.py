from PySide6.QtWidgets import QTableWidgetItem

class VideoDataModel:
    counter = 1

    def __init__(self, filePath, fileName, videoInfo, editInfo, cropList = [], status = 'Waiting', result = 'None'):
        self.no = VideoDataModel.counter
        VideoDataModel.counter += 1

        self.filePath = QTableWidgetItem(filePath)
        self.fileName = QTableWidgetItem(fileName)
        self.videoInfo = QTableWidgetItem(videoInfo)
        self.editInfo = QTableWidgetItem(editInfo)

        self.cropList = cropList

        # status : Waiting, Image Stitching, Crack Detecting, Completed
        self.status = QTableWidgetItem(status)
        self.result = QTableWidgetItem(result)
        
    def __repr__(self): 
        return (f"VideoDataModel(no={self.no}, filePath={self.filePath.text()}, " 
                f"fileName={self.fileName.text()}, videoInfo={self.videoInfo.text()}, editInfo={self.editInfo.text()}, " 
                f"status={self.status.text()}, result={self.result.text()})")