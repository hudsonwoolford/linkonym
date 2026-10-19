import FileManager as FileManager
import os
import torch
from torch import load as torchLoad

_WordData = None #global word data (feature removed)
_OtherData = None #global word info for words with extra features (non feature removed)
_BannedData = None #global banned word data
_DailyData = None #global daily data
_WordAdjacency = None #global word adjacency list

def TensorCosSimilarity(t1: torch.Tensor, t2: torch.Tensor) -> float:
    cos = float(torch.dot(t1, t2) / (torch.norm(t1, dim=0)*torch.norm(t2, dim=0)))
    return (cos+1)/2

def IDTensor(id: int):
    return _WordData["emb"][id]

def WordTensor(word: str):
    return IDTensor(_WordData["vocab"][word]["id"])

def WordSim(w1: str, w2: str, roundDigits: int = 5):
    return round(TensorCosSimilarity(WordTensor(w1), WordTensor(w2)), roundDigits)

def ID2Word(id: int):
    """
    Binary search for index
    """

    values = list(_WordData['vocab'].values())
    low = 0
    high = len(values) - 1
    index = -1
    while low<=high and index == -1:
        mid = (low+high)//2

        if(values[mid] == id):
            index = mid
        elif(values[mid] < id):
            low = mid + 1
        else:
            high = mid - 1
    
    return list(_WordData['vocab'].keys())[index] if not id == -1 else None

def LoadWordData(wordPath: str, bannedPath: str, otherPath: str, dailyPath: str, adjacencyPath: str):
    global _WordData, _BannedData, _DailyData, _OtherData, _WordAdjacency

    _WordData = torchLoad(wordPath)
    _BannedData = torchLoad(bannedPath)
    _WordAdjacency = torchLoad(adjacencyPath)
    _OtherData = torchLoad(otherPath)
    _DailyData = FileManager.LoadJsonDict(dailyPath)
    print('loaded')


baseDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LoadWordData(os.path.join(baseDir,'data/2024_WikipediaWData.pt'), os.path.join(baseDir,'data/2024_WikipediaBData.pt'),  os.path.join(baseDir,'data/WikipediaOData.pt'), os.path.join(baseDir, 'data/DailyGames.json'), os.path.join(baseDir, 'data/WordAdjacency.pt'))
