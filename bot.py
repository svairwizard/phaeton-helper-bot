import os
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import logging

# указываем токены
TELEGRAM_TOKEN = 'ваш_тг_токен'
ALPHAVANTAGE_API_KEY = 'ваш_токен_альфы'

# логгирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def get_weather() -> str:
    """Получает погоду в Москве через Open-Meteo API"""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        'latitude': 55.7558,
        'longitude': 37.6176,
        'hourly': 'temperature_2m,precipitation_probability',
        'forecast_days': 1,
        'timezone': 'Europe/Moscow'
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        hourly = data['hourly']
        times = hourly['time']
        temps = hourly['temperature_2m']
        precip = hourly['precipitation_probability']
        
        temp = temps[7]
        prob = precip[7]
        
        return f"Приветствую 👋\n📍Погода в Москве:\n 🌡️Температура: {temp}°C\n ☔️Вероятность осадков: {prob}%"
    except Exception as e:
        logger.error(f"Ошибка при получении погоды: {e}")
        return "Не удалось получить данные о погоде"

def get_usd_rate() -> str:
    """Получает курс доллара от ЦБ РФ"""
    today = datetime.now().strftime('%d/%m/%Y')
    yesterday = (datetime.now() - timedelta(days=2)).strftime('%d/%m/%Y')
    
    try:
        # Сегодняшний курс
        today_url = f"https://www.cbr.ru/scripts/XML_daily.asp?date_req={today}"
        response = requests.get(today_url)
        today_rate = parse_usd_rate(response.text)
        
        # Вчерашний курс
        yesterday_url = f"https://www.cbr.ru/scripts/XML_daily.asp?date_req={yesterday}"
        response = requests.get(yesterday_url)
        yesterday_rate = parse_usd_rate(response.text)
        
        change = today_rate - yesterday_rate
        trend = "↑" if change >= 0 else "↓"
        
        return (f"💲Курс USD ЦБ РФ:\n"
                f"Сегодня: {today_rate:.2f} руб.\n"
                f"Вчера: {yesterday_rate:.2f} руб.\n"
                f"Изменение: {trend} {abs(change):.2f} руб.")
    except Exception as e:
        logger.error(f"Ошибка при получении курса USD: {e}")
        return "Не удалось получить курс USD"

def parse_usd_rate(xml_data: str) -> float:
    """Парсит XML от ЦБ РФ для получения курса USD"""
    from xml.etree import ElementTree
    
    root = ElementTree.fromstring(xml_data)
    for valute in root.findall('Valute'):
        if valute.find('CharCode').text == 'USD':
            return float(valute.find('Value').text.replace(',', '.'))
    return 0.0

def get_brent_oil() -> str:
    """Получает курс нефти Brent через Alpha Vantage API"""
    try:
        url = "https://www.alphavantage.co/query"
        params = {
            'function': 'BRENT',
            'interval': 'daily',
            'apikey': ALPHAVANTAGE_API_KEY
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        # Получаем последние 2 записи (сегодня и вчера)
        last_two = data['data'][:2]
        today = last_two[0]
        yesterday = last_two[1]
        
        change = float(today['value']) - float(yesterday['value'])
        trend = "↑" if change >= 0 else "↓"
        
        return (f"🛢 Цена нефти Brent:\n"
                f"Сегодня: {today['value']} USD/баррель\n"
                f"Вчера: {yesterday['value']} USD/баррель\n"
                f"Изменение: {trend} {abs(change):.2f} USD")
    except Exception as e:
        logger.error(f"Ошибка при получении цены на нефть: {e}")
        return "Не удалось получить цену на нефть Brent"

def send_daily_update(context: CallbackContext) -> None:
    """Отправляет ежедневное обновление в 7 утра"""
    chat_id = context.job.context
    message = format_message()
    context.bot.send_message(chat_id=chat_id, text=message)

def format_message() -> str:
    """Форматирует все данные в одно сообщение"""
    weather = get_weather()
    usd = get_usd_rate()
    oil = get_brent_oil()
    
    return f"{weather}\n\n{usd}\n\n{oil}"

def start(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    update.message.reply_text(f"Привет {user.first_name}! Вас приветствует Фаэтон!\n"
                             "Используй /now для актуальной информации.")

def now(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /now"""
    message = format_message()
    update.message.reply_text(message)

def setup_job_queue(update: Update, context: CallbackContext) -> None:
    """Настраивает ежедневную отправку в 7 утра"""
    chat_id = update.message.chat_id
    
    # Удаляем старые задания для этого чата
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in current_jobs:
        job.schedule_removal()
    
    # Добавляем новое задание
    context.job_queue.run_daily(
        send_daily_update,
        time=datetime.strptime('07:00', '%H:%M').time(),
        days=(0, 1, 2, 3, 4, 5, 6),
        context=chat_id,
        name=str(chat_id)
    )
    
    update.message.reply_text("Ежедневные обновления настроены на 7:00 утра!")

def error_handler(update: Update, context: CallbackContext) -> None:
    """Логирует ошибки"""
    logger.error(msg="Исключение при обработке команды:", exc_info=context.error)

def main() -> None:
    """Запуск бота"""
    updater = Updater(TELEGRAM_TOKEN)
    dp = updater.dispatcher
    
    # Обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("now", now))
    dp.add_handler(CommandHandler("setup", setup_job_queue))
    
    # Обработчик ошибок
    dp.add_error_handler(error_handler)
    
    # Запуск бота
    updater.start_polling()
    logger.info("Бот запущен...")
    updater.idle()

if __name__ == '__main__':
    main()
