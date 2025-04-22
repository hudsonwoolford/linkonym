import stanza
import torch
import StanzaUtility
import json
import Utility

DISTANCE_CUTOFF = 0.325 #max distance for word chain
TERMINAL_RANGE = range(100, 10000)
LEMMA_INPUT = False
WORD_CATEGORY = {
    "banned" :["PRON", "DET", "CCONJ", "SCONJ", "PART", "PUNCT", "AUX", "INTJ"],
    "halfBanned": ['PROPN', 'NUM'],
    "allowed" : ['ADJ', 'VERB', 'NOUN']
}

#persistant game variables
_nlp = None #natural language processor
_WordData = None #global word data
_BannedData = None #global banned word data

#temp game variables
_TargetWord = "" #current target word
_StartWord = "" #current start word
_WordChain = [] #current chain of words

#ensure model is downloaded
# stanza.download('en')


def WordListToInfo():
    wordList = dict(json.load(open("output/WordList.json", 'r', encoding="utf-8")))
    StanzaUtility.WordInfoJson(wordList["_word2id"], "WordInfo.json", filter = ["VERB", "NOUN", "ADJ"])

def TensorCosSimilarity(t1: torch.Tensor, t2: torch.Tensor) -> float:
    cos = torch.nn.CosineSimilarity(dim=0)
    return (1-float(cos(t1, t2)))/2

def WordTensor(word: str):
    global _WordData

    return _WordData["emb"][_WordData["vocab"][word]["id"]]

def ClosestWords(w: str, amount: int = 10) -> list:
    if(w not in _WordData["vocab"].keys()): return None

    distances = []
    for word in _WordData["vocab"].keys():
        distances.append((word, WordSim(w, word, 5)))
    
    distances.sort(key=lambda x: x[1])
    return distances[:amount]

def WordSim(w1: str, w2: str, roundDigits: int = 5):
    return round(TensorCosSimilarity(WordTensor(w1), WordTensor(w2)), roundDigits)

def GuessWord(validatedGuess: str) -> tuple[bool, str]:
    """
    Takes a **validated** guess as an input. Returns whether it was added and a message about the distance.
    """
    global _WordData

    if(validatedGuess not in _WordData["vocab"].keys()):
        print("Warning: Guess not found, did you make sure to validated?")
        return False, "Tf going on, validation?"
    
    prevWord = _WordChain[-1]
    dist = WordSim(prevWord, validatedGuess)
    if(dist <= DISTANCE_CUTOFF):
        _WordChain.append(validatedGuess)
        return True, f"Chained '{prevWord}' -> '{validatedGuess}' ({round(dist, 3)})"
    else:
        return False, f"Failed to chain '{validatedGuess}' ({round(dist, 3)} is too far)"
    

def ValidateGuess(guess: str) -> tuple[bool, str, str]:
    """
    Checks a guess inputted by user and returns [valid(bool), feedbackMessage(str), modifiedGuess(str)]:
        banned ? false, error message
        not in values ? change word to lemma
            still not in values ? false, error message
    """
    global _WordData, _BannedData

    possibleValues = list(_WordData["vocab"].keys())
    chainValues = _WordChain #cannot go back on the word chain

    guess = guess.strip().lower() #ensure no weird spaces or casing
    if(guess in possibleValues):
        guess = RemoveFeatureSuffix(guess, "Number=Plur", "s") #make plur sing
        guess = RemoveFeatureSuffix(guess, "Tense=Past", "ed") #make past present
        if(guess in chainValues):
            return False, f"'{guess}' is already in chain!", guess
    else:
        if(guess in _BannedData["vocab"].keys()):
            return False, f"'{guess}' isn't descriptive enough.", guess
        else:
            return False, "I don't know that word!", guess

        
    return True, f"Guessed '{guess}.'", guess

def RemoveFeatureSuffix(word: str, feat: str, suffix: str):
    if(feat in str(_WordData["vocab"][word]["feats"])):
        noSWord = word.removesuffix(suffix)
        if(noSWord in _WordData["vocab"].keys()):
            word = noSWord
    
    return word
    
def GenerateStartEndWords(minDistance: float = 0.325) -> tuple:
    """
    Generates start and end words for game randomly, optional minDistance parameter
    """
    global _WordChain, _WordData, _StartWord, _TargetWord

    if(len(_WordChain)>0):
        print("Warning: Word chain should be empty when calling GenerateStartEndWords")

    end = Utility.RandomKey(_WordData["vocab"], TERMINAL_RANGE)
    while _WordData["vocab"][end]["pos"] in WORD_CATEGORY["halfBanned"]:
        end = Utility.RandomKey(_WordData["vocab"], TERMINAL_RANGE)

    start = Utility.RandomKey(_WordData["vocab"], TERMINAL_RANGE)
    K = 0
    while  _WordData["vocab"][start]["pos"] in WORD_CATEGORY["halfBanned"] or WordSim(start, end) < minDistance:
        start = Utility.RandomKey(_WordData["vocab"], TERMINAL_RANGE)
        K+=1
        if(K > 10000):
            print("Warning: Taking too long to determine start and end words, maybe lower minDistance or raise terminal range?")
            break
    
    start = RemoveFeatureSuffix(start, "Number=Plur", "s") #make plur sing
    start = RemoveFeatureSuffix(start, "Tense=Past", "ed") #make past present
    end = RemoveFeatureSuffix(end, "Number=Plur", "s") #make plur sing
    end = RemoveFeatureSuffix(end, "Tense=Past", "ed") #make past present

    _WordChain.append(start)
    _StartWord = start
    _TargetWord = end
    return start, end

def RestartGame():
    """
    Resets local game variables and generates new start and target words
    """
    global _TargetWord, _WordChain

    _TargetWord = ""
    _WordChain = []
    GenerateStartEndWords(minDistance=0.5)

def InitializeGame():
    global _WordData, _BannedData, _nlp 

    _BannedData = torch.load("output/WikipediaBannedData.pt")
    _WordData = torch.load("output/WikipediaWordData.pt")

    # _WordData["vocab"] = StanzaUtility.LemmatarizedDict(_WordData["vocab"]) #get lemma only

    #stanza initialization
    if(LEMMA_INPUT):
        processors = "tokenize, mwt, pos, lemma" #processors required for lemmatarization and noun identification
        _nlp = stanza.Pipeline(lang='en', processors=processors)

    RestartGame()

# InitializeGame()
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