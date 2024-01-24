import tkinter as tk
from tkinter import filedialog
from pipeline import run

def select_input_folder():
    folder_path = filedialog.askdirectory()
    if folder_path:
        input_folder_name.set(folder_path)
    else:
        input_folder_name.set("")
        
    if input_folder_name.get():
        install_button.config(state=tk.NORMAL)


if __name__ == "__main__":
    # Create the main window
    window = tk.Tk()
    window.title("Image Processing")
    window.geometry("500x250")

    # Create a label for the selected folder
    input_folder_label = tk.Label(window, text="Select Input Folder:")
    input_folder_label.pack(pady=5, padx=10, anchor=tk.W)

    # Create a frame for the input folder
    input_frame = tk.Frame(window)
    input_frame.pack(pady=10, padx=10)

    # Create an entry for displaying the selected folder
    input_folder_name = tk.StringVar()
    input_folder_entry = tk.Entry(input_frame, textvariable=input_folder_name, width=40, state="readonly")
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

    # Create an process button
    install_button = tk.Button(window, text="process", command=lambda: run(input_folder_name.get(), output_tif.get()), state=tk.DISABLED)
    install_button.pack(pady=20, side=tk.RIGHT, padx=20, anchor=tk.SE)

    # Run the GUI
    window.mainloop()