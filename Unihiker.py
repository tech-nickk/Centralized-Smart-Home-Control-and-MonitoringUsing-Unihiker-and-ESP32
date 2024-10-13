import tkinter as tk
import socket
import json
import threading
import time
from PIL import Image, ImageTk

class Room:
    def __init__(self, name, controls, ip_address, icon_file):
        self.name = name
        self.temperature = 25
        self.humidity = 57
        self.appliances = {control: False for control in controls}
        self.ip_address = ip_address
        self.icon_file = icon_file

class Dashboard:
    def __init__(self, master):
        self.master = master
        master.title("SMART HOME")
        master.configure(bg="#2c3e50")
        
        self.rooms = [
            #You can add or rename the rooms, add devices/appliances as you please
            Room("Living Room", ["Light", "TV", "AC", "Fan"], "192.168.137.236", "living-room.png"),
            Room("Bedroom", ["Light", "Fan", "Heater"], "192.168.137.59", "bedroom.png"),
            Room("Kitchen", ["Light", "Oven", "Fridge"], "192.168.1.103", "kitchen.png"),
            Room("Bathroom", ["Light"], "192.168.1.104", "bathroom.png")
        ]
        self.current_room = None
        
        # Load and resize icons
        self.temp_icon = self.load_and_resize_icon("temp.png", (35, 35))
        self.humid_icon = self.load_and_resize_icon("humidity.png", (35, 35))
        
        # Start a thread for periodic updates
        self.update_thread = threading.Thread(target=self.periodic_update, daemon=True)
        self.update_thread.start()

        self.create_home_page()

    def load_and_resize_icon(self, filename, size):
        try:
            icon = Image.open(filename)
            icon = icon.resize(size, Image.ANTIALIAS)
            return ImageTk.PhotoImage(icon)
        except FileNotFoundError:
            print(f"Warning: Icon file {filename} not found.")
            return None

    def create_home_page(self):
        for widget in self.master.winfo_children():
            widget.destroy()
        
        tk.Label(self.master, text="SMART HOME", font=("Arial", 18, "bold"), bg="#2c3e50", fg="#ecf0f1").pack(pady=5)
        
        # Digital clock display
        self.clock_frame = tk.Frame(self.master, bg="#34495e", bd=2, relief=tk.RAISED)
        self.clock_frame.pack(fill=tk.X, padx=10, pady=3)
        self.time_label = tk.Label(self.clock_frame, font=("DS-Digital", 20), bg="#34495e", fg="#2ecc71")
        self.time_label.pack(pady=3)
        self.date_label = tk.Label(self.clock_frame, font=("Arial", 10), bg="#34495e", fg="#ecf0f1")
        self.date_label.pack(pady=3)
        self.update_clock()

        # Navigation icons
        icon_frame = tk.Frame(self.master, bg="#2c3e50")
        icon_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=3)
        icon_frame.grid_columnconfigure((0,1), weight=1)
        icon_frame.grid_rowconfigure((0,1), weight=1)

        self.create_icon(icon_frame, "Dashboard", "dashboard.png", self.create_main_dashboard, 0, 0)
        self.create_icon(icon_frame, "Alerts", "alerts.png", self.show_alerts, 0, 1)
        self.create_icon(icon_frame, "Automation", "automation.png", self.show_automation, 1, 0)
        self.create_icon(icon_frame, "Settings", "settings.png", self.show_settings, 1, 1)

    def create_icon(self, parent, text, icon_file, command, row, col):
        icon_frame = tk.Frame(parent, bg="#34495e", bd=0, relief=tk.RAISED)
        icon_frame.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)

        try:
            icon = Image.open(icon_file)
            icon = icon.resize((50, 50), Image.ANTIALIAS)
            icon_photo = ImageTk.PhotoImage(icon)
            icon_button = tk.Button(icon_frame, image=icon_photo, bg="#34495e", bd=0, command=command)
            icon_button.image = icon_photo  # Keep a reference
            icon_button.pack(pady=(10,5))
        except FileNotFoundError:
            # Fallback to text button if icon file is not found
            icon_button = tk.Button(icon_frame, text=text, font=("Arial", 14), bg="#3498db", fg="#ffffff",
                                    command=command, width=10, height=2)
            icon_button.pack(pady=(10,5))

        tk.Label(icon_frame, text=text, font=("Arial", 12), bg="#34495e", fg="#ecf0f1").pack()

    def update_clock(self):
        current_time = time.strftime("%H:%M:%S")
        current_date = time.strftime("%B %d, %Y")
        self.time_label.config(text=current_time)
        self.date_label.config(text=current_date)
        self.master.after(1000, self.update_clock)

    def create_main_dashboard(self):
        for widget in self.master.winfo_children():
            widget.destroy()
        tk.Label(self.master, text="SMART HOME", font=("Arial", 20, "bold"), bg="#2c3e50", fg="#ecf0f1").pack(pady=5)
        
        icon_frame = tk.Frame(self.master, bg="#2c3e50")
        icon_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        icon_frame.grid_columnconfigure((0,1), weight=1)
        icon_frame.grid_rowconfigure((0,1), weight=1)

        for i, room in enumerate(self.rooms):
            self.create_icon(icon_frame, room.name, room.icon_file, lambda r=room: self.show_room_dashboard(r), i//2, i%2)

        self.add_back_button(self.create_home_page)

    def show_room_dashboard(self, room):
        self.current_room = room
        for widget in self.master.winfo_children():
            widget.destroy()
        tk.Label(self.master, text=room.name, font=("Arial", 18, "bold"), bg="#2c3e50", fg="#ecf0f1").pack(pady=10)
        
        # Sensor display
        sensor_frame = tk.Frame(self.master, bg="#34495e", bd=0, relief=tk.RAISED)
        sensor_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Temperature display
        temp_frame = tk.Frame(sensor_frame, bg="#34495e")
        temp_frame.pack(side=tk.LEFT, expand=True, pady=5, padx=5)
        if self.temp_icon:
            tk.Label(temp_frame, image=self.temp_icon, bg="#34495e").pack(side=tk.LEFT, padx=(0, 5))
        self.temp_label = tk.Label(temp_frame, text=f"{room.temperature}°C", font=("Arial", 15), bg="#34495e", fg="#ffffff")
        self.temp_label.pack(side=tk.LEFT)
        
        # Humidity display
        humid_frame = tk.Frame(sensor_frame, bg="#34495e")
        humid_frame.pack(side=tk.RIGHT, expand=True, pady=5, padx=5)
        if self.humid_icon:
            tk.Label(humid_frame, image=self.humid_icon, bg="#34495e").pack(side=tk.LEFT, padx=(0, 5))
        self.humid_label = tk.Label(humid_frame, text=f"{room.humidity}%", font=("Arial", 15), bg="#34495e", fg="#ffffff")
        self.humid_label.pack(side=tk.LEFT)
        
        # Controls
        control_frame = tk.Frame(self.master, bg="#2c3e50")
        control_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        for i, (appliance, status) in enumerate(room.appliances.items()):
            button = tk.Button(
                control_frame,
                text=f"{appliance}: {'On' if status else 'Off'}",
                command=lambda a=appliance: self.toggle_appliance(a),
                font=("Arial", 12),
                bg="#2ecc71" if status else "#e74c3c",
                fg="#ffffff",
                width=15, height=2,
                relief=tk.FLAT,
            )
            button.grid(row=i//2, column=i%2, pady=5, padx=5, sticky="nsew")
        control_frame.grid_columnconfigure(0, weight=1)
        control_frame.grid_columnconfigure(1, weight=1)
        
        self.add_back_button(self.create_main_dashboard)

    def add_back_button(self, command):
        tk.Button(
            self.master, 
            text="Back", 
            command=command, 
            font=("Arial", 12), 
            bg="#7f8c8d", 
            fg="#ffffff",
            width=20, height=2,
            relief=tk.FLAT,
        ).pack(pady=5)

    def toggle_appliance(self, appliance):
        if self.current_room:
            new_status = not self.current_room.appliances[appliance]
            self.current_room.appliances[appliance] = new_status
            self.send_command(self.current_room.ip_address, appliance, new_status)
            self.show_room_dashboard(self.current_room)  # Refresh the room dashboard

    def send_command(self, ip_address, appliance, status):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((ip_address, 8080))
                command = json.dumps({"command": "set", "appliance": appliance, "status": status})
                s.sendall(command.encode())
                response = s.recv(1024).decode()
                print(f"Response from {ip_address}: {response}")
        except Exception as e:
            print(f"Error sending command to {ip_address}: {e}")

    def get_room_data(self, ip_address):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((ip_address, 8080))
                command = json.dumps({"command": "get"})
                s.sendall(command.encode())
                response = s.recv(1024).decode()
                return json.loads(response)
        except Exception as e:
            print(f"Error getting data from {ip_address}: {e}")
            return None

    def update_room_data(self, room, data):
        if data:
            room.temperature = data.get('temperature', room.temperature)
            room.humidity = data.get('humidity', room.humidity)
            room.appliances.update(data.get('appliances', {}))

    def periodic_update(self):
        while True:
            for room in self.rooms:
                data = self.get_room_data(room.ip_address)
                self.update_room_data(room, data)
            
            if self.current_room:
                self.master.after(0, self.update_current_room_display)
            
            time.sleep(5)  # Update every 5 seconds

    def update_current_room_display(self):
        if self.current_room:
            self.temp_label.config(text=f"{self.current_room.temperature}°C")
            self.humid_label.config(text=f"{self.current_room.humidity}%")

    # Placeholder methods for new pages
    def show_alerts(self):
        self.show_placeholder_page("Alerts")

    def show_automation(self):
        self.show_placeholder_page("Automation")

    def show_settings(self):
        self.show_placeholder_page("Settings")

    def show_placeholder_page(self, title):
        for widget in self.master.winfo_children():
            widget.destroy()
        tk.Label(self.master, text=title, font=("Arial", 20, "bold"), bg="#2c3e50", fg="#ecf0f1").pack(pady=20)
        tk.Label(self.master, text=f"This is the {title} page", font=("Arial", 14), bg="#2c3e50", fg="#ecf0f1").pack(pady=20)
        self.add_back_button(self.create_home_page)

def main():
    root = tk.Tk()
    root.geometry("240x320")
    dashboard = Dashboard(root)
    root.mainloop()

if __name__ == "__main__":
    main()
