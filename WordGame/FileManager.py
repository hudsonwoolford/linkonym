import stanza.resources.common
import torch
import json

def GetPretrainDict() -> dict:
    lang = 'en'

    #find torch embed file
    modelDir = stanza.resources.common.DEFAULT_MODEL_DIR
    embedPath = f"{modelDir}\{lang}\pretrain\conll17.pt"

    #load data
    data = torch.load(embedPath)
    return data

def LoadJsonDict(path: str) -> dict:
    return json.load(open(path, 'r', encoding="utf-8"))

def SaveJsonDict(dic: dict, path: str, mode: str = 'w') -> None:
    f = open(path, mode, encoding='utf-8')
    json.dump(dic, f, ensure_ascii=False, indent=4)
    f.close()

def LoadPTFile(path: str):
    return torch.load(path)


