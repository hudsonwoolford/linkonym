import torch
import matplotlib.pyplot as plt
import matplotlib.figure as figure
from sklearn.manifold import TSNE
import FileManager
import time
import random

def GraphWordInfo(data: dict, path: str = "output/WordInfo.json") -> None:
    """
    Process that graphs the 'word info' dictionary using matplotlib
        optional path parameter for specificity
    """

    #load dictionary and get words
    wordInfo = FileManager.LoadJsonDict(path)
    words = list(wordInfo.keys())

    #get all embeds
    embeds = torch.stack([data["emb"][info["id"]]for info in wordInfo.values()])

    #generate figure
    GraphVectors2D(words, embeds)
    plt.show()

def GraphVectors2D(vocab: list, embeds: list, perplexity = 30, randomState = 24) -> figure:
    """
    Generates and returns a figure for a 2D graph of word vectors using tSNE
    """

    #convert vectors to float32 for tSNE
    vectors = embeds.numpy().astype('float32')

    #create and apply tSNE transform
    tsne = TSNE(n_components=2, perplexity = perplexity, random_state=randomState)
    vectors = tsne.fit_transform(vectors)

    #generate figure and axes
    fig, axes = plt.subplots(figsize=(14, 10))
    axes.scatter(vectors[:, 0], vectors[:,1], alpha=0.6)

    #annotate points with word labels
    for i, word in enumerate(vocab):
        axes.annotate(word, (vectors[i, 0], vectors[i, 1]), fontsize=6, alpha=0.75)

    return fig


def PossibleWordsToJson(words: list, word2ID: dict, fileName: str, minLength: int = 0, maxLength: int = 1000, allowDigits: bool = False) -> None:
    """
    Process writes a list of words to a json file, optional parameters for length filtering, format |word|
    Possible as words do not have to be included in word2ID list, but will be excluded if not
    """

    numWritten: int = 0
    info = {"_word2id":{}}
    keys = word2ID.keys()
    for i, word in enumerate(words):
        if(len(word) >= minLength and len(word) <= maxLength):
            if((word.isdigit() and allowDigits) or not word.isdigit()):
                if(word in keys):
                    numWritten += 1
                    info["_word2id"][word] = word2ID[word]
    
    FileManager.SaveJsonDict(info, f"output/{fileName}")
                
    print(f"Done! Written {numWritten} of {len(words)} words to {fileName}")

def WordsToJson(words: list, ids: list, fileName: str, minLength: int = 0, maxLength: int = 1000, allowDigits: bool = False) -> None:
    """
    Process writes a list of words to a json file, optional parameters length filtering, format |word|
    """

    numWritten: int = 0
    info = {"_word2id":{}}

    for i, word in enumerate(words):
        if(len(word) >= minLength and len(word) <= maxLength):
            if((word.isdigit() and allowDigits) or not word.isdigit()):
                numWritten += 1
                info["_word2id"][word] = ids[i]
    
    FileManager.SaveJsonDict(info, f'output/{fileName}')
                
    print(f"Done! Written {numWritten} of {len(words)} words to {fileName}")

def ProfileFunction(func, *args, **kwargs) -> tuple:
    prevPerf = time.perf_counter()
    result = func(*args, **kwargs)
    return result, time.perf_counter()-prevPerf



def CreatePTFile(wordInfo: dict, embeds: list, path: str):
    finalDict = {"vocab":{}}
    usedEmbeds = []
    for i, k in enumerate(wordInfo.keys()):
        usedEmbeds.append(torch.tensor(embeds[wordInfo[k]["id"]]))
        finalDict["vocab"][k] = wordInfo[k]
        finalDict["vocab"][k]["id"] = i

    finalDict["emb"] = torch.stack(usedEmbeds)

    torch.save(finalDict, path)

def Word2Embed(wordInfo: dict, embeds: list):
    word2Embed = {}
    for i, k in enumerate(wordInfo.keys()):
        word2Embed[k] = torch.tensor(embeds[wordInfo[k]["id"]])

    return word2Embed
