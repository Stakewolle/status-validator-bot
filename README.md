# status-validator-bot
Simple Telegram bot for Cosmos-validators tracking.

To avoid situations when, for one reason or another, you find out late that your validator is not active or has been jailed, we have created a bot. The bot will notify if validator is jailed or inactive. So you don't need to waste time searching for your validator in the long list.
 There is no need for manually tracking for your validator's status, because bot updates every 3 hours and it will notify you if there is a problem.
 
All you have to do is:
1) Start the bot
2) Add your wallets
3) Be patient untill the notification comes


Functions:
/start - welcome message and basic info
/wallet - list of your wallets and /add and /remove buttons
/add - adds new wallet
/remove - opens a menue to remove wallet

## Installation
1. Setup requirements: `pip install -r requirements.txt`
2. Set telegram bot token in env. Example:
```
POSTGRES_HOST=postgres
POSTGRES_DB_NAME=bot
POSTGRES_USER=postgres
POSTGRES_PASSWORD=000000
TOKEN=89372657520:dfsljf3534lh36hFFkjbk34534kbk6
```
3. Run main.py
