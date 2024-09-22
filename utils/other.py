import os
from simple_term_menu import TerminalMenu
from utils.settings import get_setting

colorlist = [
'bg_black',
'bg_blue',
'bg_cyan',
'bg_gray',
'bg_green',
'bg_purple',
'bg_red',
'bg_yellow',
'fg_black',
'fg_blue',
'fg_cyan',
'fg_gray',
'fg_green',
'fg_purple',
'fg_red',
'fg_yellow',
'bold',
'italics',
'standout',
'underline',
'Back'
]

def clear():
	if os.name == "nt": os.system("cls")
	else: os.system("clear")

def menu(options, title="XSINT"):
	highlight = get_setting("menu", "highlight")
	cursorc = get_setting("menu", "cursorstyle")
	cursor = get_setting("menu", "cursor")
	m = TerminalMenu(
	options,
	title=title,
	menu_cursor=cursor,
	clear_screen=True,
	menu_highlight_style=(highlight, "bold"),
	menu_cursor_style=(cursorc, "bold")
	).show()
	return m
