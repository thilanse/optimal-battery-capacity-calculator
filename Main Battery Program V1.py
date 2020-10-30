import csv
import datetime
import matplotlib.pyplot as plt
import numpy as np


month = 'March'
day = 14

path = "C:/Users/DELL/Dropbox/Data/Ambatale House/1 min Averaged Sampled Data/" + month + "/" + str(day)+ ".csv"

# path = 'C:/Users/DELL/Dropbox/Data/Ambatale House/Complete Data/Month Data/May.csv'
# path = 'C:/Users/DELL/Dropbox/Data/Ambatale House/Complete Data/Week Data/week1.csv'
# path = 'C:/Users/DELL/Dropbox/Data/Ambatale House/Complete Data/2 Week Data/2week1.csv'


file = open(path)
reader = csv.reader(file)

data = []
load = []
load_batt = []
current_batt =[]
for row in reader:

    time = datetime.datetime.strptime(row[0], '%H:%M:%S')
    time_f = datetime.time(time.hour,time.minute)
    time_str = str(time_f)
    current = int(float(row[1]))

    data.append([time_str, time_f, current])
    load.append([time_str,time_f,float(row[1])])
    current_batt.append(float(row[1]))
    load_batt.append([time_f, float(row[1])])

#-----------------------------------------------------------------------------------------------------------------------

#Extract the data which can be provided by the given battery capacity

def supplied_by_battery(data, capacity):

    start_time = datetime.time(18, 30, 0)
    end_time = datetime.time(22, 30, 0)

    peak_current = [row[2] for row in data if (row[1] >= start_time and row[1] <= end_time)]
    peak_time = [row[0] for row in data if (row[1] >= start_time and row[1] <= end_time)]

    peak_load = []
    for i in range(len(peak_current)):
        peak_load.append([peak_time[i], peak_current[i]])

    # for row in peak_load:
    #     print(row)

    # plt.plot(peak_time,peak_current)
    # plt.show()

    # calculate discharge time for constant discharge rate
    def peukerts(i, c):
        try:
            t = 20 * ((float(c) / (float(i) * 20)) ** 1.17)
        except:
            t=0
            print("Invalid Current or Capacity")
        return t

    # print(peukerts(10,50))

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

    # for row in frequency:
    #     print(row)

    def actual_discharge_time(list, capacity):

        comparison = []
        for row in list:
            # print(row)
            t = peukerts(row[0], capacity)
            comparison.append([row[0], (row[1]), round(capacity, 2), round(t * 60, 2)])
            cur = row[0]
            c = cur * 20 * (((row[1] / 60) / 20) ** (1 / 1.17))
            capacity = capacity - c
            if capacity <= 0:
                capacity = 0

        for row in comparison:
            print(row)

        sum = 0
        for row in comparison:
            if (row[1] < row[3]):
                sum = sum + row[1]
            else:
                sum = sum + row[3]

        total_time = sum / 60

        if total_time>4:
            total_time=4

        return total_time

    # total_time = actual_discharge_time(frequency, capacity)
    total_test = actual_discharge_time(frequency, 20)

    h = int(total_time)
    m = int((total_time - h) * 60)
    time_v = datetime.time(h, m, 0)

    # print(time_v)

    start_time = datetime.datetime(2018, 3, 14, 18, 30, 0)
    end_time = start_time + datetime.timedelta(hours=h, minutes=m)

    end_time = end_time.time()
    start_time = start_time.time()

    batt_load = [[row[1],row[2]] for row in load if (row[1] >= start_time and row[1] <= end_time)]

    # for row in batt_load:
    #     print(row)

    return batt_load, total_time



#-----------------------------------------------------------------------------------------------------------------------

path2 = "C:/Users/DELL/Dropbox/Data/batt_details 3.csv"
file2 = open(path2)
battery_details = csv.reader(file2)

batt = []
for row in battery_details:
    batt.append(row)

max_load = max(current_batt)

inverter_size = ((max_load+(max_load*0.25))*230.0)
# print 'Invert size: '+str(inverter_size)+' W'
inverter_prize = 5000
switchgear_prize = 4500
other_cost = 9000
dod = 0.6

batt2 = []
batt_size = []
for row in batt:
    batt2.append(float(row[0])*dod)
    batt_size.append(int(row[0]))

batt_cost = []
for i in range(len(batt)):
    cost = float(batt[i][2])+float(batt[i][3])+inverter_prize+switchgear_prize+other_cost
    batt_cost.append(round(cost/(365),2))

starttime = datetime.time(0,0,0)
end_of_offpeak = datetime.time(5,30,0)
mintime = datetime.time(18,30,0)
maxtime = datetime.time(22,30,0)
endtime = datetime.time(23,59,59)

peak_load = [row for row in load_batt if(row[0]>=mintime and row[0]<=maxtime)]
off_load = [row for row in load_batt if((row[0]>=starttime and row[0]<=end_of_offpeak) or (row[0]>maxtime and row[0]<=endtime))]
day_load = [row for row in load_batt if(row[0]>end_of_offpeak and row[0]<mintime)]


def energies(load,hours):
    sum = 0
    for row in load:
        sum += float(row[1])
    average = sum/len(load)
    energy = average * hours * 0.23
    return energy

peak_energy = energies(peak_load,4)
day_energy = energies(day_load,13)
off_energy = energies(off_load,7)


new_energy = []
running_time = []
for row in batt2:

    battery_load, battery_time = supplied_by_battery(data, row)
    batt_energy = energies(battery_load, battery_time)

    new_peak_energy = peak_energy - batt_energy
    if new_peak_energy<0:
        new_peak_energy = 0
    new_off_energy  = off_energy + (batt_energy*1.2)

    new_energy.append([(row/(dod*0.23)),round(new_peak_energy,2),round(day_energy,2),round(new_off_energy,2)])

    running_time.append(round(battery_time,2))

energy_cost = []
for i in range(len(new_energy)):

    time_of_use = (new_energy[i][1]*54) + (new_energy[i][2]*25) + (new_energy[i][3]*13)
    energy_cost.append(time_of_use)

total_cost = []
for i in range(len(batt_cost)):
    total = batt_cost[i] + energy_cost[i]
    total_cost.append(round(total,2))

# for i in range(len(batt_size)):
#     print(str(batt_size[i]) + " Ah:  " + str(total_cost[i]))

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
plt.title('Total Cost vs. Battery Capacities for ' + str(month) + ' ' + str(day))
# plt.title('Total Cost vs. Battery Capacities for 2-Week 1')
# plt.show()


ax1.plot(batt_size,total_cost,'-gD', markevery=markers_on, marker = 'o', markersize = 7, markeredgewidth = 1, markeredgecolor = 'g', markerfacecolor = 'None' , color = 'Green')
ax1.set_ylabel('Total Cost (Rs.)')
ax1.tick_params(axis='y', colors='Green')
ax1.set_xlabel('Battery Capacity (Ah)')
ax1.xaxis.grid()

start, end = ax1.get_xlim()
ax1.xaxis.set_ticks(np.arange(start, end,20))

xticks = ax1.xaxis.get_major_ticks()
xticks[0].label1.set_visible(False)



ax2.plot(batt_size,running_time,'--', markevery=markers_on, color = 'Red')
ax2.set_ylabel('Battery Running Time (h)')
ax2.tick_params(axis='y', colors='Red')
ax2.yaxis.grid()


plt.show()

#-----------------------------------------------------------------------------------------------------------------------

#The fixed cost has not been added to the time-of-use tariff calculation - line 203
#The fixed cost is for the month... Include it later
