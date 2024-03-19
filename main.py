import tkinter as tk
from tkinter import filedialog
from tkinter import scrolledtext
from pipeline import run
from threading import *

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

    t = Thread(target=run, args=(input_folder, output_tif, log, done, process_btn, skip_files_start.get(), skip_files_end.get(), sizes))
    t.start()

if __name__ == "__main__":
    # Create the main window
    window = tk.Tk()
    window.title("Image Processing")
    window.geometry("500x500")

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

    # add a empty frame as a separator
    separator = tk.Frame(window, height=2, bd=1)
    separator.pack(fill=tk.X, padx=10, pady=5)

    # create a select box for output tif files or not
    output_tif = tk.IntVar()
    output_tif.set(0)
    output_tif_check = tk.Checkbutton(window, text="Output tif files", variable=output_tif)
    output_tif_check.pack(pady=5, padx=10, anchor=tk.W)

    # create a frame for the skip files
    skip_files_frame = tk.Frame(window)

    # input text box for inputting indexes of skipped files
    skip_files_start = tk.IntVar()
    skip_files_start_entry = tk.Entry(skip_files_frame, textvariable=skip_files_start, width=10, state=tk.DISABLED)
    skip_files_end = tk.IntVar()
    skip_files_end_entry = tk.Entry(skip_files_frame, textvariable=skip_files_end, width=10, state=tk.DISABLED)

    # create a select box for skipping sertain files
    skip_files = tk.IntVar()
    skip_files.set(0)
    skip_files_check = tk.Checkbutton(window, text="Bones and Stones", variable=skip_files, command=lambda: [skip_files_start_entry.config(state=tk.NORMAL) if skip_files.get() else skip_files_start_entry.config(state=tk.DISABLED), skip_files_end_entry.config(state=tk.NORMAL) if skip_files.get() else skip_files_end_entry.config(state=tk.DISABLED), skip_files_label.config(state=tk.NORMAL) if skip_files.get() else skip_files_label.config(state=tk.DISABLED)])
    skip_files_check.pack(pady=5, padx=10, anchor=tk.W)
    # insert text
    skip_files_label = tk.Label(skip_files_frame, text="Index Range:", state=tk.DISABLED)
    skip_files_label.pack(side=tk.LEFT, padx=5, anchor='w')
    skip_files_frame.pack(pady=10, padx=10, anchor=tk.W)
    skip_files_start_entry.pack(side=tk.LEFT, padx=5, anchor='w')
    skip_files_end_entry.pack(side=tk.LEFT, padx=5, anchor='w')

    # create a select box for scaled output
    scale = tk.IntVar()
    scale.set(0)
    skip_files_check = tk.Checkbutton(window, text="Output Scalled JPEG", variable=scale, command=lambda: [scalled_size_entry.config(state=tk.NORMAL) if scale.get() else scalled_size_entry.config(state=tk.DISABLED), scalled_size_label.config(state=tk.NORMAL) if scale.get() else scalled_size_label.config(state=tk.DISABLED), scalled_filename_entry.config(state=tk.NORMAL) if scale.get() else scalled_filename_entry.config(state=tk.DISABLED), scalled_filename_label.config(state=tk.NORMAL) if scale.get() else scalled_filename_label.config(state=tk.DISABLED), scalled_size_add.config(state=tk.NORMAL) if scale.get() else scalled_size_add.config(state=tk.DISABLED), scalled_size_list.config(state=tk.NORMAL) if scale.get() else scalled_size_list.config(state=tk.DISABLED), scalled_size_list_frame.config(state=tk.NORMAL) if scale.get() else scalled_size_list_frame.config(state=tk.DISABLED), ])
    skip_files_check.pack(pady=5, padx=10, anchor=tk.W)

    # create text box for inputting scalled filename and size
    scalled_frame = tk.Frame(window)
    scalled_size = tk.IntVar()
    # initialize the scalled size
    scalled_size.set(100)

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

    sizes = set()

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