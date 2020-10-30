import csv

month = ['June', 'June', 'June', 'June', 'June', 'June', 'June']
days_week = ['16', '17', '18', '19', '20', '21', '22']

input = []
for i in range(len(month)):
    input.append([month[i],days_week[i]])

days = []

path = 'C:/Users/DELL/Dropbox/Data/Ambatale House/Complete Data/'+str(month[0])+'/' + str(days_week[0]) + '.csv'
file = open(path)
reader = csv.reader(file)

time_series = []
for row in reader:
    time_series.append(row[0])

def days_of_week(month, day):

    path = 'C:/Users/DELL/Dropbox/Data/Ambatale House/Complete Data/' +str(month)+ '/' + str(day) + '.csv'
    file = open(path)
    reader = csv.reader(file)

    load = []
    for row in reader:
        load.append(float(row[1]))

    days.append(load)


for row in input:
    days_of_week(row[0],row[1])


week_average = days[0]


def averaged_week(load):

    for i in range(len(time_series)):
        sum = week_average[i] + load[i]
        week_average[i] = sum

for i in range(1,7):

    averaged_week(days[i])

final_data = []
for i in range(len(time_series)):
    final_data.append([time_series[i], round((week_average[i]/7),2)])



return_path = 'C:/Users/DELL/Dropbox/Data/Ambatale House/Complete Data/Week Data/week10.csv'
return_file = open(return_path, 'wb')
writer = csv.writer(return_file)

for row in final_data:
        writer.writerow([row[0], row[1]])





