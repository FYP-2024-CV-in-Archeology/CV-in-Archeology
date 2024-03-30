import tkinter as tk
from tkinter import filedialog
from tkinter import scrolledtext
from pipeline import run
from threading import *

class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None

        # Bind entering and leaving events
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

    def enter(self, event=None):
        # Create the tooltip window
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20

        # This is the Toplevel widget acting as the tooltip
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tooltip_window, text=self.text, background="lightyellow", relief='solid', borderwidth=1,
                         font=("Arial", "12", "normal"))
        label.pack()

    def leave(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

def select_input_folder():
    folder_path = filedialog.askdirectory()
    if folder_path:
        input_folder_name.set(folder_path)
    else:
        input_folder_name.set("")
        
    if input_folder_name.get():
        process_btn.config(state=tk.NORMAL)

def process(input_folder, output_tif):
    # create a new window to show the progress
    log_window = tk.Toplevel(window)
    log_window.title("Job Progress")
    log_window.geometry("500x300")
    log = scrolledtext.ScrolledText(log_window, width=80, height=20)
    # add scrollbar to the log

    log.see(tk.END) 
    log.pack()
    
    # add a button to cancel the process
    done = tk.Button(log_window, text="Done", command=lambda: log_window.destroy(), state=tk.DISABLED, background="blue")
    done.pack(side=tk.RIGHT, padx=10, anchor=tk.SE)
    # disable process button
    process_btn.config(state=tk.DISABLED)

    t = Thread(target=run, args=(input_folder, dpi, output_tif, log, done, process_btn, skip_files_start.get(), skip_files_end.get(), sizes))
    t.start()

if __name__ == "__main__":
    # Create the main window
    window = tk.Tk()
    window.title("Image Processing")
    window.geometry("600x600")

    # Create a label for the selected folder
    input_folder_label = tk.Label(window, text="Select Input Folder:")
    input_folder_label.pack(pady=5, padx=10, anchor=tk.W)

    # Create a frame for the input folder
    input_frame = tk.Frame(window)
    input_frame.pack(pady=10, padx=10)

    # Create an entry for displaying the selected folder
    input_folder_name = tk.StringVar()
    input_folder_entry = tk.Entry(input_frame, textvariable=input_folder_name, width=40)
    input_folder_entry.pack(side=tk.LEFT, padx=5)

    # Create a button for selecting the input folder
    input_select_button = tk.Button(input_frame, text="Browse", command=select_input_folder)
    input_select_button.pack(side=tk.LEFT)

    input_helper_label = tk.Label(input_frame, text=" ⍰ ")
    input_helper_label.pack(side=tk.LEFT, padx=5)
    Tooltip(input_helper_label, 
            '''
            Enter the path of the folder containing the images to be processed.
            You can either type the path or click the browse button to select the folder.
            ''')

    # add a empty frame as a separator
    separator = tk.Frame(window, height=2, bd=1)
    separator.pack(fill=tk.X, padx=10, pady=5)

    # create a frame for the dpi
    dpi_frame = tk.Frame(window)
    dpi_frame.pack(pady=10, padx=10, anchor=tk.W)
    dpi = tk.IntVar()
    dpi.set(1200)
    dpi_label = tk.Label(dpi_frame, text="DPI:")
    dpi_label.pack(side=tk.LEFT, padx=5, anchor='w')
    dpi_entry = tk.Entry(dpi_frame, textvariable=dpi, width=10)
    dpi_entry.pack(side=tk.LEFT, padx=5, anchor='w')
    dpi_button = tk.Button(dpi_frame, text="Set DPI", command=lambda: [dpi.set(int(dpi_entry.get()) if dpi_entry.get() else 1200), dpi_selected.config(text=dpi.get())])
    # put the button beside the dpi entry to the right
    dpi_button.pack(side=tk.LEFT, padx=5, anchor=tk.W)

    dpi_helper_label = tk.Label(dpi_frame, text=" ⍰ ")
    dpi_helper_label.pack(side=tk.LEFT, padx=5)
    Tooltip(dpi_helper_label,
            '''
            Enter the DPI (Dots Per Inch) of the images to be processed.
            The default value is 1200.
            ''')

    # add a frame to show the selected dpi
    dpi_selected_frame = tk.Frame(window)
    dpi_selected_label = tk.Label(dpi_selected_frame, text=f"Selected DPI:", state=tk.DISABLED)
    dpi_selected_label.pack(side=tk.LEFT, padx=5, anchor='w')
    dpi_selected = tk.Label(dpi_selected_frame, text=dpi.get(), state=tk.DISABLED)
    dpi_selected.pack(side=tk.LEFT, padx=5, anchor='w')
    dpi_selected_frame.pack(pady=10, padx=10, anchor=tk.W)

    # add a empty frame as a separator
    separator = tk.Frame(window, height=2, bd=1)
    separator.pack(fill=tk.X, padx=10, pady=5)

    # create a select box for output tif files or not
    output_tif_frame = tk.Frame(window)
    output_tif_frame.pack(pady=10, padx=10, anchor=tk.W)
    output_tif = tk.IntVar()
    output_tif.set(0)
    output_tif_check = tk.Checkbutton(output_tif_frame, text="Output tif files", variable=output_tif)
    output_tif_check.pack(side=tk.LEFT, pady=5, padx=10, anchor=tk.W)

    tif_helper_label = tk.Label(output_tif_frame, text=" ⍰ ")
    tif_helper_label.pack(side=tk.LEFT, pady=5, padx=10, anchor=tk.W)
    Tooltip(tif_helper_label,
            '''
            Check this box if you want the tif outputs.
            By default, the output files are in jpg format with size 450 * 300.
            ''')

    # create a frame for the skip files
    skip_files_frame = tk.Frame(window)

    # input text box for inputting indexes of skipped files
    skip_files_start = tk.IntVar()
    skip_files_start_entry = tk.Entry(skip_files_frame, textvariable=skip_files_start, width=10, state=tk.DISABLED)
    skip_files_end = tk.IntVar()
    skip_files_end_entry = tk.Entry(skip_files_frame, textvariable=skip_files_end, width=10, state=tk.DISABLED)

    # create a select box for skipping sertain files
    skip_frame2 = tk.Frame(window)
    skip_files = tk.IntVar()
    skip_files.set(0)
    skip_files_check = tk.Checkbutton(skip_frame2, text="Specific Range", variable=skip_files, command=lambda: [skip_files_start_entry.config(state=tk.NORMAL) if skip_files.get() else skip_files_start_entry.config(state=tk.DISABLED), skip_files_end_entry.config(state=tk.NORMAL) if skip_files.get() else skip_files_end_entry.config(state=tk.DISABLED), skip_files_label.config(state=tk.NORMAL) if skip_files.get() else skip_files_label.config(state=tk.DISABLED)])
    skip_files_check.pack(side=tk.LEFT, pady=5, padx=10, anchor=tk.W)
    skip_helper_label = tk.Label(skip_frame2, text=" ⍰ ")
    skip_helper_label.pack(side=tk.LEFT, padx=5)  
    Tooltip(skip_helper_label,
            '''
            Check this box if you want to specify a range of files to be processed. Enter the start and end indexes of the files, 
            or uncheck the box to process all the files.
            ''')
    skip_frame2.pack(pady=10, padx=10, anchor=tk.W)
    # insert text
    skip_files_label = tk.Label(skip_files_frame, text="Index Range:", state=tk.DISABLED)
    skip_files_label.pack(side=tk.LEFT, padx=5, anchor='w')
    skip_files_frame.pack(pady=10, padx=10, anchor=tk.W)
    skip_files_start_entry.pack(side=tk.LEFT, padx=5, anchor='w')
    skip_files_end_entry.pack(side=tk.LEFT, padx=5, anchor='w')

    # create a select box for scaled output
    scale_frame2 = tk.Frame(window)
    scale = tk.IntVar()
    scale.set(0)
    skip_files_check = tk.Checkbutton(scale_frame2, text="Output Scalled JPEG", variable=scale, command=lambda: [scalled_size_entry.config(state=tk.NORMAL) if scale.get() else scalled_size_entry.config(state=tk.DISABLED), scalled_size_label.config(state=tk.NORMAL) if scale.get() else scalled_size_label.config(state=tk.DISABLED), scalled_filename_entry.config(state=tk.NORMAL) if scale.get() else scalled_filename_entry.config(state=tk.DISABLED), scalled_filename_label.config(state=tk.NORMAL) if scale.get() else scalled_filename_label.config(state=tk.DISABLED), scalled_size_add.config(state=tk.NORMAL) if scale.get() else scalled_size_add.config(state=tk.DISABLED), scalled_size_list.config(state=tk.NORMAL) if scale.get() else scalled_size_list.config(state=tk.DISABLED), scalled_size_list_frame.config(state=tk.NORMAL) if scale.get() else scalled_size_list_frame.config(state=tk.DISABLED), ])
    skip_files_check.pack(side=tk.LEFT, pady=5, padx=10, anchor=tk.W)

    scale_helper_label = tk.Label(scale_frame2, text=" ⍰ ")
    scale_helper_label.pack(side=tk.LEFT, padx=5)
    Tooltip(scale_helper_label,
            '''
            Check this box if you want the scaled output files.
            By default, the output files are in jpg format with size 450 * 300, which will always be generated.
            Indicate the target size of the scalled images.
            ''')

    scale_frame2.pack(pady=10, padx=10, anchor=tk.W)

    # create text box for inputting scalled filename and size
    scalled_frame = tk.Frame(window)
    scalled_size = tk.IntVar()
    # initialize the scalled size
    scalled_size.set(0)

    scalled_size_entry = tk.Entry(scalled_frame, textvariable=scalled_size, width=10, state=tk.DISABLED)
    scalled_size_label = tk.Label(scalled_frame, text="Size (100-5000):", state=tk.DISABLED)
    scalled_filename = tk.StringVar()
    scalled_filename_entry = tk.Entry(scalled_frame, textvariable=scalled_filename, width=20, state=tk.DISABLED)
    scalled_filename_label = tk.Label(scalled_frame, text="Filename:", state=tk.DISABLED)

    # create a frame and put the scale size and filename in it
    scalled_frame.pack(pady=10, padx=10, anchor=tk.W)
    scalled_size_label.pack(side=tk.LEFT, padx=5, anchor='w')
    scalled_size_entry.pack(side=tk.LEFT, padx=5, anchor='w')
    # scalled_filename_label.pack(side=tk.LEFT, padx=5, anchor='w')
    # scalled_filename_entry.pack(side=tk.LEFT, padx=5, anchor='w')

    sizes = {450}


    # create a button to add the scalled size and filename
    scalled_size_add = tk.Button(scalled_frame, text="Add", command=lambda: [sizes.add(scalled_size.get()) if scalled_size.get() >= 100 and scalled_size.get() <= 5000 else None, scalled_size_list.config(text=sizes)], state=tk.DISABLED)
    scalled_size_add.pack(side=tk.LEFT, padx=5, anchor='w')

    # show the list of sizes in a seperate frame
    scalled_size_list_frame = tk.Frame(window)
    scale_label = tk.Label(scalled_size_list_frame, text="Scalled Sizes:", state=tk.DISABLED)
    scale_label.pack(side=tk.LEFT, padx=5, anchor='w')
    scalled_size_list = tk.Label(scalled_size_list_frame, text=sizes, state=tk.DISABLED)
    scalled_size_list.pack(side=tk.LEFT, padx=5, anchor='w')
    scalled_size_list_frame.pack(pady=10, padx=10, anchor=tk.W)
    

    # Create an process button
    # multithreading
    process_btn = tk.Button(window, text="process", command=lambda: process(input_folder_name.get(), output_tif.get()), state=tk.DISABLED, background="blue")
    process_btn.pack(pady=20, side=tk.RIGHT, padx=20, anchor=tk.SE)

    # Run the GUI
    window.mainloop()