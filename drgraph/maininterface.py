import os
import webbrowser
import gc
from zipfile import BadZipfile

import wx
import networkx as nx

from drgraph.concuss.stageinterface import ColorInterface, DecomposeInterface
from drgraph.stageinterface import DummyStageInterface
from drgraph.data_loader import DataLoaderFactory, UnknownPipelineError

class MainInterface(wx.Frame):
    """
    Main window of the visualization tool.

    This class defines all the GUI elements in the main window, including
    menus and their event methods, the statusbar, and the space for
    StageInterfaces.
    """

    doc_url = 'https://github.ncsu.edu/engr-csc-sdc/2016springTeam09/wiki'

    def __init__(self, parent, filename=None):
        """Create the main window and all its GUI elements"""
        super(MainInterface, self).__init__(parent, title="Visualization Tool")

        self.Bind(wx.EVT_CLOSE, self.OnClose)

        self._make_menubar()
        self.CreateStatusBar()

        self.notebook = wx.Notebook(self, wx.NewId(), style=wx.BK_DEFAULT)

        dummy = DummyStageInterface(self.notebook)
        self.add_tab(dummy)

        self._restore_geometry()

        if filename is not None:
            self.load_file(filename)

    def _make_menubar(self):
        """Create, populate, and show the menubar"""
        # Menubar setup
        menubar = wx.MenuBar()

        # Load file submenu
        fileMenu = wx.Menu()
        fitem = fileMenu.Append(wx.ID_OPEN, help='Open execution data')
        self.Bind(wx.EVT_MENU, self.OnOpen, fitem)
        fileMenu.Append(wx.NewId(), '&Config', 'Configure Pipeline Data')
        fitem = fileMenu.Append(wx.ID_EXIT, help='Quit application')
        self.Bind(wx.EVT_MENU, self.OnQuit, fitem)
        menubar.Append(fileMenu, '&File')

        # Load visualization submenu
        visualMenu = wx.Menu()
        preferencesMenu = wx.Menu()
        cb = preferencesMenu.AppendCheckItem(wx.NewId(), "Color-Blind Mode")
        self.Bind(wx.EVT_MENU, self.OnColorBlind, cb)
        visualMenu.AppendMenu(wx.NewId(), 'Preferences', preferencesMenu)
        menubar.Append(visualMenu, '&Visuals')

        # Load help submenu
        helpMenu = wx.Menu()
        doc = helpMenu.Append(wx.ID_HELP_CONTENTS, '&Documentation',
                        'Opens online documentation')
        self.Bind(wx.EVT_MENU, self.OnDoc, doc)
        about = helpMenu.Append(wx.ID_ABOUT, help='About this application')
        self.Bind(wx.EVT_MENU, self.OnAbout, about)
        menubar.Append(helpMenu, '&Help')

        self.SetMenuBar(menubar)

    def _restore_geometry(self):
        """Restore the window geometry from last time"""
        config = wx.ConfigBase.Get()
        config.SetPath("/window/geometry")
        x = config.ReadInt("x", -1)
        y = config.ReadInt("y", -1)
        w = config.ReadInt("w", -1)
        h = config.ReadInt("h", -1)
        # Restore position
        if x != -1 and y != -1:
            self.MoveXY(x, y)
        else:
            self.Center()
        # Restore size
        if w != -1 and h != -1:
            self.SetSize((w, h))

    def _save_geometry(self):
        """Store the current window geometry"""
        config = wx.ConfigBase.Get()
        config.SetPath("/window/geometry")
        x, y = self.GetPositionTuple()
        w, h = self.GetSizeTuple()
        config.WriteInt("x", x)
        config.WriteInt("y", y)
        config.WriteInt("w", w)
        config.WriteInt("h", h)

    def add_tab(self, interface):
        """Add an interface tab with the correct tab name"""
        self.notebook.AddPage(interface, interface.name)

    def remove_all_tabs(self):
        """Remove all the StageInterface tabs"""
        self.notebook.DeleteAllPages()

    def OnClose(self, e):
        """Close the main window"""
        self._save_geometry()
        self.Destroy()

    def OnOpen(self, e):
        """Open a new set of visualization data"""
        # Create the dialog
        dlg = wx.FileDialog(self, defaultDir=os.getcwd(),
                            wildcard='Visualization archives (*.zip)|*.zip|' +
                            'All files (*)|*',
                            style=wx.OPEN)

        # Show the dialog and open the file if the user selected one
        if dlg.ShowModal() == wx.ID_OK:
            self.load_file(dlg.GetPath())

        # Destroy the dialog
        dlg.Destroy()

        # At this point, we might be using several extra megabytes of RAM, so
        # run garbage collection to clean up unused objects.
        gc.collect()

    def load_file(self, filename):
        dlf = DataLoaderFactory()
        try:
            dl = dlf.load_data(filename)
        except (KeyError, BadZipfile) as e:
            e_dlg = wx.MessageDialog(None, 'File does not contain valid ' +
                                     'visualization data', 'Error',
                                     wx.ICON_ERROR)
            e_dlg.ShowModal()
        except UnknownPipelineError as e:
            e_dlg = wx.MessageDialog(None, e.msg, 'Error', wx.ICON_ERROR)
            e_dlg.ShowModal()
        else:
            colorStage = ColorInterface(self.notebook)
            self.remove_all_tabs()
            self.add_tab(colorStage)
            colorStage.vis.set_graph(dl.graph, dl.colorings)
            # Temporary: For open house 
            decomposeStage = DecomposeInterface(self.notebook, dl.graph,
                    dl.pattern, dl.colorings[-1])
            self.add_tab(decomposeStage)
            #decomposeStage.vis.set_graph(dl.graph, dl.pattern, dl.colorings[-1])

    def OnQuit(self, e):
        """Quit the application"""
        self.Close()

    def OnDoc(self, e):
        """Open the online documentation"""
        webbrowser.open(self.doc_url, new=2)

    def OnColorBlind(self, e):
        """Switch to color-blind palette"""
        # TODO: This may be tricky... need to update palette for all tabs...

    def OnAbout(self, e):
        """Show an about box"""
        info = wx.AboutDialogInfo()
        info.Name = "Visualization Tool"
        info.Copyright = "(C) 2016 Team 9"
        info.Description = "A tool for visualizing graph algorithmic pipelines"
        info.WebSite = ("https://github.ncsu.edu/engr-csc-sdc/2016springTeam09",
                        "Website")
        info.Developers = ["Yang Ho", "Clayton G. Hobbs", "Brandon Mork",
                           "Nishant G. Rodrigues"]
        info.License = "BSD"  # TODO: set this as the actual license text

        wx.AboutBox(info)
