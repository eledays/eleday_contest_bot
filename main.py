import telebot
from config import TOKEN, ADMIN_ID
from datetime import datetime

from databaser import Databaser


bot = telebot.TeleBot(TOKEN, parse_mode='html')
db = Databaser()


@bot.message_handler(commands=['start'])
def start_message(message):
    if not message.text.split()[1:]:
        bot.send_message(message.chat.id, 'Привет ✌️ ')
        return 
    
    contest_id = message.text.split()[1]
    if contest_id.isdigit():
        contest = db.get_contest(contest_id)
        if not contest:
            bot.send_message(message.chat.id, 'Конкурс не найден')
            return
    else:
        bot.send_message(message.chat.id, 'Недействительная ссылка')
        return
    
    status = db.get_contest_status(contest_id)
    text = 'Ошибка'
    markup_inline = None

    if not status[0] and status[1] == 'future':
        if contest["start_datetime"] is not None:
            start = f'Начало: {contest["start_datetime"].strftime("%d.%m.%Y %H:%M")}'
        else:
            start = 'Скоро начало'

        text = f'Этот конкурс ещё не начался. {start}\n\n'\
               f'Пока можешь ознакомиться с правилами:\n{contest["rules"]}'
    elif not status[0] and status[1] == 'past':
        text = f'Этот конкурс уже завершен {contest["end_datetime"].strftime("%d.%m.%Y %H:%M")}'
    elif status[0]:    
        text = f'Привет! Конкурс "{contest["name"]}" уже идёт, давай с нами. Перед началом ознакомься с информацией по конкурсу\n\n'\
               f'Описание:\n{contest["desc"]}\n\n'\
               f'Правила:\n{contest["rules"]}\n\n'\
               f'<i>Нажимая кнопку "Начать", Вы принимаете правила, описанные выше</i>'
    
        markup_inline = telebot.types.InlineKeyboardMarkup()
        markup_inline.add(
            telebot.types.InlineKeyboardButton(text='Начать', callback_data=f'start_{contest_id}')
        )

    bot.send_message(message.chat.id, text, reply_markup=markup_inline)
        


@bot.message_handler(commands=['help'])
def help_message(message):
    text = '<b>Управление</b>\n'\
           '/start - старт'

    if message.chat.id == ADMIN_ID:
        text += '\n\n<b>Режим админа</b>\n'\
                '/create_contest - создать конкурс\n'\
                '/start_contest <id> - старт конкурса\n'

    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['create_contest'])
def create_contest(message, step=0, info={}):
    if message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, 'Ошибка доступа')
        return
    if message.text == '/cancel':
        bot.send_message(message.chat.id, 'Отменено')
        return
    
    if step == 0:
        bot.send_message(message.chat.id, 'Отправь название')
        bot.register_next_step_handler(message, create_contest, step=1, info=info)
    elif step == 1:
        info['name'] = message.text
        bot.send_message(message.chat.id, 'Отправь описание')
        bot.register_next_step_handler(message, create_contest, step=2, info=info)
    elif step == 2:
        info['desc'] = message.text
        bot.send_message(message.chat.id, 'Отправь правила')
        bot.register_next_step_handler(message, create_contest, step=3, info=info)
    elif step == 3:
        info['rules'] = message.text
        bot.send_message(message.chat.id, 'Отправь следующие данные (необязательно, /none):\n\nstart_datetime дд.мм.гггг чч:мм\nlength_check (0 or 1)\none_solution (0 or 1)\nend_datetime дд.мм.гггг')
        bot.register_next_step_handler(message, create_contest, step=4, info=info)
    elif step == 4:
        if message.text != '/none':
            try:
                lines = message.text.split('\n')
                if len(lines) == 1:
                    info['start_datetime'] = datetime.strptime(lines[0], '%d.%m.%Y %H:%M')
                else:
                    info['start_datetime'] = datetime.strptime(lines[0], '%d.%m.%Y %H:%M')
                    info['length_check'] = bool(lines[1])
                    info['one_solution'] = bool(lines[2])
                    info['end_datetime'] = datetime.strptime(lines[3], '%d.%m.%Y %H:%M')
            except Exception as error:
                bot.send_message(message.chat.id, str(error) + '\n\nОтправь ещё раз')
                bot.register_next_step_handler(message, create_contest, step=4, info=info)
                return
        
        contest_id = db.create_contest(**info)
        info = db.get_contest(contest_id)
        bot.send_message(message.chat.id, f'<b>Конкурс создан</b>\n\n' + '\n'.join([f'{k}: {v}' for k, v in info.items()]) + 
                         f'\n\n/start_contest {contest_id} - начать конкурс')


@bot.message_handler(commands=['start_contest'])
def start_contest(message):
    if message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, 'Ошибка доступа')
        return

    try:
        _, n = message.text.split(' ')
        n = int(n)
        db.start_contest(n)
        bot.send_message(message.chat.id, f'Конкурс запущен\n\nСсылка для участия: https://t.me/eleday_contest_bot?start={n}')
        
    except Exception as error:
        bot.send_message(message.chat.id, str(error), parse_mode='markdown')


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data.startswith('start_'):
        contest_id = int(call.data.split('_')[1])
        bot.send_message(call.from_user.id, '*Текущие резы*')
        bot.send_message(call.from_user.id, 'Отправь свой код')
    


bot.infinity_polling()
