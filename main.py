import requests
import threading
import winsound
import configparser
import os
from datetime import datetime

CONFIG_FILE = 'config.ini'
config = configparser.ConfigParser()

def format_date(date: str) -> datetime:
    return datetime.strptime(date, "%Y-%m-%dT%H:%M:%S")

def save_to_config(town_from: str, town_to: str, date_time: str) -> None:
    config['DEFAULT']['town_from'] = town_from
    config['DEFAULT']['town_to'] = town_to
    config['DEFAULT']['datetime'] = date_time

    with open(CONFIG_FILE, 'w') as f:
        config.write(f)

def initialize_config() -> None:
    if not os.path.exists(CONFIG_FILE):
        config['DEFAULT'] = {
            'town_from': 'Минск',
            'town_to': 'Городок',
            'datetime': '08:50 10.11.2024'
        }
        with open(CONFIG_FILE, 'w') as f:
            config.write(f)

def get_towns() -> list:
    response = requests.get('https://v-minsk.com/api/search/suggest?user_input=&from_id=&to_id=&locale=ru',
                            headers={"x-saas-partner-id": "vminsk"})
    return response.json()

def get_rides(town_from_id: str, town_to_id: str, date: str) -> list:
    response = requests.get(
        f'https://v-minsk.com/api/search?from_id={town_from_id}&to_id={town_to_id}&calendar_width=30&date={date}&passengers=1'
    )
    return response.json().get('rides', [])

def find_ride_by_datetime(rides: list, date_time: datetime) -> dict:
    return next((ride for ride in rides
                 if datetime.strptime(ride['departure'], "%Y-%m-%dT%H:%M:%S") == date_time), None)

def get_user_input(towns: list) -> tuple:
    print("Доступные города:", '; '.join(town['name'] for town in towns))
    town_from = input('Город отправления: ')
    town_to = input('Город прибытия: ')
    date_time = input('Время и дата (пример: "08:50 10.11.2024"): ')
    return town_from, town_to, date_time

def timer_func(town_from_id: str, town_to_id: str, date_time: datetime) -> None:
    rides = get_rides(town_from_id, town_to_id, date_time.strftime('%Y-%m-%d'))
    ride = find_ride_by_datetime(rides, date_time)

    if ride:
        print(f'Текущее время: {datetime.now().strftime("%H:%M:%S")} '
              f'Свободно мест: {ride["freeSeats"]} '
              f'{format_date(ride["departure"]).strftime("%H:%M")}-{format_date(ride["arrival"]).strftime("%H:%M")} '
              f'{format_date(ride["departure"]).strftime("%d.%m.%Y")}-{format_date(ride["arrival"]).strftime("%d.%m.%Y")}.')
        
        if ride['freeSeats'] > 0:
            winsound.PlaySound("SystemHand", winsound.SND_ALIAS)

    threading.Timer(2.0, timer_func, [town_from_id, town_to_id, date_time]).start()

def main():
    initialize_config()
    config.read(CONFIG_FILE)

    towns = get_towns()
    print("Выберите метод ввода данных:\n1. Загрузить из конфигурационного файла\n2. Ввести вручную")
    choice = input("Введите 1 или 2: ")

    if choice == '1':
        town_from = config['DEFAULT']['town_from']
        town_to = config['DEFAULT']['town_to']
        date_time = config['DEFAULT']['datetime']

        if not town_from or not town_to or not date_time:
            print("В конфигурационном файле отсутствуют данные. Пожалуйста, введите их вручную.")
            town_from, town_to, date_time = get_user_input(towns)
    else:
        town_from, town_to, date_time = get_user_input(towns)

    town_from_id = next(town['id'] for town in towns if town['name'] == town_from)
    town_to_id = next(town['id'] for town in towns if town['name'] == town_to)
    parsed_date = datetime.strptime(date_time, "%H:%M %d.%m.%Y")

    save_to_config(town_from, town_to, date_time)
    timer_func(town_from_id, town_to_id, parsed_date)

if __name__ == "__main__":
    main()