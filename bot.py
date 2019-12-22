import os

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, Filters, CallbackQueryHandler

import logging
from rpiradioalarm import ApiHelper, COMMANDS, RpiArgumentParser

from helper.RadioResponseParser import RadioResponseParser

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


class RpiAlarmBot(object):
    default_button_list = [
        InlineKeyboardButton("Get Alarms", callback_data=COMMANDS.GET_ALARMS.value),
    ]

    def __init__(self, token):
        self.updater = Updater(token=token, use_context=True)
        self.dispatcher = self.updater.dispatcher
        default_filter = Filters.user(user_id=int(os.getenv('ALLOWED-USER')))
        self.dispatcher.add_handler(CommandHandler('start', self.start, default_filter))
        self.dispatcher.add_handler(CommandHandler('stop_radio', self.stop_radio, default_filter))
        self.dispatcher.add_handler(CommandHandler('start_radio', self.start_radio, default_filter))
        self.dispatcher.add_handler(CommandHandler('change_alarm', self.change_alarm, default_filter))
        self.dispatcher.add_handler(CallbackQueryHandler(self.handle_button, default_filter))
        self.api_helper = ApiHelper()
        self.argument_parser = RpiArgumentParser()
        self.response_parser = RadioResponseParser()

    def start(self, update, context):

        reply_markup = InlineKeyboardMarkup(self.build_menu(self.default_button_list, n_cols=2))
        context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!",
                                 reply_markup=reply_markup)

    def run(self):
        self.updater.start_polling(clean=True)

    def change_alarm(self, update, context):
        str = COMMANDS.CHANGE_ALARM.value + ' ' + ' '.join(context.args)
        cmd, args = self.argument_parser.parse_arguments(str)
        result = self.api_helper.do_command(cmd=COMMANDS.CHANGE_ALARM, args=args)
        context.bot.send_message(chat_id=update.effective_chat.id, text=result)

    def handle_button(self, update, context):
        query = update.callback_query
        cmd, args = self.argument_parser.parse_arguments(query.data)
        text_resp = self.api_helper.do_command(cmd=cmd, args=args)
        button_list = []
        if cmd == COMMANDS.GET_ALARMS:
            for idx, alarm in enumerate(text_resp):
                button_list.append(InlineKeyboardButton("Get Alarm " + str(idx) + ': ' + alarm['name'],
                                                        callback_data=COMMANDS.GET_ALARM.value + ' ' + str(idx)))
                base_callback = COMMANDS.CHANGE_ALARM.value + str(idx)
                if alarm['on'] == True:
                    btn_text = 'Turn off'
                    callback_data = base_callback + ' on false'
                else:
                    btn_text = 'Turn on'
                    callback_data = base_callback + ' on true'

                button_list.append(InlineKeyboardButton(btn_text, callback_data=callback_data))
            text_resp = 'got all alarms'
        else:
            text_resp = self.response_parser.parse_response(cmd, args, text_resp)
        reply_markup = InlineKeyboardMarkup(
            self.build_menu(button_list, header_buttons=self.default_button_list, n_cols=2))

        context.bot.send_message(text=text_resp, chat_id=query.message.chat_id,
                                 reply_markup=reply_markup)

    @staticmethod
    def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
        menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
        if header_buttons:
            menu.insert(0, header_buttons)
        if footer_buttons:
            menu.append(footer_buttons)
        return menu

    def stop_radio(self, update, context):
        result = self.api_helper.do_command(COMMANDS.STOP_RADIO, '')
        context.bot.send_message(chat_id=update.effective_chat.id, text=result)

    def start_radio(self, update, context):
        result = self.api_helper.do_command(COMMANDS.START_RADIO, '')
        context.bot.send_message(chat_id=update.effective_chat.id, text=result)


load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
client = RpiAlarmBot(TOKEN)
client.run()
