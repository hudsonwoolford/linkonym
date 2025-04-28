import enchant
import stanza.pipeline
import torch
import stanza
import time
import GameLogic
import pandas as pd

def AddWord(embedsPath: str, appendPath: str, appendWord: str):
    appendWord = appendWord.lower()

    f = open(embedsPath, "r", encoding="utf-8")
    content = f.read()
    f.close()

    lines = content.split("\n")

    processors = "tokenize, mwt, pos, lemma" #processors required for lemmatarization and noun identification
    nlp = stanza.Pipeline(lang='en', processors=processors, device='cuda', download_method=None)

    wordData = torch.load(appendPath)

    for line in lines:
        things = line.split(" ")
        firstWord = things[0]

        if(firstWord == appendWord):
            firstWord = list(nlp(appendWord).iter_words())[0]
            wordData["vocab"][appendWord] = {
                "id" : len(wordData["vocab"].keys()),
                "pos" : firstWord.pos,
                "lemma" : firstWord.lemma,
                "feats" : firstWord.feats
            }
            vector = torch.tensor([float(things[i]) for i in range(1, len(things))])
            wordData["emb"] = torch.vstack((wordData["emb"], vector))
    
    torch.save(wordData, appendPath)

def TransferPosWords(fromPath: str, toPath: str, posFilter: list = None):
    fromData = torch.load(fromPath)
    toData = torch.load(toPath)

    deleteWords = []
    addTensors = []
    for w in fromData["vocab"].keys():
        if(fromData["vocab"][w]["pos"] in posFilter):
            toData["vocab"][w] = fromData["vocab"][w] #add dictionary entry in new
            toData["vocab"][w]["id"] = len(toData["emb"]) + len(addTensors)
            addTensors.append(fromData["emb"][fromData["vocab"][w]["id"]])
            deleteWords.append(w)

    for w in deleteWords:
        del fromData["vocab"][w] #delete dictionary entry in old
    
    torch.save(fromData, fromPath)
    torch.save(toData, toPath)

def ProcessEmbedsToPT(path: str, 
                     minLength: int = 3, 
                     maxLength: int = 50, 
                     alphabetOnly: bool = False, 
                     checkDic: bool = False, 
                     allowDigits: bool = True,
                     bannedPos: list = None,
                     skipLines: list = None,
                     dataPath: str = "output/WordData.pt",
                     bannedPath: str = "output/BannedData.pt",
                     nlp: stanza.Pipeline = None
                     ) -> None:
    """
    Robust process function to convert an embeds file to a data dictionary stored in a .pt file.
    Generates an allowed and banned dictionary in the format:
        vocab
        -word
        --id
        --lemma
        --pos
        --feats
        emb
    
    The 'emb' key holds an N dimensional tensor with word embeds corresponding to the index=word-id
    """

    #initialize nlp
    if(nlp == None):
        processors = "tokenize, mwt, pos, lemma" #processors required for lemmatarization and noun identification
        nlp = stanza.Pipeline(lang='en', processors=processors, device='cuda', download_method=None)
        del processors

    #read embed file
    f = open(path, "r", encoding="utf-8")
    content = f.read()
    f.close()
    lines = content.split("\n")

    #initializate dictionaries
    wordData = {"vocab":{}}
    bannedWordData = {"vocab":{}}
    bannedTensor = []
    wordTensor = []

    #download pyenchant dic
    wordDic = enchant.Dict("en_US")

    #iteration tracking
    bannedIteration: int = 0
    wordIteration: int = 0
    timer = time.time()
    lastTime = timer

    #loop through each line
    print(f"Now processing {path}")
    for i, line in enumerate(lines):
        if(i in skipLines): #functionality to skip certain lines
            continue

        #console tracking
        if(i != 0 and i % 10000 == 0):
            sinceStart = time.time() - timer
            unitTime = sinceStart/i
            print(f"{i} out of {len(lines)} processed. {bannedIteration} banned {wordIteration} allowed. {sinceStart} seconds since start, {time.time() - lastTime} for last 10k. Est remaining: {unitTime*(len(lines)-i)} seconds")
            lastTime = time.time() 

            #update and save files in case of crash
            bannedWordData["emb"] = torch.stack(bannedTensor)
            wordData["emb"] = torch.stack(wordTensor)
            torch.save(bannedWordData, bannedPath)
            torch.save(wordData, dataPath)

        #get line things
        things = line.rstrip().split(" ")   
        if(len(things)>0):
            word = str(things[0])
        else:
            continue #this implies the line is empty
            
        
        #basic barriers
        barrier = False
        barrier |= len(word) < minLength or len(word) > maxLength
        if(not allowDigits): barrier |= word.isdigit()
        if(barrier): continue

        if(alphabetOnly):
            for c in list(word):
                barrier |= ord(c) < 97 or ord(c)>122
                if(barrier): break
        if(barrier): continue

        firstWord = ""
        if(checkDic):
            if(not wordDic.check(word)): #not in dictionary\
                barrier |= True
        if(barrier): continue

        #nlp barrier
        doc = nlp(word)
        firstWord = list(doc.iter_words())[0]
        if(firstWord.pos == "AUX" or firstWord.pos == "INTJ"):
            doc = nlp(f"the {word}")
            firstWord = list(doc.iter_words())[1]

        #vector tensor
        vector = ""
        try:
            vector = torch.tensor([float(things[x]) for x in range(1, len(things))])
        except:
            vector = torch.tensor([1 * 300])
            print(f"Warning: could not create vector on word '{word}'")

        #set dictionaries
        if(firstWord.pos in bannedPos):
            bannedWordData["vocab"][word] = {
                "id" : bannedIteration,
                "pos" : firstWord.pos,
                "lemma" : firstWord.lemma,
                "feats" : firstWord.feats
            }
            bannedTensor.append(vector)
            bannedIteration+=1
        else:
            wordData["vocab"][word] = {
                "id" : wordIteration,
                "pos" : firstWord.pos,
                "lemma" : firstWord.lemma,
                "feats" : firstWord.feats
            }
            wordTensor.append(vector)
            wordIteration+=1

    del lines #let go of memory

    #stack embeds - should all be valid tensors
    bannedWordData["emb"] = torch.stack(bannedTensor)
    wordData["emb"] = torch.stack(wordTensor)

    #save files
    torch.save(wordData, dataPath)
    torch.save(bannedWordData, bannedPath)
    print(f"Done! Completed file - wrote {wordIteration} words and {bannedIteration} banned words to their respective files.")

import torch
import pandas as pd

def CreateEdgeCSV(edgePath: str, wordData: dict, similarityCutoff: float = 0.675):
    print("Initializing...")
    edgeDict = {
        'source': [],
        'target': [],
    }

    wordInfo = wordData['vocab']
    allWords = list(wordInfo.keys())

    embeds = []
    for w in allWords:
        embeds.append(wordData['emb'][wordInfo[w]['id']])

    vectors: torch.Tensor = torch.stack(embeds)
    
    print("Normalizing...")
    vectors = vectors / vectors.norm(dim=1, keepdim=True) #normalize
    print("Multiplying...")
    simMatrix = (torch.matmul(vectors, vectors.T)+1)/2
    print("Culling...")
    simMatrix = torch.triu(simMatrix, diagonal=1)
    print("Comparing...")
    simMatrix = torch.nonzero(simMatrix>similarityCutoff)

    print("Appending...")
    for coords in simMatrix:
        edgeDict['source'].append(allWords[coords[0]])
        edgeDict['target'].append(allWords[coords[1]])

    print("Saving...")
    edgeDf = pd.DataFrame(edgeDict)
    edgeDf.to_csv(edgePath, index=False)

def ConvertCSVToID(loadPath: str, savePath: str, wordData: dict):
    df = pd.read_csv(loadPath)

    newList = []
    for w in df['source']:
        newList.append(wordData['vocab'][w]['id'])
    
    df['source'] = newList

    newList = []
    for w in df['target']:
        newList.append(wordData['vocab'][w]['id'])
    
    df['target'] = newList
    
    df.to_csv(savePath)

def CreateNodesCSV(nodePath: str, wordData: dict):
    nodeDict = {
        'id': [],
        'label': [],
    }

    wordInfo = wordData['vocab']
    allWords = list(wordInfo.keys())
    # Iterate over all words to populate the node dictionary
    for word in allWords:
        nodeDict["id"].append(wordInfo[word]['id'])
        nodeDict["label"].append(word)
    
    # Convert dictionaries to DataFrames and write them to CSV
    nodeDf = pd.DataFrame(nodeDict)
    
    nodeDf.to_csv(nodePath, index=False)

# CreateEdgeCSV('output/WordEdges.csv', GameLogic._WordData)
ConvertCSVToID('output/WordEdges.csv', 'output/WordEdgesID.csv', GameLogic._WordData)
# processors = "tokenize, mwt, pos, lemma" #processors required for lemmatarization and noun identification
# prenlp = stanza.Pipeline(lang='en', processors=processors, device='cuda', download_method=None)
# del processors

# ProcessEmbedsToPT("input/numberbatch-en.txt"                        , nlp=prenlp, minLength=3, maxLength=50, alphabetOnly=True, checkDic=True, allowDigits=False, bannedPos=["PRON", "DET", "CCONJ", "SCONJ", "PART", "PUNCT", "AUX", "INTJ", "ADV", "ADP"], skipLines=[0], dataPath="output/NumberBatchWData.pt", bannedPath="output/NumberBatchBData.pt")
# ProcessEmbedsToPT("input/wiki-news-300d-1M.vec"                     , nlp=prenlp, minLength=3, maxLength=50, alphabetOnly=True, checkDic=True, allowDigits=False, bannedPos=["PRON", "DET", "CCONJ", "SCONJ", "PART", "PUNCT", "AUX", "INTJ", "ADV", "ADP"], skipLines=[0], dataPath="output/WikiNewsWData.pt", bannedPath="output/WikiNewsBData.pt")
# ProcessEmbedsToPT("input/GoogleNews-vectors-negative300.txt"        , nlp=prenlp, minLength=3, maxLength=50, alphabetOnly=True, checkDic=True, allowDigits=False, bannedPos=["PRON", "DET", "CCONJ", "SCONJ", "PART", "PUNCT", "AUX", "INTJ", "ADV", "ADP"], skipLines=[0], dataPath="output/GoogleNewsWData.pt", bannedPath="output/GoogleNewsBData.pt")
# ProcessEmbedsToPT("input/lexvec.commoncrawl.300d.W.pos.neg3.vectors", nlp=prenlp, minLength=3, maxLength=50, alphabetOnly=True, checkDic=True, allowDigits=False, bannedPos=["PRON", "DET", "CCONJ", "SCONJ", "PART", "PUNCT", "AUX", "INTJ", "ADV", "ADP"], skipLines=[0], dataPath="output/LexVecWData.pt", bannedPath="output/LexVecBData.pt")
