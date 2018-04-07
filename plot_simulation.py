import matplotlib.pyplot as pyplot
import prices
import simulation

def plot_beliefs(beliefs, color='k'):
    belief_by_time = {}
    for time, belief in beliefs:
        belief_by_time.setdefault(time, []).append(belief)
    x = belief_by_time.keys()
    y = [sum(a) / float(len(a)) for a in belief_by_time.values()]
    pyplot.plot(x, y, color=color)
    return x

def run(traders, timesteps=100, lmsr_b=150):
    market_fact = prices.LMSRFactory(lmsr_b)
    sim_obj = simulation.Simulation(
        timesteps, market_fact, traders)
    sim_obj.simulate()
    pyplot.figure()
    x_overall = plot_beliefs(sim_obj.log.beliefs)
    pyplot.plot(range(len(sim_obj.p_vec)),
                [a * 100.0 for a in sim_obj.p_vec],
                ls='--', color='r')
    pyplot.ylim((0, 100))
    print sim_obj.profits_by_user()
    pyplot.show()
