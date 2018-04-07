import other_bots
import traders
import run_experiments
import plot_simulation
import statsmodels.stats.proportion as statistics


class MyBot(traders.Trader):
    name = 'my_bot'

    def simulation_params(self, timesteps,
                          possible_jump_locations,
                          single_jump_probability):
        """Receive information about the simulation."""
        # Number of trading opportunities
        self.timesteps = timesteps
        # A list of timesteps when there could be a jump
        self.possible_jump_locations = possible_jump_locations
        # For each of the possible jump locations, the probability of
        # actually jumping at that point. Jumps are normally
        # distributed with mean 0 and standard deviation 0.2.
        self.single_jump_probability = single_jump_probability
        # A place to store the information we get
        self.information = []

        # the bot's belief of p_i (starting in the middle, which is 50)
        self.belief = 50.0
        # the market maker's list of beliefs.
        self.market_beliefs = []
        # length of the sliding window to check for a jump
        self.window_length = 20

    def new_information(self, info, time):
        """Get information about the underlying market value.
        
        info: 1 with probability equal to the current
          underlying market value, and 0 otherwise.
        time: The current timestep for the experiment. It
          matches up with possible_jump_locations. It will
          be between 0 and self.timesteps - 1."""
        self.information.append(info)

    def trades_history(self, trades, time):
        """A list of everyone's trades, in the following format:
        [(execution_price, 'buy' or 'sell', quantity,
          previous_market_belief), ...]
        Note that this isn't just new trades; it's all of them."""
        self.trades = trades

    def trading_opportunity(self, cash_callback, shares_callback,
                            check_callback, execute_callback,
                            market_belief):
        """Called when the bot has an opportunity to trade.
        
        cash_callback(): How much cash the bot has right now.
        shares_callback(): How many shares the bot owns.
        check_callback(buysell, quantity): Returns the per-share
          price of buying or selling the given quantity.
        execute_callback(buysell, quantity): Buy or sell the given
          quantity of shares.
        market_belief: The market maker's current belief.

        Note that a bot can always buy and sell: the bot will borrow
        shares or cash automatically.
        """
        # keep track of the market beliefs
        self.market_beliefs.append(market_belief)
        time_step = len(self.information)

        # number of successes
        count = sum(self.information)
        # total number of trials ( current timestep )
        nobs = time_step
        #  asymptotic normal approximation
        # 95% confident p_i is between ci_low and ci_high (covers 1-alpha)
        ci_low, ci_upp = statistics.proportion_confint(count, nobs, alpha=0.05, method='normal')

        # average of market's belief and my p_i estimate
        p_i_estimate = float(count) / float(time_step)
        self.belief = (100 * p_i_estimate + market_belief) / 2
        # self.belief = (ci_upp * 100 + ci_low * 100 + market_belief) / 3

        # detect jump
        if time_step > self.window_length:
            # normal distribution centered at p_i with standard deviation of 0.2
            mu = self.belief
            sigma = 20

            jump_low = mu - 1 * sigma
            jump_upp = mu + 1 * sigma

            last_elts = -self.window_length + 1
            sliding_average = sum(self.information[last_elts:]) / float(len(self.information[last_elts:]))
            sliding_average *= 100
            if sliding_average < jump_low:
                # jump detected, reset our information as it is no longer valid
                self.information = []
            elif sliding_average > jump_upp:
                # jump detected, reset our information as it is no longer valid
                self.information = []

        best_buy_qty, expected_buy_profit = self.maximize_buysell_profit_qty('buy', self.belief, ci_low, ci_upp,
                                                                             check_callback)
        best_sell_qty, expected_sell_profit = self.maximize_buysell_profit_qty('sell', self.belief, ci_low, ci_upp,
                                                                               check_callback)

        # if there is a profitable action, execute it
        if expected_buy_profit > expected_sell_profit and best_buy_qty > 0:
            # print 'buying',best_buy_qty, self.belief, time_step
            execute_callback('buy', best_buy_qty)
        elif expected_buy_profit <= expected_sell_profit and best_sell_qty > 0:
            # print 'buying', best_sell_qty, self.belief, time_step
            execute_callback('sell', best_sell_qty)

    @staticmethod
    def maximize_buysell_profit_qty(action, p_i_estimate, ci_low, ci_upp, check_callback):
        """ maximize the profit, while minimizing risk
        returns the quantity that maximizes the expected profit
        """
        ci_range = ci_upp - ci_low
        if ci_range > 0:
            confidence = max(0, int(1 / ci_range ** 2) - 1)
            riskiness = 1
            max_quantity = int(confidence * riskiness)
            quantity = max_quantity
            while quantity > 0:
                if action is 'buy' and p_i_estimate > check_callback(action, quantity):
                    expected_profit = quantity * ((p_i_estimate * 100) - check_callback(action, quantity))
                    return quantity, expected_profit
                elif action is 'sell' and p_i_estimate < check_callback(action, quantity):
                    expected_profit = quantity * ((p_i_estimate * 100) - check_callback(action, quantity))
                    return quantity, expected_profit
                quantity -= 1
            return 0, 0
        else:
            return 0, 0


def main():
    bots = [MyBot()]
    # 5,2 to start
    num_fundamentals = 8
    num_technical = 2
    bots.extend(other_bots.get_bots(num_fundamentals, num_technical))
    # Plot a single run. Useful for debugging and visualizing your
    # bot's performance. Also prints the bot's final profit, but this
    # will be very noisy.
    plot_simulation.run(bots, lmsr_b=250)

    # Calculate statistics over many runs. Provides the mean and
    # standard deviation of your bot's profit.
    run_experiments.run(bots, num_processes=4, simulations=1000, lmsr_b=250)


# Extra parameters to plot_simulation.run:
#   timesteps=100, lmsr_b=150

# Extra parameters to run_experiments.run:
#   timesteps=100, num_processes=2, simulations=2000, lmsr_b=150

# Descriptions of extra parameters:
# timesteps: The number of trading rounds in each simulation.
# lmsr_b: LMSR's B parameter. Higher means prices change less,
#           and the market maker can lose more money.
# num_processes: In general, set this to the number of cores on your
#                  machine to get maximum performance.
# simulations: The number of simulations to run.

if __name__ == '__main__':  # If this file is run directly
    main()
