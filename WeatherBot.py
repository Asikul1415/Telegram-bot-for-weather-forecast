import requests
import re
import textwrap
import aiogram
from aiogram import Bot, types
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from bs4 import BeautifulSoup

bot = Bot(token='YOUR TOKEN')
dp = Dispatcher(bot)

weather_now_button = KeyboardButton("Погода сейчас")
weather_today_button = KeyboardButton("Погода на сегодня")
weather_tomorrow_button = KeyboardButton("Погода на завтра")
weather_for_the_week_button = KeyboardButton("Погода на неделю")

keyboard = ReplyKeyboardMarkup(resize_keyboard=True).row(weather_now_button, weather_today_button).row(
    weather_tomorrow_button, weather_for_the_week_button)


class Weather:
    def __init__(self, now=False, today=False, tomorrow=False, week=False):
        if now:
            self.soup = self.get_soup('https://www.gismeteo.ru/weather-yekaterinburg-4517/now/')
            self.temperature_now = self.get_temperature_now()[0]
            self.temperature_by_feelings = self.get_temperature_now()[1]
            self.weather_now = self.get_weather_now()
            self.wind_now = self.get_wind_now()
            self.pressure = self.get_pressure_now()
            self.humidity = self.get_humidity()
        elif today:
            self.soup = self.get_soup('https://www.gismeteo.ru/weather-yekaterinburg-4517/')
            self.min_temperature = self.get_temperature()[0]
            self.max_temperature = self.get_temperature()[1]
            self.weather_for_today = self.get_weather()
            self.middle_pressure = self.get_middle_pressure()
            self.middle_fallout = self.get_middle_fallout()
            self.middle_wind_speed = self.get_middle_wind_speed()
        elif tomorrow:
            self.soup = self.get_soup('https://www.gismeteo.ru/weather-yekaterinburg-4517/tomorrow/')
            self.min_temperature = self.get_temperature()[0]
            self.max_temperature = self.get_temperature()[1]
            self.weather_for_today = self.get_weather()
            self.middle_pressure = self.get_middle_pressure()
            self.middle_fallout = self.get_middle_fallout()
            self.middle_wind_speed = self.get_middle_wind_speed()
        elif week:
            self.soup = self.get_soup('https://www.gismeteo.ru/weather-yekaterinburg-4517/weekly/')
            print(self.soup)
            self.dates_of_week = self.get_days_and_dates_of_week("date")
            self.days_of_week = self.get_days_and_dates_of_week("day")
            self.max_temperatures = self.get_temperatures_for_week('maxt')
            self.min_temperatures = self.get_temperatures_for_week('mint')
            self.winds_speeds = self.get_winds_speeds_for_week()
            self.winds_directions = self.get_winds_directions_for_week()
            self.fallout = self.get_fallout_for_week()
            self.humidity = self.get_humidity_for_week()

    def get_soup(self, url):
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})

        return BeautifulSoup(response.text, 'lxml')

    # WEATHER NOW
    def get_temperature_now(self):
        temperature = self.soup.find_all('span', {'class': 'unit unit_temperature_c'})

        return 'На улице: ' + temperature[0].text + '°', 'По ощущениям: ' + temperature[1].text + '°'

    def get_weather_now(self):
        return "Погода: " + self.soup.find('div', {'class': 'now-desc'}).text

    def get_wind_now(self):
        wind_temp = self.soup.find('div', {'class': 'unit unit_wind_m_s'}).text

        return "Ветер: " + re.sub(r'(\d+)(м/c)(\D+)', r'\1 \2 \3', wind_temp)

    def get_pressure_now(self):
        pressure_temp = self.soup.find('div', {'class': 'unit unit_pressure_mm_hg_atm'}).text

        return "Давление: " + re.sub(r'(\d+)(\D+)', r'\1 \2', pressure_temp)

    def get_humidity(self):
        humidity_temp = self.soup.find('div', {'class': 'now-info-item humidity'}).text

        return re.sub(r'(\D+)(\d+)(%)', r'\1 \2 \3', humidity_temp)

    # WEATHER FOR TODAY and TOMORROW
    def get_temperature(self):
        temp = self.soup.find_all('span', {'class': 'unit_temperature_c'})

        return "Минимальная температура: " + temp[2].text + "°", "Максимальная температура: " + temp[3].text + "°"

    def get_weather(self):
        weather = self.soup.find('a', {'class': 'weathertab weathertab-block tooltip'})

        return weather['data-text']

    def get_middle_pressure(self):
        pressures = self.soup.find_all('span', {'class': 'unit unit_pressure_mm_hg_atm'})
        sum = 0
        i = 1
        while i < len(pressures):
            sum += float(re.sub(r'(\d+)(\D+)', r'\1', pressures[i].text))
            i += 1

        return "Среднее давление: " + str(int(sum / (len(pressures) - 1))) + " мм рт.ст"

    def get_middle_wind_speed(self):
        wind = self.soup.find('div', {'class': 'widget-row widget-row-wind-speed row-with-caption'})
        winds = wind.find_all('div', {'class': 'row-item'})
        sum = 0
        i = 0
        while i < len(winds):
            sum += int(re.sub(r'(\d+)( )(\d+)', r'\1', winds[i].text))
            i += 1

        return "Средняя скорость ветра: " + str(int(sum / (len(winds)))) + " м/с"

    def get_middle_fallout(self):
        fallout_temp = self.soup.find('div', {'class': 'widget-row widget-row-icon-snow row-with-caption'})
        fallout = fallout_temp.find_all('div', {'class': 'row-item'})
        i = 0
        sum = 0
        while i < len(fallout):
            if ',' in fallout[i].text:
                sum += float(fallout[i].text.replace(',', '.'))
            elif fallout[i].text == "—":
                i += 1
                continue
            else:
                sum += float(fallout[i].text)
            i += 1

        return "Осадки: " + str(sum) + "мм"

    # WEATHER FOR THE WEEK

    def get_days_and_dates_of_week(self,class_name):
        temp = self.soup.find('div', {'class': 'widget-row widget-row-days-date'})

        return temp.find_all('div', {'class': {class_name}})

    def get_temperatures_for_week(self,_class):
        temp = self.soup.find_all('div', {'class': {_class}})
        temperatures = []
        for temperature in temp:
            temperatures.append(temperature.find('span', {'class': 'unit unit_temperature_c'}))

        return temperatures

    def get_fallout_for_week(self):
        temp = self.soup.find('div', {'class': 'widget-row widget-row-precipitation-bars row-with-caption'})

        return temp.find_all('div', {'class': 'row-item'})

    def get_winds_speeds_for_week(self):
        temp = self.soup.find('div', {'class': 'widget-row widget-row-wind-speed row-with-caption'})
        winds_temp = temp.find_all('div', {'class': 'row-item'})
        winds = []
        for wind in winds_temp:
            winds.append(wind.find('span', {'class': 'wind-unit unit unit_wind_m_s'}))

        return winds

    def get_winds_directions_for_week(self):
        directions_temp = self.soup.find('div', {'class': 'widget-row widget-row-wind-direction row-with-caption'})

        return directions_temp.find_all('div', {'class': 'row-item'})

    def get_humidity_for_week(self):
        humidity_temp = self.soup.find('div', {'class': 'widget-row widget-row-humidity row-with-caption'})
        humidity_for_week = []
        for humidity in humidity_temp:
            humidity_for_week.append(humidity)

        return humidity_for_week


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await bot.send_message(message.chat.id, f"Привет, {message.from_user.first_name}!" + "\nЯ бот погоды,"
                                        "который используется для тестирования парсинга с сайта gismeteo.",
                                        reply_markup=keyboard)


@dp.message_handler(Text(equals="Погода сейчас"))
async def weather_now(message: types.Message):
    weather = Weather(now=True)
    text = f"""\
    Сейчас:

    {weather.temperature_now}
    {weather.temperature_by_feelings}
    {weather.weather_now}
    {weather.wind_now}
    {weather.pressure}
    {weather.humidity}"""

    await bot.send_message(message.chat.id, textwrap.dedent(text))


@dp.message_handler(Text(equals="Погода на сегодня"))
async def weather_today(message: types.Message):
    weather = Weather(today=True)
    text = f"""\
    Сегодня: 

    {weather.weather_for_today}
    {weather.max_temperature}
    {weather.min_temperature}
    {weather.middle_pressure}
    {weather.middle_wind_speed}
    {weather.middle_fallout}
    """
    await bot.send_message(message.chat.id, textwrap.dedent(text))


@dp.message_handler(Text(equals="Погода на завтра"))
async def weather_today(message: types.Message):
    weather = Weather(tomorrow=True)
    text = f"""\
    Завтра: 

    {weather.weather_for_today}
    {weather.max_temperature}
    {weather.min_temperature}
    {weather.middle_pressure}
    {weather.middle_wind_speed}
    {weather.middle_fallout}
    """
    await bot.send_message(message.chat.id, textwrap.dedent(text))


@dp.message_handler(Text(equals="Погода на неделю"))
async def weather_for_the_week(message: types.Message):
    weather = Weather(week=True)
    i = 0
    while i < 7:
        text = f"""\
        {weather.dates_of_week[i].text} {weather.days_of_week[i].text}\
    
        \nМаксимальная температура: {weather.max_temperatures[i].text}°\
        \nМинимальная температура: {weather.min_temperatures[i].text}°\
        \nВетер: {weather.winds_speeds[i].text} м/с {weather.winds_directions[i].text}\
        \nОсадки: {weather.fallout[i].text} мм\
        \nВлажность: {weather.humidity[i].text} %
        """
        await bot.send_message(message.chat.id, textwrap.dedent(text))
        i += 1


if __name__ == '__main__':
    executor.start_polling(dp)
