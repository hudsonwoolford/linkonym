from nicegui import ui
import GameLogic
import time
import math
import asyncio

#UI variables
_WinDialog: ui.dialog = None
_ChainScrollArea: ui.scroll_area = None
PAGES = {
    1 : "Normal",
    2 : "Themed"
}

#UI functions
def RestartBtn():
    GameLogic.RestartGame()
    StartTargetCards.refresh()
    WordChain.refresh()
    _WinDialog.clear()

#when user inputs guess from textbox
def GuessInput(inputBox: ui.input):
    guess = inputBox.value
    
    valid, message, guess = GameLogic.ValidateGuess(guess) #if guess is valid/(if it is in possible values and not banned)
    if(valid):
        valid, message = GameLogic.GuessWord(guess) #get result of guessing the word, valid if it is within distance

        if(valid):
            WordChain.refresh()
            ui.notify(message, type='positive', timeout=1500, position='bottom')
            if(guess == GameLogic._TargetWord):
                WinDialog(_WinDialog)
        else:
            ui.notify(message, type='warning', timeout=1500, position='bottom')
    else:
        ui.notify(message, type='negative', timeout=1500, position='bottom')

    #reset and refocus box
    inputBox.value = ""
    ui.run_javascript(f"document.getElementById('{inputBox.id}').focus()")

#dialog card when you win the game
def WinDialog(dialog: ui.dialog):
    #set all parameters
    with dialog, ui.card().classes('w-96 h-108 no-shadow border-[3px] items-center justify-center'):
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
    with ui.column().classes("w-full gap-1"):
        for i, word in enumerate(GameLogic._WordChain[::-1]):
            realI = len(GameLogic._WordChain) - 1 - i

            chainMessage = f"({GameLogic.WordSim(word, GameLogic._TargetWord, 3)}) to '{GameLogic._TargetWord}'"
            if(not i == 0):
                chainMessage = f"({GameLogic.WordSim(word, GameLogic._WordChain[realI-1], 3)})"

            with ui.card(align_items='center').style("height: 2rem").classes('py-0 border-[1px] no-shadow w-full'):
                with ui.row().classes('w-full h-full justify-between items-center'):
                    ui.icon("sym_r_keyboard_double_arrow_up")
                    ui.label(chainMessage).style('font-weight: bold')
                    ui.icon("sym_r_keyboard_double_arrow_up")
            with ui.card(align_items='left').style("height: 3rem").classes('py-0 border-[1px] no-shadow w-full items-center'):
                with ui.row().classes('gap-4 h-full w-full items-center'):
                    ui.label(f'{realI+1}').style('color: #555555')
                    ui.label(word).style('font-weight: bold')
                    # ui.label(f'({distToTarget}) to {GameLogic._TargetWord}').style('color: #777777').classes('ml-auto')
    
@ui.refreshable 
def StartTargetCards():
    #create cards for start and target
    with ui.row().classes('gap-0 items-center'):
            with ui.card(align_items='center').style("width: 10rem").classes('no-shadow border-[1px]'):
                ui.label(GameLogic._StartWord)
            ui.icon("sym_r_keyboard_double_arrow_right", size="4rem")
            with ui.card(align_items='center').style("width: 10rem").classes('w-48 no-shadow border-[1px]'):
                ui.label(GameLogic._TargetWord)
@ui.refreshable
def RenderPage(page: int):
    global _ChainScrollArea

    if(PAGES[page] == "Normal"):
        with ui.column().classes('w-full h-full items-center'):
            ui.chip(f"A max distance of ({GameLogic.DISTANCE_CUTOFF}) can be chained.",icon="sym_r_arrow_forward", on_click=lambda e: ui.notify("Build a chain to the target word")).props("outlined")

            #show start and target
            StartTargetCards()

            #word box
            inputText = ui.input(placeholder="chain a word...").props('outlined dense autocomplete=off autocapitalize=off').classes('w-96')
            inputText.on('keydown', lambda e: GuessInput(inputText) if e.args['key'] == "Enter" else None)

            #word chain scroll area
            with ui.element().classes("h-screen"):
                with ui.scroll_area().style("height: 60%").classes('border-[3px] rounded w-96') as scrollArea:
                    _ChainScrollArea = scrollArea
                    WordChain()

#start of program
if(__name__ == "__main__"):
    GameLogic.InitializeGame() #start game / processors

    #start of UI
    ui.dark_mode().enable()
    ui.add_head_html('<style>body { overflow: hidden; }</style>') #disable scrolling

    #winning dialogue setup
    _WinDialog = ui.dialog()
    _WinDialog.close()

    #info dialogue setup
    infoDialogue = ui.dialog()
    with infoDialogue,  ui.card().classes('w-96 h-108 no-shadow border-[5px] items-center justify-center'):
        with ui.row().classes('justify-between items-center'):
            ui.icon('sym_r_info', size="150%")
            ui.label("Info").style("font-weight: bold; font-size: 150%")
        with ui.expansion(text="How do I play?").classes('w-full'):
            ui.label(f"""The goal is to create a chain of related words to reach a 'target' word. 
                     The start and ending positions are determined randomly, and linked words must be a 
                     distance of {GameLogic.DISTANCE_CUTOFF} from the previous.""")
            ui.label("""*Some words may seem obviously related but have a high distance.
                      The algorithm determines similarity based upon similar contexts, 
                     not necessarily similar meaning""").style('color: #777777')
            
    #header
    with ui.header().style('background-color: #222222').style('font-size: 24').classes('h-16 w-screen font-weight-bold'):
        with ui.row().classes('items-center h-full w-full'):
                ui.toggle(PAGES, value=1, on_change=lambda e:RenderPage.refresh(e.value))
                ui.label('Linkedle').style('font-size: 250%; font-weight: bold').classes('absolute-center')
                ui.button(icon='sym_r_refresh', on_click=lambda e: RestartBtn())
                ui.button(icon='sym_r_info', on_click=lambda e: infoDialogue.open()).classes('ml-auto')
    
    RenderPage(1)
    
    
ui.run(reload=False) #dont use reload (watch files) because leads to errors

