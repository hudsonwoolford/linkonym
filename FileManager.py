import json



def LoadJsonDict(path: str) -> dict:
    return json.load(open(path, 'r', encoding="utf-8"))

def SaveJsonDict(dic: dict, path: str, mode: str = 'w') -> None:
    f = open(path, mode, encoding='utf-8')
    json.dump(dic, f, ensure_ascii=False, indent=4)
    f.close()



