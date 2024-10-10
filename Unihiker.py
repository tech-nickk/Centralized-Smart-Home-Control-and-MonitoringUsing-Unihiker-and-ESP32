import tkinter as tk
import socket
import json
import threading
import time

class Room:
    def __init__(self, name, controls, ip_address):
        self.name = name
        self.temperature = 20
        self.humidity = 50
        self.appliances = {control: False for control in controls}
        self.ip_address = ip_address

class Dashboard:
    def __init__(self, master):
        self.master = master
        master.title("SMART HOME")
        master.configure(bg="#2c3e50")
        
        self.rooms = [
            Room("Living Room", ["Light", "TV", "AC", "Fan"], "192.168.137.57"),
            Room("Bedroom", ["Light", "Fan", "Heater"], "192.168.1.102"),
            Room("Kitchen", ["Light", "Oven", "Fridge"], "192.168.1.103"),
            Room("Bathroom", ["Light"], "192.168.1.104")
        ]
        self.current_room = None
        self.create_main_dashboard()
        
        # Start a thread for periodic updates
        self.update_thread = threading.Thread(target=self.periodic_update, daemon=True)
        self.update_thread.start()

    def create_main_dashboard(self):
        for widget in self.master.winfo_children():
            widget.destroy()
        tk.Label(self.master, text="SMART HOME", font=("Arial", 20, "bold"), bg="#2c3e50", fg="#ecf0f1").pack(pady=10)
        button_styles = {
            "Living Room": "#e74c3c", "Bedroom": "#3498db",
            "Kitchen": "#2ecc71", "Bathroom": "#f1c40f",
        }
        for room in self.rooms:
            tk.Button(
                self.master, 
                text=room.name, 
                command=lambda r=room: self.show_room_dashboard(r),
                font=("Arial", 13),
                bg=button_styles[room.name],
                fg="#ffffff", 
                width=18, height=2,
                relief=tk.FLAT,
            ).pack(pady=5)

    def show_room_dashboard(self, room):
        self.current_room = room
        for widget in self.master.winfo_children():
            widget.destroy()
        tk.Label(self.master, text=room.name, font=("Arial", 18, "bold"), bg="#2c3e50", fg="#ecf0f1").pack(pady=10)
        
        # Sensor display
        sensor_frame = tk.Frame(self.master, bg="#34495e", bd=2, relief=tk.RAISED)
        sensor_frame.pack(fill=tk.X, padx=10, pady=5)
        self.temp_label = tk.Label(sensor_frame, text=f"Temp: {room.temperature}°C", font=("Arial", 13), bg="#34495e", fg="#ffffff")
        self.temp_label.pack(side=tk.LEFT, expand=True, pady=10)
        self.humid_label = tk.Label(sensor_frame, text=f"Hum: {room.humidity}%", font=("Arial", 13), bg="#34495e", fg="#ffffff")
        self.humid_label.pack(side=tk.RIGHT, expand=True, pady=10)
        
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
        
        tk.Button(
            self.master, 
            text="Back to Main", 
            command=self.create_main_dashboard, 
            font=("Arial", 12), 
            bg="#7f8c8d", 
            fg="#ffffff",
            width=20, height=2,
            relief=tk.FLAT,
        ).pack(pady=10)

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
            self.temp_label.config(text=f"Temp: {self.current_room.temperature}°C")
            self.humid_label.config(text=f"Hum: {self.current_room.humidity}%")
            self.show_room_dashboard(self.current_room)

def main():
    root = tk.Tk()
    root.geometry("240x320")
    dashboard = Dashboard(root)
    root.mainloop()

if __name__ == "__main__":
    main()
