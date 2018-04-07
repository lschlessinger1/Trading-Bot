import random
import prices
import traders
import information

class Flag(object):
    def __init__(self, default=False):
        self.value = default

class Log(object):
    def __init__(self):
        self.events = []
        self.beliefs = []
        self.execution_prices = []

    def event(self, time, event_type, user, buysell, quantity, mu,
              other=None):
        self.events.append((time, event_type, user.name, buysell, quantity,
                            other))
        if event_type == 'execute' and other is not None:
            self.execution_prices.append((other, buysell, quantity, mu))

    def filter(self, event_type):
        return [e for e in self.events if e[1] == event_type]

def make_cash_callback(user):
    def cash_callback():
        return user.cash
    return cash_callback

def make_shares_callback(user, market):
    def shares_callback():
        return user.shares.get(market.id, 0)
    return shares_callback

def make_check_callback(market_maker, user, flag, log, time):
    def check_callback(buysell, quantity):
        assert buysell in ['buy', 'sell']
        assert quantity > 0
        flag.value = True
        per_share = prices.check(buysell, quantity, market_maker, user)
        log.event(time, 'check', user, buysell, quantity, market_maker.mu,
                  other=per_share)
        return per_share
    return check_callback

def make_execute_callback(market_maker, user, flag, log, time):
    def execute_callback(buysell, quantity):
        assert buysell in ['buy', 'sell']
        assert quantity > 0
        flag.value = True
        previous_mu = market_maker.mu
        success = prices.execute(buysell, quantity, market_maker, user)
        log.event(time, 'execute', user, buysell, quantity,
                  previous_mu, other=success)
        return success
    return execute_callback

class Simulation(object):
    def __init__(self, timesteps, market_fact, trader_list,
                 initial_cash=0, initial_shares=0,
                 jump_probability=None, initial_p=None,
                 spread_calculations=None):
        self.traders = trader_list
        self.possible_jump_locations = [a for a in range(timesteps)]
        if jump_probability is None:
            self.jump_probability = 1.0 / float(len(
                    self.possible_jump_locations))
        else:
            self.jump_probability = jump_probability
        self.initial_cash = initial_cash
        self.initial_shares = initial_shares
        self.timesteps = timesteps
        self.market_fact = market_fact
        self.p_vec = None
        self.user_list = None
        self.liqudiation = None
        self.market_maker_user = None
        self.log = Log()
        self.initial_p = initial_p
        
    def simulate(self):
        market = self.market_fact.make()
        def user_callback(trader, i):
            return prices.User(self.initial_cash,
                               {market.id:self.initial_shares},
                               name='%d (%s)' % (i, trader.name))
        trading_bots = traders.TradingPopulation(
            self.timesteps, self.possible_jump_locations,
            self.jump_probability, self.traders,
            user_callback=user_callback)
        binom = information.BinomialDraws(self.initial_p)
        p_vec = []
        for i in range(self.timesteps):
            if random.random() < self.jump_probability:
                binom.do_jump()
            p_vec.append(binom._p)
            self.log.beliefs.append((i, market.mu))
            if binom._p == 1.0 or binom._p == 0.0:
                break
            trading_bots.new_information(
                binom.get_draw,
                self.log.execution_prices, i)
            active_traders = trading_bots.get_traders()
            for trader, trader_user in active_traders:
                check_flag = Flag()
                execute_flag = Flag()
                trader.trading_opportunity(
                    make_cash_callback(trader_user),
                    make_shares_callback(trader_user, market),
                    make_check_callback(market, trader_user,
                                        check_flag, self.log, i),
                    make_execute_callback(market, trader_user,
                                          execute_flag, self.log, i),
                    market.mu)
        self.p_vec = p_vec
        self.user_list = trading_bots.all_users(
            lambda trader:(trader[0].name, trader[1]))
        self.liquidation = {market.id:100.0 * p_vec[-1]}
        self.market_maker_user = market.user_account

    def profits_by_user(self):
        assert self.user_list is not None
        ret = {self.market_fact.name:[self.market_maker_user.profit(
                self.liquidation)]}
        for trader_name, user in self.user_list:
            ret.setdefault(trader_name, []).append(
                user.profit(self.liquidation))
        for trader_name, profit_list in ret.iteritems():
            ret[trader_name] = sum(profit_list)
        return ret
