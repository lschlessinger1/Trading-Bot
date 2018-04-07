import math

def hansonPriceCheck(transaction, qtyToBuySell, qtyOutstanding, maxLoss):
    newq1 = qtyOutstanding
    q2 = newq2 = 0
    maxLoss = float(maxLoss)
    if transaction == "buy":
        newq1 += qtyToBuySell
    elif transaction == "sell":
        newq1 -= qtyToBuySell
    # Cost function evaluated at current quantities outstanding
    cost_init = maxLoss * math.log(
        math.exp(qtyOutstanding/maxLoss) + math.exp(q2/maxLoss))
    # Cost function evaluated at new quantities outstanding
    cost_final = maxLoss * math.log(
        math.exp(newq1/maxLoss) + math.exp(newq2/maxLoss))
    costToUser = (cost_final - cost_init) * 100
    currentPrice = (math.exp(newq1/maxLoss)
                    / (math.exp(newq1/maxLoss)
                       + math.exp(newq2/maxLoss))) * 100
    return (abs(costToUser), newq1, currentPrice)

def prediction_limit(val):
    if val > 100:
        return float(100)
    if val < 0:
        return float(0)
    return val
