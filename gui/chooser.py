import Tkinter as tk

root = tk.Tk()


class OptionChooser(tk.Frame):
    __bgs = ['white', 'gray']

    def __init__(self, *args, **kwargs):
        def __popKwarg(name, default):
            if name in kwargs:
                value = kwargs[name]
                del kwargs[name]
            else:
                value = default
            return value

        self.__optionWidth = __popKwarg('optionWidth', 0)

        tk.Frame.__init__(self, *args, **kwargs)
        self.__counter = 0
        self.__images = []
        self.__labels = []
        self.__texts = []
        self.__selectedIndex = None
        self.rowconfigure(0, weight=1)

    def getSelectedIndex(self):
        return self.__selectedIndex

    def selectIndex(self, index):
        """ Select a new index. """
        if index < 0 or index >= len(self.__labels):
            raise Exception("Invalid index %s" % index)
        self.__select(index)

    def getSelectedText(self):
        return self.__texts[self.getSelectedIndex()]

    def __select(self, index):
        i = self.__selectedIndex  # short notation

        if index != i:
            if i is not None:
                self.__labels[i].config(relief='flat')
            self.__labels[index].config(relief='solid')
            self.__selectedIndex = index
            if self.__onSelectionChangedCallback:
                self.__onSelectionChangedCallback(self)

    def addOption(self, text, imagePath=None):
        """ Add a new option to the OptionChooser. """
        c = self.__counter
        img = tk.PhotoImage(file=imagePath) if imagePath else None
        label = tk.Label(self, text=text, image=img, compound=tk.TOP,
                         borderwidth=2, relief='flat',
                         font="Verdana 14")
        label.grid(row=0, column=c, padx=10, pady=5, sticky='news')
        self.columnconfigure(c, weight=1)
        self.columnconfigure(c, minsize=self.__optionWidth)
        label.bind("<Button-1>", lambda e: self.__select(c))
        self.__images.append(img)
        self.__labels.append(label)
        self.__texts.append(text)
        self.__counter = c + 1

    def onSelectionChanged(self, callbackFunc):
        """ Register a callback function to be called when selection changes.
        """
        self.__onSelectionChangedCallback = callbackFunc


def onSelection(chooser):
    print "Selection changed on %s" % chooser
    print "     index: ", chooser.getSelectedIndex()
    print "      text: ", chooser.getSelectedText()

f1 = tk.Frame(root, bg='white')
f1 = OptionChooser(root, bg='white', optionWidth=200)
f1.onSelectionChanged(onSelection)

f1.grid(row=0, column=0, padx=10, pady=10)

f1.addOption('Krios 1', "titan_small.gif")
f1.addOption('Talos', "talos_small.gif")
f1.selectIndex(1)

f2 = OptionChooser(root, bg='white', optionWidth=200)
f2.onSelectionChanged(onSelection)
f2.grid(row=1, column=0, padx=10, pady=20)
f2.addOption('K2')
f2.addOption('Falcon 3')

# explanation = "Krios 1"



# w2 = tk.Label(f,
#               justify=tk.LEFT,
#               padx = 10,
#               bd=2,
#               image=logo,
#               bg=bgs[0],
#               compound=tk.TOP,
#               text=explanation,
#               font = "Verdana 14")
#
# def changeBg(e):
#     """ Change background of w2 """
#     w2.bgIndex = 1 - w2.bgIndex
#     w2.config(bg=bgs[w2.bgIndex])
#
#
# w2.grid(row=0, column=0)
# w2.bind("<Button-1>", changeBg)
# w2.bgIndex = 0

root.mainloop()
