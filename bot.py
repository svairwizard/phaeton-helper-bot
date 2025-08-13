import requests
from datetime import datetime, timedelta, time
from xml.etree import ElementTree
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio
import logging
from bs4 import BeautifulSoup
import pytz

#logs
if not logging.getLogger().handlers:
    logging.basicConfig(
        filename='bot.log',
        level=logging.INFO,
        format='%(asctime)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

TELEGRAM_TOKEN = 'token' 
ALPHAVANTAGE_API_KEY = 'token' 
CHAT_ID = your_id #ваш ID в тг

#cbr
def get_cbr_key_rate() -> dict:
    today = datetime.now().strftime('%Y-%m-%d')
    result = {'key_rate': None, 'date': today}
    
    try:
        url = 'https://www.cbr.ru/hd_base/keyrate/'
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        rate_table = soup.find('table', {'class': 'data'})
        
        if rate_table:
            last_row = rate_table.find_all('tr')[-1]
            result['key_rate'] = last_row.find_all('td')[1].text.strip()
    except Exception as e:
        result['error'] = f"Ошибка получения ключевой ставки: {str(e)}"
    
    return result

#weather
def get_weather() -> str:
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        today = datetime.now().strftime("%Y-%m-%d")
        
        params = {
            "latitude": 55.7558,
            "longitude": 37.6176,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "timezone": "Europe/Moscow",
            "start_date": today,
            "end_date": today
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        max_temp = data["daily"]["temperature_2m_max"][0]
        min_temp = data["daily"]["temperature_2m_min"][0]
        prob = data["daily"]["precipitation_probability_max"][0]
        
        return (
            f"Сводка на {today}\n"
            f"🌤️ Погода в Москве:\n"
            f"• 🌡️: от {min_temp}°C до {max_temp}°C\n"
            f"• ☔️ Вероятность осадков: {prob}%"
        )
    except Exception as e:
        return f"❌ Ошибка получения погоды: {str(e)}"

#USD
async def get_usd_rate() -> str:
    try:
        today = datetime.now().strftime('%d/%m/%Y')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%d/%m/%Y')
        
        today_response = requests.get(
            f"https://www.cbr.ru/scripts/XML_daily.asp?date_req={today}",
            timeout=10
        )
        today_rate = parse_usd_rate(today_response.text)
        
        yesterday_response = requests.get(
            f"https://www.cbr.ru/scripts/XML_daily.asp?date_req={yesterday}",
            timeout=10
        )
        yesterday_rate = parse_usd_rate(yesterday_response.text)
        
        change = today_rate - yesterday_rate
        trend = "↑" if change >= 0 else "↓"
        
        return (
            f"💲 Курс USD ЦБ РФ:\n"
            f"• ❇️ Сегодня: {today_rate:.2f} руб.\n"
            f"• 📊 Изменение: {trend} {abs(change):.2f} руб."
        )
    except Exception as e:
        return f"❌ Ошибка получения курса USD: {str(e)}"

def parse_usd_rate(xml_data: str) -> float:
    root = ElementTree.fromstring(xml_data)
    for valute in root.findall('Valute'):
        if valute.find('CharCode').text == 'USD':
            return float(valute.find('Value').text.replace(',', '.'))
    return 0.0

#NEFT
async def get_brent_price() -> str:
    try:
        response = requests.get(
            "https://www.alphavantage.co/query",
            params={
                'function': 'BRENT',
                'interval': 'daily',
                'apikey': ALPHAVANTAGE_API_KEY
            },
            timeout=10
        )
        data = response.json()
        
        if 'data' not in data:
            return "❌ Не удалось получить данные о нефти"
            
        today = data['data'][0]
        yesterday = data['data'][1]
        change = float(today['value']) - float(yesterday['value'])
        trend = "↑" if change >= 0 else "↓"
        
        return (
            f"🛢 Нефть Brent:\n"
            f"• ❇️ Сегодня: {today['value']} USD/барр.\n"
            f"• 📊 Изменение: {trend} {abs(change):.2f} USD"
        )
    except Exception as e:
        return f"❌ Ошибка получения цены на нефть: {str(e)}"

#result message
async def generate_daily_summary() -> str:
    weather = get_weather()
    usd_rate = await get_usd_rate()
    brent_price = await get_brent_price()
    cbr_data = get_cbr_key_rate()
    
    return (
        f"{weather}\n\n"
        f"{usd_rate}\n\n"
        f"{brent_price}\n\n"
        f"🏦 Ключевая ставка ЦБ РФ: {cbr_data.get('key_rate', 'Н/Д')}%"
    )

#/now
async def now_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        message = await update.message.reply_text("⌛ Запрашиваю актуальные данные...")
        result_message = await generate_daily_summary()
        
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=message.message_id,
            text=result_message
        )
    except Exception as e:
        await update.message.reply_text(f"⚠️ Произошла ошибка: {str(e)}")

#dailу sent
async def send_daily_message(context: ContextTypes.DEFAULT_TYPE):
    try:
        text = await generate_daily_summary()
        await context.bot.send_message(chat_id=CHAT_ID, text=text)
    except Exception as e:
        logging.error(f"Ошибка при отправке ежедневного сообщения: {str(e)}")

def main() -> None:
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("now", now_command))
    
    # 7AM
    moscow_tz = pytz.timezone("Europe/Moscow")
    time_moscow = time(hour=7, minute=0, tzinfo=moscow_tz)
    job_queue = application.job_queue
    job_queue.run_daily(
        send_daily_message,
        time=time_moscow,
        days=(0, 1, 2, 3, 4, 5, 6),
    )
    
    print("стартуем....")
    application.run_polling()

if __name__ == '__main__':
    main()
