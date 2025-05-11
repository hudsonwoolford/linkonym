from torch import Tensor
from torch.nn import CosineSimilarity 
from torch import load as torchLoad
import random
import datetime
import os
import FileManager
import Dijkstra
import math

FEAT_SUFFIX_REMOVE = {
    'Number=Plur' : [
        ('s', ''),
        ('es', ''),
        ('ies', 'y')
    ],
    'Tense=Past' : [
        ('d', ''),
        ('d', 'e'),
        ('ed', ''),
        ('ied', 'y')
    ]

}
SIM_CUTOFF = 0.675 #min similarity for word chain
TERMINAL_RANGE = range(100, 10000)
WORD_CATEGORY = {
    "banned" :["PRON", "DET", "CCONJ", "SCONJ", "PART", "PUNCT", "AUX", "INTJ"],
    "halfBanned": ['PROPN', 'NUM'],
    "allowed" : ['ADJ', 'VERB', 'NOUN']
}

#persistant game variables
_nlp = None #natural language processor
_WordData = None #global word data (feature removed)
_OtherData = None #global word info for words with extra features (non feature removed)
_BannedData = None #global banned word data
_DailyData = None #global daily data
_WordAdjacency = None #global word adjacency list

def RandomKey(dic: dict, dataRange: range = None):
    keyList =  list(dic.keys())

    if(dataRange == None):
        dataRange = range(0, len(keyList))
    else:
        dataRange = range(0, min(len(keyList), dataRange.stop), dataRange.step)
    return str(keyList[random.randrange(dataRange.start, dataRange.stop, dataRange.step)])

def HintWord(w1: str, w2: str, wordChain: list) -> str:
    startSim = WordSim(w1, w2)
    if(startSim >= SIM_CUTOFF):
        return w2

    allWords = list(_WordData['vocab'].keys())
    random.shuffle(allWords)
    for w in allWords:
        if(w in wordChain):
            continue
        
        if(WordSim(w1, w) >= SIM_CUTOFF):
            jump = WordSim(w, w2) - startSim
            if(jump > 0.01 and jump < 0.1):
                return w

    print('falling back')
    return SolutionPath(w1, w2, wordChain)[0] #fallback

def SolutionPath(w1: str, w2: str, wordChain: list) -> list[str]:
    id1 = _WordData['vocab'][w1]['id']
    id2 = _WordData['vocab'][w2]['id']
    idChain = [_WordData['vocab'][w]['id'] for w in wordChain]

    allWords = [str(w) for w in _WordData['vocab'].keys()]
    path = Dijkstra.DijkstraPath(_WordAdjacency, id1, id2, idChain[:-1])
    wordPath = [allWords[id] for id in path]

    return wordPath

def TensorCosSimilarity(t1: Tensor, t2: Tensor) -> float:
    cos = CosineSimilarity(dim=0)
    return (float(cos(t1, t2))+1)/2

def WordTensor(word: str):
    global _WordData

    return _WordData["emb"][_WordData["vocab"][word]["id"]]

def ClosestWords(w: str, amount: int = 10, rangeSelect: range = None, searchInfo: dict = _WordData) -> list:
    allWords = list(searchInfo.keys())
    if(w not in allWords): return None
    if(rangeSelect == None): rangeSelect = range(0, len(allWords))
    rangeSelect = range(rangeSelect.start, min(len(allWords), rangeSelect.stop), rangeSelect.step)

    distances = []
    for i in rangeSelect:
        distances.append((allWords[i], WordSim(w, allWords[i], 5)))
    
    distances.sort(key=lambda x: x[1])
    return distances[:amount]

def WordSim(w1: str, w2: str, roundDigits: int = 5):
    return round(TensorCosSimilarity(WordTensor(w1), WordTensor(w2)), roundDigits)

def ValidateWordSim(validatedGuess: str, wordChain: list) -> tuple[bool, str]:
    """
    Takes a **validated** guess as an input. Returns whether it is valid in terms of similarity and a message about the similarity.
    """
    global _WordData

    if(validatedGuess not in _WordData["vocab"].keys()):
        print("Warning: Guess not found, did you make sure to validated?")
        return False, "Tf going on, validation?"
    
    prevWord = wordChain[-1]
    dist = WordSim(prevWord, validatedGuess)
    if(dist >= SIM_CUTOFF):
        return True, f"Chained '{prevWord}' and '{validatedGuess}' ({math.floor(dist*100)}%)"
    else:
        return False, f"'{validatedGuess}' isn't similar enough ({math.floor(dist*100)}%)"

def ValidateGuess(guess: str, wordChain: list) -> tuple[bool, str, str]:
    """
    Checks a guess inputted by user and returns [valid(bool), feedbackMessage(str), modifiedGuess(str)]:
        banned ? false, error message
        not in values ? change word to lemma
            still not in values ? false, error message
    """
    global _WordData, _BannedData

    possibleValues = list(_WordData["vocab"].keys())

    guess = guess.strip().lower() #ensure no weird spaces or casing
    guess = FeatSuffixRemove(guess) #make plur sing and past present

    if(guess in possibleValues):
        if(guess in wordChain):
            return False, f"'{guess}' is already in chain!", guess
    else:
        if(guess in _BannedData["vocab"].keys()):
            return False, f"'{guess}' isn't descriptive enough", guess
        else:
            return False, "I don't know that word", guess

        
    return True, f"Guessed '{guess}.'", guess

def FeatSuffixRemove(word: str):
    if(word not in _OtherData['vocab'].keys()): return word

    for f in FEAT_SUFFIX_REMOVE.keys():
        if(f not in str(_OtherData["vocab"][word]["feats"])):
            continue

        for sufReplace in FEAT_SUFFIX_REMOVE[f]:
            if(word[-len(sufReplace[0]):] == sufReplace[0]):
                newW = word
                newW = newW.removesuffix(sufReplace[0])
                newW += sufReplace[1]
                if(newW in _WordData['vocab'].keys()):
                    return newW

    return word

def FSRDict():
    fsrDict = {}
    wordInfo = _WordData['vocab']
    for i, w in enumerate(wordInfo.keys()):
        fsr = FeatSuffixRemove(w)
        if(fsr in wordInfo.keys() and fsr not in fsrDict.keys()):
            fsrDict[fsr] = wordInfo[fsr]
    
    return fsrDict

def GenerateStartEndWords(maxSimilarity: float = 0.675) -> tuple[str, str]:
    """
    Generates start and end words for game randomly, optional maxSimilarity parameter
    """
    wordInfo = _WordData['vocab']

    end = RandomKey(wordInfo, TERMINAL_RANGE)
    while wordInfo[end]["pos"] in WORD_CATEGORY["halfBanned"]:
        end = RandomKey(wordInfo, TERMINAL_RANGE)


    K = 0
    start = RandomKey(wordInfo, TERMINAL_RANGE)
    while  wordInfo[start]["pos"] in WORD_CATEGORY["halfBanned"] or WordSim(start, end) > maxSimilarity:
        start = RandomKey(wordInfo, TERMINAL_RANGE)
        K+=1
        if(K > 10000):
            print("Warning: Taking too long to determine start and end words, maybe lower minDistance or raise terminal range?")
            break

    return start, end

def LoadWordData(wordPath: str, bannedPath: str, otherPath: str, dailyPath: str, adjacencyPath: str):
    global _WordData, _BannedData, _DailyData, _OtherData, _WordAdjacency

    _WordData = torchLoad(wordPath)
    _BannedData = torchLoad(bannedPath)
    _DailyData = FileManager.LoadJsonDict(dailyPath)
    _WordAdjacency = torchLoad(adjacencyPath)
    _OtherData = torchLoad(otherPath)

    # _WordData["vocab"] = StanzaUtility.LemmatarizedDict(_WordData["vocab"]) #get lemma only

def CreateDailyGames(amount: int, seed: int) -> dict:
    random.seed(seed)
    currentTime = datetime.datetime.now()
    dailyGames = {}

    for i in range(0, amount):
        currentDate = str((currentTime + datetime.timedelta(i)).date())

        start, end = GenerateStartEndWords(minDistance=0.5)
        dailyGames[currentDate] = f"{start}, {end}"
    
    return dailyGames

#get word data
baseDir = os.path.dirname(os.path.abspath(__file__))
LoadWordData(os.path.join(baseDir,'data/WikipediaWData.pt'), os.path.join(baseDir,'data/WikipediaBData.pt'),  os.path.join(baseDir,'data/WikipediaOData.pt'), os.path.join(baseDir, 'data/DailyGames.json'), os.path.join(baseDir, 'data/WordAdjacency.pt'))

# dailyGames = CreateDailyGames(365, 0)
# import FileManager
# FileManager.SaveJsonDict(dailyGames, 'data/DailyGames.json')




# LoadWordData('output/WikipediaWData.pt','output/WikipediaBData.pt')
# while True:
#     print(ClosestWords(input("Word: "), amount=50))

# InitializeGame()
# print(ValidateGuess("fire"))
# print(GuessWord("fire"))
# print(_WordChain)

#start of program
# data = FileManager.GetPretrainDict()


# chain = "par -> golf -> hole -> circle -> ball -> small -> tiny -> big -> large -> huge -> explosion -> bomb -> atomic"
# words = chain.split(" -> ")
# embeds = []
# for w in words:
#     embeds.append(WordTensor(w))

# fig = Utility.GraphVectors2D(words, torch.stack(embeds), perplexity=7)
# plt.show()

# topNouns = open("input/top_english_nouns_lower_10000.txt", 'r', encoding='utf-8').read().split('\n')
# StanzaUtility.PossibleWordsToJson(topNouns, data["vocab"]["_unit2id"], "WordList.json", minLength=3, maxLength=10)
# WordListToInfo()

# DataToWordList(data, range(0, 100000))
# WordListToInfo()




    

"""
fully banned:
PRON - No, things like you, he, them - not interesting
DET
CCONJ
SCONJ
PART
PUNCT

half banned:
PROPN - No, because I feel like things like "joseph" makes no sense
NUM - No

allowed:
ADJ - Yeah
VERB - Yeah
NOUN - Yeah
"""