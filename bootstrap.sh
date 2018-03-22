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

cp api-creds-telegram.json.sample api-creds-telegram.json

read -p "Do you want to run hodlmybot as a service [y/n]? " -n 1 -r
if [[ $REPLY =~ ^[Yy]$ ]]
then
	sudo cp $WORKING_DIR/init/hodlmybot.service /lib/systemd/system
	sudo systemctl enable hodlmybot 
fi

read -p "Install cron jobs [y/n]? " -n 1 -r
if [[ $REPLY =~ ^[Yy]$ ]]
then
	crontab -l > mycron
	echo "# Every hour" >> mycron
	echo "0 * * * * $WORKING_DIR/cron/cron-reddit.py >/dev/null 2>&1" >> mycron
	echo "0 * * * * $WORKING_DIR/cron/cron-cmc.py >/dev/null 2>&1">> mycron
	echo "0 * * * * $WORKING_DIR/cron/cron-twitter.py >/dev/null 2>&1" >>  mycron
	echo >> mycron
	echo "# Every week" >> mycron
	echo "0 0 * * 0 $WORKING_DIR/cron/cron-reddit-update.py >/dev/null 2>&1" >> mycron
	echo "0 0 * * 0 $WORKING_DIR/cron/cron-twitter-update.py >/dev/null 2>&1" >> mycron
	crontab mycron
	rm mycron
fi

echo
echo 'Bootstrap complete.'
echo
echo 'Remember to change the api-creds-telegram.json.sample file, and see README.md for details on how to proceed!'
echo
echo 'If you are running hodlmybot as a service you can start it with:'
echo
echo '    $ sudo service hodlmybot start'
echo
echo 'GLHF!'
echo

