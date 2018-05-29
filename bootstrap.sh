#!/bin/bash
#
# Ubuntu bootstrap script
#

WORKING_DIR=/opt/hodlmybot
REL=$(cat /etc/issue | head -n +1 | awk '{print $1}')

sudo apt-get -y install python3-venv

python3 -m venv .

. ./bin/activate

pip install -r requirements.txt

if [ ! -f api-creds-bot.json ]; then
	cp api-creds-bot.sample api-creds-bot.json
if [ ! -f api-creds-twitter.json ]; then
	cp api-creds-twitter.sample api-creds-twitter.json

read -p "Do you want to run hodlmybot-telegram as a service [y/n]? " -n 1 -r
if [[ $REPLY =~ ^[Yy]$ ]]
then
	sudo cp $WORKING_DIR/init/hodlmybot-telegram.service /lib/systemd/system
	sudo systemctl enable hodlmybot-telegram
fi

read -p "Do you want to run hodlmybot-slack as a service [y/n]? " -n 1 -r
if [[ $REPLY =~ ^[Yy]$ ]]
then
	sudo cp $WORKING_DIR/init/hodlmybot-slack.service /lib/systemd/system
	sudo systemctl enable hodlmybot-slack
fi

read -p "Do you want to run hodlmybot-discord as a service [y/n]? " -n 1 -r
if [[ $REPLY =~ ^[Yy]$ ]]
then
	sudo cp $WORKING_DIR/init/hodlmybot-discord.service /lib/systemd/system
	sudo systemctl enable hodlmybot-discord
fi

read -p "Install cron jobs [y/n]? " -n 1 -r
if [[ $REPLY =~ ^[Yy]$ ]]
then
	crontab -l > mycron
	echo "# Every hour" >> mycron
	echo "0 * * * * $WORKING_DIR/hodlcore/updater.py >/dev/null 2>&1" >> mycron
	# echo "# Every week" >> mycron
	# echo "0 0 * * 0 $WORKING_DIR/hodlcore/updater.py >/dev/null 2>&1" >> mycron
	crontab mycron
	rm mycron
fi

echo
echo 'Bootstrap complete.'
echo
echo 'Remember to change the api-creds-bot.json and api-creds-twitter.json files, and see README.md for details on how to proceed!'
echo
echo 'If you are running hodlmybots as services you can start it with:'
echo
echo '    $ sudo service hodlmybot-telegram start'
echo '    $ sudo service hodlmybot-slack start'
echo
echo 'HODL!'
echo

