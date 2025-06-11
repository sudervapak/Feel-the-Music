# gui.py

import os  # Operating system functions
import tkinter as tk  # GUI building
from tkinter import filedialog  # File dialog for selecting files
from PIL import Image, ImageTk  # Image processing for background images
import threading  # Running tasks in parallel (non-blocking GUI)
from core import process_midi_file  # Import the function from core.py

# Get base folder
base_folder = os.path.dirname(os.path.abspath(__file__))
midi_folder = os.path.join(base_folder, "midi_files")

# Function to load available instruments (folders)
def load_instruments(folder=midi_folder):
    if not os.path.exists(folder):
        print("⚠️ midi_files folder not found!")
        exit()
    return [f for f in os.listdir(folder) if os.path.isdir(os.path.join(folder, f))]

# Function to load available songs for a selected instrument
def load_songs_from_folder(instrument, folder=midi_folder):
    path = os.path.join(folder, instrument)
    return [{"name": f, "path": os.path.join(path, f)} for f in os.listdir(path) if f.endswith(".mid")]

# Main application class for MIDI GUI
class MidiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Instrument and Song Selection")
        self.root.geometry("500x600")
        self.root.configure(bg="white")

        self.stop_flag = False  # Flag to stop playback
        self.current_song_list = []  # Current list of songs for selected instrument

        # Create GUI elements
        self.title_label = tk.Label(root, text="🎵 Select Instrument and Song", font=("Arial", 18, "bold"), bg="white")
        self.title_label.pack(pady=20)

        self.instrument_listbox = tk.Listbox(root, width=40, height=5)
        self.instrument_listbox.pack(pady=5)

        self.song_listbox = tk.Listbox(root, width=40, height=10)
        self.song_listbox.pack(pady=5)

        # Load instruments into the listbox
        self.instrument_list = load_instruments()
        for i, instrument in enumerate(self.instrument_list):
            self.instrument_listbox.insert(i, instrument)

        self.select_button = tk.Button(root, text="Select Instrument", command=self.select_instrument)
        self.select_button.pack(pady=5)

        self.play_button = tk.Button(root, text="▶️ Start Playback", font=("Arial", 14), bg="lightgreen", command=self.start_playback)
        self.play_button.pack(pady=5)

        self.stop_button = tk.Button(root, text="⏹ Stop Playback", font=("Arial", 14), bg="lightcoral", command=self.stop_playback)
        self.stop_button.pack(pady=5)

        self.result_label = tk.Label(root, text="", wraplength=440, justify="left", bg="white", font=("Arial", 10))
        self.result_label.pack(pady=10)

    def select_instrument(self):
        idx = self.instrument_listbox.curselection()
        if not idx:
            return
        selected = self.instrument_list[idx[0]]
        self.current_song_list = load_songs_from_folder(selected)

        self.song_listbox.delete(0, tk.END)
        for i, song in enumerate(self.current_song_list):
            self.song_listbox.insert(i, song["name"])

    def start_playback(self):
        idx = self.song_listbox.curselection()
        if not idx:
            return
        self.stop_flag = False
        song_info = self.current_song_list[idx[0]]
        t = threading.Thread(target=process_midi_file, args=(song_info["path"], self.get_stop_flag))
        t.start()

    def stop_playback(self):
        self.stop_flag = True
        print("🛑 Playback stopped.")

    def get_stop_flag(self):
        return self.stop_flag

# Start screen class for initial interface
class StartScreen(tk.Toplevel):
    def __init__(self, master, on_start):
        super().__init__(master)
        self.on_start = on_start
        self.title("Feel the Music")
        self.geometry("400x600")
        self.configure(bg="white")

        try:
            image_path = os.path.join(base_folder, "photo.png")
            self.image = Image.open(image_path)
            self.image = self.image.resize((400, 600))
            self.photo = ImageTk.PhotoImage(self.image)
            self.image_label = tk.Label(self, image=self.photo, bg="white")
            self.image_label.pack()
        except Exception as e:
            print(f"⚠️ Image could not be loaded: {e}")

        self.start_button = tk.Button(self, text="Start to Feel!", font=("Arial", 18, "italic"),
                                      bg="white", fg="black", padx=10, pady=5,
                                      borderwidth=0, relief="ridge", command=self.start_app)
        self.start_button.place(x=116, y=422, width=160, height=40)

    def start_app(self):
        self.destroy()
        launch_midi_app()

# Launch the main MIDI app
def launch_midi_app():
    new_root = tk.Tk()
    MidiApp(new_root)
    new_root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    StartScreen(root, on_start=None)
    root.mainloop()
