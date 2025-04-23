from nicegui import ui
import GameLogic
import time
import math
import pyperclip
import asyncio

#UI variables
_WinDialog: ui.dialog = None
_ChainScrollArea: ui.scroll_area = None
_EmbedOptionKey: str = "Wikipedia2014" #default embed path
PAGES = {
    1 : "Normal",
    2 : "Themed"
}
#UI colours and parameters
BORDER_COLOR = '#AAAAAA'
BORDER_WIDTH = '0px'
BORDER_RADIUS = '10px'
BORDER_SETTINGS = f'border-color: {BORDER_COLOR}; border-width: {BORDER_WIDTH}; border-radius: {BORDER_RADIUS}'
TEXT_PRIMARY = 'white'
TEXT_BLACK = 'black'
TEXT_SECONDARY = '#777777'
TEXT_DARK_GREY = '#555555'
PRIMARY = '#FD3DB5'
# PRIMARY = '#5898d4'
SECONDARY =  '#26a69a'
ACCENT = '#9c27b0'
DARK = '#1d1d1d'
DARK_PAGE = '#121212'
POSITIVE = '#21ba45'
NEGATIVE = '#c10015'
INFO = '#31ccec'
WARNING = '#f2c037'

"""
DEFAULTS
primary:	Primary color (default: "#5898d4")
secondary:	Secondary color (default: "#26a69a")
accent:	Accent color (default: "#9c27b0")
dark:	Dark color (default: "#1d1d1d")
dark_page:	Dark page color (default: "#121212")
text_white: White text color (default: "#555555")
text_grey: Grey text color (default: "#777777")
border_white: White border color (default: "#AAAAAA")
positive:	Positive color (default: "#21ba45")
negative:	Negative color (default: "#c10015")
info:	Info color (default: "#31ccec")
warning:	Warning color (default: "#f2c037")
custom_colors:	Custom color definitions for branding (needs ui.colors to be called before custom color is ever used, added in version 2.2.0)
"""
EMBED_OPTIONS = {
    "Wikipedia2014" :
    {
        "words"  : "output/WikipediaWData.pt",
        "banned" : "output/WikipediaBData.pt"
    },
    "WikiNews2017" :
    {
        "words"  : "output/WikiNewsWData.pt",
        "banned" : "output/WikiNewsBData.pt"
    },
    "Google" :
    {
        "words"  : "output/GoogleNewsWData.pt",
        "banned" : "output/GoogleNewsBData.pt"
    },
    "LexVec" :
    {
        "words"  : "output/LexVecWData.pt",
        "banned" : "output/LexVecBData.pt"
    },
    "NumberBatch" :
    {
        "words"  : "output/NumberBatchWData.pt",
        "banned" : "output/NumberBatchBData.pt"
    }
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
            ui.notify(message, type='positive', timeout=1500, position='bottom', badgeColor=POSITIVE, badgeTextColor=TEXT_PRIMARY)
            if(guess == GameLogic._TargetWord):
                WinDialog(_WinDialog)
                
        else:
            ui.notify(message, type='warning', timeout=1500, position='bottom', badgeColor=WARNING, badgeTextColor=TEXT_BLACK)
    else:
        ui.notify(message, type='negative', timeout=1500, position='bottom', badgeColor=NEGATIVE, badgeTextColor=TEXT_PRIMARY)

    #reset and refocus box
    inputBox.value = ""
    ui.run_javascript(f"document.getElementById('{inputBox.id}').focus()")

#dialog card when you win the game
def WinDialog(dialog: ui.dialog):
    ##set all parameters
    with dialog, ui.card().style(BORDER_SETTINGS).classes(f'w-64 h-108 no-shadow items-center justify-center'):
        ui.label("You won!").style(f"font-weight: bold; font-size: 150%; color: {TEXT_PRIMARY}")
        ui.label(f"Score: {len(GameLogic._WordChain)-1} links").style(f'color: {TEXT_SECONDARY}')
        ui.label(f"Chain:")
        with ui.scroll_area().classes('border rounded w-full') as scrollArea:
            with ui.timeline(side='right', layout='dense').classes('gap-0 p-0 h-full'):
                for i, w in enumerate(GameLogic._WordChain):
                    GameLogic.WordSim(w, GameLogic._TargetWord, 3)
                    ui.timeline_entry("",subtitle=w).style('height: 4rem').classes('p-0')
                scrollArea.scroll_to(percent=100, duration=1)

        with ui.row().style('width: 100%; height: 100%').classes('justify-center'):
            ui.button(icon='sym_r_refresh', on_click=lambda e: (dialog.close(), RestartBtn()))
            ui.button(icon='sym_r_share', on_click=lambda e: (dialog.close(), RestartBtn()))

        
    dialog.open() #show card

def CopyClipboardGame():
    chain = ""
    for word in GameLogic._WordChain:
        chain += f"||{word}||\n"
    pyperclip.copy(f"""Check out my Linkedle game! 🙂

Here's my word chain from '{GameLogic._StartWord}' to '{GameLogic._TargetWord}': 🔗

{chain}

Score: {len(GameLogic._WordChain)} 🔥

You can play the same seed here: """)

def InfoDialog(dialog: ui.dialog):
    dialog.open()


@ui.refreshable
def WordChain():
    #create a card for each word
    with ui.column().classes("w-full gap-2"):
        for i, word in enumerate(GameLogic._WordChain):
            chainMessage = f"({GameLogic.WordSim(word, GameLogic._TargetWord, 3)}) to '{GameLogic._TargetWord}'"
            # if(not i == len(GameLogic._WordChain)-1):
            #     chainMessage = f"({GameLogic.WordSim(word, GameLogic._WordChain[i+1], 3)})"

            with ui.card(align_items='left').style(f"height: 3rem; {BORDER_SETTINGS}").classes(f'py-0 no-shadow w-full items-center'):
                with ui.row().classes('gap-4 h-full w-full items-center'):
                    ui.label(f'{i+1}').style(f'color: {TEXT_SECONDARY}')
                    ui.label(word).style(f'font-weight: normal; color: {TEXT_PRIMARY}')
                    ui.label(f'{chainMessage}').style(f'color: {TEXT_SECONDARY}').classes('ml-auto')
    
    ui.element().style("width: 8rem")
    
@ui.refreshable 
def StartTargetCards():
    #create cards for start and target
    with ui.row().classes('gap-4 items-center'):
            with ui.card(align_items='center').style(f"height: 3rem; width: 10rem; {BORDER_SETTINGS}").classes(f'no-shadow'):
                ui.label(GameLogic._StartWord).style(f'color: {TEXT_PRIMARY}; font-weight: normal').classes('absolute-center')
            ui.icon("sym_r_keyboard_double_arrow_right", size="2rem", color=BORDER_COLOR)
            with ui.card(align_items='center').style(f"height: 3rem; width: 10rem; {BORDER_SETTINGS}").classes(f'w-48 no-shadow'):
                ui.label(GameLogic._TargetWord).style(f'color: {TEXT_PRIMARY}; font-weight: normal').classes('absolute-center')

@ui.refreshable
def RenderPage(page: int):
    global _ChainScrollArea

    if(PAGES[page] == "Normal"):
        with ui.column().classes('w-full h-full items-center'):
            # ui.chip(f"A max distance of ({GameLogic.DISTANCE_CUTOFF}) can be chained.",icon="sym_r_arrow_forward", on_click=lambda e: ui.notify("Build a chain to the target word")).props("outlined")

            #show start and target
            StartTargetCards()

#             #word box
#             ui.add_body_html("""
# <div width=100%>
#     <q-input color="purple-12" v-model="text" label="Label">
#         <template v-slot:prepend>
#             <q-icon name="event" />
#         </template>
#     </q-input>
# </div>
# """)
            inputText = ui.input(placeholder="chain a word...").props(f'autocomplete=off; autocapitalize=off; input-style="color: {BORDER_COLOR}"').classes(f'color-red-300 w-96')
            inputText.on('keydown', lambda e: GuessInput(inputText) if e.args['key'] == "Enter" else None)

            #word chain scroll area
            with ui.element().classes("h-screen"):
                with ui.scroll_area().style(f"height: 60%; border-color: {BORDER_COLOR}; border-width: 1px; border-radius: {BORDER_RADIUS}").classes(f'rounded w-96 p-0') as scrollArea:
                    _ChainScrollArea = scrollArea
                    WordChain()

def SelectEmbedOption(option: str):
    global _EmbedOptionKey
    _EmbedOptionKey = option

#start of program
if(__name__ == "__main__"):

    #load data and start game
    GameLogic.LoadWordData(EMBED_OPTIONS[_EmbedOptionKey]["words"], EMBED_OPTIONS[_EmbedOptionKey]["banned"])
    GameLogic.RestartGame()

    #start of UI
    ui.colors(primary=PRIMARY, secondary=SECONDARY, accent=ACCENT, positive=POSITIVE, negative=NEGATIVE, info=INFO, warning=WARNING, dark=DARK, dark_page=DARK_PAGE)
    ui.dark_mode().enable()
    ui.add_head_html('<style>body { overflow: hidden; }</style>') #disable scrolling

    #winning dialogue setup
    _WinDialog = ui.dialog()
    _WinDialog.close()

    #info dialogue setup
    infoDialogue = ui.dialog()
    with infoDialogue, ui.card().style(f"{BORDER_SETTINGS}").classes('w-96 h-108 no-shadow border-[5px] items-center justify-center'):
        with ui.row().classes('justify-between items-center'):
            ui.icon('sym_r_info', size="150%", color=TEXT_PRIMARY)
            ui.label("Info").style(f"color: {TEXT_PRIMARY}; font-weight: bold; font-size: 150%")
        with ui.expansion(text="How do I play?").style(f"color: {TEXT_PRIMARY};").classes('w-full'):
            ui.label(f"""The goal is to create a chain of related words to reach a 'target' word. 
                     The start and ending positions are determined randomly, and linked words must be a 
                     distance of {GameLogic.DISTANCE_CUTOFF} from the previous.""").style(f"color: {TEXT_SECONDARY};")
            ui.label("""*Some words may seem obviously related but have a high distance.
                      The algorithm determines similarity based upon similar contexts, 
                     not necessarily similar meaning""").style(f'color: {TEXT_PRIMARY}')
            
    #header
    with ui.header().style(f'background-color: {DARK}').style('font-size: 24').classes('h-16 w-screen font-weight-bold'):
        with ui.row().classes('items-center h-full w-full'):
                ui.toggle(PAGES, value=1, on_change=lambda e:RenderPage.refresh(e.value))
                ui.label('Linkedle').style(f'color: {TEXT_PRIMARY}; font-size: 250%; font-weight: bold').classes('absolute-center')
                with ui.dropdown_button('Embed Files', icon="sym_r_storage"):
                    for opt in EMBED_OPTIONS.keys():
                        ui.item(str(opt), on_click=lambda e: SelectEmbedOption(str(opt)))
                ui.button(icon='sym_r_refresh', on_click=lambda e: RestartBtn())
                ui.button(icon='sym_r_info', on_click=lambda e: infoDialogue.open()).classes('ml-auto')
    
    RenderPage(1)
    
ui.run(reload=False) #dont use reload (watch files) because leads to errors

