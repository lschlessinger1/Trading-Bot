import abc
import copy
import marketmaker

class MarketMaker(object):
    @abc.abstractmethod
    def execute(self, buysell, quantity, user, cancel=False):
        pass

    @abc.abstractmethod
    def price_check(self, buysell, quantity):
        pass

    def _price_per_share(self, quantity, total_cost):
        return marketmaker.prediction_limit(
            float(total_cost) / float(quantity))

class User(object):
    def __init__(self, cash, initial_shares, name=None):
        self.cash = float(cash)
        self.initial_cash = self.cash
        self.shares = copy.deepcopy(initial_shares)
        self.initial_shares = copy.deepcopy(initial_shares)
        self.name = name

    def change_cash(self, amount):
        self.cash += amount

    def change_portfolio(self, stock, amount):
        self.shares[stock.id] = self.shares.get(stock.id, 0) + amount

    def profit(self, stock_values):
        profit = 0.0
        for stock_id in self.shares.keys():
            profit += stock_values[stock_id] * (
                self.shares[stock_id] - self.initial_shares.get(
                    stock_id, 0))
        profit += self.cash - self.initial_cash
        return profit

class LMSR(MarketMaker):
    def __init__(self, max_loss, quantity_outstanding=0, mu=50.0,
                 user_account=None):
        self.max_loss = float(max_loss)
        self.quantity_outstanding = float(quantity_outstanding)
        self.mu = float(mu)
        if user_account:
            self.user_account = user_account
        else:
            self.user_account = User(0, {})
        self.cancels = []
        self.id = hash(self)

    def _get_update(self, buysell, quantity):
        (offered_price, new_quantity_outstanding,
         new_mu) = marketmaker.hansonPriceCheck(
            transaction=buysell, qtyToBuySell=quantity,
            qtyOutstanding=self.quantity_outstanding,
            maxLoss=self.max_loss)
        return (self._price_per_share(quantity, offered_price),
                new_quantity_outstanding, new_mu)

    def price_check(self, buysell, quantity):
        price_per_share, _, _ = self._get_update(
            buysell, quantity)
        return price_per_share

    def execute(self, buysell, quantity, user, cancel=False):
        if cancel:
            return
        (offered_price, self.quantity_outstanding,
         self.mu) = self._get_update(buysell, quantity)
        return offered_price

def check(buysell, quantity, stock_maker, user):
    return stock_maker.price_check(buysell, quantity)

def execute(buysell, quantity, stock_maker, user):
    '''Executes a user's order if the market state is consistent'''
    costPerShare = stock_maker.price_check(buysell, quantity)
    offeredPrices = costPerShare * quantity

    if not 0.01 < costPerShare and buysell == 'sell':
        cancel(buysell, quantity, stock_maker, user)
        return None
    elif not costPerShare < 100 and buysell == 'buy':
        cancel(buysell, quantity, stock_maker, user)
        return None

    user_power = user.cash
    
    current_position = user.shares.get(stock_maker.id, 0)
    
    if buysell=='buy':
        trade_position = quantity
    if buysell=='sell':
        trade_position = -1 * quantity
    
    allow_trade = True

    if allow_trade == False:
        return None

    executed_price = stock_maker.execute(buysell, quantity, user)
    # Preliminary processing
    if buysell=="sell":
        offeredPrices = offeredPrices * -1
        quantity = quantity * -1

    maker_account = stock_maker.user_account
    # Change cash values
    user.change_cash(-1*offeredPrices)
    maker_account.change_cash(offeredPrices)
    
    # Change holdings
    user.change_portfolio(stock_maker, quantity)
    maker_account.change_portfolio(stock_maker, -1*quantity)
    return executed_price

def cancel(buysell, quantity, stock_maker, user):
    stock_maker.cancels.append(user)
    stock_maker.execute(buysell, quantity, user, cancel=True)

class LMSRFactory(object):
    def __init__(self, b):
        self.b = b
        self.name = 'LMSR (b=%1.2f)' % (b,)
        
    def make(self):
        return LMSR(self.b)
