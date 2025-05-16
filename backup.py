import json
import tkinter as tk
from tkinter import filedialog, messagebox
import traceback
from PIL import Image, ImageTk
from colormath.color_conversions import convert_color
from colormath.color_objects import CMYKColor, sRGBColor
import cv2
import numpy as np
import os
from tkinter import messagebox
import datetime

class PaintMixerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Paint Mixer")
        self.root.geometry("2000x900")
        self.image = None

        self.trays = []

        self.main_frame = tk.Frame(root)
        self.main_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

        self.left_frame = tk.Frame(self.main_frame, relief="solid", bd=2, width=800, height=600)  
        self.left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ns")
        self.add_bordered_label(self.left_frame, "Left Frame (Color Previews)")
        self.left_frame.grid_propagate(False)

        self.left_canvas = tk.Canvas(self.main_frame, width=800, height=600)
        self.left_scrollbar = tk.Scrollbar(self.main_frame, orient="vertical", command=self.left_canvas.yview)
        self.scrollable_left_frame = tk.Frame(self.left_canvas)

        self.scrollable_left_frame.bind(
            "<Configure>",
            lambda e: self.left_canvas.configure(
                scrollregion=self.left_canvas.bbox("all")
            )
        )

        self.left_canvas.create_window((0, 0), window=self.scrollable_left_frame, anchor="nw")
        self.left_canvas.configure(yscrollcommand=self.left_scrollbar.set)

        self.left_canvas.grid(row=0, column=0, sticky="nsew")
        self.left_scrollbar.grid(row=0, column=1, sticky="ns")

        self.tray_count = 0
        self.tray_container = tk.Frame(self.left_frame)
        self.tray_container.grid(row=2, column=0, pady=10, sticky="nsew")
        self.tray_container.columnconfigure(0, weight=1)
        self.tray_container.rowconfigure(999, weight=1)

        self.right_frame = tk.Frame(self.main_frame, relief="solid", bd=2)
        self.right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_columnconfigure(1, weight=0)  
        self.add_bordered_label(self.right_frame, "Right Frame (Image Preview)")

        self.main_frame.grid_columnconfigure(0, weight=1)  
        self.main_frame.grid_columnconfigure(1, weight=2) 
        self.main_frame.grid_rowconfigure(0, weight=1)

        self.color_preview_frame = tk.Frame(self.scrollable_left_frame)
        self.color_preview_frame.pack(padx=5, pady=5, fill="x")
        self.add_bordered_label(self.color_preview_frame, "Color Preview Frame")

        self.add_tray_button = tk.Button(root, text="Add Tray", command=self.create_color_previews)
        self.add_tray_button.grid(row=0, column=0, padx=5, pady=5)

        self.load_button = tk.Button(root, text="Load Image", command=self.load_image)
        self.load_button.grid(row=0, column=1, padx=5, pady=5)

        self.tray_container = tk.Frame(self.scrollable_left_frame)
        self.tray_container.pack(pady=10, fill="x")
        self.tray_container.columnconfigure(0, weight=1)
        self.tray_container.rowconfigure(999, weight=1)

        self.ml_buttons = []
        self.cmyk_labels = []
        self.selected_colors = [] 
        self.edit_buttons = [] 

        self.canvas = tk.Canvas(self.right_frame, width=500, height=500, bg="gray", relief="solid", bd=2)
        self.canvas.grid(row=0, column=0, padx=10, pady=10, sticky="n")
        self.canvas.bind("<Motion>", self.on_mouse_hover)
        self.canvas.bind("<B1-Motion>", self.on_mouse_hover)

        self.canvas.bind("<Button-1>", self.on_canvas_click)

        self.add_bordered_label(self.canvas, "Image Display Canvas")

        self.zoom_canvas = tk.Canvas(self.right_frame, width=150, height=150, bg="white", relief="solid", bd=2)
        self.zoom_canvas.grid(row=0, column=1, padx=10, pady=10, sticky="n")
        self.add_bordered_label(self.zoom_canvas, "Zoom Preview Canvas")

        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        self.left_canvas.bind_all("<MouseWheel>", self.on_mousewheel)

    def on_mousewheel(self, event):
        self.left_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def add_bordered_label(self, widget, label_text):
        def place_label():
            x, y = widget.winfo_rootx(), widget.winfo_rooty() - 20
            label = tk.Label(self.root, text=label_text, font=("Arial", 8), fg="black", bg="lightgray")
            label.place(x=x, y=y)
        
        self.root.after(100, place_label) 

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if not file_path:
            return

        self.image_path = file_path
        self.image = cv2.imread(file_path)
        self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        self.display_image()

    def display_image(self):
        if self.image is None:
            return

        self.resized_image = cv2.resize(self.image, (500, 500))
        self.tk_image = ImageTk.PhotoImage(Image.fromarray(self.resized_image))
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

    def on_mouse_hover(self, event):
        if self.image is None:
            return

        x, y = event.x, event.y
        if 0 <= x < 500 and 0 <= y < 500:
            color = self.resized_image[y, x]
            self.show_zoom(x, y, color)

    def on_canvas_click(self, event):
        try:
            x, y = event.x, event.y  
            print(f"🟢 DEBUG: User clicked at ({x}, {y})")

            if self.image is None:
                messagebox.showwarning("Warning", "Please load an image first.")
                return

            try:
                rgb_color = self.get_color_from_image(x, y)
                print(f"🟢 DEBUG: Extracted color at ({x},{y}) = {rgb_color}")
            except Exception as color_error:
                messagebox.showerror("Color Extraction Error", str(color_error))
                return

            self.add_color_to_tray(rgb_color)

        except Exception as e:
            messagebox.showerror("Unexpected Error", str(e))

    def add_color_to_tray(self, rgb_color):
        try:
            print(f"🟢 DEBUG: Entering add_color_to_tray with color: {rgb_color}")
            print(f"🟢 DEBUG: Color type: {type(rgb_color)}")
            
            if not isinstance(rgb_color, tuple) or len(rgb_color) != 3:
                raise ValueError(f"Invalid color format: {rgb_color}")

            rgb_color = tuple(max(0, min(255, int(c))) for c in rgb_color)
            print(f"🟢 DEBUG: Normalized Color: {rgb_color}")
            rgb_color = self.adjust_color_brightness(rgb_color)

            hex_color = "#{:02x}{:02x}{:02x}".format(*rgb_color)
            print(f"🟢 DEBUG: RGB Color: {rgb_color}")
            print(f"🟢 DEBUG: Hex Color: {hex_color}")

            active_trays = [tray for tray in self.trays if isinstance(tray, (tk.Frame, tuple))]
            
            if not active_trays:
                messagebox.showwarning("Warning", "No active trays found. Add a tray first.")
                return

            uppermost_tray = active_trays[-1]
            print(f"🟢 DEBUG: Uppermost Tray Type: {type(uppermost_tray)}")
            print(f"🟢 DEBUG: Uppermost Tray Contents: {uppermost_tray}")

            try:
                if isinstance(uppermost_tray, tk.Frame):
                    color_previews = []
                    cmyk_labels = []
                    
                    for child in uppermost_tray.winfo_children():
                        try:
                            if (isinstance(child, tk.Canvas) and 
                                child.winfo_exists() and 
                                child.cget('bg') in ['white', 'White', '#FFFFFF']):
                                color_previews.append(child)
                            elif isinstance(child, tk.Label):
                                cmyk_labels.append(child)
                        except tk.TclError:
                            print(f"🔴 DEBUG: Skipping destroyed widget: {child}")
                    
                    if not color_previews or not cmyk_labels:
                        raise ValueError("Could not find color previews or CMYK labels in the Frame")
                
                elif isinstance(uppermost_tray, (list, tuple)) and len(uppermost_tray) >= 3:
                    color_previews = uppermost_tray[0]
                    cmyk_labels = uppermost_tray[2]
                    
                    if not isinstance(color_previews, list):
                        raise ValueError("Color previews must be a list")
                    if not isinstance(cmyk_labels, list):
                        raise ValueError("CMYK labels must be a list")
                else:
                    raise ValueError(f"Unsupported tray type or insufficient elements. Found {type(uppermost_tray)}")

            except (ValueError, TypeError) as unpack_error:
                print(f"🔴 ERROR: Could not unpack tray details: {unpack_error}")
                messagebox.showerror("Tray Error", f"Invalid tray configuration: {unpack_error}")
                return

            empty_slots = []
            for i, preview in enumerate(color_previews):
                try:
                    if preview.winfo_exists() and preview.cget('bg') in ['white', 'White', '#FFFFFF']:
                        empty_slots.append(i)
                except tk.TclError:
                    print(f"🔴 DEBUG: Skipping destroyed preview at index {i}")
            
            if not empty_slots:
                messagebox.showwarning("Warning", "Tray is already full!")
                return

            slot_index = empty_slots[0]
            color_preview = color_previews[slot_index]

            try:
                color_preview.config(bg=hex_color)
            except tk.TclError:
                print(f"🔴 ERROR: Could not set color for preview at index {slot_index}")
                return
            
            while len(self.selected_colors) <= slot_index:
                self.selected_colors.append(None)
            self.selected_colors[slot_index] = rgb_color

            if slot_index < len(cmyk_labels):
                try:
                    cmyk_values = self.calculate_cmyk(rgb_color)
                    label_text = "C: {:.2f} M: {:.2f} Y: {:.2f} K: {:.2f}".format(
                        cmyk_values['Cyan'] * 100, 
                        cmyk_values['Magenta'] * 100, 
                        cmyk_values['Yellow'] * 100, 
                        cmyk_values['Black'] * 100
                    )
                    
                    label_widget = cmyk_labels[slot_index]
                    if isinstance(label_widget, list):
                        label_widget = label_widget[0]
                    
                    label_widget.config(text=label_text)
                except Exception as cmyk_error:
                    print(f"🔴 ERROR: CMYK label update failed: {cmyk_error}")

            self.update_color_previews()

            print(f"🟢 DEBUG: Color added to tray at index {slot_index}")
            print(f"🟢 DEBUG: Updated selected colors: {self.selected_colors}")

        except Exception as e:
            error_message = f"Color Tray Error: {str(e)}"
            print(f"🔴 ERROR in add_color_to_tray: {error_message}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Color Tray Error", error_message)

    def show_zoom(self, x, y, color):
        if self.image is None:
            return

        zoomed_region = np.full((150, 150, 3), color, dtype=np.uint8)

        zoomed_image = ImageTk.PhotoImage(Image.fromarray(zoomed_region))
        self.zoom_canvas.create_image(0, 0, anchor=tk.NW, image=zoomed_image)
        self.zoom_canvas.image = zoomed_image  

    def get_color_from_image(self, x, y):
        try:
            original_height, original_width = self.image.shape[:2]
            resized_height, resized_width = 500, 500

            scaled_x = int(x * (original_width / resized_width))
            scaled_y = int(y * (original_height / resized_height))

            if (scaled_x < 0 or scaled_x >= original_width or 
                scaled_y < 0 or scaled_y >= original_height):
                raise ValueError(f"Coordinates out of bounds: ({scaled_x}, {scaled_y})")

            rgb_color = tuple(map(int, self.image[scaled_y, scaled_x]))

            print(f"🟢 DEBUG: Raw Color Extraction:")
            print(f"   Original Coords: ({x}, {y})")
            print(f"   Scaled Coords: ({scaled_x}, {scaled_y})")
            print(f"   Extracted Color: {rgb_color}")

            return rgb_color

            if not hasattr(self, 'image') or self.image is None:
                print(f"🔴 ERROR: No image loaded")
                return (255, 255, 255)

            height, width = self.image.shape[:2]
            
            if x < 0 or x >= width or y < 0 or y >= height:
                print(f"🔴 Error: Click coordinates ({x}, {y}) out of bounds. Image size: {width}x{height}")
                return (255, 255, 255)

            raw_color = self.image[y, x]
            
            print(f"🟢 DEBUG: Raw Color Type: {type(raw_color)}")
            print(f"🟢 DEBUG: Raw Color Value: {raw_color}")
            
            if isinstance(raw_color, np.ndarray):
                if raw_color.ndim == 1:
                    rgb_color = tuple(map(int, raw_color[:3]))
                else:
                    rgb_color = tuple(map(int, raw_color))
            else:
                rgb_color = tuple(map(int, [raw_color]))
            
            rgb_color = tuple(max(0, min(255, int(c))) for c in rgb_color[:3])
            
            print(f"🟢 DEBUG: Extracted color at ({x},{y}) = {rgb_color}")
            print(f"🟢 DEBUG: Image Shape: {self.image.shape}")
            print(f"🟢 DEBUG: Image Data Type: {self.image.dtype}")
            
            return rgb_color

        except Exception as e:
            print(f"🔴 ERROR in get_color_from_image: {str(e)}")
            import traceback
            traceback.print_exc()
            return (255, 255, 255)  

    def adjust_color_brightness(self, rgb_color, min_brightness=50):
        print(f"🟢 DEBUG: Original Color: {rgb_color}")
        print(f"🟢 DEBUG: Original Brightness: {sum(rgb_color) / 3}")
        
        return rgb_color

    def show_color_info(self, color):
        """Display color information when hovering over a color preview."""
        try:
            self.color_info_window = tk.Toplevel(self.root)
            self.color_info_window.wm_overrideredirect(True)
            self.color_info_window.wm_geometry(f"+{self.root.winfo_pointerx()}+{self.root.winfo_pointery() + 20}")
            
            r, g, b = color
            hex_color = '#{:02x}{:02x}{:02x}'.format(r, g, b)
            
            brightness = round((r * 299 + g * 587 + b * 114) / 1000, 2)
            
            tk.Label(self.color_info_window, text=f"RGB: {r}, {g}, {b}", font=("Arial", 10)).pack()
            tk.Label(self.color_info_window, text=f"HEX: {hex_color}", font=("Arial", 10)).pack()
            tk.Label(self.color_info_window, text=f"Brightness: {brightness}", font=("Arial", 10)).pack()
            
            preview_label = tk.Label(
                self.color_info_window, 
                width=10, 
                height=3, 
                bg=hex_color
            )
            preview_label.pack(pady=5)
        
        except Exception as e:
            print(f"🔴 DEBUG: Error in show_color_info: {e}")

    def load_batch_colors(self, batch_colors):
        """Load colors from a selected batch into the current tray."""
        try:
            self.selected_colors.clear()
            
            for color in batch_colors:
                # Ensure we don't exceed 6 colors
                if len(self.selected_colors) < 6:
                    self.selected_colors.append((color[0], color[1], color[2]))
            
            self.update_color_previews()
            
            print(f"🟢 DEBUG: Loaded {len(batch_colors)} colors into current tray")
        
        except Exception as e:
            print(f"🔴 DEBUG: Error loading batch colors: {e}")
    
    def remove_batch(self, json_file):
        """Remove a specific color batch file."""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(script_dir, json_file)
            
            confirm = messagebox.askyesno("Remove Batch", 
                f"Are you sure you want to remove the batch {json_file}?")
            
            if confirm:
                os.remove(file_path)
                self.display_recent_batch()
                
                print(f"🟢 DEBUG: Removed batch file {json_file}")
        
        except Exception as e:
            print(f"🔴 DEBUG: Error removing batch: {e}")
            messagebox.showerror("Error", f"Could not remove batch: {str(e)}")

    def hide_color_info(self, event=None):
        """Hide color information window."""
        try:
            if hasattr(self, 'color_info_window'):
                self.color_info_window.destroy()
        except Exception as e:
            print(f"🔴 DEBUG: Error in hide_color_info: {e}")

    def display_recent_batch(self, colors=None):
            """Display all color batches in a scrollable frame, with latest on top."""
            try:
                if hasattr(self, "recent_batch_frame"):
                    self.recent_batch_frame.destroy()
                
                self.recent_batch_frame = tk.Frame(self.right_frame, relief="solid", bd=2)
                self.recent_batch_frame.grid(row=1, column=0, columnspan=2, pady=10, sticky="nsew")
                
                canvas = tk.Canvas(self.recent_batch_frame)
                scrollbar = tk.Scrollbar(self.recent_batch_frame, orient="vertical", command=canvas.yview)
                scrollable_frame = tk.Frame(canvas)

                scrollable_frame.bind(
                    "<Configure>",
                    lambda e: canvas.configure(
                        scrollregion=canvas.bbox("all")
                    )
                )

                canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
                canvas.configure(yscrollcommand=scrollbar.set)

                tk.Label(scrollable_frame, text="COLOR BATCHES", font=("Arial", 12, "bold")).pack(pady=10)

                script_dir = os.path.dirname(os.path.abspath(__file__))
                json_files = [f for f in os.listdir(script_dir) if f.startswith('color_batch_') and f.endswith('.json')]
                
                sorted_files = sorted(json_files, key=lambda x: x.split('_')[2].split('.')[0], reverse=True)
                
                for json_file in sorted_files:
                    file_path = os.path.join(script_dir, json_file)
                    try:
                        with open(file_path, 'r') as f:
                            batch_data = json.load(f)
                            batch_colors = [(color['rgb']['r'], color['rgb']['g'], color['rgb']['b']) for color in batch_data.get('colors', [])]
                            
                            batch_frame = tk.Frame(scrollable_frame)
                            batch_frame.pack(pady=5, fill="x")
                            
                            controls_frame = tk.Frame(batch_frame)
                            controls_frame.pack(fill="x")
                            
                            tk.Label(controls_frame, text=f"Batch: {json_file}", font=("Arial", 10)).pack(side="left", padx=5)
                            
                            select_btn = tk.Button(
                                controls_frame, 
                                text="Select", 
                                command=lambda jf=json_file, bc=batch_colors: self.load_batch_colors(bc)
                            )
                            select_btn.pack(side="right", padx=5)
                            
                            remove_btn = tk.Button(
                                controls_frame, 
                                text="Remove", 
                                command=lambda jf=json_file: self.remove_batch(jf)
                            )
                            remove_btn.pack(side="right", padx=5)
                            
                            color_preview_frame = tk.Frame(batch_frame)
                            color_preview_frame.pack(fill="x")
                            
                            for row in range(2):
                                row_frame = tk.Frame(color_preview_frame)
                                row_frame.pack(fill="x")
                                
                                for col in range(6):
                                    index = row * 6 + col
                                    if index < len(batch_colors):
                                        color = batch_colors[index]
                                        color_preview = tk.Label(
                                            row_frame, 
                                            width=5, 
                                            height=2, 
                                            bg='#{:02x}{:02x}{:02x}'.format(*color)
                                        )
                                        color_preview.pack(side="left", padx=2, pady=2)
                                        
                                        color_preview.bind('<Enter>', lambda e, c=color: self.show_color_info(c))
                                        color_preview.bind('<Leave>', self.hide_color_info)
                    
                    except Exception as e:
                        print(f"🔴 DEBUG: Error reading {json_file}: {e}")
                
                if not sorted_files and colors:
                    batch_frame = tk.Frame(scrollable_frame)
                    batch_frame.pack(pady=5, fill="x")
                    
                    tk.Label(batch_frame, text="Current Batch", font=("Arial", 10)).pack()
                    
                    color_preview_frame = tk.Frame(batch_frame)
                    color_preview_frame.pack(fill="x")
                    
                    for row in range(2):
                        row_frame = tk.Frame(color_preview_frame)
                        row_frame.pack(fill="x")
                        
                        for col in range(6):
                            index = row * 6 + col
                            if index < len(colors):
                                color = colors[index]
                                color_preview = tk.Label(
                                    row_frame, 
                                    width=5, 
                                    height=2, 
                                    bg='#{:02x}{:02x}{:02x}'.format(*color)
                                )
                                color_preview.pack(side="left", padx=2, pady=2)
                
                canvas.pack(side="left", fill="both", expand=True)
                scrollbar.pack(side="right", fill="y")
                
                print(f"🟢 DEBUG: Displayed color batches from {len(sorted_files)} files")
            
            except Exception as e:
                print(f"🔴 DEBUG: Error in display_recent_batch: {e}")
                traceback.print_exc()

    def update_table(self, cmyk_values):
        for idx, header in enumerate(["Cyan", "Magenta", "Yellow", "Black"]):
            proportion = cmyk_values[header]
            self.values[idx].config(text=f"{proportion:.2%}")

    def show_buttons(self, event, idx):
        if idx < len(self.ml_buttons):
            for btn in self.ml_buttons[idx]:
                btn.pack() 

    def hide_buttons(self, event, idx):
        if idx < len(self.selected_colors):  
            return  
        
        self.root.after(200, lambda: self._delayed_hide_buttons(idx))

    def _delayed_hide_buttons(self, idx):
        widget_under_cursor = self.root.winfo_containing(self.root.winfo_pointerx(), self.root.winfo_pointery())

        relevant_widgets = [self.color_previews[idx], self.edit_buttons[idx]] + list(self.ml_buttons[idx])

        if widget_under_cursor in relevant_widgets:
            return  

        if idx < len(self.ml_buttons):
            for btn in self.ml_buttons[idx]:
                btn.pack_forget()

        if idx < len(self.edit_buttons):
            self.edit_buttons[idx].pack_forget()

    def create_color_previews(self):
        tray_frame = tk.Frame(self.tray_container, relief="solid", bd=2)
        tray_frame.grid(row=self.tray_count, column=0, sticky="ew", padx=5, pady=5)  
        tk.Label(tray_frame, text=f"Tray {self.tray_count + 1}", font=("Arial", 12)).pack(pady=5)
        
        self.trays.append(tray_frame)

        self.color_previews = [] 
        self.cmyk_labels = []
        self.edit_buttons = []  
        self.ml_buttons = []
        self.selected_ml_buttons = [None] * 6

        self.edit_icon = ImageTk.PhotoImage(Image.open("edit.png").resize((20, 20)))  # Resize if needed

        for i in range(6):
            color_frame = tk.Frame(tray_frame)
            color_frame.pack(side="left", padx=5, pady=5)

            color_canvas = tk.Canvas(color_frame, 
                                width=50, 
                                height=50, 
                                relief="solid", 
                                bd=2, 
                                bg="white",  
                                highlightthickness=1)  
            initial_bg = color_canvas.cget('bg')
            print(f"🟢 DEBUG: Initial Canvas Background: {initial_bg}")

            try:
                color_canvas.configure(bg='white')
                print(f"🟢 DEBUG: Configured background to white")
                
                after_config_bg = color_canvas.cget('bg')
                print(f"🟢 DEBUG: Background after configuration: {after_config_bg}")
                
                canvas_bg_dict = color_canvas['bg']
                print(f"🟢 DEBUG: Background via dictionary: {canvas_bg_dict}")
            except Exception as bg_error:
                print(f"🔴 ERROR: Could not set background: {bg_error}")

            color_canvas.pack(side="top")

            if initial_bg != 'white':
                color_canvas.config(bg='white')
                print("🔴 WARNING: Reset canvas background to white")

            color_canvas.pack(side="top") 

            cmyk_frame = tk.Frame(color_frame)
            cmyk_frame.pack(side="top", pady=2)

            labels = []
            for color in ["C", "M", "Y", "K"]:
                lbl = tk.Label(color_frame, text=f"{color}: 0%", font=("Arial", 10))
                lbl.pack(side="top")
                labels.append(lbl)

            edit_button = tk.Button(color_frame, image=self.edit_icon, command=lambda idx=i: self.edit_selected_color(idx))
            edit_button.pack(side="top", pady=2)
            edit_button.pack_forget()  

            button_frame = tk.Frame(color_frame)
            button_frame.pack(side="left", padx=5)

            ml_frame = tk.Frame(color_frame)
            ml_frame.pack(side="top", pady=2)

            button_3ml = tk.Button(ml_frame, text="3mL", command=lambda idx=i: self.toggle_ml_button(idx, "3mL"))
            button_5ml = tk.Button(ml_frame, text="5mL", command=lambda idx=i: self.toggle_ml_button(idx, "5mL"))
            button_7ml = tk.Button(ml_frame, text="7mL", command=lambda idx=i: self.toggle_ml_button(idx, "7mL"))

            for btn in (button_3ml, button_5ml, button_7ml):
                btn.pack(side="left", padx=2)
                btn.pack_forget() 

            color_canvas.bind("<Enter>", lambda event, i=i: self.show_buttons(event, i))
            color_canvas.bind("<Leave>", lambda event, i=i: self.hide_buttons(event, i))

            self.color_previews.append(color_canvas)
            self.cmyk_labels.append(labels)
            self.edit_buttons.append(edit_button)
            self.ml_buttons.append((button_3ml, button_5ml, button_7ml))  # Store buttons

        self.trays.append((self.color_previews, self.color_previews, self.cmyk_labels,self.edit_buttons, self.ml_buttons, self.selected_ml_buttons, tray_frame)) 
        close_button = tk.Button(tray_frame, text="Close", fg="white", bg="red",
                                command=lambda frame=tray_frame: self.remove_tray(frame))
        close_button.pack(side="right", padx=10)
        print_button = tk.Button(tray_frame, text="Print", bg="blue", fg="white",
                                command=lambda frame=tray_frame: self.save_colors(frame))
        print_button.pack(side="right", padx=10, pady=5)
        self.tray_container.update_idletasks()
        self.tray_count += 1

    def print_tray_info(self, frame):
        try:
            print(f"🔍 DEBUG: Frame type: {type(frame)}")
            print(f"🔍 DEBUG: Frame contents (repr): {repr(frame)}")
            
            color_previews = []
            
            if isinstance(frame, (list, tuple)):
                print("🔍 DEBUG: Frame is a list/tuple")
                for item in frame:
                    print(f"🔍 DEBUG: Item type: {type(item)}, Item repr: {repr(item)}")
                    
                    if isinstance(item, list):
                        color_previews.extend(item)
                    
                    elif hasattr(item, 'winfo_children'):
                        children = [
                            child for child in item.winfo_children() 
                            if isinstance(child, tk.Canvas) or hasattr(child, 'cget')
                        ]
                        color_previews.extend(children)
                    
                    else:
                        color_previews.append(item)
            
            elif hasattr(frame, 'winfo_children'):
                color_previews = [
                    child for child in frame.winfo_children() 
                    if isinstance(child, tk.Canvas) or hasattr(child, 'cget')
                ]
            
            print(f"🔍 DEBUG: Extracted color previews:")
            for i, preview in enumerate(color_previews):
                print(f"  {i}: Type = {type(preview)}, Repr = {repr(preview)}")
            
            tray_colors = []
            for canvas in color_previews:
                try:
                    color = None
                    
                    if hasattr(canvas, 'cget'):
                        try:
                            color = canvas.cget('bg')
                        except Exception as cget_error:
                            print(f"🔴 Error with cget: {cget_error}")
                    
                    if color is None and hasattr(canvas, 'bg'):
                        color = canvas.bg
                    
                    if color is None:
                        color = str(canvas)
                    
                    print(f"🔍 Retrieved color: {color} (Type: {type(color)})")

                    if isinstance(color, tuple):

                        tray_colors.append(list(map(int, color)))
                    elif isinstance(color, str):

                        if color.startswith('#'):
                            try:

                                color = color.lstrip('#')
                                rgb = [int(color[:2], 16), int(color[2:4], 16), int(color[4:], 16)]
                                tray_colors.append(rgb)
                            except Exception as hex_error:
                                print(f"🔴 Error converting hex color {color}: {hex_error}")
                                tray_colors.append(color)
                        else:

                            tray_colors.append(color)
                    else:

                        tray_colors.append(str(color))

                except Exception as canvas_error:
                    print(f"🔴 Error processing canvas color: {canvas_error}")
                    traceback.print_exc()


            data = {"colors": tray_colors}

            print("Data to be saved:", data)

            file_path = os.path.join(os.path.dirname(__file__), f'tray_colors_{str(self.tray_count)}.json')

            with open(file_path, 'w') as json_file:
                json.dump(data, json_file, indent=4)

            messagebox.showinfo("Success", f"Tray colors saved to {file_path}")

        except Exception as e:
            print(f"🔴 ERROR in print_tray_info: {str(e)}")
            traceback.print_exc()  
            messagebox.showerror("Error", f"An error occurred while saving the tray colors:\n{str(e)}")
            
    def remove_tray(self, tray_frame):
        print(f"Debug: Attempting to remove tray {tray_frame}")
        if tray_frame in self.trays:
            print(f"Debug: Found tray {tray_frame}, deleting...")

            for widget in tray_frame.winfo_children():
                print(f"Debug: Destroying widget {widget}")
                widget.destroy()

            tray_frame.destroy()
            print(f"Debug: Destroyed tray frame {tray_frame}")

            self.trays.remove(tray_frame)
            print(f"Debug: Tray removed. Current trays: {self.trays}")
        
        else:
            print(f"Debug: Tray {tray_frame} not found in self.trays")


    def set_mL(self, index, amount):
        if index < len(self.selected_colors):
            messagebox.showinfo("Paint Volume", f"Selected {amount}mL for color {index+1}")

    def toggle_ml_button(self, index, button_text):
        current_buttons = self.ml_buttons[index]

        button_map = {"3mL": current_buttons[0], "5mL": current_buttons[1], "7mL": current_buttons[2]}
        selected_button = button_map[button_text]

        if self.selected_ml_buttons[index] == selected_button:
            selected_button.config(relief="raised", bg="SystemButtonFace")  
            self.selected_ml_buttons[index] = None
        else:
            for btn in current_buttons:
                btn.config(relief="raised", bg="SystemButtonFace")  
            selected_button.config(relief="sunken", bg="yellow") 
            self.selected_ml_buttons[index] = selected_button  

    def replace_color(self, index):
        if self.image is None:
            messagebox.showwarning("Warning", "Please load an image first.")
            return

        self.replace_window = tk.Toplevel(self.root)
        self.replace_window.title("Select a New Color")
        self.replace_window.geometry("600x600")
        self.replace_window.transient(self.root)  

        self.replace_canvas = tk.Canvas(self.replace_window, width=500, height=500, bg="gray", relief="solid", bd=2)
        self.replace_canvas.pack(pady=10)

        self.replace_tk_image = ImageTk.PhotoImage(Image.fromarray(self.resized_image))
        self.replace_canvas.create_image(0, 0, anchor=tk.NW, image=self.replace_tk_image)
        self.replace_canvas.bind("<Button-1>", lambda event: self.update_selected_color(index, event))

        tk.Label(self.replace_window, text="Click on the image to select a new color", font=("Arial", 12)).pack()

    def update_selected_color(self, index, event):
        if self.image is None:
            return

        x, y = int(event.x), int(event.y)
        if 0 <= x < 500 and 0 <= y < 500:
            new_color = self.resized_image[y, x] 

            self.selected_colors[index] = new_color

            self.update_color_previews()

            self.replace_window.destroy()

    def edit_selected_color(self, index):
        if self.image is None:
            messagebox.showwarning("Warning", "Please load an image first.")
            return

        self.edit_window = tk.Toplevel(self.root)
        self.edit_window.title("Select a New Color")
        self.edit_window.geometry("800x700") 
        self.edit_window.transient(self.root)  

        edit_frame = tk.Frame(self.edit_window)
        edit_frame.pack(pady=10, padx=10, expand=True, fill='both')

        self.edit_canvas = tk.Canvas(edit_frame, width=500, height=500, bg="gray", relief="solid", bd=2)
        self.edit_canvas.pack(side=tk.LEFT, padx=10)

        self.edit_zoom_canvas = tk.Canvas(edit_frame, width=150, height=150, bg="white", relief="solid", bd=2)
        self.edit_zoom_canvas.pack(side=tk.RIGHT, padx=10)

        self.edit_tk_image = ImageTk.PhotoImage(Image.fromarray(self.resized_image))
        self.edit_canvas.create_image(0, 0, anchor=tk.NW, image=self.edit_tk_image)
        
        self.edit_canvas.bind("<Motion>", self.edit_mouse_hover)
        self.edit_canvas.bind("<B1-Motion>", self.edit_mouse_hover)
        self.edit_canvas.bind("<Button-1>", lambda event: self.update_selected_color(index, event))

        tk.Label(self.edit_window, text="Click on the image to select a new color", font=("Arial", 12)).pack(pady=5)

    def edit_mouse_hover(self, event):
        if self.image is None:
            return

        x, y = int(event.x), int(event.y)
        if 0 <= x < 500 and 0 <= y < 500:
            color = self.resized_image[y, x]
            zoomed_region = np.full((150, 150, 3), color, dtype=np.uint8)
            zoomed_image = ImageTk.PhotoImage(Image.fromarray(zoomed_region))
            self.edit_zoom_canvas.delete("all")
            self.edit_zoom_canvas.create_image(0, 0, anchor=tk.NW, image=zoomed_image)
            self.edit_zoom_canvas.image = zoomed_image
            
    def update_selected_color(self, index, event):
        if self.image is None:
            return

        x, y = int(event.x), int(event.y)
        if 0 <= x < 500 and 0 <= y < 500:
            new_color = self.resized_image[y, x]  

            self.selected_colors[index] = new_color

            self.update_color_previews()

            self.edit_window.destroy()

    def update_color_previews(self):
        print(f"Updating color previews: {self.selected_colors}")  

        for i, color in enumerate(self.selected_colors):
            if i < len(self.color_previews):
                color_rgb = tuple(map(int, color)) 

                preview_image = Image.new("RGB", (50, 50), color_rgb)
                preview_image_tk = ImageTk.PhotoImage(preview_image)
                self.color_previews[i].delete("all")
                self.color_previews[i].create_image(0, 0, anchor=tk.NW, image=preview_image_tk)
                self.color_previews[i].image = preview_image_tk 

                cmyk_values = self.calculate_cmyk(color_rgb)

                self.cmyk_labels[i][0].config(text=f"C: {str(round(cmyk_values['Cyan'] * 100, 2))}%")
                self.cmyk_labels[i][1].config(text=f"M: {str(round(cmyk_values['Magenta'] * 100, 2))}%")
                self.cmyk_labels[i][2].config(text=f"Y: {str(round(cmyk_values['Yellow'] * 100, 2))}%")
                self.cmyk_labels[i][3].config(text=f"K: {str(round(cmyk_values['Black'] * 100, 2))}%")

                if i < len(self.edit_buttons):
                    self.edit_buttons[i].pack()

                if i < len(self.ml_buttons):
                    for button in self.ml_buttons[i]:
                        button.pack()

        for i in range(len(self.selected_colors), len(self.color_previews)):
            self.color_previews[i].delete("all")
            for label in self.cmyk_labels[i]:
                label.config(text="0.00%")

            if i < len(self.edit_buttons):
                self.edit_buttons[i].pack_forget()

            if i < len(self.ml_buttons):
                for button in self.ml_buttons[i]:
                    if button.winfo_ismapped():
                        button.pack_forget()

    def calculate_cmyk(self, rgb_color):
        rgb = tuple(int(c) for c in rgb_color) 
        r, g, b = [x / 255.0 for x in rgb] 

        k = 1 - max(r, g, b)
        if k < 1:
            c = (1 - r - k) / (1 - k)
            m = (1 - g - k) / (1 - k)
            y = (1 - b - k) / (1 - k)
        else:
            c, m, y = 0, 0, 0

        return {
            "Cyan": round(float(c), 4),
            "Magenta": round(float(m), 4),
            "Yellow": round(float(y), 4),
            "Black": round(float(k), 4)
        }


    def reset_colors(self):
            self.selected_colors.clear()
            self.update_color_previews()

    def extract_color_from_label(self, label):
        try:
            # Try getting background color directly
            try:
                # Try different methods to get background color
                bg_color = label.cget("bg")
                print(f"🔍 DEBUG: Retrieved background color via cget: {bg_color}")
            except Exception:
                try:
                    bg_color = label['background']
                    print(f"🔍 DEBUG: Retrieved background color via dictionary: {bg_color}")
                except Exception:
                    # If no background color found
                    print(f"🔴 DEBUG: No background color found for {label}")
                    return None
            
            # Hex color conversion
            if isinstance(bg_color, str) and bg_color.startswith('#'):
                try:
                    # Convert hex to RGB
                    r = int(bg_color[1:3], 16)
                    g = int(bg_color[3:5], 16)
                    b = int(bg_color[5:7], 16)
                    print(f"🟢 DEBUG: Converted hex color {bg_color} to RGB: ({r}, {g}, {b})")
                    return (r, g, b)
                except Exception as hex_err:
                    print(f"🔴 DEBUG: Hex conversion error: {hex_err}")
                    return None
            
            # Handle system colors
            def get_system_color_rgb(color_name):
                system_colors = {
                    'systembuttonface': (240, 240, 240),
                    'systemwindow': (255, 255, 255),
                    'systemwindowtext': (0, 0, 0),
                    'systemhighlighttext': (255, 255, 255),
                    'systemhighlight': (0, 120, 215)
                }
                return system_colors.get(color_name.lower(), None)
            
            # Predefined color map
            color_map = {
                'red': (255, 0, 0),
                'green': (0, 255, 0),
                'blue': (0, 0, 255),
                'white': (255, 255, 255),
                'black': (0, 0, 0),
                'yellow': (255, 255, 0),
                'cyan': (0, 255, 255),
                'magenta': (255, 0, 255)
            }
            
            if isinstance(bg_color, str):
                color_lower = bg_color.lower()
                
                system_rgb = get_system_color_rgb(color_lower)
                if system_rgb:
                    print(f"🟢 DEBUG: Converted system color {bg_color}: {system_rgb}")
                    return system_rgb
                
                if color_lower in color_map:
                    print(f"🟢 DEBUG: Found predefined color {color_lower}: {color_map[color_lower]}")
                    return color_map[color_lower]
            
            if isinstance(bg_color, str) and bg_color.startswith('rgb'):
                try:
                    rgb_values = tuple(map(int, bg_color[4:-1].split(',')))
                    print(f"🟢 DEBUG: Converted RGB string {bg_color} to {rgb_values}")
                    return rgb_values
                except Exception as rgb_err:
                    print(f"🔴 DEBUG: RGB string conversion error: {rgb_err}")
                    return None
            
            if isinstance(bg_color, tuple) and len(bg_color) == 3:
                try:
                    rgb_values = tuple(map(int, bg_color))
                    print(f"🟢 DEBUG: Converted tuple color {bg_color} to {rgb_values}")
                    return rgb_values
                except Exception as tuple_err:
                    print(f"🔴 DEBUG: Tuple color conversion error: {tuple_err}")
                    return None
            
            print(f"🔴 DEBUG: Failed to convert color: {bg_color}")
            return None
        
        except Exception as general_err:
            print(f"🔴 DEBUG: General color extraction error: {general_err}")
            return None
         
    def save_colors(self, frame=None):
        """Save selected colors and display them as 'Recent Batch'."""
        try:
            print("🟢 DEBUG: save_colors method called")
            
            if len(self.selected_colors) != 6:
                messagebox.showwarning("Warning", "You must select exactly 6 colors to save.")
                return
            
            all_tray_data = []
            
            for color_index, color in enumerate(self.selected_colors):
                try:
                    r, g, b = map(int, color)
                    
                    hex_color = '#{:02x}{:02x}{:02x}'.format(r, g, b)
                    
                    def get_color_name(rgb):
                        color_names = {
                            (255, 0, 0): "Red",
                            (0, 255, 0): "Green", 
                            (0, 0, 255): "Blue",
                            (255, 255, 255): "White",
                            (0, 0, 0): "Black",
                            (240, 240, 240): "SystemButtonFace",
                            (255, 204, 0): "Yellow",
                            (255, 102, 0): "Orange"
                        }
                        
                        # Exact match
                        if tuple(rgb) in color_names:
                            return color_names[tuple(rgb)]
                        
                        # Approximate color names
                        def color_distance(c1, c2):
                            return sum((a-b)**2 for a, b in zip(c1, c2))
                        
                        closest_color = min(color_names.keys(), 
                                            key=lambda x: color_distance(x, rgb))
                        return color_names[closest_color]
                    
 # CMYK extraction from current tray's CMYK labels
                    # CMYK extraction from current tray's CMYK labels
                    def extract_cmyk_from_tray():
                        # Comprehensive debug logging for self.trays
                        print("🔍 DEBUG: Tray Debugging Start")
                        print(f"🔍 DEBUG: Total trays: {len(self.trays)}")
                        
                        # Print detailed information about trays
                        for tray_index, tray in enumerate(self.trays):
                            print(f"\n🔍 DEBUG: Tray {tray_index}:")
                            print(f"   Type: {type(tray)}")
                            
                            # Try to print as much information as possible
                            try:
                                print(f"   Length: {len(tray)}")
                                for item_index, item in enumerate(tray):
                                    print(f"   Item {item_index}:")
                                    print(f"     Type: {type(item)}")
                                    
                                    # If it's a list or tuple, show its contents
                                    if isinstance(item, (list, tuple)):
                                        print(f"     Length: {len(item)}")
                                        for sub_index, sub_item in enumerate(item):
                                            print(f"     Subitem {sub_index}:")
                                            print(f"       Type: {type(sub_item)}")
                                            
                                            # If it's a Tkinter widget, show its properties
                                            try:
                                                if hasattr(sub_item, 'cget'):
                                                    print(f"       Background: {sub_item.cget('bg')}")
                                            except Exception as widget_err:
                                                print(f"       Error getting widget info: {widget_err}")
                            except Exception as tray_err:
                                print(f"   Error processing tray: {tray_err}")
                        
                        print("🔍 DEBUG: Tray Debugging End\n")
                        
                        # Fallback to default if no matching tray found
                        print("🔴 DEBUG: No matching tray found for CMYK extraction")
                        return {"c": 0.0, "m": 0.0, "y": 0.0, "k": 0.0}
                    
                    # Get CMYK values
                    cmyk_values = extract_cmyk_from_tray()
                    
                    # Prepare color data with comprehensive details
                    color_data = {
                        "index": color_index,
                        "rgb": {
                            "r": r,
                            "g": g,
                            "b": b
                        },
                        "hex": hex_color,
                        "name": get_color_name((r, g, b)),
                        "cmyk": cmyk_values,
                        "brightness": round((r * 299 + g * 587 + b * 114) / 1000, 2)
                    }
                    
                    print(f"🟢 DEBUG: Processed color data: {color_data}")
                    
                    all_tray_data.append(color_data)
                
                except Exception as color_err:
                    print(f"🔴 Error processing color {color_index}: {color_err}")
            
            # Prepare data for saving
            data = {
                "colors": all_tray_data,
                "timestamp": datetime.datetime.now().isoformat(),
                "total_colors": len(all_tray_data)
            }
            
            # Automatically save in the same directory with a timestamped filename
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            script_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(script_dir, f"color_batch_{timestamp}.json")
            
            with open(file_path, "w") as f:
                json.dump(data, f, indent=4)
            
            print(f"🟢 DEBUG: Saved color batch to {file_path}")
            messagebox.showinfo("Success", f"Saved {len(all_tray_data)} colors to {os.path.basename(file_path)}")
            
            # Display recent batch with RGB tuples
            self.display_recent_batch([(color_data['rgb']['r'], color_data['rgb']['g'], color_data['rgb']['b']) for color_data in all_tray_data])
        
        except Exception as e:
            print(f"🔴 Error in save_colors(): {traceback.format_exc()}")
            messagebox.showerror("Error", f"An unexpected error occurred:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PaintMixerApp(root)
    root.mainloop()