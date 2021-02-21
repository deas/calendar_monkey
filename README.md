# Calendar 🐒 - Resilience all the way down!

!["Netflix's Chaos Monkey tool, but instead of randomly killing containers it randomly cancels meetings on my calendar"](./calendar_monkey.png)
[@magiceldridge on twitter](https://twitter.com/magiceldridge/status/1362069116148994051?s=09)

## Prerequisites
- Dependencies : `pip install -r requirements.txt`
- Microsoft Graph Access : See [`./calendar_monkey_sample.json`](./calendar_monkey_sample.json) and `Calendars.ReadWrite` permission

## Usage
```sh
cp ./calendar_monkey_sample.json ./calendar_monkey.json
# Set proper values in calendar_monkey.json
python3 ./main.py cancel-entries --help
python3 ./main.py cancel-entries
```
