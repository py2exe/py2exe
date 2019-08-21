import tkinter as tk

class MainApplication(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        root.title('aTitle')

        self.lab = tk.Label(self, text="ThisIsALabel")
        self.lab.pack()

if __name__ == "__main__":
    root=tk.Tk()
    MainApplication(root).pack(side="top", fill="both", expand=True)
    root.update()