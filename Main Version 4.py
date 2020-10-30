from Tkinter import *
from tkFileDialog import *
import csv
import datetime
import matplotlib.pyplot as plt
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import time


#-----------------------------------------------------------------------------------------------------------------------

#FUNCTIONS USED INSIDE THE MAIN PROGRAM

desired_payback_period = 1
peak_rate = 54
day_rate = 25
off_rate = 13

dod = 0.6


#obtain load data via path, return specific lists of load data
def getLoadData(path):

    file = open(path)
    reader = csv.reader(file)

    data = []
    load = []
    load_batt = []
    current_batt = []
    for row in reader:
        time = datetime.datetime.strptime(row[0], '%H:%M:%S')
        time_f = datetime.time(time.hour, time.minute)
        time_str = str(time_f)
        kW = float(row[1])
        current = kW * (1000./230.)
        quantized_current = int(current) + 1

        data.append([time_str, time_f, quantized_current])
        load.append([time_str, time_f, current])
        current_batt.append(current)
        load_batt.append([time_f, current])

    return data, load, current_batt, load_batt

#output the battery details, battery_dod, battery sizes
def getBatteryList(dod):

    path2 = "C:/Users/DELL/Dropbox/Data/batt_details 4.csv"
    file2 = open(path2)
    battery_details = csv.reader(file2)

    batt = []
    for row in battery_details:
        batt.append(row)

    batt_dod = []
    batt_size = []
    batt_cost = []
    for row in batt:
        batt_dod.append(float(row[4]) * dod)  # This was changed... it was row[0]
        batt_size.append(int(row[4]))
        batt_cost.append(row[5])

    return batt, batt_dod, batt_size, batt_cost

# calculate discharge time for constant discharge rate
                                                                #the current value was changed by *(230/24)
def peukerts(i, c):
    try:
        i = i * (230/24)
        t = 20 * ((float(c) / (float(i) * 20)) ** 1.17)
    except:
        t = 0
        # print("Invalid Current or Capacity")
    return t

#Calculate the actual discharge time for the given battery capacity
                                                                #cur value was changed *(230/24)
def actual_discharge_time(list, capacity):
    comparison = []
    for row in list:
        t = peukerts(row[0], capacity)
        comparison.append([row[0], (row[1]), round(capacity, 2), round(t * 60, 2)])
        cur = row[0]
        cur = cur * (230/24)
        c = cur * 20 * (((row[1] / 60) / 20) ** (1 / 1.17))
        capacity = capacity - c
        if capacity <= 0:
            capacity = 0

    # for row in comparison:
    #     print(row)

    sum = 0
    for row in comparison:
        if (row[1] < row[3]):
            sum = sum + row[1]
        else:
            sum = sum + row[3]

    total_time = sum / 60

    if total_time > 4:
        total_time = 4

    return total_time

# Extract the data which can be provided by the given battery capacity
def supplied_by_battery(data, capacity, load):

    start_time = datetime.time(18, 30, 0)
    end_time = datetime.time(22, 30, 0)

    peak_current = [row[2] for row in data if (row[1] >= start_time and row[1] <= end_time)]
    peak_time = [row[0] for row in data if (row[1] >= start_time and row[1] <= end_time)]

    peak_load = []
    for i in range(len(peak_current)):
        peak_load.append([peak_time[i], peak_current[i]])

    count = 0
    current_load = 0
    previous_load = peak_load[0][1]
    frequency = []
    for row in peak_load:
        current_load = row[1]
        if previous_load == current_load:
            count = count + 1
            if row[0] == '22:30:00':
                frequency.append([float(previous_load), float(count)])
        else:
            frequency.append([float(previous_load), float(count)])
            previous_load = current_load
            count = 1

    total_time = actual_discharge_time(frequency, capacity)

    h = int(total_time)
    m = int((total_time - h) * 60)
    time_v = datetime.time(h, m, 0)

    # print(time_v)

    start_time = datetime.datetime(2018, 3, 14, 18, 30, 0)
    end_time = start_time + datetime.timedelta(hours=h, minutes=m)

    end_time = end_time.time()
    start_time = start_time.time()

    batt_load = [[row[1], row[2]] for row in load if (row[1] >= start_time and row[1] <= end_time)]

    # for row in batt_load:
    #     print(row)

    return batt_load, total_time

#return the inverter price based on the inverter size
def inverter(size):

    path = 'C:/Users/DELL/Dropbox/Data/Inverter_details.csv'
    file = open(path)
    reader = csv.reader(file)

    inverter_data = []
    for row in reader:
        inverter_data.append(row)

    # for row in inverter_data:
    #     print(row)

    for row in inverter_data:
        min = int(row[0])
        max = int(row[1])
        price = int(row[2])

        if size>min and size<=max:
            return price

#calculate and return energy based on the load data and number of hours
def energies(load, hours):
    sum = 0
    for row in load:
        sum += float(row[1])
    average = sum / len(load)
    energy = average * hours * (0.23)
    return energy

#calculate and return the savings due to each battery
def calculate_savings(peak,day,off, new_energy):
    # start = time.time()
    time_of_use = (peak * peak_rate) + (day * day_rate) + (off * off_rate)

    saving = time_of_use-new_energy

    return round(saving,2)

#calculate block tariff based on the monthly consumption
def block_cost(total):
    if total < 60:
        if total < 30:
            cost = (total * 2.5) + 30
        else:
            cost = (30 * 2.5) + ((total - 30) * 4.85) + 60
    else:
        if total < 90:
            cost = (60 * 7.85) + ((total - 60) * 10) + 90
        elif total > 90 and total < 120:
            cost = (60 * 7.85) + (30 * 10) + ((total - 90) * 27.75) + 480
        elif total > 120 and total < 180:
            cost = (60 * 7.85) + (30 * 10) + (30 * 27.75) + ((total - 120) * 32) + 480
        else:
            cost = (60 * 7.85) + (30 * 10) + (30 * 27.75) + (60 * 32) + ((total - 180) * 45) + 540

    return cost


def savings_block(total_energy, new_energy):

    cost_block = block_cost(total_energy)

    saving = cost_block - new_energy

    return saving

#calculate payback period for each battery
def payback(size, savings, battery_cost):

    details = []
    for i in range(len(savings)):

        payback_in_days = battery_cost[i]/savings[i]
        # print(payback_in_days)
        payback_in_years = payback_in_days/365
        # print(payback_in_years)

        details.append([size[i],round(savings[i]),battery_cost[i],round(payback_in_days,2),round(payback_in_years,2)])

    return details

#calculate return on investment based on time period
#this time period could be the life time of the battery...check this
def return_on_investment(size,number_of_years,savings,battery_cost):

    roi_details = []
    for i in range(len(savings)):

        total_savings = float(number_of_years*365*savings[i])
        roi = float(total_savings - battery_cost[i])

        roi_details.append([size[i],round(savings[i],2),battery_cost[i],round(roi,2)])



    return roi_details

#select proper inverter size for the calculated size
def inverter_propersize(inverter_size):
    inverter_size = inverter_size*1.25
    inverter_sizes = [500,1000,1500,2000,2500,3000,3500,4000,4500,5000,5500,6000,6500,7000,7500,8000,8500,9000,9500,10000]
    for row in inverter_sizes:
        if row > inverter_size:
            proper_size = row
            return proper_size

#output energies at different periods of the day (peak,day,off)
def getEnergies(load_batt):

    starttime = datetime.time(0, 0, 0)
    end_of_offpeak = datetime.time(5, 30, 0)
    mintime = datetime.time(18, 30, 0)
    maxtime = datetime.time(22, 30, 0)
    endtime = datetime.time(23, 59, 59)

    peak_load = [row for row in load_batt if (row[0] >= mintime and row[0] <= maxtime)]
    off_load = [row for row in load_batt if
                ((row[0] >= starttime and row[0] <= end_of_offpeak) or (row[0] > maxtime and row[0] <= endtime))]
    day_load = [row for row in load_batt if (row[0] > end_of_offpeak and row[0] < mintime)]

    peak_energy = energies(peak_load, 4)
    day_energy = energies(day_load, 13)
    off_energy = energies(off_load, 7)

    return peak_energy, day_energy, off_energy

#get energy cost and battery running time
def getEnergyCost(batt_dod, data, load, peak_energy, day_energy, off_energy, dod):


    new_energy = []
    running_time = []
    for row in batt_dod:

        battery_load, battery_time = supplied_by_battery(data, row, load)

        batt_energy = energies(battery_load, battery_time)

        new_peak_energy = peak_energy - batt_energy
        if new_peak_energy < 0:
            new_peak_energy = 0
        new_off_energy = off_energy + (batt_energy * 1.2)

        new_energy.append(
            [(row / dod), round(new_peak_energy, 2), round(day_energy, 2), round(new_off_energy, 2)])

        running_time.append(round(battery_time, 2))

    energy_cost = []
    for i in range(len(new_energy)):
        time_of_use = (new_energy[i][1] * peak_rate) + (new_energy[i][2] * day_rate) + (new_energy[i][3] * off_rate)
        energy_cost.append(time_of_use)



    # print("Done")
    return energy_cost, running_time


def get_energycost_block(batt_dod, data, load, peak_energy, day_energy, off_energy, dod):


    battery_load, battery_time = supplied_by_battery(data, batt_dod, load)
    # print(battery_time)
    batt_energy = energies(battery_load, battery_time)
    # print(batt_energy)
    new_peak_energy = peak_energy - batt_energy
    if new_peak_energy < 0:
        new_peak_energy = 0
    new_off_energy = off_energy + (batt_energy * 1.2)

    time_of_use = (new_peak_energy * peak_rate) + (day_energy * day_rate) + (new_off_energy * off_rate)
    # print(time_of_use)
    return time_of_use

#get battery cost and inverter size based on battery details
def getBatterySystemCost(batt, current_batt):

    max_load = max(current_batt)

    inverter_size = ((max_load + (max_load * 0.25)) * 230.0)
    # print 'Invert size: ' + str(inverter_size) + ' W'
    proper_inverter_size = inverter_propersize(inverter_size)
    inverter_price = inverter(inverter_size)
    # print(inverter_prize)
    switchgear_price = 4500
    other_cost = 9000

    batt_cost = []
    actual_battery_cost = []
    for i in range(len(batt)):
        cost = float(batt[i][5]) + float(
            batt[i][3]) + inverter_price + switchgear_price + other_cost  # This was changed batt[i][2]
        batt_cost.append(round(cost / (365 * 5), 2))  # this was also changed
        actual_battery_cost.append(round(cost))

    return batt_cost, actual_battery_cost, proper_inverter_size


#-----------------------------------------------------------------------------------------------------------------------

#CALCULATING NPV BASED ON ANNUAL VALUES

inflation = 0.07
dep_rate = 0.4
life_time = 5

#calculate annual depreciation rate of battery capacity
def depreciation_rate(start_capacity, end_capacity, num_of_years):

    A = float(end_capacity)
    P = float(start_capacity)
    n = float(num_of_years)

    r = 1 - ((A/P)**(1/n))

    return float(round(r,3))

# print(depreciation_rate(100, 60, 1))

#get the depreciated battery capacities based on the depreciation rate and number of years
def getDepreciatedCapacities(capacity, dep_rate, years):

    constant_capacity = 4

    depreciated_capacities = []
    for i in range(0, years + 1):

        if i <= constant_capacity:
            r = 0
        else:
            r = dep_rate
            i = i - constant_capacity

        dep_capacity = capacity * (1 - r) ** i

        depreciated_capacities.append([i, round(dep_capacity, 2)])

    return depreciated_capacities

dep_caps = getDepreciatedCapacities(600, dep_rate, life_time)
print(dep_caps)

#calculate the annual savings based on a month of data and for a specific battery capacity
def annual_saving(month, capacity):
    batt_dod = capacity*dod

    monthly_savings = 0
    total_monthly_energy = 0
    total_peak = 0
    total_day = 0
    total_off = 0
    for day in range(1, 32):
        try:
            path = "C:/Users/DELL/Dropbox/Data/Ambatale House/kWh Data/" + str(month) + "/" + str(day) + ".csv"

            data, load, current_batt, load_batt = getLoadData(path)

            peak_energy, day_energy, off_energy = getEnergies(load_batt)

            energy_cost = get_energycost_block(batt_dod, data, load, peak_energy, day_energy, off_energy, dod)

            time_of_use = (peak_energy * peak_rate) + (day_energy * day_rate) + (off_energy * off_rate)

            savings = time_of_use - energy_cost

            monthly_savings = monthly_savings + savings
            # print(time_of_use, energy_cost, savings)
        except:
            pass

    return monthly_savings*12

# month = 'July'
# day = 30
# path = "C:/Users/DELL/Dropbox/Data/Ambatale House/kWh Data/" + str(month) + "/" + str(day) + ".csv"
#
# data, load, current_batt, load_batt = getLoadData(path)
#
# peak_energy, day_energy, off_energy = getEnergies(load_batt)
#
# # print(peak_energy, day_energy, off_energy)
#
# energy_cost = get_energycost_block(600*dod, data, load, peak_energy, day_energy, off_energy, dod)
# # print(energy_cost)
# time_of_use = (peak_energy * peak_rate) + (day_energy * day_rate) + (off_energy * off_rate)
# # print(time_of_use)
# savings = time_of_use - energy_cost
# # print(savings)
#
#
# print(annual_saving('July', 600))


# print(annual_saving('July',600))

# for row in dep_caps:
#     print(row[1], annual_saving('July', row[1]))

#obtain the inverter size based on the highest current for the entire month
def inverter_size_for_month(month):

    max_load_perday = []
    for day in range(1,32):
        try:
            path = "C:/Users/DELL/Dropbox/Data/Ambatale House/kWh Data/" + str(month) + "/" + str(day) + ".csv"

            data, load, current_batt, load_batt = getLoadData(path)

            max_load = max(current_batt)

            max_load_perday.append(max_load)

        except:
            pass

    final_max_load = max(max_load_perday)

    return final_max_load

#get the present value based on the inflation rate and year
def presentValue_Savings(annual_savings, inflation_rate, year):

    FV = float(annual_savings)
    r = float(inflation_rate)
    n = float(year)

    PV = float(FV/((1+r)**n))

    return PV

#obtain present values for all annual savings and output total present inflow
def presentInflow(dep_caps):
    future_values = []
    present_values = []
    for row in dep_caps:
        annual_savings = annual_saving('July', row[1])

        future_values.append([row[0], round(annual_savings, 2)])

        present_value = presentValue_Savings(annual_savings, inflation, row[0])

        present_values.append([row[0], round(present_value, 2)])

    # print(future_values)
    # print(present_values)

    sum = 0
    for row in present_values:
        sum = sum + row[1]

    total_presentInflow = sum

    return total_presentInflow

# print(presentInflow(dep_caps))

#obtain the total present outflow based on the battery system cost
def presentOutflow(batt, capacity):

    batterycosts = []
    for row in batt:
        if int(row[4]) == capacity:
            battery_cost = float(row[5])
            charger_cost = float(row[3])
            batterycosts.append([battery_cost, charger_cost])


    max_load = inverter_size_for_month('July')

    inverter_size = ((max_load + (max_load * 0.25)) * 230.0)
    proper_inverter_size = inverter_propersize(inverter_size)
    inverter_price = inverter(proper_inverter_size)
    # print(inverter_price)
    switchgear_price = 4500
    other_cost = 9000


    total_cost = batterycosts[0][0] + batterycosts[0][1] + inverter_price + switchgear_price + other_cost


    return total_cost


#obtain the NPV value for a specific battery bank capacity
def NPV(capacity):

    batt, batt_dod, batt_size, batt_cost = getBatteryList(dod)

    presentOutflow_value = presentOutflow(batt, capacity)

    # print(presentOutflow_value)

    dep_caps = getDepreciatedCapacities(capacity, dep_rate, life_time)

    presentInflow_value = presentInflow(dep_caps)

    # print(presentInflow_value)

    # battery_cost = 0
    # for row in batt:
    #     if int(row[4]) == capacity:
    #         battery_cost = int(row[5])
    #
    # scrap_value = battery_cost/4
    #
    # scrap_value = presentValue_Savings(scrap_value, inflation,5)
    #
    # presentInflow_value = presentInflow_value + scrap_value

    NPV_value = presentInflow_value - presentOutflow_value

    return NPV_value

batt, batt_dod, batt_size, batt_cost = getBatteryList(dod)

npv_list = []
for row in batt:
    batt_capacity = int(row[4])
    npv = NPV(batt_capacity)
    npv_list.append(npv)
    print(batt_capacity,round(npv,2))

#-----------------------------------------------------------------------------------------------------------------------

fig, ax = plt.subplots()

# Twin the x-axis twice to make independent y-axes.
axes = [ax, ax.twinx()]

# Make some space on the right side for the extra y-axis.
# fig.subplots_adjust(right=0.75)

# Move the last y-axis spine over to the right by 20% of the width of the axes
# axes[-1].spines['right'].set_position(('axes', 1.2))

# To make the border of the right-most axis visible, we need to turn the frame
# on. This hides the other plots, however, so we need to turn its fill off.
axes[-1].set_frame_on(True)
axes[-1].patch.set_visible(False)

# And finally we get to plot things...
# colors = ('Green', 'Red')
# for ax, color in zip(axes, colors):
#     ax.plot(data, marker='o', linestyle='none', color=color)
#     ax.set_ylabel('%s Thing' % color, color=color)
#     ax.tick_params(axis='y', colors=color)
# axes[0].set_xlabel('X-axis')

ax1 = axes[0]
ax2 = axes[1]

markers_on = []
for i in range(len(batt)):
    if batt[i][0] == batt[i][1]:
        markers_on.append(i)

# plt.plot(batt_size,total_cost,'-gD', markevery=markers_on)

# plt.xlabel('Battery Capacity (Ah)')
# plt.ylabel('Total Cost (Rs.)')
# plt.title('Total Cost vs. Battery Capacities for ' + str(month) + ' ' + str(day))
# plt.title('Total Cost vs. Battery Capacities for 2-Week 1')
# plt.show()

ax1.plot(batt_size, npv_list, '-gD', markevery=markers_on, marker='o', markersize=7, markeredgewidth=1,
         markeredgecolor='g', markerfacecolor='None', color='Green')
ax1.set_ylabel('Total Cost (Rs.)')
ax1.tick_params(axis='y', colors='Green')
ax1.set_xlabel('Battery Capacity (Ah)')
ax1.xaxis.grid()

start, end = ax1.get_xlim()
ax1.xaxis.set_ticks(np.arange(start, end, 20))

xticks = ax1.xaxis.get_major_ticks()
xticks[0].label1.set_visible(False)
#
# ax2.plot(batt_size, running_time, '--', markevery=markers_on, color='Red')
# ax2.set_ylabel('Battery Running Time (h)')
# ax2.tick_params(axis='y', colors='Red')
# ax2.yaxis.grid()

plt.show()