import abc
import random

class Trader(object):
    name = 'generic'
    def simulation_params(self, timesteps,
                          possible_jump_locations,
                          single_jump_probability):
        pass
    
    def new_information(self, info, time):
        pass

    def trades_history(self, trades, time):
        pass

    @abc.abstractmethod
    def trading_opportunity(self, cash_callback, shares_callback,
                            check_callback, execute_callback, mu):
        pass

class TradingPopulation(object):
    def __init__(self, timesteps, possible_jump_locations,
                 single_jump_probability, traders,
                 user_callback=lambda trader, i:None):
        self.timesteps = timesteps
        self.possible_jump_locations = possible_jump_locations
        self.single_jump_probability = single_jump_probability
        self.active_traders = []
        self.populations = {}
        for i, trader in enumerate(traders):
            trader.simulation_params(timesteps, possible_jump_locations,
                                     single_jump_probability)
            trader_tuple = (trader, user_callback(trader, i))
            self.populations.setdefault(
                trader.name, []).append(trader_tuple)
            self.active_traders.append(trader_tuple)

    def new_information(self, get_info_callback, execution_prices,
                        round_number):
        for trader_type, traders in self.populations.iteritems():
            for trader in traders:
                trader[0].trades_history(
                    execution_prices, round_number)
                trader[0].new_information(
                    get_info_callback(), round_number)

    def get_traders(self):
        random.shuffle(self.active_traders)
        return self.active_traders

    def all_users(self, key):
        ret = []
        for trader_type, traders in self.populations.iteritems():
            ret.extend(key(trader) for trader in traders)
        return ret
