#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import logging
import toml
import telegram

from telegram.ext import Updater, CommandHandler, Job
from PIL import Image
from io import BytesIO

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

channel = "" # CHANNEL PLZ
telegram_api_token = "" # KEY PLZ
update_time = 300
config_file = './config.toml'

def model_check(bot, job):
	logger.info(f'Updating . . . (Interval {update_time}s/update)')
	logger.info(f'Loading source file at {config_file}.')
	config = toml.load(config_file)
	
	
	for m in config['sources']:
		model = config['sources'][m]

		r = requests.get(model['url'])
		modified = r.headers['Last-Modified']
		
		# Get photo ready for sending to Telegram
		updated_image = Image.open(BytesIO(r.content))
		image = BytesIO()
		image.name = 'updated.png'
		updated_image.save(image, 'PNG')
		image.seek(0)
		
		if model['modified'] == modified:
			logger.info(f"No update found for {model['name']}")
		else:
			logger.info(f"{model['name']} updated at {modified}, posting to channel")
			config['sources'][m]['modified'] = modified # Update last modified date to check against later
			bot.send_photo(chat_id=channel, photo=image, caption=f"{model['name']} at {modified}")
	
	with open(config_file, 'w') as f:
		f.write(toml.dumps(config))
	logger.info(f'Updated source file at {config_file}')
	
def get_model(bot, update):
	config = toml.load(config_file)
	keyboard = []
	
	for m in config['sources']:
		keyboard.append([telegram.KeyboardButton(text=f'/show_model {m}')])
		
	reply_markup = telegram.ReplyKeyboardMarkup(keyboard)
	update.message.reply_text(text="Please select a model to view", reply_markup=reply_markup)
	
def show_model(bot, update, args):
	config = toml.load(config_file)
	requested_model = args[0]
	valid_models = []
	
	for m in config['sources']:
		valid_models.append(m)
		
	if requested_model in valid_models:
		name = config['sources'][requested_model]['name']
		url = config['sources'][requested_model]['url']
		modified = config['sources'][requested_model]['modified']
		
		r = requests.get(url)
		# Get photo ready for sending to Telegram
		updated_image = Image.open(BytesIO(r.content))
		image = BytesIO()
		image.name = 'updated.png'
		updated_image.save(image, 'PNG')
		image.seek(0)
		
		update.message.reply_photo(photo=image, caption=f"{name} at {modified}")
	
		
def get_help(bot, update):
	update.message.reply_text('Usage: /models - List available models')
	
def error(bot, update, error):
	logging.warning('Update "%s" caused error "%s"' % (update, error))
    
def main():
	updater = Updater(token=telegram_api_token)
	
	# Run update function repeatedly
	j = updater.job_queue
	j.run_repeating(model_check, interval=update_time, first=0)
	
	updater.dispatcher.add_handler(CommandHandler('help', get_help))
	updater.dispatcher.add_handler(CommandHandler('models', get_model))
	updater.dispatcher.add_handler(CommandHandler('show_model', show_model, pass_args=True))
	updater.dispatcher.add_error_handler(error)
	updater.start_polling()
	updater.idle()

if __name__ == '__main__':
	main()
