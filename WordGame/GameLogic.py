import stanza
import torch
import StanzaUtility
import json
import enchant
import random
import FileManager
import matplotlib.pyplot as plt
import Utility

DISTANCE_CUTOFF = 0.32 #max distance for word chain
TERMINAL_RANGE = range(100, 3000)
LEMMA_INPUT = False

#persistant game variables
_nlp = None #natural language processor
_WordData = None #global word data

#temp game variables
_TargetWord = "" #current target word
_StartWord = "" #current start word
_WordChain = [] #current chain of words

#ensure model is downloaded
# stanza.download(lang)


def WordListToInfo():
    wordList = dict(json.load(open("output/WordList.json", 'r', encoding="utf-8")))
    StanzaUtility.WordInfoJson(wordList["_word2id"], "WordInfo.json", filter = ["VERB", "NOUN", "ADJ"])

def TensorCosSimilarity(t1: torch.Tensor, t2: torch.Tensor) -> float:
    cos = torch.nn.CosineSimilarity(dim=0)
    return (1-float(cos(t1, t2)))/2

def WordTensor(word: str):
    global _WordData

    return _WordData["emb"][_WordData["vocab"][word]["id"]]

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
    

def ValidateGuess(guess: str) -> tuple[bool, str]:
    """
    Checks a guess inputted by user and returns [valid(bool), feedbackMessage(str)]:
        banned ? false, error message
        not in values ? change word to lemma
            still not in values ? false, error message
    """
    global _WordData

    possibleValues = list(_WordData["vocab"].keys())
    bannedValues = _WordChain #cannot go back on the word chain

    guess = guess.strip().lower() #ensure no weird spaces or casing
    
    if(guess in bannedValues):
        return False, f"'{guess}' has been banned!"
    
    if(guess not in possibleValues):
        if(not LEMMA_INPUT):
            return False, "I don't know that word!"
        prevGuess = guess
        guess = StanzaUtility.LemmaWord(guess, _nlp)
        if(guess not in possibleValues):
            return False, "I dont know that word!"
        else:
            print(f"Found {guess} by using lemma of {prevGuess}")
        
    return True, f"Guessed '{guess}.'"
    
def GenerateStartEndWords(minDistance: float = 0.325) -> tuple:
    """
    Generates start and end words for game randomly, optional minDistance parameter
    """
    global _WordChain, _WordData, _StartWord, _TargetWord

    if(len(_WordChain)>0):
        print("Warning: Word chain should be empty when calling GenerateStartEndWords")

    end = Utility.RandomKey(_WordData["vocab"], TERMINAL_RANGE)
    start = Utility.RandomKey(_WordData["vocab"], TERMINAL_RANGE)
    K = 0
    while WordSim(start, end) < minDistance:
        start = Utility.RandomKey(_WordData["vocab"], TERMINAL_RANGE)
        K+=1
        if(K > 10000):
            print("Warning: Taking too long to determine start and end words, maybe lower minDistance?")
            break

    _WordChain.append(start)
    _StartWord = start
    _TargetWord = end
    return start, end

def RestartGame():
    global _TargetWord, _WordChain

    _TargetWord = ""
    _WordChain = []
    GenerateStartEndWords(minDistance=0.45)

def InitializeGame():
    global _WordData, _nlp 

    _WordData = torch.load("output/WikipediaWordData.pt")

    _WordData["vocab"] = StanzaUtility.LemmatarizedDict(_WordData["vocab"]) #get lemma only

    # #stanza initialization
    if(LEMMA_INPUT):
        processors = "tokenize, mwt, pos, lemma" #processors required for lemmatarization and noun identification
        _nlp = stanza.Pipeline(lang='en', processors=processors)

    RestartGame()

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
PROPN - No, because I feel like things like "joseph" makes no sense
PRON - No, things like you, he, them - not interesting
ADJ - Yeah
VERB - Yeah
NOUN - Yeah
NUM - No
Anything else?: No
"""
