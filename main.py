import tkinter as tk
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText
from multiprocessing import Pool, Manager
import time
import random
from threading import Thread
from pipeline_parallel_v2 import init_worker, read_path, run

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

def worker_pool_tasks(root, dpi_value, tif, start, end, sizes, overwrite_files, num_processes):
    """Function to submit tasks to the pool with parameters and handle results."""
    t = time.time()
    with Pool(initializer=init_worker, initargs=(queue,), processes=num_processes) as pool:
        pathes = read_path(root, start, end)
        tasks = [(path, dpi_value, tif, sizes, overwrite_files) for path in pathes]
        results = pool.starmap_async(run, tasks)
        results.wait()  # Wait for all tasks to complete
        queue.put(None)  # Signal the GUI to stop updating
        queue.put(f"Done! Time taken: {time.time() - t:.2f} seconds")

def update_gui(shared_queue, text_widget):
    try:
        while True:
            message = shared_queue.get_nowait()
            if message is None:
                time = shared_queue.get()
                text_widget.insert(tk.END, time + '\n')
                text_widget.see(tk.END)
                break
            text_widget.insert(tk.END, message + '\n')
            text_widget.see(tk.END)
    except:
        pass
    text_widget.after(100, update_gui, shared_queue, text_widget)

def select_input_folder():
    folder_path = filedialog.askdirectory()
    if folder_path:
        input_folder_name.set(folder_path)
    else:
        input_folder_name.set("")
        
    if input_folder_name.get():
        process_btn.config(state=tk.NORMAL)

def start_tasks(sizes):
    root = input_folder_entry.get()  # Get parameter from the entry widget
    dpi_value = dpi.get()  # Get the DPI value
    tif = output_tif.get()  # Get the output tif value
    start = files_start.get()  # Get the start index
    end = files_end.get()  # Get the end index
    overwrite_files = overwrite.get()  # Get the overwrite value
    processes = num_processes.get()  # Get the number of processes

    # show the log window
    log_window.deiconify()

    # Start the background tasks in a thread
    Thread(target=worker_pool_tasks, args=(root, dpi_value, tif, start, end, sizes, overwrite_files, processes)).start()

if __name__ == "__main__":
    manager = Manager()
    queue = manager.Queue()

    window = tk.Tk()
    window.title("Image Processing")

    # Create a label for the selected folder
    input_folder_label = tk.Label(window, text="Select Input Folder:")
    input_folder_label.pack(pady=5, padx=10, anchor=tk.W)

    # Create a frame for the input folder
    input_frame = tk.Frame(window)
    input_frame.pack(pady=10, padx=10, anchor=tk.W)

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
            Check this box if you want the tif outputs for the corrected images.
            The generated tif files will be scaled to the DPI value entered.
            ''')
    
    # create a frame for checking whether overwrite the existing files
    overwrite_frame = tk.Frame(window)
    overwrite_frame.pack(pady=10, padx=10, anchor=tk.W)
    overwrite = tk.IntVar()
    overwrite.set(0)
    overwrite_check = tk.Checkbutton(overwrite_frame, text="Overwrite existing files", variable=overwrite)
    overwrite_check.pack(side=tk.LEFT, pady=5, padx=10, anchor=tk.W)
    # helper label for the overwrite check box
    overwrite_helper_label = tk.Label(overwrite_frame, text=" ⍰ ")
    overwrite_helper_label.pack(side=tk.LEFT, pady=5, padx=10, anchor=tk.W)
    Tooltip(overwrite_helper_label,
            '''
            Check this box if you want to overwrite the existing files.
            If unchecked, the program will not overwrite any existing files.
            ''')

    # create a frame for selecting files indexes to be processed
    files_frame = tk.Frame(window)

    # input text box for inputting indexes of files
    files_start = tk.IntVar()
    files_start_entry = tk.Entry(files_frame, textvariable=files_start, width=10, state=tk.DISABLED)
    files_end = tk.IntVar()
    files_end_entry = tk.Entry(files_frame, textvariable=files_end, width=10, state=tk.DISABLED)

    # create a select box for choosing sertain files
    frame2 = tk.Frame(window)
    files = tk.IntVar()
    files.set(0)
    files_check = tk.Checkbutton(frame2, text="Specific Range", variable=files, command=lambda: [files_start_entry.config(state=tk.NORMAL) if files.get() else files_start_entry.config(state=tk.DISABLED), files_end_entry.config(state=tk.NORMAL) if files.get() else files_end_entry.config(state=tk.DISABLED), files_label.config(state=tk.NORMAL) if files.get() else files_label.config(state=tk.DISABLED)])
    files_check.pack(side=tk.LEFT, pady=5, padx=10, anchor=tk.W)
    helper_label = tk.Label(frame2, text=" ⍰ ")
    helper_label.pack(side=tk.LEFT, padx=5)  
    Tooltip(helper_label,
            '''
            Check this box if you want to specify a range of files to be processed. Enter the start and end indexes of the files, 
            or uncheck the box to process all the files.
            ''')
    frame2.pack(pady=10, padx=10, anchor=tk.W)
    # insert text
    files_label = tk.Label(files_frame, text="Index Range:", state=tk.DISABLED)
    files_label.pack(side=tk.LEFT, padx=5, anchor='w')
    files_frame.pack(pady=10, padx=10, anchor=tk.W)
    files_start_entry.pack(side=tk.LEFT, padx=5, anchor='w')
    files_end_entry.pack(side=tk.LEFT, padx=5, anchor='w')


    scale = tk.IntVar()
    scale.set(0)
    sizes = {450}

    # show the list of sizes in a seperate frame
    scalled_size_list_frame = tk.Frame(window)
    scale_label = tk.Label(scalled_size_list_frame, text="Scalled Sizes:")
    scale_label.pack(side=tk.LEFT, padx=5, anchor='w')
    scalled_size_list = tk.Label(scalled_size_list_frame, text=sizes)
    scalled_size_list.pack(side=tk.LEFT, padx=5, anchor='w')
    scalled_size_list_frame.pack(pady=10, padx=10, anchor=tk.W)

    # create text box for inputting scalled filename and size
    scalled_frame = tk.Frame(window)
    scalled_size = tk.IntVar()
    # initialize the scalled size
    scalled_size.set(0)

    scalled_size_entry = tk.Entry(scalled_frame, textvariable=scalled_size, width=10)
    scalled_filename = tk.StringVar()
    scalled_filename_entry = tk.Entry(scalled_frame, textvariable=scalled_filename, width=20)
    scalled_filename_label = tk.Label(scalled_frame, text="Filename:")

    # create a frame and put the scale size and filename in it
    scalled_frame.pack(pady=10, padx=10, anchor=tk.W)
    scalled_size_entry.pack(side=tk.LEFT, padx=5, anchor='w')

    # create a button to add the scalled size and filename
    scalled_size_add = tk.Button(scalled_frame, text="Add", command=lambda: [sizes.add(scalled_size.get()) if scalled_size.get() >= 100 and scalled_size.get() <= 5000 else None, scalled_size_list.config(text=sizes)])
    scalled_size_add.pack(side=tk.LEFT, padx=5, anchor='w')

    scale_helper_label = tk.Label(scalled_frame, text=" ⍰ ")
    scale_helper_label.pack(side=tk.LEFT, padx=5)
    Tooltip(scale_helper_label,
            '''
            Add any specific sizes for the corrected jpgs.
            By default, one jpg with size 450 * 300 will always be generated.
            Newly added size should be between 100-5000.
            ''')
    
    # let the users choose the number of processes
    num_processes_frame = tk.Frame(window)
    num_processes_frame.pack(pady=10, padx=10, anchor=tk.W)
    num_processes_label = tk.Label(num_processes_frame, text="Number of Processes:")
    num_processes_label.pack(side=tk.LEFT, padx=5, anchor='w')
    num_processes = tk.IntVar()
    num_processes.set(2)
    num_processes_entry = tk.Entry(num_processes_frame, textvariable=num_processes, width=10)
    num_processes_entry.pack(side=tk.LEFT, padx=5, anchor='w')
    num_processes_helper_label = tk.Label(num_processes_frame, text=" ⍰ ")
    num_processes_helper_label.pack(side=tk.LEFT, padx=5)
    Tooltip(num_processes_helper_label,
            '''
            Enter the number of processes to be used for parallel processing.
            ''')

    process_btn = tk.Button(window, text="Start Tasks", command=lambda: start_tasks(sizes))
    process_btn.pack(pady=20, side=tk.RIGHT, padx=20, anchor=tk.SE)

    # create a new window to show the logs
    log_window = tk.Toplevel(window)
    log_window.title("Job Progress")
    log_window.geometry("600x400")
    # hide the log window
    log_window.withdraw()

    log_display = ScrolledText(log_window, height=20, state='normal')
    log_display.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)    

    window.after(100, update_gui, queue, log_display)

    window.mainloop()
