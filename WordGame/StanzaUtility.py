import stanza
import stanza.pipeline
import FileManager



def WordInfoJson(word2ID: dict, fileName: str, filter: list = list()) -> None:
    """
    Process writes json with format word -> |id|lemma|pos| from vocab list using an nlp
        filter is a string list of the allowed POS values (eg NOUN, VERB, ADJ), empty will allow all values
    """

    #stanza stuff
    processors = "tokenize, mwt, pos, lemma" #processors required for lemmatarization and noun identification
    nlp = stanza.Pipeline(lang='en', processors=processors)

    #analyse and add each word
    infoDict = {}
    print(f"Analyzing words...")
    def AnalyseWords():
        numI = 0 #for a progress check
        for word in list(word2ID.keys()):
            numI+=1
            if(numI % 1000 == 0):
                print(f"Iteration: {numI}") 
            doc = nlp(word)
            firstWord = list(doc.iter_words())[0]
            if(len(filter) > 0 and firstWord.pos not in filter):
                #filter so skip unwanted pos types
                continue
            
            #dictionary etry
            infoDict[firstWord.text] = {
                "id"   : int(word2ID[word]),
                "lemma": firstWord.lemma,
                "pos"  : firstWord.pos
            }

    AnalyseWords()

    FileManager.SaveJsonDict(infoDict, f"output/{fileName}")   

    print(f"Done! Wrote {len(word2ID)} words to {len(infoDict)} word infos to {fileName}")


def GetDataRange(data: dict, dataRange: range) -> dict:

    #general structure for clarity
    resDict = {
        "vocab" : {
            "_unit2id": {}, #will be filled
            "_id2unit": {}  #will be filled
        },
        "emb" : "" #will be filled
    }

    for i in dataRange:
        resDict["vocab"]["_unit2id"][data["vocab"]["_id2unit"][i]] = i
        resDict["vocab"]["_id2unit"][i] = data["vocab"]["_id2unit"][i]

    resDict["emb"] = data["emb"][dataRange.start:dataRange.stop].clone() #THIS DOESN'T ACCOUNT FOR STRANGE RANGE PARAMETERS

    print(f"Culled data from {len(data['emb'])} to {dataRange.stop - dataRange.start} values")
    return resDict

def LemmaWord(word: str, nlp: stanza.pipeline) -> str:
    doc = nlp(word)
    first = list(doc.iter_words())[0]
    return first.lemma

def LemmatarizedDict(wordInfo: dict):
    lemmaDict = {}
    for i, w in enumerate(wordInfo.keys()):
        lemmaWord = wordInfo[w]["lemma"] 
        if(lemmaWord in wordInfo.keys() and lemmaWord not in lemmaDict.keys()):
            lemmaDict[lemmaWord] = wordInfo[lemmaWord]
    
    return lemmaDict

def Word2Embed(wordInfo: dict, emb: dict) -> dict:
    word2Embed = {}
    for w in wordInfo.keys():
        word2Embed[w] = emb[wordInfo[w]["id"]]
    
    return word2Embed