import enchant
import torch
import stanza


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
    nlp = stanza.Pipeline(lang='en', processors=processors, device='cuda')
    del processors

    f = open(path, "r", encoding="utf-8")
    content = f.read()
    f.close()

    wordData = {"vocab":{}}
    bannedWordData = {"vocab":{}}
    lines = content.split("\n")

    bannedTensor = []
    wordTensor = []

    bannedIteration: int = 0
    wordIteration: int = 0
    for i, line in enumerate(lines):
        if(i != 0 and i % 1000 == 0):
            print(f"{i} out of {len(lines)} processed. \n {bannedIteration} banned\n {wordIteration} allowed")
            break

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

        if(checkDic):
            wordDic = enchant.Dict("en_US")
            barrier |= not wordDic.check(word)
        if(barrier): continue

        #nlp barrier
        doc = nlp(word)
        firstWord = list(doc.iter_words())[0]

        # print(f"{word} {firstWord.text}: {firstWord.pos}")
        vector = torch.tensor([float(things[i]) for i in range(1, len(things))])
        if(firstWord.pos in bannedPos):
            bannedWordData["vocab"][word] = {}
            bannedWordData["vocab"][word]["pos"] = firstWord.pos
            bannedWordData["vocab"][word]["lemma"] = firstWord.lemma
            bannedWordData["vocab"][word]["id"] = bannedIteration
            bannedTensor.append(vector)
            bannedIteration+=1
        else:
            wordData["vocab"][word] = {}
            wordData["vocab"][word]["pos"] = firstWord.pos
            wordData["vocab"][word]["pos"] = firstWord.lemma
            wordData["vocab"][word]["id"] = wordIteration
            wordTensor.append(vector)
            wordIteration+=1

    bannedWordData["emb"] = torch.stack(bannedTensor)
    wordData["emb"] = torch.stack(wordTensor)

    torch.save(bannedWordData, "output/WikipediaBannedData.pt")
    torch.save(wordData, "output/WikipediaWordData.pt")

# print(f"Is CUDA supported by this system? {torch.cuda.is_available()}")
# print(f"CUDA version: {torch.version.cuda}")
 
# # Storing ID of current CUDA device
# cuda_id = torch.cuda.current_device()
# print(f"ID of current CUDA device:{torch.cuda.current_device()}")
       
# print(f"Name of current CUDA device:{torch.cuda.get_device_name(cuda_id)}")
ProcessGloveToPT("input/glove.6B.300d.txt", minLength=3, maxLength=50, alphabetOnly=True, checkDic=True, allowDigits=False, bannedPos=["PRON", "DET", "CCONJ", "SCONJ", "PART", "PUNCT", "SIM", "NUM"])
