from nicegui import ui
import GameLogic
import time
import math
import asyncio

#UI variables
_WinDialog: ui.dialog = None
_ChainScrollArea: ui.scroll_area = None

#UI functions
def RestartBtn():
    GameLogic.RestartGame()
    StartTargetCards.refresh()
    WordChain.refresh()
    _WinDialog.clear()

#when user inputs guess from textbox
def GuessInput(inputBox: ui.input):
    guess = inputBox.value
    
    valid, message = GameLogic.ValidateGuess(guess) #if guess is valid/(if it is in possible values and not banned)
    if(valid):
        valid, message = GameLogic.GuessWord(guess) #get result of guessing the word, valid if it is within distance

        if(valid):
            WordChain.refresh()
            ui.notify(message, type='positive', timeout=1500, position='top')
            if(guess == GameLogic._TargetWord):
                WinDialog(_WinDialog)
        else:
            ui.notify(message, type='warning', timeout=1500, position='top')
    else:
        ui.notify(message, type='negative', timeout=1500, position='top')

    #reset and refocus box
    inputBox.value = ""
    ui.run_javascript(f"document.getElementById('{inputBox.id}').focus()")

#dialog card when you win the game
def WinDialog(dialog: ui.dialog):
    #set all parameters
    with dialog, ui.card().classes('w-96 h-108 no-shadow border-[1px] items-center justify-center'):
        ui.label("You won!").style("font-weight: bold; font-size: 150%")
        ui.label(f"Score: {len(GameLogic._WordChain)-1} links").style('color: #777777')
        ui.label(f"Chain:")
        with ui.scroll_area().classes('border rounded'):
            with ui.list().classes('gap-2 justify-center'):
                for w in GameLogic._WordChain:
                    ui.label(w)
        ui.button(icon='r_refresh', on_click=lambda e: (dialog.close(), RestartBtn()))
        
    dialog.open() #show card


def InfoDialog(dialog: ui.dialog):
    dialog.open()


@ui.refreshable
def WordChain():
    #create a card for each word
    for i, word in enumerate(GameLogic._WordChain):
        distToTarget = GameLogic.WordSim(word, GameLogic._TargetWord, 3)

        with ui.card(align_items='left').classes('border-[1px] no-shadow w-full'):
            with ui.row().classes('gap-4 w-full'):
                ui.label(f'{i+1}').style('color: #555555')
                ui.label(word).style('font-weight: bold')
                ui.label(f'({distToTarget}) to {GameLogic._TargetWord}').style('color: #777777').classes('ml-auto')
    
    #scroll to end of chain
    _ChainScrollArea.scroll_to(percent=100, duration=0.5)
    
@ui.refreshable 
def StartTargetCards():
    #create cards for start and target
    with ui.row().classes('gap-0'):
            with ui.card(align_items='center').classes('w-48 no-shadow border-[1px]'):
                ui.label(GameLogic._StartWord)
            with ui.card(align_items='center').classes('w-48 no-shadow border-[1px]'):
                ui.label(GameLogic._TargetWord)

#start of program
if(__name__ == "__main__"):
    GameLogic.InitializeGame() #start game / processors

    #start of UI
    ui.dark_mode().enable()
    
    #winning dialogue setup
    _WinDialog = ui.dialog()
    _WinDialog.close()

    #info dialogue setup
    infoDialogue = ui.dialog()
    with infoDialogue,  ui.card().classes('w-96 h-108 no-shadow border-[1px] items-center justify-center'):
        with ui.row().classes('justify-between items-center'):
            ui.icon('r_info')
            ui.label("Info").style("font-weight: bold; font-size: 150%")
        with ui.expansion(text="How do I play?").classes('w-full'):
            ui.label(f"""The goal is to create a chain of related words to reach a 'target' word. 
                     The start and ending positions are determined randomly, and linked words must be a 
                     distance of {GameLogic.DISTANCE_CUTOFF} from the previous.""")
            ui.label("""*Some words may seem obviously related but have a high distance.
                      The algorithm determines similarity based upon similar contexts, 
                     not necessarily similar meaning""").style('color: #777777')

    #header
    with ui.header().style('background-color: #222222').style('font-size: 24').classes('h-16 font-weight-bold'):
        with ui.row().classes('justify-between items-center h-full w-full'):
                ui.button(icon='r_refresh', on_click=lambda e: RestartBtn())
                ui.label('Linkedle').style('font-size: 250%; font-weight: bold')
                ui.button(icon='r_info', on_click=lambda e: infoDialogue.open())  
                
    #show start and target
    with ui.column().classes('w-full h-full justify-center items-center'):
        StartTargetCards()
        
        #word box
        inputText = ui.input(placeholder="chain a word...").props('outlined dense autocomplete=off autocapitalize=off').classes('w-96')
        inputText.on('keydown', lambda e: GuessInput(inputText) if e.args['key'] == "Enter" else None)

        #word chain scroll area
        with ui.scroll_area().classes('border rounded w-96 h-512 gap-2') as scrollArea:
            _ChainScrollArea = scrollArea
            WordChain()
    
    
ui.run(reload=False) #dont use reload (watch files) because leads to errors

