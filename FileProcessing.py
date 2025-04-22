import enchant
import torch
import stanza
import time


def ProcessGloveToPT(path: str, 
                     minLength: int = 3, 
                     maxLength: int = 50, 
                     alphabetOnly: bool = False, 
                     checkDic: bool = False, 
                     allowDigits: bool = True,
                     bannedPos: list = None
                     ) -> None:
    #initialize nlp
    processors = "tokenize, mwt, pos, lemma" #processors required for lemmatarization and noun identification
    nlp = stanza.Pipeline(lang='en', processors=processors, device='cuda', download_method=None)
    del processors

    f = open(path, "r", encoding="utf-8")
    content = f.read()
    f.close()

    wordData = {"vocab":{}}
    bannedWordData = {"vocab":{}}
    lines = content.split("\n")

    bannedTensor = []
    wordTensor = []

    wordDic = enchant.Dict("en_US")

    bannedIteration: int = 0
    wordIteration: int = 0
    timer = time.time()
    lastTime = timer
    for i, line in enumerate(lines):
        if(i != 0 and i % 1000 == 0):
            sinceStart = time.time() - timer
            unitTime = sinceStart/i
            print(f"{i} out of {len(lines)} processed. \n {bannedIteration} banned\n {wordIteration} allowed. {sinceStart} seconds since start, {time.time() - lastTime} for last 1k. Est remaining: {unitTime*(len(lines)-i)} seconds")
            lastTime = time.time() 
            torch.save(bannedWordData, "output/WikipediaBannedData.pt")
            torch.save(wordData, "output/WikipediaWordData.pt")

        things = line.split(" ")
        word = str(things[0])
        
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

        isProperNoun = False
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

        # print(f"{word} {firstWord.text}: {firstWord.pos}")
        vector = torch.tensor([float(things[i]) for i in range(1, len(things))])
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

    bannedWordData["emb"] = torch.stack(bannedTensor)
    wordData["emb"] = torch.stack(wordTensor)

    torch.save(bannedWordData, "output/WikipediaBannedData.pt")
    torch.save(wordData, "output/WikipediaWordData.pt")


ProcessGloveToPT("input/glove.6B.100d.txt", minLength=3, maxLength=50, alphabetOnly=True, checkDic=True, allowDigits=False, bannedPos=["PRON", "DET", "CCONJ", "SCONJ", "PART", "PUNCT", "AUX", "INTJ"])
wordData = torch.load("output/WikipediaWordData.pt")
print(wordData["vocab"])
