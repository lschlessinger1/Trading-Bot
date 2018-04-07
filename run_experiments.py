import multiprocessing
import numpy
import prices
import simulation
import sys

def worker_process(sim_obj):
    try:
        sim_obj.simulate()
    except Exception, e:
        print >> sys.stderr, type(e), e.args
        return (None, None)
    assert len(sim_obj.log.beliefs) == len(sim_obj.p_vec)
    return (sim_obj.market_fact.name, sim_obj.profits_by_user())

def run(trader_list, timesteps=100, num_processes=2, simulations=2000,
        lmsr_b=150):
    marketmakers = [prices.LMSRFactory(lmsr_b)]
    
    pool = multiprocessing.Pool(num_processes)
    sim_objects = []
    for marketmaker_fact in marketmakers:
        for i in range(simulations):
            sim_objects.append(simulation.Simulation(
                    timesteps, marketmaker_fact,
                    trader_list))
    results = pool.map(worker_process, sim_objects)
    results_by_market = {}
    max_profit_by_market = {}
    min_profit_by_market = {}
    for market_name, profits_by_user  in results:
        if market_name is None:
            continue
        for user_type, profit_list in profits_by_user.iteritems():
            results_by_market.setdefault(market_name, {}).setdefault(
                user_type, []).append(profit_list)
            if user_type == market_name:
                if profit_list > max_profit_by_market.get(
                    market_name, float('-inf')):
                    max_profit_by_market[market_name] = profit_list
                if profit_list < min_profit_by_market.get(
                    market_name, float('inf')):
                    min_profit_by_market[market_name] = profit_list
    for market_name, profit_dict in results_by_market.iteritems():
        print ('%s profit: %1.2f (min %1.2f, '
               'max %1.2f, %d samples)') % (
            market_name, numpy.mean(profit_dict[market_name]),
            min_profit_by_market[market_name],
            max_profit_by_market[market_name],
            len(profit_dict[market_name]))
        for user_type, profit_list in profit_dict.iteritems():
            if user_type == market_name:
                continue
            print ('    %s profit: %1.2f (%1.2f min, %1.2f max, '
                   '%1.2f std, %d samples)') % (
                user_type, numpy.mean(profit_list),
                min(profit_list), max(profit_list),
                numpy.std(profit_list), len(profit_list))
