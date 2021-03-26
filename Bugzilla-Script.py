import requests
import re
from bs4 import BeautifulSoup
import csv
import cProfile
import os
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog
from tkfilebrowser import askopendirname, askopenfilenames, asksaveasfilename
import queue
import threading

"""
id="version" for build in format XX_\d.\d.\d (Mav/RPs)
class="bz_comment_text" for corrections
"""

class Bug:
    """
    Class that gets all the info about a bug from bugzilla given its bug number
    """
    html = None
    number = None
    device = None
    host = None
    os = None
    switch = None
    failure = None
    DUTs = None
    monitor = None

    def __init__(self, num, Username, Password):
        """
        creates a new Bug and fills out all the properites that can be found on
        bugzilla
        """
        self.number = num
        print(self.number)
        try:

            self.html = Bug.getHTML(num, Username, Password)
            self.device = self.getSelectedFromID("component")
            print(self.device)
            self.host = self.getSelectedFromID("cf_host")
            print(self.host)
            self.failure = self.getSelectedFromID("cf_failtype")
            print(self.failure)
            self.os = self.getSelectedFromID("op_sys")
            print(self.os)
            #print(self.html)

            first_comment_html = BeautifulSoup(str(self.html.find(class_="bz_comment bz_first_comment")), 'html.parser').contents[0]
            #print(first_comment_html)
            try:
                for html in first_comment_html:
                    switch = re.search(r"(Switch:) (.*)\n", str(html))
                    if switch:
                        self.switch = switch.group(2)
                        print(self.switch)
            except:
                    #print("No switch found")
                self.switch = "No switch found: but check this"
            try:
                for html in first_comment_html:
                    DUTs = re.finditer(r"(Port \d:\W*)(.*)", str(html))
                    DUTstr = ""
                    for dut in DUTs:
                        if "n/a" not in dut.group(2):
                            print("DUT: ", dut.group(2))
                            DUTstr = DUTstr + str(dut.group(2)) + "\n"
                            print("DUTstr: ", DUTstr)
                            self.DUTs = DUTstr
                            #self.DUTs.append(dut.group(2))
                    #print("DUTstr: ", DUTstr)
                    #self.DUTs = DUTstr
            except:
                print("No duts found")
                self.DUTs = "None found"
            try:
                if "Maverick" in self.device:
                    for html in first_comment_html:
                        monitors = re.finditer(r"(Monitor: )(.*)", str(html))
                        for monitor in monitors:
                            if monitor.group(2) not in "n/a":
                                print("Monitor: ", monitor.group(2))
                                self.monitor = monitor.group(2)
                else:
                    self.monitors = ""
            except:
                print("No monitor found")
                self.monitors = "None found"

        except:
            print("Failed to get data")
            self.html = 'Error'
            self.device = 'Error'
            self.host = 'Error'
            self.os = 'Error'
            self.switch = 'Error'
            self.failure = 'Error'
            self.DUTs = 'Error'
            self.monitor = 'Error'
        print("self.DUTs = ", self.DUTs)

    def getHTML(num, Username, Password):
        """
        gets and returns the HTML from the bug number's bugzilla Page, needs a Username and Password
        """
        return BeautifulSoup(requests.get('http://shamrock.maxim-ic.com/bugzilla/show_bug.cgi?id=' + str(num), auth=(Username, Password)).text, 'html.parser')
        #print(self.html)

    def getSelectedFromID(self, ID):
        """
        Searches thought this bugs HTML for a certian ID and returns the
        selected item in that ID
        """
        category = BeautifulSoup(str(self.html.find(id=ID)),
                                 'html.parser').contents[0].children
        for line in category:
            if "selected" in str(line):
                #print(ent)
                selection = re.search(r"(<.*\">)(.*)(\n*.*<.*>)", str(line))
                #print(self.number)print("selection: ", selection.group(2))
                return selection.group(2)

    def csvStyle(self, write_order):
        """
        Returns a list of the bugs properties in the the requested order
        """
        list = []
        for item in write_order:
            if 'device' in item:
                list.append(self.device)
            elif 'number' in item:
                list.append(self.number)
            elif 'host' in item:
                list.append(self.host)
            elif 'failure' in item:
                list.append(self.failure)
            elif 'os' in item:
                list.append(self.os)
            elif 'switch' in item:
                list.append(self.switch)
            elif 'monitor' in item:
                list.append(self.monitor)
            elif 'DUT' in item:
                print(self.DUTs)
                list.append(self.DUTs)
            else:
                list.append("")
        #print(list)
        return list


def bugsToCSV(filename, list_of_bugs, write_order=['device', 'number', 'host', 'failure', 'switch']):
    """
    Fills out a .csv file in the same directory as the original file with the
    all the bug info in the same order as originally speciifed (or a default order)
    """
    with open(filename[:-4] + "_filled_out.csv", 'w', newline='') as file:
        writer = csv.writer(file, delimiter=',')
        writer.writerow(write_order)
        for bug in list_of_bugs:
            if bug == "":
                writer.writerow([''])
            else:
                writer.writerow(bug.csvStyle(write_order))


def getWriteOrder(filename):
    """
    Returns a list of the headers (interpreted into ['device', 'number', 'host', 'failure', 'switch'])
    in the order they appeared in the original file
    """
    with open(filename, 'r', newline='') as file:
        reader = csv.reader(file, delimiter=',')
        line = reader.__next__()
        #print("line: ",line)
        return line


def bugList(filename):
    """
    returns a list of all the bug numbers in the sheet
    """
    bugNumCol = 0
    bugs = []
    with open(filename, 'r', newline='') as file:
        reader = csv.reader(file, delimiter=',')
        header = reader.__next__()
        print(header)
        for bugNumCol in range(len(header)):
            print(header[bugNumCol])
            if "number" in header[bugNumCol]:
                break
        print(bugNumCol)
        for row in reader:
            print("row: ", row)
            try:
                bugs.append(int(row[bugNumCol])) #todo
            except:
                bugs.append(None)
    print(bugs)
    return bugs

class gui:
    """
    Class that creates and runs the GUI (basically main)
    """
    CSVFile = None
    master = None
    Username = None
    Password = None
    bug_table = {}
    def __init__(self):
        """
        Creates a new GUI interface
        """
        #set up
        self.master = tk.Tk()
        tk.Label(self.master,
                 text="Username").grid(row=0)
        tk.Label(self.master,
                 text="Password").grid(row=1)
        tk.Label(self.master,
                 text="Path").grid(row=2)


        #Text entry
        self.Username = tk.Entry(self.master)
        self.Password = tk.Entry(self.master, show="*")

        self.Username.grid(row=0, column=1)
        self.Password.grid(row=1, column=1)

        #Buttons
        tk.Button(self.master,
                  text='Quit',
                  command=self.master.quit).grid(row=3,
                                            column=0,
                                            sticky=tk.W,
                                            pady=4)
        tk.Button(self.master,
                  text='Go', command=self.main).grid(row=3,
                                                               column=1,
                                                               sticky=tk.W,
                                                               pady=4)

        tk.Button(self.master, text="File", command=self.c_open_file).grid(row=2,
                                                                 column=1,
                                                                 sticky=tk.W,
                                                                 pady=4)

        #Starts GUI
        tk.mainloop()

    def main(self) -> None:
        """
        Turns the gui's inputs into a .csv file that contains all info about the
        bugs and displays it in the same order as the original file given to the
        gui
        """
        Bugs = []
        que = queue.Queue()
        threads = []
        #print(self.CSVFile)
        write_order = getWriteOrder(self.CSVFile)
        lobn = bugList(self.CSVFile)
        for bn in lobn:
            if bn is not None:
                t = threading.Thread(target=lambda q, num, user, pwd: q.put(Bug(num, user, pwd)), args=(que, int(bn), self.Username.get(), self.Password.get()))
                threads.append(t)
                t.start()
            else:
                pass
                #Bugs.append("")
        for t in threads:
            print("joining")
            t.join()
        while not que.empty():
            bug = que.get()
            #print("bug:", bug)
            self.bug_table[str(bug.number)] = bug
        for bn in lobn:
            #print(type(bn))
            #print(self.bug_table)
            if bn != "" and bn != None:
                Bugs.append(self.bug_table[str(bn)])
            else:
                Bugs.append("")
        bugsToCSV(self.CSVFile, Bugs, write_order) #change Name: CORRECTED In bugsToCSV
        print("Program complete")

    def c_open_file(self):
        """
        Opens, stores, and returns the .csv file selected by the user in the GUI
        """
        rep = filedialog.askopenfilenames(parent=self.master, initialdir='/', initialfile='tmp',
                                          filetypes=[("CSV", "*.csv"), ("All files", "*")])
        self.CSVFile = rep[0]
        return rep[0]


#actaully runs the code lol
GUI = gui()
GUI.main()
