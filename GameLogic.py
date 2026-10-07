import random
import datetime
import Dijkstra
import math
import WordManager as wm

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
    "halfBanned": ['PROPN', 'NUM', 'VERB', 'ADJ'],
    "allowed" : ['ADJ', 'VERB', 'NOUN']
}

def RandomKey(dic: dict, dataRange: range = None):
    keyList =  list(dic.keys())

    if(dataRange == None):
        dataRange = range(0, len(keyList))
    else:
        dataRange = range(0, min(len(keyList), dataRange.stop), dataRange.step)
    return str(keyList[random.randrange(dataRange.start, dataRange.stop, dataRange.step)])

def HintWord(w1: str, w2: str, wordChain: list) -> str:
    startSim = wm.WordSim(w1, w2)
    if(startSim >= SIM_CUTOFF):
        return w2

    allWords = list(wm._WordData['vocab'].keys())
    random.shuffle(allWords)
    for w in allWords:
        if(w in wordChain):
            continue
        
        if(wm.WordSim(w1, w) >= SIM_CUTOFF):
            jump = wm.WordSim(w, w2) - startSim
            if(jump > 0.01 and jump < 0.1):
                return w

    print('falling back')
    return SolutionPath(w1, w2, wordChain)[0] #fallback

def SolutionPath(w1: str, w2: str, wordChain: list) -> list[str]:
    id1 = wm._WordData['vocab'][w1]['id']
    id2 = wm._WordData['vocab'][w2]['id']
    idChain = [wm._WordData['vocab'][w]['id'] for w in wordChain]

    allWords = [str(w) for w in wm._WordData['vocab'].keys()]
    path = Dijkstra.DijkstraPath(wm._WordAdjacency, id1, id2, idChain[:-1])
    wordPath = [allWords[id] for id in path]

    return wordPath

def ClosestWords(w: str, amount: int = 10, rangeSelect: range = None, searchInfo: dict = wm._WordData) -> list:
    allWords = list(searchInfo.keys())
    if(w not in allWords): return None
    if(rangeSelect == None): rangeSelect = range(0, len(allWords))
    rangeSelect = range(rangeSelect.start, min(len(allWords), rangeSelect.stop), rangeSelect.step)

    distances = []
    for i in rangeSelect:
        distances.append((allWords[i], wm.WordSim(w, allWords[i], 5)))
    
    distances.sort(key=lambda x: x[1])
    return distances[:amount]

def ValidateWordSim(validatedGuess: str, wordChain: list) -> tuple[bool, str]:
    """
    Takes a **validated** guess as an input. Returns whether it is valid in terms of similarity and a message about the similarity.
    """

    if(validatedGuess not in wm._WordData["vocab"].keys()):
        print("Warning: Guess not found, did you make sure to validated?")
        return False, "Tf going on, validation?"
    
    prevWord = wordChain[-1]
    dist = wm.WordSim(prevWord, validatedGuess)
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

    possibleValues = list(wm._WordData["vocab"].keys())

    guess = guess.strip().lower() #ensure no weird spaces or casing
    guess = FeatSuffixRemove(guess) #make plur sing and past present

    if(guess in possibleValues):
        if(guess in wordChain):
            return False, f"'{guess}' is already in chain!", guess
    else:
        if(guess in wm._BannedData["vocab"].keys()):
            return False, f"'{guess}' isn't descriptive enough", guess
        else:
            return False, "I don't know that word", guess

        
    return True, f"Guessed '{guess}.'", guess

def FeatSuffixRemove(word: str):
    if(word not in wm._OtherData['vocab'].keys()): return word

    for f in FEAT_SUFFIX_REMOVE.keys():
        if(f not in str(wm._OtherData["vocab"][word]["feats"])):
            continue

        for sufReplace in FEAT_SUFFIX_REMOVE[f]:
            if(word[-len(sufReplace[0]):] == sufReplace[0]):
                newW = word
                newW = newW.removesuffix(sufReplace[0])
                newW += sufReplace[1]
                if(newW in wm._WordData['vocab'].keys()):
                    return newW

    return word

def FSRDict():
    fsrDict = {}
    wordInfo = wm._WordData['vocab']
    for i, w in enumerate(wordInfo.keys()):
        fsr = FeatSuffixRemove(w)
        if(fsr in wordInfo.keys() and fsr not in fsrDict.keys()):
            fsrDict[fsr] = wordInfo[fsr]
    
    return fsrDict

def GenerateStartEndWords(maxSimilarity: float = 0.675) -> tuple[str, str]:
    """
    Generates start and end words for game randomly, optional maxSimilarity parameter
    """
    wordInfo = wm._WordData['vocab']

    end = FeatSuffixRemove(RandomKey(wordInfo, TERMINAL_RANGE))
    while wordInfo[end]["pos"] in WORD_CATEGORY["halfBanned"]:
        end = FeatSuffixRemove(RandomKey(wordInfo, TERMINAL_RANGE))


    K = 0
    start = FeatSuffixRemove(RandomKey(wordInfo, TERMINAL_RANGE))
    while  wordInfo[start]["pos"] in WORD_CATEGORY["halfBanned"] or wm.WordSim(start, end) > maxSimilarity:
        start = FeatSuffixRemove(RandomKey(wordInfo, TERMINAL_RANGE))
        K+=1
        if(K > 10000):
            print("Warning: Taking too long to determine start and end words, maybe lower minDistance or raise terminal range?")
            break

    return start, end

def CreateDailyGames(amount: int, seed: int) -> dict:
    random.seed(seed)
    currentTime = datetime.datetime.now()
    dailyGames = {}

    for i in range(0, amount):
        currentDate = str((currentTime + datetime.timedelta(i)).date())

        start, end = GenerateStartEndWords(maxSimilarity=0.5)
        dailyGames[currentDate] = f"{start}, {end}"
    
    return dailyGames

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