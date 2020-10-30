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

dod = 0.5


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
    energy = average * hours * 0.23
    return energy

#calculate and return the savings due to each battery
def calculate_savings(peak,day,off, new_energy):
    # start = time.time()
    time_of_use = (peak * peak_rate) + (day * day_rate) + (off * off_rate)

    savings = []
    for row in new_energy:
        saving = time_of_use-row
        savings.append(round(saving,2))

    # print("Savings Done")

    # end = time.time()
    # elapsed_time = end - start
    #
    # print("Total time elapsed: " + str(time.strftime("%H:%M:%S", time.gmtime(elapsed_time))))
    return savings

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

    batt_energy = energies(battery_load, battery_time)

    new_peak_energy = peak_energy - batt_energy
    if new_peak_energy < 0:
        new_peak_energy = 0
    new_off_energy = off_energy + (batt_energy * 1.2)

    time_of_use = (new_peak_energy * peak_rate) + (day_energy * day_rate) + (new_off_energy * off_rate)

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

#MAIN PROGRAM

# def main(path):
#
#     data, load, current_batt, load_batt = getLoadData(path)
#
#     batt, batt_dod, batt_size, batt_cost = getBatteryList(dod)
#
#     batt_cost, actual_battery_cost, proper_inverter_size = getBatterySystemCost(batt, current_batt)
#
#     peak_energy, day_energy, off_energy = getEnergies(load_batt)
#
#     energy_cost, running_time = getEnergyCost(batt_dod, data, load, peak_energy, day_energy, off_energy, dod)
#
#     savings = calculate_savings(peak_energy,day_energy,off_energy,energy_cost)
#
#     # payback_details = payback(batt_size, savings,actual_battery_cost)
#
#     # for row in payback_details:
#     #     print(row)
#
#     roi_details = return_on_investment(batt_size,desired_payback_period,savings,actual_battery_cost)
#
#     # for row in roi_details:
#     #     print(row)
#
#     total_cost = []
#     for i in range(len(batt_cost)):
#         total = batt_cost[i] + energy_cost[i]
#         total_cost.append(round(total, 2))
#
#     final_results = []
#     for i in range(len(batt_size)):
#         # print(str(batt_size[i]) + " Ah:  " + str(total_cost[i]))
#         final_results.append([batt_size[i], total_cost[i]])
#
#     finalresults_cost = [row[1] for row in final_results]
#
#     optimum_capacity = 0
#     for row in final_results:
#         if row[1] == min(finalresults_cost):
#             optimum_capacity = row[0]
#
#     return optimum_capacity, proper_inverter_size, batt, batt_size,total_cost, running_time, savings

#-----------------------------------------------------------------------------------------------------------------------

#TKINTER INTERFACE

# class App(Tk):
#
#     def __init__(self, *args, **kwargs):
#         Tk.__init__(self, *args, **kwargs)
#
#         self.wm_title("Browser")
#         self.geometry('700x400')
#
#         self.container = Frame(self)
#         self.container.pack(side = "top", fill = "both", expand = True)
#
#         self.container.grid_rowconfigure(0, weight = 1)
#         self.container.grid_columnconfigure(0, weight = 1)
#
#         self.frames = {}
#
#         for F in (StartPage, GraphPage, PageTwo):
#             frame = F(self.container, self)
#             self.frames[F] = frame
#             frame.grid(row = 0, column = 0, sticky = "nsew")
#
#         self.show_frame(StartPage)
#
#     def show_frame(self, cont):
#
#         # if cont is GraphPage:
#         #     entry = StartPage(self.container,self).entry
#         #
#         #     graph = GraphPage(self.container, self)
#         #     graph.displayPlot(entry)
#         #     frame = self.frames[cont]
#         #     frame.tkraise()
#         # else:
#         frame = self.frames[cont]
#         frame.tkraise()
#
#
#     # browse the file and insert the file path into the entry
#     def browsefunc(self, entry):
#         entry.delete(0, END)
#         fileName = askopenfilename(parent=self)
#         entry.insert(0, fileName)
#
#     # obtain path from entry and provide the optimum capacity and inverter size
#     def printPath(self, entry, entry_capacity, entry_inverter):
#         entry_capacity.delete(0, END)
#         entry_inverter.delete(0, END)
#
#         path = entry.get()
#         optimum, inverter, batt_data, battSize, totalCost, runningTime, savings = main(path)
#         entry_capacity.insert(0, optimum)
#         entry_inverter.insert(0, inverter)
#         # print(optimum)
#
# class StartPage(Frame):
#
#
#     def __init__(self, parent, controller):
#         Frame.__init__(self, parent)
#
#         broButton = Button(self, text='Browse', width=6, command = lambda: controller.browsefunc(self.entry) )
#         broButton.grid(row=0, column=0, padx=2, pady=2)
#
#         self.entryValue = StringVar
#         self.entry = Entry(self, width=70, textvariable = self.entryValue)
#         self.entry.grid(row=0, column=1, padx=30, pady=10)
#
#         computeButton = Button(self, text = "Compute", width = 6, command = lambda: controller.printPath(self.entry, entry_capacity,entry_inverter))
#         computeButton.grid(row = 1, column = 0, padx = 2, pady=2,)
#
#         # graph = GraphPage(parent, controller)
#
#
#         # plotButton = Button(self, text="Plot", width=6, command= lambda: controller.show_frame(GraphPage))
#         # plotButton.grid(row=1, column=1, padx=2, pady=2, )
#
#
#         label_battery = Label(self, text = "Optimum Battery Capacity = ")
#         label_battery.grid(row = 2, column = 0, pady = 20)
#
#         entry_capacity = Entry(self, width = 30)
#         entry_capacity.grid(row = 2, column = 1, pady = 20)
#
#         label_inverter = Label(self, text = "Inverter Size = ")
#         label_inverter.grid(row = 3, column = 0, pady = 20)
#
#         entry_inverter = Entry(self, width = 30)
#         entry_inverter.grid(row = 3, column = 1, pady = 20)
#
#         button1 = Button(self, text="Graph", command=lambda: controller.show_frame(GraphPage))
#         button1.grid()
#
# class GraphPage(Frame):
#
#
#     def __init__(self, parent, controller):
#         Frame.__init__(self, parent)
#
#         # broButton = Button(self, text='Browse', width=6, command=lambda: controller.browsefunc(entry))
#         # # broButton.grid(row=0, column=1, padx=2, pady=2, rowspan = 3)
#         # broButton.pack()
#         #
#         # entry = Entry(self, width=70)
#         # # entry.grid(row=0, column=2, padx=30, pady=10, rowspan = 3)
#         # entry.pack()
#         start = StartPage(parent, controller)
#
#         entry = start.entry
#
#         plotButton = Button(self, text="Plot", width=6, command=lambda: self.displayPlot(entry))
#         # plotButton.grid(row=1, column=1, padx=2, pady=2, rowspan = 3)
#         plotButton.pack()
#
#
#         button1 = Button(self, text="Back", command=lambda: controller.show_frame(StartPage))
#         # button1.grid(row = 3, column = 1, columnspan = 3)
#         button1.pack()
#
#     # draw plot inside the interface
#     def show_plot(self, batt, batt_size, total_cost, running_time):
#
#         f1 = Figure(figsize=(5, 5), dpi=100)
#         ax1 = f1.add_subplot(111)
#         ax2 = ax1.twinx()
#
#         markers_on = []
#         for i in range(len(batt)):
#             if batt[i][0] == batt[i][1]:
#                 markers_on.append(i)
#
#
#         #ATTEMPT TO LIMIT THE X LABEL
#         # batt_size_limited = []
#         # for row in batt_size:
#         #     battery_size = row/3
#         #     if battery_size%50 == 0:
#         #         batt_size_limited.append(battery_size)
#         #     else:
#         #         batt_size_limited.append(None)
#
#
#         ax1.plot(batt_size, total_cost, '-gD', markevery=markers_on, marker='o', markersize=7, markeredgewidth=1,
#                  markeredgecolor='g', markerfacecolor='None', color='Green')
#         ax1.set_ylabel('Total Cost (Rs.)')
#         ax1.tick_params(axis='y', colors='Green')
#         ax1.set_xlabel('Battery Capacity (Ah)')
#         ax1.xaxis.grid()
#
#         start, end = ax1.get_xlim()
#         ax1.xaxis.set_ticks(np.arange(start, end, 20))
#
#         xticks = ax1.xaxis.get_major_ticks()
#         xticks[0].label1.set_visible(False)
#
#         ax2.plot(batt_size, running_time, '--', markevery=markers_on, color='Red')
#         ax2.set_ylabel('Battery Running Time (h)')
#         ax2.tick_params(axis='y', colors='Red')
#         ax2.yaxis.grid()
#
#         canvas = FigureCanvasTkAgg(f1, self)
#         canvas.get_tk_widget().pack(fill=BOTH, expand=TRUE, padx=50)
#         # canvas.get_tk_widget().grid(row = 2, padx = 50)
#         f1.canvas.draw()
#
#     # draw plot when button pressed
#     def displayPlot(self, entry):
#         path = entry.get()
#         optimum, inverter, batt_data, battSize, totalCost, runningTime, savings = main(path)
#
#         self.show_plot(batt_data, battSize, totalCost, runningTime)
#
# class PageTwo(Frame):
#
#     def __init__(self, parent, controller):
#         Frame.__init__(self, parent)
#
#
# app = App()
# app.mainloop()

#-----------------------------------------------------------------------------------------------------------------------

#COMPARING THE SAVINGS/COST RATIO FOR EACH BATTERY CAPACITY

#monthly saving for each battery is found, then divided by cost to obtain best ratio
def calculation_for_month(month):
    month_battery_inverter_info = []
    monthly_savings_list = []
    for day in range(1, 32):
        try:
            path = 'C:/Users/DELL/Dropbox/Data/Ambatale House/Complete Data/' +str(month)+ '/' + str(day) + '.csv'

            optimum_capacity, proper_inverter_size, batt, batt_size, total_cost, running_time, savings = main(path)

            month_battery_inverter_info.append([day, optimum_capacity, proper_inverter_size])

            monthly_savings_list.append(savings)
        except:
            pass

    sum = 0
    monthly_savings = []
    savings = monthly_savings_list[0]
    for i in range(len(savings)):
        for row in monthly_savings_list:
            sum = sum + row[i]
        monthly_savings.append(round(sum,2))
        sum = 0

    batt, batt_dod, batt_size, batt_cost = getBatteryList()

    savings_for_each_battery = []
    ratio_list = []
    for i in range(len(batt_size)):
        if i == 0:
            continue

        saving = float(monthly_savings[i])
        cost = float(batt_cost[i]) / (365 * 4)
        ratio = saving / cost
        savings_for_each_battery.append([batt_size[i], saving, round(cost, 2), round(ratio, 2)])
        ratio_list.append(round(ratio, 2))

    # for row in month_battery_inverter_info:
    #     print(row)

    best_value = max(ratio_list)

    for row in savings_for_each_battery:
        print(row)

    # for row in monthly_savings_list:
    #     print(row)

    for row in savings_for_each_battery:
        if row[3] == best_value:
            print("Optimum is " + str(row[0]))

# calculation_for_month("July")


#calculates the ratios for each day and adds the ratios for the whole month
def something(month):
    month_battery_inverter_info = []
    monthly_ratio_list = []
    for day in range(1, 32):
        try:
            path = 'C:/Users/DELL/Dropbox/Data/Ambatale House/Complete Data/' + str(month) + '/' + str(day) + '.csv'

            optimum_capacity, proper_inverter_size, batt, batt_size, total_cost, running_time, savings = main(path)

            batt, batt_dod, batt_size, batt_cost = getBatteryList()

            savings_to_cost = []
            ratio_list = []
            for i in range(len(batt_size)):
                if i == 0:
                    continue

                saving = float(savings[i])
                cost = float(batt_cost[i]) / (365 * 4)
                ratio = saving / cost
                savings_to_cost.append([batt_size[i], saving, round(cost, 2), round(ratio, 2)])
                ratio_list.append(round(ratio, 2))

            monthly_ratio_list.append(ratio_list)
        except:
            pass

    batt, batt_dod, batt_size, batt_cost = getBatteryList()

    # for row in savings_to_cost:
    #     print(row)

    sum = 0
    monthly_ratios = []
    ratios = monthly_ratio_list[0]
    for i in range(len(batt_size)-1):
        for row in monthly_ratio_list:
            sum = sum + row[i]
        monthly_ratios.append(round(sum, 2))
        sum = 0

    best_value = max(monthly_ratios)

    ratios_for_each_battery = []
    for i in range(len(monthly_ratios)):
        ratios_for_each_battery.append([batt_size[i],monthly_ratios[i]])

    for row in ratios_for_each_battery:
        if row[1] == best_value:
            print("Optimum is " + str(row[0]))

# something("May")

#-----------------------------------------------------------------------------------------------------------------------

#CALCULATING NPV BASED ON ANNUAL VALUES

inflation = 0.07
dep_rate = 0.08
life_time = 5

#calculate annual depreciation rate of battery capacity
def depreciation_rate(start_capacity, end_capacity, num_of_years):

    A = float(end_capacity)
    P = float(start_capacity)
    n = float(num_of_years)

    r = 1 - ((A/P)**(1/n))

    return float(round(r,3))

#get the depreciated battery capacities based on the depreciation rate and number of years
def getDepreciatedCapacities(capacity, dep_rate, years):

    r = dep_rate

    depreciated_capacities = []
    for i in range(0, years + 1):
        dep_capacity = capacity * (1 - r) ** i

        depreciated_capacities.append([i, round(dep_capacity, 2)])

    return depreciated_capacities

#calculate the annual savings based on a month of data and for a specific battery capacity
def annual_saving(month, capacity):
    batt_dod = capacity * dod

    total_monthly_energy = 0
    total_energy_cost = 0

    for day in range(1, 32):
        try:
            path = "C:/Users/DELL/Dropbox/Data/Ambatale House/kWh Data/" + str(month) + "/" + str(day) + ".csv"

            data, load, current_batt, load_batt = getLoadData(path)

            peak_energy, day_energy, off_energy = getEnergies(load_batt)

            total_energy = energies(load_batt, 24)
            total_monthly_energy = total_monthly_energy + total_energy

            energy_cost = get_energycost_block(batt_dod, data, load, peak_energy, day_energy, off_energy, dod)
            total_energy_cost = total_energy_cost + energy_cost

        except:
            pass

    savings = savings_block(total_monthly_energy, total_energy_cost + 540)

    # print(block_cost(total_monthly_energy), total_energy_cost+540)

    return savings * 12


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

# batt, batt_dod, batt_size, batt_cost = getBatteryList(dod)
#
# for row in batt:
#     batt_capacity = int(row[4])
#     npv = NPV(batt_capacity)
#     print(batt_capacity,round(npv,2))


#-----------------------------------------------------------------------------------------------------------------------

#CALCULATING NPV BASED ON MONTHLY VALUES

annual_inflation_rate = 0.1
# life_time = 3
capacity_reduction_percentage = 0.4



#get monthly inflation rate based on the annual inflation rate
def get_monthly_inflation(r_annual):

    r_annual = float(r_annual)
    r_month = (1+r_annual)**(1./12.) - 1
    return r_month

#get monthly reduction rate of battery capacity
def get_monthly_depreciation(depreciation_of_capacity, lifetime):

    period_of_constant_capacity = 2

    n = (lifetime - period_of_constant_capacity)*12

    # n = life_time*12
    r_annual = float(depreciation_of_capacity)
    r_month = 1 - (1-r_annual)**(1./float(n))
    return r_month

#obtain the total monthly present outflow based on the battery system cost
def presentOutflow_month(batt, capacity, life_time):

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

    total_cost = total_cost/float(life_time*12)

    return total_cost

#get the depreciated battery capacities based on the depreciation rate and number of years
def getMonthlyDepreciatedCapacities(capacity, dep_rate, years):

    depreciated_capacities = []

    period_of_constant_capacity = 2


    for i in range(0, (years*12) + 1):

        if i <= (period_of_constant_capacity*12):
            r = 0
        else:
            r = dep_rate
            i = i - period_of_constant_capacity*12

        # r = dep_rate

        dep_capacity = capacity * (1 - r) ** i

        depreciated_capacities.append([i, round(dep_capacity, 2)])

    return depreciated_capacities

#calculate the monthly savings based on a month of data and for a specific battery capacity
def monthly_saving(month, capacity, dod):
    batt_dod = []
    batt_dod.append(capacity*dod)

    sum = 0

    for day in range(1,32):
        try:
            path = "C:/Users/DELL/Dropbox/Data/Ambatale House/kWh Data/" + str(month) + "/" + str(day) + ".csv"

            data, load, current_batt, load_batt = getLoadData(path)

            peak_energy, day_energy, off_energy = getEnergies(load_batt)

            energy_cost, running_time = getEnergyCost(batt_dod, data, load, peak_energy, day_energy, off_energy, dod)

            savings = calculate_savings(peak_energy, day_energy, off_energy, energy_cost)

            sum = sum + savings[0]

        except:
            pass

    return float(sum)

def monthly_saving_block(month, capacity, dod):

    batt_dod = capacity * dod

    sum = 0
    total_monthly_energy = 0
    total_energy_cost = 0

    for day in range(1, 32):
        try:
            path = "C:/Users/DELL/Dropbox/Data/Ambatale House/kWh Data/" + str(month) + "/" + str(day) + ".csv"

            data, load, current_batt, load_batt = getLoadData(path)

            peak_energy, day_energy, off_energy = getEnergies(load_batt)

            total_energy = energies(load_batt, 24)
            total_monthly_energy = total_monthly_energy + total_energy

            energy_cost= get_energycost_block(batt_dod, data, load, peak_energy, day_energy, off_energy, dod)
            total_energy_cost = total_energy_cost + energy_cost

        except:
            pass

    savings = savings_block(total_monthly_energy, total_energy_cost + 540)

    # print(block_cost(total_monthly_energy), total_energy_cost+540)

    return savings



#get the present value based on the inflation rate and year
def calculate_presentValue(monthly_savings, inflation_rate, year):

    FV = float(monthly_savings)
    r = float(inflation_rate)
    n = float(year)

    PV = float(FV/((1+r)**n))

    return PV

#obtain present values for all monthly savings and output total present inflow
def calculate_present_inflow(dep_caps, inflation, years):
    future_values = []
    present_values = []
    for row in dep_caps:
        month_savings = monthly_saving_block('July', row[1], dod)

        future_values.append([row[0], round(month_savings, 2)])

        present_value = calculate_presentValue(month_savings, inflation, row[0])

        present_values.append([row[0], round(present_value, 2)])

    # print(future_values)
    # print(present_values)

    sum = 0
    for row in present_values:
        sum = sum + row[1]

    total_presentInflow = sum/(years*12)

    return total_presentInflow

#get scrap value based on the mass and the lifetime... Rs.150/kg
def getScrapValue(mass, life):

    return_perkg = 150

    scrap_v = return_perkg*mass*6

    return scrap_v/(float(life*12))


monthly_inflation_rate = get_monthly_inflation(annual_inflation_rate)

monthly_depreciation_rate = get_monthly_depreciation(capacity_reduction_percentage, life_time)

# depreciated_capacities = getMonthlyDepreciatedCapacities(600,monthly_depreciation_rate,life_time)
# print(depreciated_capacities)
# print("Depreciation capacities: Done")

# total_inflow = calculate_present_inflow(depreciated_capacities,monthly_inflation_rate,life_time)
# print("Total inflow: Done")

batt, batt_dod, batt_size, batt_cost = getBatteryList(dod)

# total_outflow = presentOutflow_month(batt, 600,life_time)
# print("Total outflow: Done")

# battery_cost = 0
# for row in batt:
#     if int(row[4]) == 600:
#         battery_cost = int(row[5])

# scrap_value = battery_cost*0.05*(1/float(life_time*12))

# scrap_value = getScrapValue(60, life_time)
#
# scrap_value = presentValue_Savings(scrap_value, monthly_inflation_rate,life_time)
# print(scrap_value)
# total_inflow = total_inflow + scrap_value

# print(total_inflow)
# print(total_outflow)


# batt, batt_dod, batt_size, batt_cost = getBatteryList()

# print(presentOutflow_month(batt, 600, life_time))




# for row in batt:
#     depreciated_capacities = getMonthlyDepreciatedCapacities(float(row[4]), monthly_depreciation_rate, life_time)
#     # print(depreciated_capacities)
#     # print("Depreciation capacities: Done")
#
#     total_inflow = calculate_present_inflow(depreciated_capacities, monthly_inflation_rate, life_time)
#     # print("Total inflow: Done")
#
#     total_outflow = presentOutflow_month(batt, float(row[4]), life_time)
#
#     print(row[4], total_inflow)


#-----------------------------------------------------------------------------------------------------------------------

#THIRD TRY FOR CALCULATING OPTIMUM - MONTHLY



