#!/usr/bin/env python

"""
Python indicator applet to show the status of several git repositories

Behaviour
---------
When first opened, all repo's in `~/.batchgit` are checked against the remote.
A label is assigned of the form ahead, diverged, behind, up-to-date or no-state
is recorded for each repo. The menu is then set-up in the following way: The
main menu icon displays some global information - either all okay, or action
required; each individual menu item is assigned a symbol to reflect its current
status. In addition each menu item is given a `+n` to indicate the `n` modified
files.

The indicator then periodically checks all repo's locally with a frequency set
by `update_period` (by default this is 300 seconds); it will also check the
remote repositorys with a frequency set by `update_period_remote` (by default
this is 3600 seconds). To update against the remote at other times, a `manual
update` entry is provided in the menu itself.

"""

# Python 2.7.x standard library imports
import subprocess
import os
import sys
import argparse

sys.tracebacklimit = 2

try:
    import pygtk
    pygtk.require('2.0')
    import gobject
    import gtk
except ImportError:
    raise ImportError(
    "The python package gobject or gtk required for the batchgit indicator\n"
    "is not installed. To install you may use\n\n"
    "    apt-get install python-gobject\n"
    "    apt-get install python-gtk2\n"
    )
except AssertionError:
    raise ImportError(
    "The python package gtk2 required for the batchgit indicator\n"
    "is not installed. To install you may use\n\n"
    "    apt-get install python-gtk2\n")

try:
    import appindicator
except ImportError:
    raise ImportError(
    "The python package appindicator required for the batchgit indicator\n"
    "is not installed. To install you may use\n\n"
    "    apt-get install python-appindicator\n")


class AppIndicator:
    def __init__(self, dirs, args, update_period=300,
                 update_period_remote=3600):

        self.args = args
        self.dirs = dirs
        self.update_period = update_period
        self.update_period_remote = update_period_remote
        self.remote = False  # Flag to update the remote
        self.ind = appindicator.Indicator(
            "checkgit", "", appindicator.CATEGORY_APPLICATION_STATUS)

        self.ind.set_status(appindicator.STATUS_ACTIVE)
        self.ind.set_attention_icon("indicator-messages-new")

        self.IconMenuDictionary = {'ahead': gtk.STOCK_GO_UP,
                                   'diverged': gtk.STOCK_REFRESH,
                                   'behind': gtk.STOCK_GO_DOWN,
                                   'up-to-date': gtk.STOCK_YES,
                                   'no-state': gtk.STOCK_HELP
                                   }
        # create a menu
        menu = gtk.Menu()

        ManualCheck = gtk.ImageMenuItem(gtk.STOCK_REFRESH)
        ManualCheck.set_always_show_image(True)
        ManualCheck.show()
        ManualCheck.connect("activate", self.SetIconAndMenuRemote2)
        menu.append(ManualCheck)

        ManualUpdate = gtk.ImageMenuItem(gtk.STOCK_HOME)
        ManualUpdate.set_always_show_image(True)
        ManualUpdate.show()
        ManualUpdate.connect("activate", self.PullPushAll)
        ManualUpdate.connect("activate", self.SetIconAndMenuRemote2)
        menu.append(ManualUpdate)

        dirs_items = []
        for dir in self.dirs:
            label_name = self.ClearDirName(dir)
            item = gtk.ImageMenuItem(gtk.STOCK_YES, label_name)
            item.show()
            item.set_always_show_image(True)
            menu.append(item)
            dirs_items.append(item)

        self.dirs_items = dirs_items

        quit = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        quit.connect("activate", self.quit)
        quit.set_always_show_image(True)
        quit.show()
        menu.append(quit)

        self.ind.set_menu(menu)

        # Update the custom labels: must be done after `set_menu`.
        ManualCheck.set_label("Check status")
        ManualUpdate.set_label("Pull/Push")

        self.SetIconAndMenu(remote=True)  # Initialise the icon

        gobject.timeout_add_seconds(int(self.update_period),
                                    self.SetIconAndMenu)
        gobject.timeout_add_seconds(int(self.update_period_remote),
                                    self.SetIconAndMenuRemote)
        gtk.threads_init()

    def ClearDirName(self, dir):
        """ Give a cleaner directory name """
        home_dir = os.environ['HOME']
        return dir.replace(home_dir, "~")

    def CheckState(self, path):
        """ Check the state information of path, if remote is true then it will
        also be compared to see if the path is behind

        Returns
        =======
        state: str
            One of ahead, diverged, behind, or up-to-date

        """

        path = path.rstrip("/") + "/"

        if self.remote and not self.args.no_remote:
            # Check if there is a remote
            cmd_line = ("git --git-dir={}.git "
                        "--work-tree={} remote update".format(path, path))
            try:
                status = subprocess.check_output(cmd_line, shell=True)
            except subprocess.CalledProcessError as e:
                print("WARNING: Checking the remote failed. "
                      "I will try to continue with no remote")
                self.remote = False
                pass

        cmd_line = "git --git-dir={}.git --work-tree={} status".format(
            path, path)
        status = subprocess.check_output(cmd_line, shell=True)

        for state in ['ahead', 'diverged', 'behind', 'up-to-date']:
            if state in status:
                return state

        return 'no-state'

    def ModifiedCount(self, path):
        path = path.rstrip("/") + "/"
        cmd_line = "git --git-dir={}.git --work-tree={} ls-files -m".format(
            path, path)
        output = subprocess.check_output(cmd_line, shell=True)
        modified_files = output.split("\n")
        return len(modified_files) - 1

    def CheckAllDirStatus(self):
        stati = {}
        for (dir, list_item) in zip(self.dirs, self.dirs_items):
            if os.path.isdir(dir):
                status = {'state_to_origin': self.CheckState(dir),
                          'modified': self.ModifiedCount(dir),
                          }
                stati[dir] = status
            else:
                stati[dir] = {'state_to_origin': 'no-state',
                              'modified': 0
                              }
        return stati

    def GetIconFromDirStates(self):
        """ Logic for setting the main icon """

        stati = self.CheckAllDirStatus()
        states = [dic['state_to_origin'] for dic in stati.values()]

        states = filter(lambda a: a != "no-state", states)  # Remove no-state

        if 'diverged' in states:
            return gtk.STOCK_DIALOG_WARNING
        elif all([state == 'up-to-date' for state in states]):
            return gtk.STOCK_YES
        elif ('behind' in states) and ('ahead' in states):
            return gtk.STOCK_DIALOG_WARNING
        elif ('behind' in states):
            return gtk.STOCK_GO_DOWN
        elif ('ahead' in states):
            return gtk.STOCK_GO_UP
        else:
            print(states)
            return gtk.STOCK_MISSING_IMAGE

    def SetIconAndMenu(self, remote=False, *args):
        """ Sets the icon and menu items

        Parameters
        ----------
        remote : bool
            If true then update the remote for this time only

        Returns
        -------
        True
        """

        if remote:
            self.remote = True
        else:
            self.remote = False
        # Set the main icon
        self.ind.set_icon(self.GetIconFromDirStates())

        # Set individual menu items
        stati = self.CheckAllDirStatus()
        for i, dir_item in enumerate(self.dirs_items):
            dir = self.dirs[i]
            label = self.ClearDirName(str(dir))
            status = stati[dir]

            if status['state_to_origin'] is not None:
                img = self.IconMenuDictionary[status['state_to_origin']]
                dir_item.get_image().set_from_stock(img,
                                                    gtk.ICON_SIZE_MENU)

                modified_count = stati[dir]['modified']
                if modified_count > 0:
                    label += " (+{})".format(modified_count)

                dir_item.set_label(label)

        self.remote = False

        return True

    SetIconAndMenuRemote2 = lambda self, args: self.SetIconAndMenu(self)
    SetIconAndMenuRemote = lambda self : self.SetIconAndMenu(self)

    def quit(self, widget, data=None):
        gtk.main_quit()

    def PullPushAll(self):
        """ Runs bactchgit -u """
        cmd_line = "batchgit -u"
        status = subprocess.check_output(cmd_line, shell=True)


def _rcfile_help_messg(rcfile):
    mssg = """ The rcfile {} does not exist

Details:
checkgit uses the rcfile to load the paths of repo's that you want to check.
You can create an rcfile for it to use by creating a file `~/.batchgitrc` in
your home directory which contains lines with

/path/to/your/repo
"""
    return mssg

def main():
    # Set up the argparse
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        '--no_remote', action='store_true',
        help='If set then do not check the remote ever')
    parser.add_argument(
        '-r', '--RCFILENAME', default=".batchgitrc",
        help='If set use supplied RCFILENAME otherwise use the default')

    args = parser.parse_args()

    RCFILENAME = args.RCFILENAME
    rcfile = os.path.expanduser("~") + "/" + RCFILENAME
    if os.path.isfile(rcfile):
        dirs = []
        with open(rcfile, "r") as f:
            for line in f:
                dirs.append(line.rstrip("\n"))

        indicator = AppIndicator(dirs, args),

        gtk.main()
    else:
        raise ValueError(_rcfile_help_messg(rcfile))

if __name__ == "__main__":
    main()
