import json

def LoadJsonDict(path: str) -> dict:
    return json.load(open(path, 'r', encoding="utf-8"))

def SaveJsonDict(dic: dict, path: str, mode: str = 'w', indent:int=4) -> None:
    f = open(path, mode, encoding='utf-8')
    json.dump(dic, f, ensure_ascii=False, indent=indent)
    f.close()



