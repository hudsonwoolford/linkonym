from torch import Tensor
from torch.nn import CosineSimilarity 
from torch import load as torchLoad
import random
import datetime
import os
import FileManager

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
DISTANCE_CUTOFF = 0.325 #max distance for word chain
TERMINAL_RANGE = range(100, 10000)
WORD_CATEGORY = {
    "banned" :["PRON", "DET", "CCONJ", "SCONJ", "PART", "PUNCT", "AUX", "INTJ"],
    "halfBanned": ['PROPN', 'NUM'],
    "allowed" : ['ADJ', 'VERB', 'NOUN']
}

#persistant game variables
_nlp = None #natural language processor
_WordData = None #global word data
_FSRWordInfo = None #global word info for only lemma
_BannedData = None #global banned word data
_DailyData = None #global daily data

def RandomKey(dic: dict, dataRange: range = None):
    keyList =  list(dic.keys())

    if(dataRange == None):
        dataRange = range(0, len(keyList))
    else:
        dataRange = range(0, min(len(keyList), dataRange.stop), dataRange.step)
    return str(keyList[random.randrange(dataRange.start, dataRange.stop, dataRange.step)])

def HintWord(w1: str, w2: str, wordChain: list, maxDistanceJump: float = 0.25, chunkSize: int = 10000) -> str:
    t1 = _WordData['emb'][_WordData['vocab'][w1]['id']]
    t2 = _WordData['emb'][_WordData['vocab'][w2]['id']]
    
    currentChunk = 0

    while currentChunk < len(_WordData['vocab'].keys()):
        currentDist = TensorCosSimilarity(t1, t2)

        twentyClosest = ClosestWords(w1, 30, rangeSelect=range(currentChunk, currentChunk+chunkSize), searchInfo=_FSRWordInfo)
        bestGuess = ("PLACEHOLDER", 1000)
        #calculate distances from all closest to the target
        for worddist in twentyClosest:
            #barriers from being valid
            if(worddist[0] == w2): continue #cant be target
            if(worddist[1] > DISTANCE_CUTOFF): continue #cant be a guess out of range
            if(worddist[0] in wordChain): continue #cant be already guessed

            t = _WordData['emb'][_WordData['vocab'][worddist[0]]['id']]
            dist = TensorCosSimilarity(t, t2)

            #skip if the hint is too good
            if(currentDist - dist > maxDistanceJump): continue

            
            if(bestGuess[1] > dist):
                bestGuess = (worddist[0], dist)

        if(currentDist - bestGuess[1] <= maxDistanceJump):
            return bestGuess[0]
        else:
            currentChunk += chunkSize
    
    return 'FAILFAILFAIL'

def TensorCosSimilarity(t1: Tensor, t2: Tensor) -> float:
    cos = CosineSimilarity(dim=0)
    return (1-float(cos(t1, t2)))/2

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

def ValidateWordDist(validatedGuess: str, wordChain: list) -> tuple[bool, str]:
    """
    Takes a **validated** guess as an input. Returns whether it is valid in terms of distance and a message about the distance.
    """
    global _WordData

    if(validatedGuess not in _WordData["vocab"].keys()):
        print("Warning: Guess not found, did you make sure to validated?")
        return False, "Tf going on, validation?"
    
    prevWord = wordChain[-1]
    dist = WordSim(prevWord, validatedGuess)
    if(dist <= DISTANCE_CUTOFF):
        return True, f"Chained '{prevWord}' -> '{validatedGuess}' ({round(dist, 3)})"
    else:
        return False, f"Failed to chain '{validatedGuess}' ({round(dist, 3)} is too far)"
    

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
    if(guess in possibleValues):
        guess = FeatSuffixRemove(guess) #make plur sing and past present
        if(guess in wordChain):
            return False, f"'{guess}' is already in chain!", guess
    else:
        if(guess in _BannedData["vocab"].keys()):
            return False, f"'{guess}' isn't descriptive enough.", guess
        else:
            return False, "I don't know that word!", guess

        
    return True, f"Guessed '{guess}.'", guess

def FeatSuffixRemove(word: str):

    for f in FEAT_SUFFIX_REMOVE.keys():
        if(f not in str(_WordData["vocab"][word]["feats"])):
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

def GenerateStartEndWords(minDistance: float = 0.325) -> tuple[str, str]:
    """
    Generates start and end words for game randomly, optional minDistance parameter
    """

    end = RandomKey(_FSRWordInfo, TERMINAL_RANGE)
    while _FSRWordInfo[end]["pos"] in WORD_CATEGORY["halfBanned"]:
        end = RandomKey(_FSRWordInfo, TERMINAL_RANGE)


    K = 0
    start = RandomKey(_FSRWordInfo, TERMINAL_RANGE)
    while  _FSRWordInfo[start]["pos"] in WORD_CATEGORY["halfBanned"] or WordSim(start, end) < minDistance:
        start = RandomKey(_FSRWordInfo, TERMINAL_RANGE)
        K+=1
        if(K > 10000):
            print("Warning: Taking too long to determine start and end words, maybe lower minDistance or raise terminal range?")
            break

    return start, end


def LoadWordData(wordPath: str, bannedPath: str, dailyPath: str):
    global _WordData, _BannedData, _DailyData, _FSRWordInfo

    _WordData = torchLoad(wordPath)
    _BannedData = torchLoad(bannedPath)
    _DailyData = FileManager.LoadJsonDict(dailyPath)
    _FSRWordInfo = FSRDict()

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
LoadWordData(os.path.join(baseDir,'data/WikipediaWData.pt'), os.path.join(baseDir,'data/WikipediaBData.pt'), os.path.join(baseDir, 'data/DailyGames.json'))

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