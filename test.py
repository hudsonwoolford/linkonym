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


""" 
-------------------------------------------------------------------------------

UTILITY FUNCTIONS

-------------------------------------------------------------------------------
"""

""" 
-------------------------------------------------------------------------------

REFRESHABLE ELEMENTS

-------------------------------------------------------------------------------
"""
#dialog card when you win the game

""" 
-------------------------------------------------------------------------------

PAGES

-------------------------------------------------------------------------------
"""
def CustomHTMTL():
    color = app.storage.user.get('color')

    #global setup - colours
    ui.dark_mode().enable() 

    #global setup - html
    ui.add_head_html(
    r'''
    <style>
    @keyframes fade {from {opacity: 0;} to {opacity: 1.0;}}
    </style>
    ''') #fading

    ui.add_head_html(
    r'''
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
    <style>
    .custom-button-content .q-btn__content {
        width: 100% !important;
        padding: 0 !important;
        display: flex !important;
        align-items: stretch !important;
    }
    .no-backdrop-dialog .q-dialog__backdrop{
        background: rgba(0,0,0,0) !important; /* nothing - this better work */   
    }
    
    </style>
    ''')#other html

    ui.add_head_html(
    '''
    <style>
    :root {
    --selection-color:''' + color + ''';
    }
    ::selection {
    background: var(--selection-color);
    }
    </style>
    ''') #selection color
    ui.add_css("""
        body {
            font-size: 16px; !important
        }
        .q-btn, .q-label, .q-input, .q-chip{
            font-size: 16px; !important
        }
    """)
    ui.add_css("""
        body {
            overflow-y: auto;  /* Ensures vertical scrolling */
        }
    """)


            
@ui.page('/dev')
def DevPage():
    ui.dark_mode().enable() 
    ui.label('nice try')

async def GamePage(_Seed: str, mode: str):
    CustomHTMTL()
    @ui.refreshable
    def reloadme():
        for i in range(0, 5):
            ui.label('fade').style('animation: fade 0.5s')

    
    reloadme()

    ui.button('Click', on_click=lambda: reloadme.refresh())


@ui.page('/{_Seed}')
async def DailyPage(_Seed):
    await GamePage(_Seed, 's')

@ui.page('/')
async def Page():
    ui.navigate.to('/dsf')

""" 
-------------------------------------------------------------------------------

START OF AUTO-INDEX OR LOGIC

-------------------------------------------------------------------------------
"""
ui.run(
    reload=False,
    title=f"GAME_NAME",
    show=False,
    storage_secret='SWINGULARITY',
    port=8000,
    favicon='<svg xmlns="http://www.w3.org/2000/svg" enable-background="new 0 0 24 24" height="24px" viewBox="0 0 24 24" width="24px" fill="#e3e3e3"><g><rect fill="none" height="24" width="24"/></g><g><path d="M15,16v1.26l-6-3v-3.17L11.7,8H16V2h-6v4.9L7.3,10H3v6h5l7,3.5V22h6v-6H15z M12,4h2v2h-2V4z M7,14H5v-2h2V14z M19,20h-2v-2 h2V20z"/></g></svg>' #figure out how to scale this correctly
)

