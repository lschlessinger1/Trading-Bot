import traders

def get_bots(fundamentals, technical):
    ret = []
    for i in range(fundamentals):
        ret.append(MovingAverageBot())
    for i in range(technical):
        if i % 2 == 0:
            ret.append(RangeTechnical())
        else:
            ret.append(ShortLongTechnical())
    return ret

class MovingAverageBot(traders.Trader):
    name = 'fund_moving_average'

    def simulation_params(self, timesteps,
                          possible_jump_locations,
                          single_jump_probability,
                          start_belief=50.0,
                          alpha=0.9,
                          min_block_size=2,
                          start_block_size=20):
        self.timesteps = timesteps
        self.possible_jump_locations = possible_jump_locations
        self.single_jump_probability = single_jump_probability
        self.belief = start_belief
        self.alpha = alpha
        self.min_block_size = min_block_size
        self.start_block_size = start_block_size
    
    def new_information(self, info, time):
        self.belief = (self.belief * self.alpha
                       + info * 100 * (1 - self.alpha))

    def trades_history(self, trades, time):
        self.trades = trades

    def trading_opportunity(self, cash_callback, shares_callback,
                            check_callback, execute_callback,
                            market_belief):
        current_belief = (self.belief + market_belief) / 2.0
        current_belief = max(min(current_belief, 99.0), 1.0)
        bought_once = False
        sold_once = False
        block_size = self.start_block_size
        while True:
            if (not sold_once
                and (check_callback('buy', block_size)
                     < current_belief)):
                execute_callback('buy', block_size)
                bought_once = True
            elif (not bought_once
                  and (check_callback('sell', block_size)
                       > current_belief)):
                execute_callback('sell', block_size)
                sold_once = True
            else:
                if block_size == self.min_block_size:
                    break
                block_size = block_size // 2
                if block_size < self.min_block_size:
                    block_size = self.min_block_size

def optimize_shares(objective, feasible, initial_price):
    price = initial_price
    shares = 1
    cancel = True
    previous_objective = 0.0
    while True:
        feas, used_cancel = feasible(shares)
        if not feas:
            cancel = used_cancel
            break
        current_objective = objective(shares)
        if current_objective <= previous_objective:
            break
        previous_objective = current_objective
        shares += 1
    return shares - 1, cancel

def execute_max(shares, execute):
    price_per_share = None
    while price_per_share is None and shares > 0:
        price_per_share = execute(shares)
        shares -= 1
    return price_per_share, shares + 1
                    
class ShortLongTechnical(traders.Trader):
    name = 'tech_short_long'
    def simulation_params(self, timesteps,
                          possible_jump_locations,
                          single_jump_probability,
                          short_length=10, long_length=30,
                          max_long_exceed=2.0, max_short_exceed=2.0,
                          margin=0.05):
        self.short_length = short_length
        self.long_length = long_length
        self.max_long_exceed = max_long_exceed
        self.max_short_exceed = max_short_exceed
        self.margin = margin
        self.state = None
        self.execution_prices = None
        self.trade = False
        self.long_average = None
        self.short_average = None
    
    def trades_history(self, trades, time):
        def mean(lst):
            return sum(lst) / float(len(lst))
        execution_prices = [pr[0] for pr in trades]
        self.execution_prices = execution_prices
        if len(self.execution_prices) < self.long_length:
            self.trade = False
            return
        self.short_average = mean(
            self.execution_prices[-self.short_length:])
        self.long_average = mean(
            self.execution_prices[-self.long_length:])
        if self.state is None:
            self.trade = False
            if self.short_average > self.long_average:
                self.state = 'high'
            else:
                self.state = 'low'
        elif self.state == 'high':
            if (self.long_average
                > self.short_average + self.margin * self.short_average):
                self.state = 'low'
                self.trade = 'sell'
        elif self.state == 'low':
            if (self.long_average
                < self.short_average - self.margin * self.short_average):
                self.state = 'high'
                self.trade = 'buy'

    def trading_opportunity(self, cash_callback, shares_callback,
                            check_callback, execute_callback, mu):
        if self.trade == False:
            return

        execute_buy = lambda amount: execute_callback(
            'buy', amount)
        execute_sell = lambda amount: execute_callback(
            'sell', amount)
        if self.trade == 'sell':
            def objective(amount):
                execution_price = check_callback('sell', amount)
                if (execution_price
                    >= self.long_average - self.max_long_exceed
                    and execution_price
                    >= self.short_average - self.max_short_exceed
                    and execution_price < 100.0
                    and execution_price > 0.0):
                    return amount
                else:
                    return -1
            feasible = lambda amount: (amount < 200, False)
            shares, cancel = optimize_shares(
                objective, feasible, mu)
            if shares > 0:
                price_per_share, shares = execute_max(
                    shares, execute_sell)
        elif self.trade == 'buy':
            def objective(amount):
                execution_price = check_callback('buy', amount)
                if (execution_price
                    <= self.long_average + self.max_long_exceed
                    and execution_price
                    <= self.short_average + self.max_short_exceed
                    and execution_price < 100.0
                    and execution_price > 0.0):
                    return amount
                else:
                    return -1
            feasible = lambda amount: (amount < 200, False)
            shares, cancel = optimize_shares(
                objective, feasible, mu)
            if shares > 0:
                price_per_share, shares = execute_max(
                    shares, execute_buy)

class RangeTechnical(traders.Trader):
    name = 'tech_range'
    def simulation_params(self, timesteps,
                          possible_jump_locations,
                          single_jump_probability,
                          window=20, margin=0.05, max_exceed=2.0):
        self.window = window
        self.margin = margin
        self.max_exceed = max_exceed
        self.execution_prices = None
    
    def trades_history(self, trades, time):
        execution_prices = [pr[0] for pr in trades]
        self.execution_prices = execution_prices

    def trading_opportunity(self, cash_callback, shares_callback,
                            check_callback, execute_callback, mu):
        if len(self.execution_prices) < self.window + 1:
            return
        window_trades = self.execution_prices[-(self.window + 1):-1]
        min_price = min(window_trades)
        max_price = max(window_trades)
        execute_buy = lambda amount: execute_callback(
            'buy', amount)
        execute_sell = lambda amount: execute_callback(
            'sell', amount)
        if self.execution_prices[-1] > max_price + max_price * self.margin:
            def objective(amount):
                price = check_callback('buy', amount)
                if (price <= max_price + self.max_exceed
                    and price > 0.0 and price < 100.0):
                    return amount
                else:
                    return -1
            feasible = lambda amount: (amount < 200, False)
            shares, cancel = optimize_shares(
                objective, feasible, mu)
            if shares > 0:
                price_per_share, shares = execute_max(
                    shares, execute_buy)
        elif self.execution_prices[-1] < (
            min_price - min_price * self.margin):
            def objective(amount):
                price = check_callback('sell', amount)
                if (price >= min_price - self.max_exceed
                    and price < 100.0 and price > 0.0):
                    return amount
                else:
                    return -1
            feasible = lambda amount: (amount < 200, False)
            shares, cancel = optimize_shares(
                objective, feasible, mu)
            if shares > 0:
                price_per_share, shares = execute_max(
                    shares, execute_sell)
