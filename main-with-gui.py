import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import xml.etree.ElementTree as ET
import source_helper
import tkinter as tk
from tkinter import simpledialog

version = 1.1
prog = "TransitTracker"

print(f"Welcome to {prog} version {version}")

def _create_http_session():
    session = requests.Session()
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "POST"),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

_HTTP_SESSION = _create_http_session()

def http_get(url, **kwargs):
    timeout = kwargs.pop("timeout", 10)
    return _HTTP_SESSION.get(url, timeout=timeout, **kwargs)

def http_stop_search(search):

    response = http_get(f"https://api.winnipegtransit.com/v4/stops:{search}?api-key={source_helper.api_key}")

    response.raise_for_status()

    # Parse XML response
    root = ET.fromstring(response.text)

    # Find all stop elements
    stops = root.findall('.//stop')

    if not stops:
        print("No stops found")
        print("Raw XML response:")
        print(response.text)
    else:
        for stop in stops:
            # Extract stop information
            name = stop.find('name')
            name_text = name.text if name is not None else "N/A"
            
            street = stop.find('street')
            street_name = street.find('name') if street is not None else None
            street_text = street_name.text if street_name is not None else "N/A"
            
            # Get geographic coordinates
            geographic = stop.find('geographic')
            if geographic is not None:
                lat = geographic.find('latitude')
                lon = geographic.find('longitude')
                lat_text = lat.text if lat is not None else "N/A"
                lon_text = lon.text if lon is not None else "N/A"
            else:
                lat_text = lon_text = "N/A"
            
            print(f"Name: {name_text}")
            print(f"Street: {street_text}")
            print(f"Lat: {lat_text} Long: {lon_text}")
            input("Press Enter to list next stop... ")

def busTimer(self, stopToGet):
    response = http_get(f"https://api.winnipegtransit.com/v4/stops/{stopToGet}/schedule?api-key={source_helper.api_key}")

    response.raise_for_status()

    # Parse XML response
    root = ET.fromstring(response.text)

    # Find the stop element within stop-schedule
    stop = root.find('stop')
    
    if stop is None:
        print("No stop found")
        return

    # Get stop information
    stop_name = stop.find("name")
    stop_name_text = stop_name.text if stop_name is not None else "N/A"
    
    direction = stop.find("direction")
    direction_text = direction.text if direction is not None else "N/A"
    
    street = stop.find("street")
    street_name = street.find("name") if street is not None else None
    street_text = street_name.text if street_name is not None else "N/A"
    
    cross_street = stop.find("cross-street")
    cross_street_name = cross_street.find("name") if cross_street is not None else None
    cross_street_text = cross_street_name.text if cross_street_name is not None else "N/A"
    
    print(f"Stop: {stop_name_text}")
    print(f"Direction: {direction_text}")
    print(f"Street: {street_text}")
    print(f"Cross Street: {cross_street_text}")
    print("-" * 50)

    # Find route-schedules container
    route_schedules_container = root.find("route-schedules")
    
    if route_schedules_container is None:
        print("No route schedules found")
        return

    # Find all route-schedule elements within the container
    route_schedules = route_schedules_container.findall("route-schedule")
    
    for route_schedule in route_schedules:
        # Get route information
        route = route_schedule.find("route")
        if route is not None:
            route_key = route.find("key")
            route_name = route.find("name")
            self.route_key_text = route_key.text if route_key is not None else "N/A"
            route_name_text = route_name.text if route_name is not None else "N/A"
            
            print(f"Route: {self.route_key_text} - {self.route_name_text}")
            
            # Get scheduled stops (not "schedule" - it's "scheduled-stops")
            scheduled_stops = route_schedule.find("scheduled-stops")
            if scheduled_stops is not None:
                stops = scheduled_stops.findall("scheduled-stop")
                for stop in stops:
                    stop_key = stop.find("key")
                    trip_key = stop.find("trip-key")
                    self.stop_key_text = stop_key.text if stop_key is not None else "N/A"
                    trip_key_text = trip_key.text if trip_key is not None else "N/A"
                    
                    # Get times
                    times = stop.find("times")
                    if times is not None:
                        arrival = times.find("arrival")
                        departure = times.find("departure")
                        
                        if arrival is not None:
                            arrival_scheduled = arrival.find("scheduled")
                            arrival_estimated = arrival.find("estimated")
                            self.arrival_sched_text = arrival_scheduled.text if arrival_scheduled is not None else "N/A"
                            self.arrival_est_text = arrival_estimated.text if arrival_estimated is not None else "N/A"
                        else:
                            self.arrival_sched_text = self.arrival_est_text = "N/A"
                            
                        if departure is not None:
                            departure_scheduled = departure.find("scheduled")
                            departure_estimated = departure.find("estimated")
                            departure_sched_text = departure_scheduled.text if departure_scheduled is not None else "N/A"
                            departure_est_text = departure_estimated.text if departure_estimated is not None else "N/A"
                        else:
                            departure_sched_text = departure_est_text = "N/A"
                        
                        print(f"  Stop: {self.self.stop_key_text} (Trip: {trip_key_text})")
                        print(f"    Arrival: {self.arrival_sched_text} (est: {self.arrival_est_text})")
                        print(f"    Departure: {departure_sched_text} (est: {departure_est_text})")
                    else:
                        print(f"  Stop: {self.stop_key_text} (Trip: {trip_key_text}) - no times")
                print()
            else:
                print("  No scheduled stops found")
        else:
            print("No route information found")
class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry("400x400")
        self.root.title(f"{prog}")
        
        self.startWindow = tk.Toplevel(self.root)

        self.stopSearchButton = tk.Button(self.startWindow, text="Stop Search",
                    command=self.stopSearch,
                )
        self.stopSearchButton.pack(pady=5)
        self.busSearchButton = tk.Button(self.startWindow, text="Bus Schedule",
            command=self.busSchedule,
        )
        self.busSearchButton.pack(pady=5)

        # StringVars for showing values in the UI (initialize properly)
        self.route_var = tk.StringVar(self.root)
        self.stop_var = tk.StringVar(self.root)
        self.arrival_var = tk.StringVar(self.root)
        self.arrival_est_var = tk.StringVar(self.root)
        self.departure_var = tk.StringVar(self.root)
        self.departure_est_var = tk.StringVar(self.root)

        self.route_label = tk.Label(self.root, textvariable=self.route_var,
            fg="cyan", bg="black",
            font=("Courier", 10), justify="left"
        )
        self.route_label.pack()

    def stopSearch(self):
        value = simpledialog.askstring("Stop Search", "Enter stop number or query:", parent=self.root)
        if value is None or value.strip() == "":
            return
        http_stop_search(value.strip())
    def busSchedule(self):
        value = simpledialog.askstring("Bus Schedule", "Enter stop number to see schedule: ", parent=self.root)
        if value is None or value.strip() == "":
            return
        self.busTimer(value.strip())

    def busTimer(self, stopToGet):
        response = http_get(f"https://api.winnipegtransit.com/v4/stops/{stopToGet}/schedule?api-key={source_helper.api_key}")

        response.raise_for_status()

        root_xml = ET.fromstring(response.text)

        stop = root_xml.find('stop')
        if stop is None:
            print("No stop found")
            return

        stop_name = stop.find("name")
        self.stop_name_text = stop_name.text if stop_name is not None else "N/A"

        direction = stop.find("direction")
        self.direction_text = direction.text if direction is not None else "N/A"

        street = stop.find("street")
        street_name = street.find("name") if street is not None else None
        self.street_text = street_name.text if street_name is not None else "N/A"

        cross_street = stop.find("cross-street")
        cross_street_name = cross_street.find("name") if cross_street is not None else None
        self.cross_street_text = cross_street_name.text if cross_street_name is not None else "N/A"

        print(f"Stop: {self.stop_name_text}")
        print(f"Direction: {self.direction_text}")
        print(f"Street: {self.street_text}")
        print(f"Cross Street: {self.cross_street_text}")
        print("-" * 50)

        route_schedules_container = root_xml.find("route-schedules")
        if route_schedules_container is None:
            print("No route schedules found")
            return

        route_schedules = route_schedules_container.findall("route-schedule")
        for route_schedule in route_schedules:
            route = route_schedule.find("route")
            if route is not None:
                route_key = route.find("key")
                route_name = route.find("name")
                self.route_key_text = route_key.text if route_key is not None else "N/A"
                self.route_name_text = route_name.text if route_name is not None else "N/A"

                print(f"Route: {self.route_key_text} - {self.route_name_text}")

                scheduled_stops = route_schedule.find("scheduled-stops")
                if scheduled_stops is not None:
                    stops = scheduled_stops.findall("scheduled-stop")
                    for scheduled_stop in stops:
                        stop_key = scheduled_stop.find("key")
                        trip_key = scheduled_stop.find("trip-key")
                        self.stop_key_text = stop_key.text if stop_key is not None else "N/A"
                        trip_key_text = trip_key.text if trip_key is not None else "N/A"

                        times = scheduled_stop.find("times")
                        if times is not None:
                            arrival = times.find("arrival")
                            departure = times.find("departure")

                            if arrival is not None:
                                arrival_scheduled = arrival.find("scheduled")
                                arrival_estimated = arrival.find("estimated")
                                self.arrival_sched_text = arrival_scheduled.text if arrival_scheduled is not None else "N/A"
                                self.arrival_est_text = arrival_estimated.text if arrival_estimated is not None else "N/A"
                            else:
                                self.arrival_sched_text = "N/A"
                                self.arrival_est_text = "N/A"

                            if departure is not None:
                                departure_scheduled = departure.find("scheduled")
                                departure_estimated = departure.find("estimated")
                                self.departure_sched_text = departure_scheduled.text if departure_scheduled is not None else "N/A"
                                self.departure_est_text = departure_estimated.text if departure_estimated is not None else "N/A"
                            else:
                                self.departure_sched_text = "N/A"
                                self.departure_est_text = "N/A"

                            print(f"  Stop: {self.stop_key_text} (Trip: {trip_key_text})")
                            print(f"    Arrival: {self.arrival_sched_text} (est: {self.arrival_est_text})")
                            print(f"    Departure: {self.departure_sched_text} (est: {self.departure_est_text})")
                            self.valuesToScreen()
                        else:
                            print(f"  Stop: {self.stop_key_text} (Trip: {trip_key_text}) - no times")
                    print()
                else:
                    print("  No scheduled stops found")
            else:
                print("No route information found")

        # Optionally update bound variables for UI
        self.valuesToScreen()

    def valuesToScreen(self):
        # Safely set values if they exist
        if hasattr(self, 'route_name_text'):
            self.route_var.set(self.route_name_text)
        if hasattr(self, 'stop_key_text'):
            self.stop_var.set(self.stop_key_text)
        if hasattr(self, 'arrival_sched_text'):
            self.arrival_var.set(self.arrival_sched_text)
        if hasattr(self, 'arrival_est_text'):
            self.arrival_est_var.set(self.arrival_est_text)
        if hasattr(self, 'departure_sched_text'):
            self.departure_var.set(self.departure_sched_text)
        if hasattr(self, 'departure_est_text'):
            self.departure_est_var.set(self.departure_est_text)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = App()
    app.run()