from nicegui import ui, app
import GameLogic
from CustomUI import ToggleButton
from CustomUI import ToggleButtonManager
import Dictionary as WordDictionary
import asyncio
import random
import FileManager
import datetime
import os

#region PARAMETERS
#constant UI colours and parameters
GAME_NAME = "Linkonym"
BORDER_COLOR = '#AAAAAA'
BORDER_WIDTH = '0px'
BORDER_RADIUS = '10px'
BORDER_SETTINGS = f'border-color: {BORDER_COLOR}; border-width: {BORDER_WIDTH}; border-radius: {BORDER_RADIUS}'
TEXT_PRIMARY = 'white'
TEXT_BLACK = 'black'
TEXT_SECONDARY = '#777777'
TEXT_DARK_GREY = '#555555'
PRIMARY = '#005c2e'
SECONDARY =  '#26a69a'
ACCENT = '#9c27b0'
DARK = '#1d1d1d'
DARK_PAGE = '#121212'
POSITIVE = '#21ba45'
NEGATIVE = '#c10015'
INFO = '#31ccec'
WARNING = '#f2c037'
GAME_WIDTH= '24rem'
HEADER_HEIGHT = '4rem'
NUM_DEFINITIONS = 2
MAX_TRACK_GAMES = 50
PORT = 8000

#other globals (not constant)
_WebRandom = random.Random()
#endregion

#region PAGES
#stat page
@ui.page('/pistats')
def PiStatsPage():
    ui.markdown(f"""
{os.popen('vcgencmd measure_temp').readline()}
{os.popen("df -h /").read()}
{os.popen('free').read()}
{os.popen('uptime').readline()}
""")

#root page
@ui.page('/')
def RootPage():
    ui.navigate.to('/daily')

#daily game page
@ui.page('/daily')
async def DailyPage():
    await GamePage('daily', mode='daily')

#practice game page
@ui.page('/practice/{seed}')
async def DailyPage(seed: str):
    await GamePage(seed, mode='practice')

#shared game page for rendering everything
async def GamePage(seed: str, mode: str = 'daily'):
#endregion

    #region REFRESHABLES
    @ui.refreshable
    def HeaderRow(dialogs: dict):
        """
        Creates all the objects seen in the website header. Should be a child of a header element.
        """

        modeIcon = 'sym_r_today' if mode == 'daily' else 'sym_r_all_inclusive'

        #row for the entire header
        with ui.row().style(f'height: {HEADER_HEIGHT}').classes('justify-between items-center w-full'):
            #first 30%
            with ui.row().classes('justify-start').style('width: 30%'):
                with ui.dropdown_button().props(f'dropdown-icon={modeIcon} no-icon-animation transition-show=jump-down transition-hide=jump-up') as dropdownButton:
                    with ui.item(on_click=lambda: ChangeMode('daily')) as specialItem:
                        specialItem.on_click(lambda: dropdownButton.close())
                        with ui.row().classes('justify-center items-center gap-1.5'):
                            ui.icon('sym_r_today', color=TEXT_PRIMARY, size='125%')
                            ui.label("Daily").style(f"color: {TEXT_PRIMARY}")
                    with ui.item(on_click= lambda: ChangeMode('practice')) as specialItem:
                        specialItem.on_click(lambda: dropdownButton.close())
                        with ui.row().classes('justify-center items-center gap-1.5'):
                            ui.icon('sym_r_all_inclusive', color=TEXT_PRIMARY, size='125%')
                            ui.label("Seeded").style(f"color: {TEXT_PRIMARY}")
                ui.button(icon='sym_r_undo', on_click=lambda: (RemoveLastLink(), WordChain.refresh(False)))

                # ui.button(icon='sym_r_add_circle', on_click=lambda e: RestartBtn()).style('width: 10%')

            #game name
            ui.label(f'{GAME_NAME}').style(f'color: {TEXT_PRIMARY}; font-size: 200%; font-weight: bold').classes('absolute-center')

            async def HintLocal():
                await Hint(WordChain.refresh)
            async def GiveUpLocal():
                await GiveUp(WordChain.refresh)

            #last 30%
            with ui.row().classes('justify-end').style('width: 30%'):
                with ui.dropdown_button().props('dropdown-icon=sym_r_more_vert no-icon-animation transition-show=jump-down transition-hide=jump-up') as dropdownButton:
                    with ui.item(on_click=HintLocal) as specialHintItem:
                        specialHintItem.on_click(lambda: dropdownButton.close())
                        with ui.row().classes('justify-center items-center gap-1.5'):
                            ui.icon('sym_r_lightbulb', color=TEXT_PRIMARY, size='125%')
                            ui.label("Hint").style(f"color: {TEXT_PRIMARY}")
                    with ui.item(on_click=GiveUpLocal) as specialGiveUpItem:
                        specialGiveUpItem.on_click(lambda: dropdownButton.close())
                        with ui.row().classes('justify-center items-center gap-1.5'):
                            ui.icon('sym_r_flag', color=TEXT_PRIMARY, size='125%')
                            ui.label("Give up").style(f"color: {TEXT_PRIMARY}")
                    with ui.item(on_click=lambda: (dialogs['stats'].open(), dropdownButton.close())):
                        with ui.row().classes('justify-center items-center gap-1.5'):
                            ui.icon('sym_r_bar_chart', color=TEXT_PRIMARY, size='125%')
                            ui.label("Stats").style(f"color: {TEXT_PRIMARY}")
                    with ui.item(on_click=lambda: (dialogs['settings'].open(), dropdownButton.close())):
                        with ui.row().classes('justify-center items-center gap-1.5'):
                            ui.icon('sym_r_build', color=TEXT_PRIMARY, size='125%')
                            ui.label("Settings").style(f"color: {TEXT_PRIMARY}")
                ui.button(icon='sym_r_info', on_click=lambda: dialogs['info'].open())
    
    @ui.refreshable
    def StatsElements():
        """
        Creates all the elements found in the stats dialog. Should be a child of the dialog element.
        """

        gameScores: list = app.storage.user.get('game-scores')
        gamesPlayed: int = app.storage.user.get('games-played')
        with ui.row().classes('justify-center items-center gap-1.5'):
                ui.icon('sym_r_bar_chart', size="150%", color=TEXT_PRIMARY)
                ui.label("Stats").style(f"color: {TEXT_PRIMARY}; font-weight: bold; font-size: 150%")

        if(len(gameScores) > 0):
            ui.echart({
            'height' : '60%',
            'title': {
                'text': 'Previous scores',  #title text
                'subtext': f'Maxes at {MAX_TRACK_GAMES} games',  #subtitle
                'left': 'center', 
                'top': 'top', 
                'textStyle': {
                    'color': TEXT_PRIMARY,
                    'fontSize': 16
                },
            },
            'tooltip': {
                'trigger': 'item', 
                ':formatter': """
                    function(params) {
                        return 'Score: ' + params.value + '<br>' +
                            'Seed: ' + params.name + '<br>' +
                            'Date: ' + params.data.date;
                    }
                """
            },
            'xAxis' : {'show' : False, 'type' : 'category', 'data' : [score['seed'] for score in gameScores]},
            'yAxis' : {'type' : 'value', 'splitLine' : {
                'lineStyle': {
                    'type' : 'dashed',
                    'color': TEXT_SECONDARY
                }
            }, ''
            'interval': 2},
            'legend': {'show' :  False },
            'series': [
                {
                    'type' : 'bar',
                    'data': [{'name': score['seed'], 'value': score['score'], 'date': score['date']} for score in gameScores],
                    'name' : 'Score',
                    'color': app.storage.user.get('site-color')
                }
            ]
            })

            avgScore = 0
            bestScore = 1000
            prevDate = ""
            streak = 0
            for gs in gameScores:
                if(gs['seed'] == 'daily'):
                    gameDate = datetime.datetime.strptime(gs['date'], '%d/%m/%y')
                    if(prevDate == ""):
                        prevDate = gameDate
                        streak = 1
                    elif(prevDate != gameDate):
                        if((gameDate - prevDate).days == 1):
                            streak +=1
                        else:
                            streak = 0
                    prevDate = gameDate
                    
                avgScore += gs['score']
                bestScore = min(bestScore, gs['score'])
                

            numGameScore = len(gameScores) if(len(gameScores)) != 0 else 1
            avgScore = round(avgScore / numGameScore, 2)

            with ui.row().classes('w-full justify-between items-center'):
                ui.markdown(f'Average chain length')
                ui.label(avgScore).style(f'color: {TEXT_SECONDARY}')

            with ui.row().classes('w-full justify-between items-center'):
                ui.markdown(f'Shortest chain length')
                ui.label(bestScore).style(f'color: {TEXT_SECONDARY}')

            with ui.row().classes('w-full justify-between items-center'):
                ui.markdown(f'Daily streak')   
                ui.label(streak).style(f'color: {TEXT_SECONDARY}')
            
            with ui.row().classes('w-full justify-between items-center'):
                ui.markdown(f'Games played')   
                ui.label(gamesPlayed).style(f'color: {TEXT_SECONDARY}')
            
        else:
            ui.markdown('**No data yet!**').classes('absolute-center')
    
    @ui.refreshable
    def WinElements():
        """
        Creates all the elements for the win dialog. Should be a child of a dialog element.
        """

        wordChain = app.storage.tab.get('word-chain')
        givenUp = app.storage.tab.get('given-up')
        numHints = app.storage.tab.get('num-hints')
        terminalWords = app.storage.tab.get('terminal-words')

        #store parameters
        #set all parameters
        with ui.row().classes('justify-center items-center gap-1.5'):
            ui.icon('sym_r_emoji_events' if not givenUp else 'sym_r_flag', size="150%", color=TEXT_PRIMARY)
            ui.label("You won!" if not givenUp else "Gave up!").style(f"color: {TEXT_PRIMARY}; font-weight: bold; font-size: 150%")

        with ui.row().classes('justify-center items-center gap-1.5'):
            ui.chip(f"{len(wordChain)-1} links", icon='sym_r_link')

            ui.chip(f"{numHints} hint" + ('s' if numHints != 1 else ''), icon='sym_r_lightbulb')

        with ui.scroll_area().style(f'border-color: {BORDER_COLOR}; border-radius: {BORDER_RADIUS}; border-width: 1px; width: 90%').classes('h-full') as scrollArea:
            with ui.timeline(side='right', layout='dense').classes('gap-0 p-0 h-full'):
                for i, w in enumerate(wordChain):
                    GameLogic.WordSim(w, terminalWords[1], 3)
                    ui.timeline_entry("",subtitle=w).style('height: 4rem').classes('p-0')
                scrollArea.scroll_to(percent=0)
                ui.run_javascript(f"getElement('{scrollArea.id}').setScrollPercentage('vertical', 1, 750)")

        with ui.row().style('width: 100%; height: 10%').classes('justify-center'):
            ui.button(icon='sym_r_add_circle', on_click=lambda e: (ui.navigate.to(f'/practice/{_WebRandom.randint(0, 50000000)}')))
            ui.button(icon='sym_r_ios_share', on_click=lambda e: CopyClipboardGame())
    
    @ui.refreshable 
    def TerminalCards():
        """
        Creates the start and target cards (terminals)
        """

        terminalWords = app.storage.tab.get('terminal-words')
        color = app.storage.user.get('site-color')

        #create cards for start and target
        with ui.row().classes('gap-0 items-center justify-between w-full'):
            start = ToggleButton(linkedId=terminalWords[0], label=terminalWords[0], col1=DARK, col2=color, on_enable=lambda e: DictionaryText.refresh()).style(BORDER_SETTINGS+"; width: 40%")
            ui.icon("sym_r_keyboard_double_arrow_right", size="2rem", color=BORDER_COLOR)
            end = ToggleButton(linkedId=terminalWords[1], label=terminalWords[1], col1=DARK, col2=color, on_enable=lambda e: DictionaryText.refresh()).style(BORDER_SETTINGS+"; width: 40%")
            RegisterTglBtn(start)
            RegisterTglBtn(end)
    
    @ui.refreshable
    def WordChain(fadeIn: bool = True):
        """
        Creates the elements for the word chain. Should be a child of a scroll area.
            Also calls win game if target word is the last word
        """
        
        terminalWords = app.storage.tab.get('terminal-words')
        wordChain = app.storage.tab.get('word-chain')
        color = app.storage.user.get('site-color')

        #create a card for each word
        with ui.column().classes("w-full gap-2"):
            for i, word in enumerate(wordChain):
                chainMessage = f"({GameLogic.WordSim(word, terminalWords[1], 3)}) to '{terminalWords[1]}'"
                # if(not i == len(GameLogic._WordChain)-1):
                #     chainMessage = f"({GameLogic.WordSim(word, GameLogic._WordChain[i+1], 3)})"
                appendStyle = "" if i != len(wordChain) - 1 or not fadeIn  else "; animation: fade 0.3s"
                
                tglBtn = ToggleButton(linkedId=word, col1=DARK, col2=color, on_enable=lambda e: DictionaryText.refresh()).style(f"width: 100%; {BORDER_SETTINGS}" + appendStyle).classes(f'custom-button-content')
                RegisterTglBtn(tglBtn)
                with tglBtn:
                    with ui.row().style('width: 100%').classes('gap-4 h-full items-center justify-start text-left'):
                        ui.label(f'{i+1}').style(f'color: {TEXT_SECONDARY}')
                        ui.label(word).style(f'font-weight: normal; color: {TEXT_PRIMARY}')
                        ui.label(f'{chainMessage}').style(f'color: {TEXT_SECONDARY}').classes('ml-auto')
                
                if(word == terminalWords[1]):
                    WinGame(StatsElements.refresh, WinElements.refresh)

        
        ui.element().style("height: 8rem").classes('w-full')
    
    @ui.refreshable
    def DictionaryText():
        word = app.storage.client.get('selected-word')
        if(word != None and word != ''):
            ui.separator().style(f'background-color: {BORDER_COLOR}; animation: fade 0.5s')            
            ui.element('div').classes('my-2')

            #retrieve definition
            definitionNotFound = False
            definitions = WordDictionary.getRecordsAdvanced(word)
            if(definitions == None or len(definitions.keys())==0): 
                word = GameLogic._WordData['vocab'][word]['lemma']
                definitions = WordDictionary.getRecordsAdvanced(word)

            if(definitions == None or len(definitions.keys())==0):
                definitionNotFound = True
                definitions = {
                    'definition_1' : f'https://www.google.com/search?q=define%20{word} to find the meaning',
                    'pos_1' : 'No available definition'
                }
            
            #dictionary entry
            ui.label(word).style(f'font-size: 250%; font-weight: bold; color: {TEXT_PRIMARY}; text-align: left; animation: fade 1s')
            total = min(NUM_DEFINITIONS, sum(1 for key in definitions if key.startswith("definition_")))
            for i in range(1, total+1):
                ui.element('div').classes('my-2')
                ui.label(f"{i}. {definitions[f'pos_{i}']}").style(f'color: {TEXT_PRIMARY}; text-align: left; animation: fade 1s').classes('text-italic')
                ui.element('div').classes('my-2')

                if(not definitionNotFound):
                    ui.label(definitions[f'definition_{i}']).style(f' color: {TEXT_PRIMARY}; text-align: left; animation: fade 1s')
                else:
                    ui.link(text = f"Please visit https://www.google.com/search?q=define%20{word} for the meaning", target=f'https://www.google.com/search?q=define%20{word}', new_tab=True).style(f' color: {TEXT_PRIMARY}; text-align: left; animation: fade 1s')
            
            ui.element('div').classes('my-4')
            ui.separator().style(f'background-color: {BORDER_COLOR}; animation: fade 0.5s')
    #endregion

    #region INITIALIZATION
    await ui.context.client.connected()
    userAgent = ui.context.client.request.headers['user-agent']
    mobile = 'iPhone' in userAgent or 'Android' in userAgent

    random.seed(seed)
    startWord, targetWord = GetStartEndWords(seed, mode)

    InitializeStorage(seed, startWord, targetWord) #initialize all storage variables
    HeaderHTML() #inject custom html to header
    dialogs = CreateDialogs(StatsElements, WinElements) #get dialogs
    app.storage.client['dialogs'] = dialogs #store dialogs

    #endregion
    #region ELEMENTS
    
    #header
    with ui.header().style(f'background-color: {DARK}').style(f'font-size: 24; height: {HEADER_HEIGHT}').classes('py-0 w-screen font-weight-bold'):
        HeaderRow(dialogs)

    #main game column
    gameWidth = '22rem' if mobile else GAME_WIDTH
    with ui.column().style(f'width: {gameWidth}; padding-top: 1rem').classes('h-screen items-center mx-auto'):
        with ui.row().classes('justify-center items-center w-full'):
            ui.chip(f"Chain similar words to get to the target",icon="sym_r_link").props("outlined")


        #show start and target
        TerminalCards()
        
        inputWordBox = ui.input(placeholder="chain a word..."
                            ).props(f'autocomplete=off; autocapitalize=off; input-style="color: {BORDER_COLOR}"; autofocus'
                            ).classes(f' gap-0 items-center w-full')

        #word chain scroll area
        scrollArea = None
        with ui.scroll_area().style(f"height: 40%; border-color: {BORDER_COLOR}; border-width: 1px; border-radius: {BORDER_RADIUS}; scroll-behaviour: smooth").classes(f'rounded w-full') as sa:

            scrollArea = sa
            WordChain(scrollArea)

        with ui.element().style('height: 30%').classes('justify-start w-full'):
            DictionaryText()

        #wrapper function for what happens when the user enters a word
        def OnEnterWord():
            GuessInput(inputWordBox.value, WordChain.refresh)
            inputWordBox.value = ""
            ui.run_javascript(f"getElement('{inputWordBox.id}').focus()")
            ui.run_javascript(f"getElement('{scrollArea.id}').setScrollPercentage('vertical', 1, 400)")
            scrollArea.scroll_to(percent=100, axis='vertical')


        inputWordBox.on('keydown', lambda e: OnEnterWord() if e.args['key'] == "Enter" else None) #call wrapper if key is enter

    
            


    #endregion

#region UTILITY
def HeaderHTML():
    """
    Add custom head html for global custom classes, font-sizes, etc
        Requires site color storage to be set
    """
    
    siteColor = app.storage.user.get('site-color')

    #Global site colors
    ui.colors(primary=siteColor, secondary=SECONDARY, accent=ACCENT, positive=POSITIVE, negative=NEGATIVE, info=INFO, warning=WARNING, dark=DARK, dark_page=DARK_PAGE)
    ui.dark_mode().enable() 

    #Fade animation
    ui.add_head_html('''
    <style>
    @keyframes fade {from {opacity: 0;} to {opacity: 1.0;}}
    </style>
    ''')
    
    #Hidden scrollbar custom class
    ui.add_head_html('''
    <style>
    .hidden-scrollbar {
    overflow-y: scroll;
    scrollbar-width: none; /* Firefox */
    -ms-overflow-style: none;  /* Internet Explorer 10+ */
    }

    .hidden-scrollbar::-webkit-scrollbar { /* WebKit */
    width: 0;
    height: 0;
    }
    </style>
    ''')
    
    #Custom button content for max width
    ui.add_head_html('''
    <style>
    .custom-button-content .q-btn__content {
        width: 100% !important;
        padding: 0 !important;
        display: flex !important;
        align-items: stretch !important;
    }
    </style>
    ''')

    #Dialog without backdrop class
    ui.add_head_html('''
    <style>
    .no-backdrop-dialog .q-dialog__backdrop{
        background: rgba(0,0,0,0) !important;
    }
    </style>
    ''')

    #Site selection color / highlight color
    ui.add_head_html('''
    <style>
    :root {
    --selection-color:''' + siteColor + ''';
    }
    ::selection {
    background: var(--selection-color);
    }
    </style>
    ''') 
    
    #16px global font size - Cutoff for phone not auto zooming in
    ui.add_head_html("""
    <style>
        body {
            font-size: 16px; !important
        }
        .q-btn, .q-label, .q-input, .q-chip{
            font-size: 16px; !important
        }
    </style>
    """)

    #Site scrolling
    ui.add_head_html("""
    <style>
        body {
            overflow-y: auto;  /* Ensures vertical scrolling */
        }
    </style>
    """)

def OverlayCard() -> ui.card:
    """
    Creates an overlay card with global settings, useful for dialogs like win, stats, settings etc
    """
    
    return ui.card().style(f'{BORDER_SETTINGS}; width: 20rem; height: 28rem').classes(f'hidden-scroll no-shadow items-center hidden-scrollbar')

def CreateDialogs(statElementsF, winElementsF) -> dict:
    """
    Creates all the dialogs and stores them in a dictionary
    """

    dialogs = {}

    #stat dialog only
    dialogs['stats'] = ui.dialog()
    statRadio = None
    with dialogs['stats'], OverlayCard().classes('justify-start items-center gap-0'):
        statElementsF()

    #stat dialog combined with win dialog
    dialogs['stats-win'] = ui.dialog().props('transition-hide=fade transition-show=fade').style('backdrop-filter: none').classes('no-backdrop-dialog')
    statRadio = None
    with dialogs['stats-win'], OverlayCard().classes('justify-start items-center gap-0'):
        statElementsF()
        statRadio = ui.radio([' ', ''], value=' ', on_change= lambda e: dialogs['stats-win'].close()).props('inline size=xs')

    #winning dialogue setup
    dialogs['win'] = ui.dialog().props('persistent')
    with dialogs['win'] as dialog, OverlayCard():
        winElementsF()
        ui.radio([' ', ''], value=' ', on_change= lambda e: dialogs['stats-win'].open()).props('inline size=xs').bind_value(statRadio, 'value')
    

    #info dialogue setup
    dialogs['info'] = ui.dialog()
    with dialogs['info'], OverlayCard():

        descriptionCSS = f'color: #AAAAAA; font-style: normal; font-size: 90%'
        with ui.row().classes('justify-center items-center gap-1.5'):
            ui.icon('sym_r_info', size="150%", color=TEXT_PRIMARY)
            ui.label("Info").style(f"color: {TEXT_PRIMARY}; font-weight: bold; font-size: 150%")
        with ui.expansion(text="How do I play?", icon='sym_r_help_outline').style(f"color: {TEXT_PRIMARY}; width: 100%; font-style: oblique; border-radius: {BORDER_RADIUS}"):
            ui.label(f"""Your goal is to create a chain of related words to reach a 'target' word. 
                        Start and ending words are determined randomly, and links must have a maximum
                        similarity of {GameLogic.DISTANCE_CUTOFF} from the previous.""").style(descriptionCSS)
        with ui.expansion(text='How are word similarities determined?', icon='sym_r_help_outline').style(f"color: {TEXT_PRIMARY}; width: 100%; font-style: oblique; border-radius: {BORDER_RADIUS}"):
            ui.label(f"""{GAME_NAME} queries a database of over 70000 words that each have a corresponding vector. These vectors
                        are tweaked through NLP models. A euclidean distance operation between two word vectors returns the similarity.
                        Since similarity is based upon similar contexts, it doesn't necessarily translate to similar meaning.""").style(descriptionCSS)
        with ui.expansion(text=f'Who created {GAME_NAME}?', icon='sym_r_help_outline').style(f"color: {TEXT_PRIMARY}; width: 100%; font-style: oblique; border-radius: {BORDER_RADIUS}"):
            ui.label(f"""Hudson Woolford programmed {GAME_NAME} in python for a Computer Science project at his school.""").style(descriptionCSS)
            ui.label("""Ted Boss acted as a playtester and provided valuable feedback throughout development""").style(descriptionCSS + f'; color: {TEXT_SECONDARY}')
        with ui.expansion(text='Have you made any other products?', icon='sym_r_help_outline').style(f"color: {TEXT_PRIMARY}; width: 100%; font-style: oblique; border-radius: {BORDER_RADIUS}"):
            ui.label("""Hudson Woolford was a developer on Swingularity, an indie space golf game. Check it out!""").style(descriptionCSS)
            ui.link(text="Swingularity on STEAM", target="https://store.steampowered.com/app/3272450/Swingularity/", new_tab=True).style(descriptionCSS)

    #settings tools dialog
    dialogs['settings'] = ui.dialog()
    with dialogs['settings'], OverlayCard().style('height: 26.5rem').classes('gap-3 justify-start !important items-between'):
        with ui.row().classes('justify-center items-center gap-1.5'):
            ui.icon('sym_r_build', size="150%", color=TEXT_PRIMARY)
            ui.label("Settings").style(f"color: {TEXT_PRIMARY}; font-weight: bold; font-size: 150%")
        picker = ui.element('q-color').props('default-view=palette no-header no-footer').classes('w-full')
        picker.on('update:model-value', lambda color: ChangeSiteColor(color.args))
        # picker.q_color.props('default-view=palette no-header no-footer')
        
        ui.button(icon='sym_r_delete', text='Clear Data', on_click= lambda e: ClearUserData()).classes('justify-center w-full')

    return dialogs

def InitializeStorage(seed: str, startWord: str, targetWord: str):
    """
    Initializes all tab, user, and client storage. User storage will not be overwritten, but will be initialized if they don't exist.
    """

    #ensure user storage exists
    if(app.storage.user.get('site-color') == None):
        app.storage.user['site-color'] = PRIMARY
    if(app.storage.user.get('game-scores') == None):
        app.storage.user['game-scores'] = []
    if(app.storage.user.get('games-played') == None):
        app.storage.user['games-played'] = 0

    #temp tab storage
    app.storage.tab['seed'] = seed
    app.storage.tab['terminal-words'] = [startWord, targetWord] #store start and end words for optimisation
    app.storage.tab['word-chain'] = [startWord] #store a chain of words in the tab
    app.storage.tab['num-hints'] = 0 #store a number tracking hints in the tab
    app.storage.tab['given-up'] = False #store a boolean for given up in the tab
    app.storage.tab['mode'] = 'daily' #store a string for the users mode

    #temp client storage
    app.storage.client['toggle-btns'] = []
    app.storage.client['selected-word'] = ''

def ChangeMode(mode: str):
    app.storage.tab['mode'] = mode
    if(mode == 'practice'):
        ui.navigate.to(f'/practice/{_WebRandom.randint(0, 50000000)}')
    elif(mode=='daily'):
        ui.navigate.to('/daily')

def ChangeSiteColor(color: str):
    """
    Changes the primary color of the site to specified paremeter
    """

    app.storage.user['site-color'] = color
    ui.colors(primary=color, secondary=SECONDARY, accent=ACCENT, positive=POSITIVE, negative=NEGATIVE, info=INFO, warning=WARNING, dark=DARK, dark_page=DARK_PAGE)
    ui.run_javascript(f'''
    document.documentElement.style.setProperty('--selection-color', '{color}');
    ''')
    ui.notify(f"Changed site color to {color}", timeout=500)
    ui.navigate.reload()

def ClearUserData():
    """
    Resets all storage for the user, equivalent to clearing.
    """
    app.storage.user['color'] = PRIMARY
    app.storage.user['game-scores'] = []
    app.storage.user['games-played'] = 0
    ui.navigate.reload()

def RemoveLastLink():
    wordChain = app.storage.tab.get('word-chain')
    wordChain = wordChain[:-1] if len(wordChain) > 1 else wordChain
    app.storage.tab['word-chain'] = wordChain

def GetStartEndWords(seed: str, mode: str) -> tuple[str, str]:
    """
    Returns the start and end words for the corresponding seed and mode
    """

    if(mode == 'daily'):
        #daily word retrieval
        terminals = GameLogic._DailyData[str(datetime.datetime.now().date())].split(', ')
        return terminals[0], terminals[1]
    else:
        return GameLogic.GenerateStartEndWords(minDistance=0.5)

def CopyClipboardGame():
    """
    Copies a share message of the game to the users clipboard.
    """

    wordChain = app.storage.tab.get('word-chain')
    terminalWords = app.storage.tab.get('terminal-words')
    numHints = app.storage.tab.get('num-hints')

    #spoiler formatted chain
    chain = ""
    for word in wordChain:
        chain += f"||{word}||\n"

    #write to clipboard
    ui.clipboard.write(f"""----------
Check out my {GAME_NAME} game! 🙂

Here's my word chain from '{terminalWords[0]}' to '{terminalWords[1]}': 🔗

{chain}

Score: {len(wordChain)-1} 🔥
Hints: {numHints} 💡

You can play the same game here: http://{GAME_NAME}.com/{app.storage.tab.get('seed')}
----------""")
    
    ui.notify("Copied game to clipboard")

def GuessInput(guess: str, refreshWordChain):
    """
    Guesses the word, validates it, checks distance, notifies user on status, and appends to word chain if valid 
    """

    wordChain = app.storage.tab.get('word-chain')
    terminalWords = app.storage.tab.get('terminal-words')

    valid, message, guess = GameLogic.ValidateGuess(guess, wordChain) #if guess is valid/(if it is in possible values and not banned)
    if(valid):
        valid, message = GameLogic.ValidateWordDist(guess, wordChain) #get result of guessing the word, valid if it is within distance

        if(valid):
            wordChain.append(guess)
            app.storage.tab['word-chain'] = wordChain
            refreshWordChain(True)
            ui.notify(message, type='positive', timeout=1500, position='bottom', badgeColor=POSITIVE, badgeTextColor=TEXT_PRIMARY)
        else:
            ui.notify(message, type='warning', timeout=1500, position='bottom', badgeColor='warning', badgeTextColor=TEXT_BLACK)
    else:
        ui.notify(message, type='negative', timeout=1500, position='bottom', badgeColor=NEGATIVE, badgeTextColor=TEXT_PRIMARY)

def WinGame(refreshStats, refreshWin):
    seed = app.storage.tab.get('seed')
    wordChain = app.storage.tab.get('word-chain')
    score = len(wordChain)-1
    gameScores = app.storage.user.get('game-scores')
    gamesPlayed = app.storage.user.get('games-played')
    dialogs = app.storage.client.get('dialogs')

    #update stats
    gameScores.append({
        'score' : score,
        'seed' : seed,
        'date' : str(datetime.datetime.now().date().strftime('%d/%m/%y'))
    })
    if(len(gameScores) > MAX_TRACK_GAMES):
        gameScores = gameScores[-MAX_TRACK_GAMES:]
    app.storage.user['game-scores'] = gameScores

    gamesPlayed += 1
    app.storage.user['games-played'] = gamesPlayed

    refreshStats()

    #show dialog
    refreshWin()
    dialogs['win'].open()

def RegisterTglBtn(btn: ToggleButton):
    btns = app.storage.client.get('toggle-btns')
    btns.append(btn)
    app.storage.client['toggle-btns'] = btns

    btn.on_click(lambda: ToggleLink(btn))

def ToggleLink(btn: ToggleButton):
    enable = not btn._state
    app.storage.client['selected-word'] = btn.link if enable else ''

    btns = app.storage.client.get('toggle-btns')
    for b in btns:
        if(b.link == btn.link):
            b.enable(enable)
        else:
            b.enable(False)

async def Hint(refreshWordChain):
    """
    Queries gamelogic to determine and guess a hint
    """

    wordChain = app.storage.tab.get('word-chain')
    numHints = app.storage.tab.get('num-hints')
    terminalWords = app.storage.tab.get('terminal-words')

    lastWord = wordChain[-1]

    notif = ui.notification(timeout=None)
    notif.message = 'Calculating hint...'
    notif.spinner = True

    if(GameLogic.WordSim(lastWord, terminalWords[1]) < GameLogic.DISTANCE_CUTOFF):
        GuessInput(terminalWords[1], refreshWordChain)
    else:
        await asyncio.sleep(0.1)  #let the nicegui render the notification
        
        #run HintWord in a thread so it doesn't block
        loop = asyncio.get_running_loop()
        hint = await loop.run_in_executor(None, GameLogic.HintWord, lastWord, terminalWords[1], wordChain, 0.15)

        if(hint == 'FAILFAILFAIL'):
            ui.notify('No possible matches! Please undo.', color='negative')
        else:
            GuessInput(hint, refreshWordChain)

    refreshWordChain(True)

    notif.dismiss()

    numHints +=1
    app.storage.tab['num-hints'] = numHints

async def GiveUp(refreshWordChain):
    """
    The equivalent of looping hint until solved
    """

    wordChain = app.storage.tab.get('word-chain')
    numHints = app.storage.tab.get('num-hints')
    terminalWords = app.storage.tab.get('terminal-words')

    notif = ui.notification(timeout=None)
    notif.message = 'Solving...'
    notif.spinner = True

    await asyncio.sleep(0.1)  #let the nicegui render the notification

    #run HintWord in a thread so it doesn't block
    loop = asyncio.get_running_loop()
    for i in range(0, 20):
        lastWord = wordChain[-1]
        hint = await loop.run_in_executor(None, GameLogic.HintWord, lastWord, terminalWords[1], wordChain, 0.15, 10000 if i < 10 else 70000)
        if(hint == 'FAILFAILFAIL'):
            ui.notify('No possible matches! Winning automatically...', color='negative')
            wordChain.append(terminalWords[1])
            app.storage.tab['word-chain'] = wordChain
            refreshWordChain(True)
            break

        GuessInput(hint, refreshWordChain)
        refreshWordChain(True)
        wordChain = app.storage.tab.get('word-chain')
        numHints += 1
        if(GameLogic.WordSim(hint, terminalWords[1]) < GameLogic.DISTANCE_CUTOFF):
            await asyncio.sleep(0.5)  #wait a bit for clarity
            app.storage.tab['given-up'] = True
            app.storage.tab['num-hints'] = numHints
            GuessInput(terminalWords[1], refreshWordChain)
            numHints += 1
            refreshWordChain(True)
            break

    notif.dismiss()
    

#region LOGIC
"""

START OF AUTO INDEX PAGE / SCRIPT LOGIC

"""

#RUN UI
ui.run(
    reload=False, #watch files causes issues
    title=f"{GAME_NAME}",
    show=False, #dont reload
    storage_secret='SWINGULARITY',
    port= PORT,
    favicon='<svg xmlns="http://www.w3.org/2000/svg" enable-background="new 0 0 24 24" height="24px" viewBox="0 0 24 24" width="24px" fill="#e3e3e3"><g><rect fill="none" height="24" width="24"/></g><g><path d="M15,16v1.26l-6-3v-3.17L11.7,8H16V2h-6v4.9L7.3,10H3v6h5l7,3.5V22h6v-6H15z M12,4h2v2h-2V4z M7,14H5v-2h2V14z M19,20h-2v-2 h2V20z"/></g></svg>'
)
#endregion