from Tkinter import *
import ttk
from tkFileDialog import *
import csv
import datetime
import matplotlib.pyplot as plt
import numpy as np
import matplotlib
import time
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure

#=FUNCTIONS USED INSIDE THE MAIN PROGRAM================================================

"""This function obtains the reference time series from CSV file"""
def getTimeSeries():
    file = open("Time series.csv")
    reader = csv.reader(file)

    time_series = []
    for row in reader:
        time_series.append(row[0])

    return time_series

"""This function obtains load data of any sample time interval and modifies it to 1 min data"""
def getModifiedData(original_data):

    minutes = 1440/len(original_data)

    new_data = []
    for row in original_data:
        for i in range(minutes):
            new_data.append(row[1])

    timeseries = getTimeSeries()

    modified_data = []
    for i in range(1440):
        modified_data.append([timeseries[i],new_data[i]])

    return modified_data

"""This function obtains load data and returns specific lists of load data"""
def getLoadData(path):
    file = open(path)
    reader = csv.reader(file)

    original_data = []
    for row in reader:
        original_data.append(row)

    modified_data = getModifiedData(original_data)

    data = []
    load = []
    load_batt = []
    current_batt = []
    for row in modified_data:
        time = datetime.datetime.strptime(row[0], '%H:%M:%S')
        time_f = datetime.time(time.hour, time.minute)
        time_str = str(time_f)
        kW = float(row[1])
        current = kW * (1000. / 230.)
        quantized_current = int(current) + 1

        data.append([time_str, time_f, quantized_current])
        load.append([time_str, time_f, current])
        current_batt.append(current)
        load_batt.append([time_f, current])

    return data, load, current_batt, load_batt

"""This function obtains load data for a month of data and stores it in a list"""
def getMonthData(directory):

    month_data = []
    for day in range(1, 32):
        try:
            path = str(directory) + "/" + str(day) + ".csv"
            data, load, current_batt, load_batt = getLoadData(path)
            month_data.append([data, load, current_batt, load_batt])
        except:
            pass

    return month_data

"""This function calculates the month energy based on the given month data"""
def getMonthEnergy(month_data):

    total_month_energy = 0

    for row in month_data:
        load_batt = row[3]
        total_energy = energies(load_batt, 24)
        total_month_energy += total_energy

    return total_month_energy

"""This function obtains total monthly energy consumption from CSV file"""
def getMonthlyEnergies(energies_path):

    path = str(energies_path)
    file = open(path)
    reader = csv.reader(file)

    monthly_energies = []
    for row in reader:
        monthly_energies.append(row)

    return monthly_energies

"""This function obtains the battery details from CSV file"""
def getBatteryList(battery_path, dod):

    path2 = str(battery_path)
    file2 = open(path2)
    battery_details = csv.reader(file2)

    batt = []
    for row in battery_details:
        batt.append(row)

    batt_dod = []
    batt_size = []
    batt_cost = []
    weights = []
    for row in batt:
        batt_dod.append(float(row[4]) * dod)
        batt_size.append(int(row[4]))
        batt_cost.append(row[5])
        weights.append([int(row[4]), row[6]])

    return batt, batt_dod, batt_size, batt_cost, weights

"""This function obtains the inverter details from CSV file"""
def inverter(inverter_path):

    path = str(inverter_path)
    file = open(path)
    reader = csv.reader(file)

    inverter_data = []
    for row in reader:
        inverter_data.append(row)

    return inverter_data

"""This function obtains the inverter price for a given inverter size"""
def get_inverter_price(size, inverter_data):

    for row in inverter_data:
        min = int(row[0])
        max = int(row[1])
        price = int(row[2])

        if size > min and size <= max:
            return price

"""This function determines the inverter size based on the maximum load"""
def inverter_size_for_month(directory):
    max_load_perday = []
    for day in range(1, 32):
        try:
            path = str(directory) + "/" + str(day) + ".csv"
            data, load, current_batt, load_batt = getLoadData(path)
            max_load = max(current_batt)
            max_load_perday.append(max_load)
        except:
            pass

    final_max_load = max(max_load_perday)

    inverter_size = final_max_load * 230.0 * 1.25
    inverter_sizes = [500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000, 6500, 7000, 7500, 8000,8500, 9000, 9500, 10000]
    for row in inverter_sizes:
        if row > inverter_size:
            proper_size = row
            return proper_size

"""This function calculates the discharge time for a constant discharge rate"""
def peukerts(i, c, exp):
    try:
        i = i * (230 / 24)
        t = 20 * ((float(c) / (float(i) * 20)) ** exp)
    except:
        t = 0

    return t

"""This function calculates the discharge time for the given battery capacity"""
def actual_discharge_time(list, capacity, exponent):

    comparison = []
    for row in list:
        t = peukerts(row[0], capacity, exponent)
        comparison.append([row[0], (row[1]), round(capacity, 2), round(t * 60, 2)])
        cur = row[0]
        cur = cur * (230 / 24)
        c = cur * 20 * (((row[1] / 60) / 20) ** (1 / exponent))
        capacity = capacity - c
        if capacity <= 0:
            capacity = 0

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

"""This function extracts the portion of data supplied by the battery"""
def supplied_by_battery(data, capacity, load, exponent):

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

    total_time = actual_discharge_time(frequency, capacity, exponent)

    h = int(total_time)
    m = int((total_time - h) * 60)
    time_v = datetime.time(h, m, 0)

    start_time = datetime.datetime(2018, 3, 14, 18, 30, 0)
    end_time = start_time + datetime.timedelta(hours=h, minutes=m)

    end_time = end_time.time()
    start_time = start_time.time()

    batt_load = [[row[1], row[2]] for row in load if (row[1] >= start_time and row[1] <= end_time)]

    return batt_load, total_time

"""This function calculates the energy based on the given load data and number of hours"""
def energies(load, hours):
    sum = 0
    for row in load:
        sum += float(row[1])
    average = sum / len(load)
    energy = average * hours * (0.23)
    return energy

"""This function calculates the energy for the different periods of the day"""
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

"""This function calculates the block tariff based on the total consumption"""
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

"""This function calculates the new energies for peak, off-peak and day-peak due to the operation of the battery"""
def getNewEnergies(batt_dod, data, load, peak_energy, day_energy, off_energy, exponent):
    battery_load, battery_time = supplied_by_battery(data, batt_dod, load, exponent)

    batt_energy = energies(battery_load, battery_time)

    new_peak_energy = peak_energy - batt_energy
    if new_peak_energy < 0:
        new_peak_energy = 0
    new_off_energy = off_energy + (batt_energy * 1.2)

    return new_peak_energy, day_energy, new_off_energy, battery_time

"""This function calculates the present value"""
def presentValue(future_value, inflation_rate, year):
    FV = float(future_value)
    r = float(inflation_rate)
    n = float(year)

    PV = float(FV / ((1 + r) ** n))

    return PV

"""This function calculates the payback period for a battery"""
def payback(battery_cost, savings):
    payback = float(battery_cost)/savings
    return payback

#=CALCULATING NPV================================================================================

"""This function calculates the ratios between the energy from bills to recorded energy"""
def generateEnergyRatios(month_energy, monthly_energies):

    ratios = []
    for row in monthly_energies:
        bill_energy = float(row[1])
        ratio = bill_energy/month_energy
        ratios.append(round(ratio,2))

    return ratios

"""This function creates artificial load data for all months based on the calculated ratios"""
def generateNewData(month_data, month_energy,month_energies):

    ratios = generateEnergyRatios(month_energy,month_energies)

    new_month_data_list = []
    for x in ratios:

        ratio = x
        new_month_data = []
        for row in month_data:

            load = row[1]
            new_data = []
            new_load = []
            new_current_batt = []
            new_load_batt = []
            for row_data in load:

                time_str = row_data[0]
                time_f = row_data[1]
                current = row_data[2]

                new_current = current * ratio
                new_quantized_current = int(new_current) + 1

                new_data.append([time_str,time_f,new_quantized_current])
                new_load.append([time_str,time_f,new_current])
                new_current_batt.append(new_current)
                new_load_batt.append([time_f,new_current])

            new_month_data.append([new_data,new_load,new_current_batt,new_load_batt])

        new_month_data_list.append(new_month_data)

    return new_month_data_list

"""This function calculates the available battery capacity for each year up to the end of the battery lifetime"""
def getDepreciatedCapacities(capacity, dep_rate, years):

    constant_capacity = 4
    depreciated_capacities = []

    if years> constant_capacity:
        for i in range(1, years + 1):
            y = i
            if i <= constant_capacity:
                r = 0
            else:
                r = dep_rate
                i = i - constant_capacity

            dep_capacity = capacity * (1 - r) ** i

            depreciated_capacities.append([y, round(dep_capacity, 2)])
    else:
        for i in range(1, years+1):
            r = 0
            dep_capacity = capacity * (1 - r) ** i

            depreciated_capacities.append([i, round(dep_capacity, 2)])

    return depreciated_capacities

"""This function calculates the total present outflow for a given battery capacity"""
def presentOutflow(capacity, batt, inverter_size, inverter_data):

    batterycosts = []
    for row in batt:
        if int(row[4]) == capacity:
            battery_cost = float(row[5])
            charger_cost = float(row[3])
            batterycosts.append([battery_cost, charger_cost])

    inverter_price = get_inverter_price(inverter_size, inverter_data)

    switchgear_price = 4500
    other_cost = 9000
    tou_tariff_change = 10050

    total_cost = batterycosts[0][0] + batterycosts[0][1] + inverter_price + \
                 switchgear_price + other_cost + tou_tariff_change

    return total_cost

#=FOR BLOCK TARIFF=#

"""This function calculates the monthly savings obtained for a block tariff consumer"""
def getMonthSaving_block(capacity, new_month_data, dod, peak_rate, day_rate, off_rate, exponent):

    batt_dod = capacity * dod

    monthly_savings = 0
    total_monthly_energy = 0
    total_peak = 0
    total_day = 0
    total_off = 0
    battery_time = 0
    for row in new_month_data:
        data = row[0]
        load = row[1]
        current_batt = row[2]
        load_batt = row[3]

        peak_energy, day_energy, off_energy = getEnergies(load_batt)

        total_energy = energies(load_batt, 24)
        total_monthly_energy += total_energy

        new_peak_energy, new_day_energy, new_off_energy,battery_time = getNewEnergies(batt_dod, data, load, peak_energy, day_energy,off_energy,exponent)
        total_peak += new_peak_energy
        total_day += new_day_energy
        total_off += new_off_energy

    block_tariff_cost = block_cost(total_monthly_energy)

    time_of_use = (total_peak * peak_rate) + (total_day * day_rate) + (total_off * off_rate) + 540

    monthly_savings = block_tariff_cost - time_of_use

    return monthly_savings, battery_time

"""This function calculates the annual savings for a block tariff consumer"""
def getAnnualSaving_block(capacity, month_data, month_energy, month_energies, dod, peak_rate, day_rate, off_rate, exponent):

    new_month_data_list = generateNewData(month_data, month_energy, month_energies)

    annual_savings = 0
    battery_time = 0
    for row in new_month_data_list:

        monthly_savings,battery_time = getMonthSaving_block(capacity,row,dod,peak_rate, day_rate, off_rate, exponent)
        annual_savings = annual_savings + monthly_savings

    return annual_savings, battery_time

"""This function calculates the total present inflow for a block tariff consumer"""
def presentInflow_block(dep_caps,month_data, month_energy, month_energies, dod, inflation, peak_rate, day_rate, off_rate, exponent):

    future_values = []
    present_values = []
    battery_time_original = 0
    for row in dep_caps:

        annual_savings, battery_time = getAnnualSaving_block(row[1], month_data, month_energy, month_energies, dod,peak_rate, day_rate, off_rate, exponent)

        future_values.append([row[0], round(annual_savings, 2)])

        present_value = presentValue(annual_savings, inflation, row[0])

        present_values.append([row[0], round(present_value, 2)])

        if row == dep_caps[0]:
            battery_time_original = battery_time

    sum = 0
    for row in present_values:
        sum = sum + row[1]

    return sum, battery_time_original

"""This function calculates the net present value for a block tariff consumer for a given battery capacity"""
def NPV_block(capacity, peak_rate, day_rate, off_rate, batt, inverter_size, dep_rate, life_time, month_data, month_energy, month_energies, dod, inflation, weights, inverter_data, exponent):

    presentOutflow_value = presentOutflow(capacity, batt, inverter_size, inverter_data)

    dep_caps = getDepreciatedCapacities(capacity, dep_rate, life_time)

    presentInflow_value, battery_time = presentInflow_block(dep_caps, month_data, month_energy, month_energies, dod,inflation,peak_rate, day_rate, off_rate, exponent)
    battery_weight = 0
    for row in weights:
        if row[0] == capacity:
            try:
                battery_weight = float(row[1])
            except:
                battery_weight = 0

    scrap_value = (battery_weight*150) * 6

    scrap_value = presentValue(scrap_value,inflation,life_time)

    presentInflow_value += scrap_value

    NPV_value = presentInflow_value - presentOutflow_value

    return NPV_value, battery_time

#=FOR TIME-OF-USE TARIFF=#

"""This function calculates the monthly savings for a time-of-use tariff consumer"""
def getMonthSaving_tou(capacity, new_month_data, dod, peak_rate, day_rate, off_rate,exponent):

    batt_dod = capacity * dod

    monthly_savings = 0
    total_monthly_energy = 0
    total_peak = 0
    total_day = 0
    total_off = 0
    total_new_peak = 0
    total_new_day = 0
    total_new_off = 0
    for row in new_month_data:
        data = row[0]
        load = row[1]
        current_batt = row[2]
        load_batt = row[3]

        peak_energy, day_energy, off_energy = getEnergies(load_batt)

        total_peak += peak_energy
        total_day += day_energy
        total_off += off_energy

        new_peak_energy, new_day_energy, new_off_energy, battery_time = getNewEnergies(batt_dod, data, load, peak_energy, day_energy, off_energy, exponent)
        total_new_peak += new_peak_energy
        total_new_day += new_day_energy
        total_new_off += new_off_energy

    time_of_use_without = (total_peak * peak_rate) + (total_day * day_rate) + (total_off * off_rate) + 540
    time_of_use_with = (total_new_peak * peak_rate) + (total_new_day * day_rate) + (total_new_off * off_rate) + 540

    monthly_savings = time_of_use_without - time_of_use_with

    return monthly_savings

"""This function calculates the annual savings for a time-of-use tariff consumer"""
def getAnnualSaving_tou(capacity,month_data, month_energy, month_energies,dod, peak_rate, day_rate, off_rate, exponent):

    new_month_data_list = generateNewData(month_data, month_energy, month_energies)

    annual_savings = 0
    for row in new_month_data_list:
        monthly_savings = getMonthSaving_tou(capacity,row,dod,peak_rate, day_rate, off_rate, exponent)

        annual_savings = annual_savings + monthly_savings

    return annual_savings

"""This function calculates the total present inflow for a time-of-use tariff consumer"""
def presentInflow_tou(dep_caps,month_data, month_energy, month_energies, dod, inflation, peak_rate, day_rate, off_rate, exponent):

    future_values = []
    present_values = []
    for row in dep_caps:
        annual_savings = getAnnualSaving_tou(row[1], month_data, month_energy, month_energies, dod, peak_rate, day_rate, off_rate, exponent)

        future_values.append([row[0], round(annual_savings, 2)])

        present_value = presentValue(annual_savings, inflation, row[0])

        present_values.append([row[0], round(present_value, 2)])

    sum = 0
    for row in present_values:
        sum = sum + row[1]

    total_presentInflow = sum

    return total_presentInflow

"""This function calculates the net present value for a time-of-use tariff consumer for a given battery capacity"""
def NPV_tou(capacity, peak_rate, day_rate, off_rate, batt, inverter_size, dep_rate, life_time, month_data, month_energy, month_energies, dod, inflation, weights, inverter_data, exponent):

    presentOutflow_value = presentOutflow(capacity, batt, inverter_size, inverter_data)

    dep_caps = getDepreciatedCapacities(capacity, dep_rate, life_time)

    presentInflow_value = presentInflow_tou(dep_caps, month_data, month_energy, month_energies, dod, inflation, peak_rate, day_rate, off_rate, exponent)
    battery_weight = 0
    for row in weights:
        if row[0] == capacity:
            try:
                battery_weight = float(row[1])
            except:
                battery_weight = 0

    scrap_value = (battery_weight*150) * 6

    scrap_value = presentValue(scrap_value,inflation,life_time)

    presentInflow_value += scrap_value

    NPV_value = presentInflow_value - presentOutflow_value

    return NPV_value

#=PROGRAM INTERFACE=====================================================================================================

class App(Tk):

    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)

        self.wm_title("Project Interface")
        # self.geometry('700x400')

        self.container = Frame(self)
        self.container.pack(side = "top", fill = "both", expand = True)

        self.container.grid_rowconfigure(0, weight = 1)
        self.container.grid_columnconfigure(0, weight = 1)

        self.frames = {}

        for F in (StartPage, GraphPage, PageTwo):
            frame = F(self.container, self)
            self.frames[F] = frame
            frame.grid(row = 0, column = 0, sticky = "nsew")

        self.show_frame(StartPage)

    def show_frame(self, cont):

        frame = self.frames[cont]
        frame.tkraise()

class StartPage(Frame):

    def __init__(self, parent, controller):
        Frame.__init__(self, parent)

        browse_frame = Frame(self)
        browse_frame.grid(row = 0, column = 0)
        browse_frame.configure(pady=10, padx = 10)

        frame_two = Frame(self)
        frame_two.grid(row = 1, column = 0)
        frame_two.configure()

        frame_three = LabelFrame(self, text = 'Constants:')
        frame_three.grid(row = 2, column = 0)
        frame_three.configure(pady = 10)

        frame_four = Frame(self)
        frame_four.grid(row = 3, column = 0)
        frame_four.configure(pady = 10)

        frame_five = Frame(self)
        frame_five.grid(row=4, column=0)
        frame_five.configure()

        frame_six = Frame(self)
        frame_six.grid(row=5, column=0)
        frame_six.configure(pady = 10)

        frame_seven = Frame(self)
        frame_seven.grid(row=6, column=0)
        frame_seven.configure(pady=10)

        # =Browse Frame======================================================================

        #obtain the path for the load data directory
        label_data = ttk.Label(browse_frame, text = 'Select directory for load data:')
        label_data.grid(row = 0, columnspan = 2, sticky = W)
        # label_data.pack(side = LEFT)

        button_data = ttk.Button(browse_frame, text = 'Browse', command = lambda: self.browse_data(entry_data))
        button_data.grid(row = 1, column = 0)

        entry_data_value = StringVar()
        entry_data = ttk.Entry(browse_frame, textvariable = entry_data_value, width = 50)
        entry_data.grid(row = 1, column = 1)

        #obtain the path for the battery details csv
        label_battery = ttk.Label(browse_frame, text='Select file for battery details:')
        label_battery.grid(row=2, columnspan=2, sticky = W)

        button_battery = ttk.Button(browse_frame, text='Browse', command=lambda: self.browse_func(entry_battery))
        button_battery.grid(row=3, column=0)

        entry_battery_value = StringVar()
        entry_battery = ttk.Entry(browse_frame, textvariable=entry_battery_value, width=50)
        entry_battery.grid(row=3, column=1)


        #obtain the path for the inverter details csv
        label_inverter = ttk.Label(browse_frame, text='Select file for inverter details:')
        label_inverter.grid(row=4, columnspan=2, sticky = W)

        button_inverter = ttk.Button(browse_frame, text='Browse', command=lambda: self.browse_func(entry_inverter))
        button_inverter.grid(row=5, column=0)

        entry_inverter_value = StringVar()
        entry_inverter = ttk.Entry(browse_frame, textvariable=entry_inverter_value, width=50)
        entry_inverter.grid(row=5, column=1)


        # obtain the path for the monthly energies csv
        label_energies = ttk.Label(browse_frame, text='Select file for monthly energies:')
        label_energies.grid(row=6, columnspan=2, sticky = W)

        button_energies = ttk.Button(browse_frame, text='Browse', command=lambda: self.browse_func(entry_energies))
        button_energies.grid(row=7, column=0)

        entry_energies_value = StringVar()
        entry_energies = ttk.Entry(browse_frame, textvariable=entry_energies_value, width=50)
        entry_energies.grid(row=7, column=1)

        # =Frame Two======================================================================

        self.label_tariff_warning = Label(frame_two)
        self.label_tariff_warning.grid(row = 0, columnspan = 2)

        label_tariff = ttk.Label(frame_two, text = 'Select the tariff used:  ')
        label_tariff.grid(row = 1, column = 0)

        tariff_value = StringVar
        combo_tariff = ttk.Combobox(frame_two, textvariable = tariff_value, state = 'readonly')
        combo_tariff['values'] = ('Block Tariff', 'Time-of-Use Tariff')
        combo_tariff.grid(row = 1, column = 1)

        #=Frame Three========================================================================

        self.label_dod = ttk.Label(frame_three, text = 'Depth of discharge:')
        self.label_dod.grid(row = 0, column = 0)

        entry_dod_value = DoubleVar()
        entry_dod_value.set(0.6)
        self.entry_dod = Entry(frame_three, textvariable=entry_dod_value, width=5, state = 'disabled')
        self.entry_dod.grid(row=0, column=1)


        self.label_dep = ttk.Label(frame_three, text='Depreciation rate:')
        self.label_dep.grid(row=1, column=0)

        entry_dep_value = DoubleVar()
        entry_dep_value.set(0.4)
        self.entry_dep = Entry(frame_three, textvariable=entry_dep_value, width=5, state='disabled')
        self.entry_dep.grid(row=1, column=1)


        self.label_inf = ttk.Label(frame_three, text='Inflation rate:')
        self.label_inf.grid(row=0, column=2)

        entry_inf_value = DoubleVar()
        entry_inf_value.set(0.07)
        self.entry_inf = Entry(frame_three, textvariable=entry_inf_value, width=5, state='disabled')
        self.entry_inf.grid(row=0, column=3)


        self.label_life = ttk.Label(frame_three, text='Battery life time:')
        self.label_life.grid(row=1, column=2)

        entry_life_value = IntVar()
        entry_life_value.set(5)
        self.entry_life = Entry(frame_three, textvariable=entry_life_value, width=5, state='disabled')
        self.entry_life.grid(row=1, column=3)

        button_change = ttk.Button(frame_three, text = 'Change Values', command = self.change_disable)
        button_change.grid(row = 2, columnspan = 4)

        #=Frame Four========================================================================

        self.label_response_value = 'Please check the inputs and compute'
        self.label_response = ttk.Label(frame_four, text = self.label_response_value)
        self.label_response.grid(row = 0, column = 0)

        #=Frame Five========================================================================

        button_verify = ttk.Button(frame_five, text = 'Verify', command = self.change_label)
        button_verify.grid(row = 0, column = 0)

        button_compute = ttk.Button(frame_five, text='Compute',
                                    command = lambda: self.compute_optimum(entry_data_value, entry_battery_value,
                                                                            entry_inverter_value, entry_energies_value,
                                                                            entry_dod_value, entry_inf_value,
                                                                            entry_dep_value, entry_life_value,
                                                                           combo_tariff))
        button_compute.grid(row=0, column=1)

        #=Frame Six========================================================================

        self.progressbar = ttk.Progressbar(frame_six, orient="horizontal", length=300, mode="determinate")
        self.progressbar["value"] = 0
        # self.progressbar["maximum"] = 40
        self.progressbar.grid(row=0, column = 0)

        #=Frame Seven========================================================================

        self.label_output = ttk.Label(frame_seven)
        self.label_output.grid(row = 0, column = 0)




    # browse the file and insert the file path into the entry
    def browse_data(self, entry):
        entry.delete(0, END)
        # fileName = askopenfilename(parent=self)
        directoryPath = askdirectory()
        entry.insert(0, directoryPath)

    def browse_func(self, entry):
        entry.delete(0, END)
        fileName = askopenfilename(parent=self)
        # directoryPath = askdirectory()
        entry.insert(0, fileName)

    def change_disable(self):
        self.entry_dod.configure(state = 'normal')
        self.entry_dep.configure(state='normal')
        self.entry_inf.configure(state='normal')
        self.entry_life.configure(state='normal')

    def compute_optimum(self,entry_data_value, entry_battery_value, entry_inverter_value, entry_energies_value,
                        entry_dod_value, entry_inf_value, entry_dep_value, entry_life_value, combo_tariff):

        self.label_output['text'] = "Computing optimum value... 0%"

        directory = entry_data_value.get()
        battery_path = entry_battery_value.get()
        inverter_path = entry_inverter_value.get()
        energies_path = entry_energies_value.get()

        dod = entry_dod_value.get()
        inflation = entry_inf_value.get()
        dep_rate = entry_dep_value.get()
        life_time = entry_life_value.get()

        tariff = combo_tariff.get()

        exponent = 1.17

        if tariff == 'Block Tariff':

            peak_rate = 54
            day_rate = 25
            off_rate = 13

            month_data = getMonthData(directory)

            month_energy = getMonthEnergy(month_data)

            monthly_energies = getMonthlyEnergies(energies_path)

            batt, batt_dod, batt_size, batt_cost, weights = getBatteryList(battery_path, dod)

            inverter_size = inverter_size_for_month(directory)

            inverter_data = inverter(inverter_path)

            self.progressbar["value"] = 0
            self.progressbar["maximum"] = len(batt_size)

            npv_list = []
            npv_battery_list = []
            i = 0
            for row in batt:
                batt_capacity = int(row[4])
                npv, battery_time = NPV_block(batt_capacity, peak_rate, day_rate, off_rate, batt, inverter_size, dep_rate,
                                life_time, month_data, month_energy, monthly_energies, dod, inflation, weights,
                                inverter_data, exponent)
                npv_list.append(npv)
                print(batt_capacity, round(npv, 2))
                i += 1
                self.progressbar["value"] = i
                self.progressbar.update()
                npv_battery_list.append([batt_capacity, npv])
                percentage = ((float(i)/len(batt))*100)
                print(battery_time)
                self.label_output['text'] = "Computing optimum value... " + str(int(percentage)) + "%"


            max_npv = max(npv_list)

            optimum_capacity = 0
            for row in npv_battery_list:
                if row[1] == max_npv:
                    print("Optimum Battery Capacity: " + str(row[0]))
                    self.label_output['text'] = "Optimum Battery Capacity: " + str(row[0]) + " Ah"
                    optimum_capacity = row[0]

            total_cost = presentOutflow(optimum_capacity,batt, inverter_size, inverter_data)
            annual_savings, time = getAnnualSaving_block(optimum_capacity,month_data, month_energy,
                                                 monthly_energies,dod, peak_rate, day_rate, off_rate,exponent)

            print(payback(total_cost,annual_savings))

            #================================================================================

            fig, ax = plt.subplots()

            # Twin the x-axis twice to make independent y-axes.
            # axes = [ax, ax.twinx()]
            axes = [ax]

            # Make some space on the right side for the extra y-axis.
            fig.subplots_adjust(left=0.2)

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
            # ax2 = axes[1]

            # markers_on = []
            # for i in range(len(batt)):
            #     if batt[i][0] == batt[i][1]:
            #         markers_on.append(i)

            # plt.plot(batt_size,total_cost,'-gD', markevery=markers_on)

            # plt.xlabel('Battery Capacity (Ah)')
            # plt.ylabel('Total Cost (Rs.)')
            # plt.title('Total Cost vs. Battery Capacities for ' + str(month) + ' ' + str(day))
            plt.title('Net Present Value (NPV) vs. Battery Capacity')
            # plt.show()

            ax1.plot(batt_size, npv_list, '-gD', color='Green', marker = ',')
            ax1.set_ylabel('Net Present Value (NPV)')
            ax1.tick_params(axis='y', colors='Green')
            ax1.set_xlabel('Battery Capacity (Ah)')
            # ax1.set_ylim((max_npv * -1), (max_npv + 10000))
            # ax1.set_xlim(0, optimum_capacity*2)
            ax1.set_xlim(0,max(batt_size))
            ax1.xaxis.grid()

            start, end = ax1.get_xlim()
            ax1.xaxis.set_ticks(np.arange(start, end, 120))

            # xticks = ax1.xaxis.get_major_ticks()
            # xticks[0].label1.set_visible(True)
            #
            # ax2.plot(batt_size, running_time, '--', markevery=markers_on, color='Red')
            # ax2.set_ylabel('Battery Running Time (h)')
            # ax2.tick_params(axis='y', colors='Red')
            # ax2.yaxis.grid()

            #==========================================================================

            plt.show()

        elif tariff == 'Time-of-Use Tariff':

            peak_rate = 54
            day_rate = 25
            off_rate = 13

            month_data = getMonthData(directory)

            month_energy = getMonthEnergy(month_data)

            monthly_energies = getMonthlyEnergies(energies_path)

            batt, batt_dod, batt_size, batt_cost, weights = getBatteryList(battery_path, dod)

            max_load_for_the_month = inverter_size_for_month(directory)

            inverter_data = inverter(inverter_path)

            npv_list = []
            npv_battery_list = []
            i = 0
            for row in batt:
                batt_capacity = int(row[4])
                npv = NPV_tou(batt_capacity, peak_rate, day_rate, off_rate, batt, max_load_for_the_month, dep_rate,
                              life_time, month_data, month_energy, monthly_energies, dod, inflation, weights,
                              inverter_data, exponent)

                npv_list.append(npv)
                print(batt_capacity, round(npv, 2))
                i += 1
                self.progressbar["value"] = i
                self.progressbar.update()
                npv_battery_list.append([batt_capacity, npv])

            #================================================================================
            fig, ax = plt.subplots()

            # Twin the x-axis twice to make independent y-axes.
            # axes = [ax, ax.twinx()]
            axes = [ax]

            # Make some space on the right side for the extra y-axis.
            fig.subplots_adjust(left=0.2)

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
            # ax2 = axes[1]

            markers_on = []
            for i in range(len(batt)):
                if batt[i][0] == batt[i][1]:
                    markers_on.append(i)

            # plt.plot(batt_size,total_cost,'-gD', markevery=markers_on)

            # plt.xlabel('Battery Capacity (Ah)')
            # plt.ylabel('Total Cost (Rs.)')
            # plt.title('Total Cost vs. Battery Capacities for ' + str(month) + ' ' + str(day))
            plt.title('Net Present Value (NPV) vs. Battery Capacity')
            # plt.show()

            ax1.plot(batt_size, npv_list, '-gD', markevery=markers_on, marker='o', markersize=7, markeredgewidth=1,
                     markeredgecolor='g', markerfacecolor='None', color='Green')
            ax1.set_ylabel('Net Present Value (NPV)')
            ax1.tick_params(axis='y', colors='Green')
            ax1.set_xlabel('Battery Capacity (Ah)')
            # ax1.set_ylim((max_npv * -1), (max_npv + 10000))
            # ax1.set_xlim(0, optimum_capacity*2)
            ax1.set_xlim(0,1200)
            ax1.xaxis.grid()

            start, end = ax1.get_xlim()
            ax1.xaxis.set_ticks(np.arange(start, end, 120))

            xticks = ax1.xaxis.get_major_ticks()
            xticks[0].label1.set_visible(True)
            #
            # ax2.plot(batt_size, running_time, '--', markevery=markers_on, color='Red')
            # ax2.set_ylabel('Battery Running Time (h)')
            # ax2.tick_params(axis='y', colors='Red')
            # ax2.yaxis.grid()

            #=================================================================================

            max_npv = max(npv_list)
            for row in npv_battery_list:
                if row[1] == max_npv:
                    print("Optimum Battery Capacity: " + str(row[0]))
                    self.label_output['text'] = "Optimum Battery Capacity: " + str(row[0]) + " Ah"

        else:
            self.label_tariff_warning.configure(text='Please select the tariff')
            self.label_tariff_warning.configure(foreground='red')

    def change_label(self):
        self.label_response.configure(text = 'All set!')

class GraphPage(Frame):

    def __init__(self, parent, controller):
        Frame.__init__(self, parent)

        label = Label(self, text='Graph Page')
        label.pack()

        button = Button(self, text='Home', command=lambda: controller.show_frame(StartPage))
        button.pack()

class PageTwo(Frame):

    def __init__(self, parent, controller):
        Frame.__init__(self, parent)

root = App()
root.mainloop()

# -----------------------------------------------------------------------------------------------------------------------

# fig, ax = plt.subplots()
#
# # Twin the x-axis twice to make independent y-axes.
# axes = [ax, ax.twinx()]
#
# # Make some space on the right side for the extra y-axis.
# # fig.subplots_adjust(right=0.75)
#
# # Move the last y-axis spine over to the right by 20% of the width of the axes
# # axes[-1].spines['right'].set_position(('axes', 1.2))
#
# # To make the border of the right-most axis visible, we need to turn the frame
# # on. This hides the other plots, however, so we need to turn its fill off.
# axes[-1].set_frame_on(True)
# axes[-1].patch.set_visible(False)
#
# # And finally we get to plot things...
# # colors = ('Green', 'Red')
# # for ax, color in zip(axes, colors):
# #     ax.plot(data, marker='o', linestyle='none', color=color)
# #     ax.set_ylabel('%s Thing' % color, color=color)
# #     ax.tick_params(axis='y', colors=color)
# # axes[0].set_xlabel('X-axis')
#
# ax1 = axes[0]
# ax2 = axes[1]
#
# markers_on = []
# for i in range(len(batt)):
#     if batt[i][0] == batt[i][1]:
#         markers_on.append(i)
#
# # plt.plot(batt_size,total_cost,'-gD', markevery=markers_on)
#
# # plt.xlabel('Battery Capacity (Ah)')
# # plt.ylabel('Total Cost (Rs.)')
# # plt.title('Total Cost vs. Battery Capacities for ' + str(month) + ' ' + str(day))
# # plt.title('Total Cost vs. Battery Capacities for 2-Week 1')
# # plt.show()
#
# ax1.plot(batt_size, npv_list, '-gD', markevery=markers_on, marker='o', markersize=7, markeredgewidth=1,
#          markeredgecolor='g', markerfacecolor='None', color='Green')
# ax1.set_ylabel('Total Cost (Rs.)')
# ax1.tick_params(axis='y', colors='Green')
# ax1.set_xlabel('Battery Capacity (Ah)')
# ax1.xaxis.grid()
#
# start, end = ax1.get_xlim()
# ax1.xaxis.set_ticks(np.arange(start, end, 20))
#
# xticks = ax1.xaxis.get_major_ticks()
# xticks[0].label1.set_visible(False)
# #
# # ax2.plot(batt_size, running_time, '--', markevery=markers_on, color='Red')
# # ax2.set_ylabel('Battery Running Time (h)')
# # ax2.tick_params(axis='y', colors='Red')
# # ax2.yaxis.grid()
#
# plt.show()

# def printModifiedLoad():
#     path = "E:/FYP USA Test Data/USA January/1.csv"
#
#     data, load, current_batt, load_batt = getLoadData(path)
#
#     batt_dod = 240 * 0.6
#
#     battery_load, battery_time = supplied_by_battery(data, batt_dod, load)
#     batt_energy = energies(battery_load, battery_time)
#
#     total_time = battery_time
#
#     h = int(total_time)
#     m = int((total_time - h) * 60)
#     time_v = datetime.time(h, m, 0)
#
#     # print(time_v)
#
#     start_time = datetime.datetime(2018, 3, 14, 18, 30, 0)
#     end_time = start_time + datetime.timedelta(hours=h, minutes=m)
#
#     end_time = end_time.time()
#     start_time = start_time.time()
#
#     day_starttime = datetime.time(0, 0, 0)
#     end_of_offpeak = datetime.time(5, 30, 0)
#     end_of_peak = datetime.time(22, 30, 0)
#     day_endtime = datetime.time(23, 59, 59)
#
#     average_value = (batt_energy) / 7
#
#     affected_load_data = []
#     for row in load:
#         load_value = row[2]*0.23
#         if row[1] >= start_time and row[1] <= end_time:
#             affected_load_data.append([row[0], 0, 0,load_value])
#         elif ((row[1] >= day_starttime and row[1] <= end_of_offpeak) or (
#                 row[1] > end_of_peak and row[1] <= day_endtime)):
#             affected_load_data.append([row[0], load_value, average_value,0])
#         else:
#             affected_load_data.append([row[0], load_value, 0,0])
#
#     return_path = 'C:/Users/DELL/Dropbox/Main Battery Program/Reference Data/load_with_system 3.csv'
#     return_file = open(return_path, 'wb')
#     writer = csv.writer(return_file)
#
#     for row in affected_load_data:
#         writer.writerow([row[0], row[1], row[2],row[3]])
#
#     return_path2 = 'C:/Users/DELL/Dropbox/Main Battery Program/Reference Data/load_without_system 3.csv'
#     return_file2 = open(return_path2, 'wb')
#     writer = csv.writer(return_file2)
#
#     for row in load:
#         kwh = row[2]*0.23
#         writer.writerow([row[0], kwh])

# printModifiedLoad()