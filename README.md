# Trading-Bot
A trading strategy for prediction markets mediated by the logarithmic market scoring rule (LMSR) market maker

To run the simulation:
  `python my_bot.py`

You can choose between plotting a single simulation and printing
aggregate statistics for multiple simulations by
commenting/uncommenting the appropriate lines in `main()`.

Required Python packages:
  - numpy
  - matplotlib

In general, the line:

`bots.extend(other_bots.get_bots(num_fundamentals, num_technical))`

...will create a simulation with 1 + `num_fundamentals` + `num_technical`
traders including your bot. You can include multiple copies of your
bot or other bots in the simulation by adding them to the list with
`bots.append` (for a single bot) or `bots.extend` (for a list of bots).

`other_bots.py` includes one type of fundamentals trader and two types
of technical traders (`get_bots()` splits `num_technical` evenly between
these two types). The technical traders use the price history only,
and do not make money on average: they simulate noise traders which we
often see in real markets.
