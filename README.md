This was used once upon a time to gather some data at random to make some cool charts about league of legends players. The dependencies are out of date, the data was gathered in season 3 so that is all out of date, and the key that I checked into the repo (which I should not have done) is expired.

### Running

Put your API key in a `tokens.env` file that looks like this:

```
RIOT_API_KEY=yourr-iotapikeygoes-here-sdgr-83jg98w3983h
```

Then:

```
pipenv install
source tokens.env
pipenv run league.py
```
