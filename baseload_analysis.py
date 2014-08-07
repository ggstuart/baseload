import logging
import os.path
from smartdata import SmartspacesCSVAdapter
from matplotlib import pyplot as plt, dates
from pandas import DataFrame 

logging.basicConfig(level=logging.INFO)

do_subset = 0

adapter = SmartspacesCSVAdapter()
datasets = [
    {'lbl': 'Queens', 'id': 3},
    {'lbl': 'Hugh Aston', 'id': 6},
    {'lbl': 'Kimberlin', 'id': 8},	
    {'lbl': 'Campus Centre', 'id': 10},
    {'lbl': 'John Whitehead', 'id': 12},
    {'lbl': '16 New Walk', 'id': 18},
    {'lbl': 'African Caribbean Centre', 'id': 22},
    {'lbl': 'Aylestone Leisure Centre', 'id': 25},
    {'lbl': 'Beaumont Lodge Primary School', 'id': 28},
    {'lbl': 'Belgrave C of E Primary School', 'id': 31},
    {'lbl': 'Belgrave Neighbourhood Centre', 'id': 34},
    {'lbl': 'Braunstone Leisure Centre', 'id': 37},
    {'lbl': 'Coleman Primary School','id': 40},
    {'lbl': 'Cossington St Sports Centre', 'id': 43},
    {'lbl': 'De Monfort Hall', 'id': 46},
    {'lbl': 'Evington Leisure Centre', 'id': 49},
    {'lbl': 'Fosse Primary School', 'id': 52},
    {'lbl': 'Inglehurst Infants School', 'id': 55},
    {'lbl': 'Inglehurst Junior School', 'id': 58},
    {'lbl': 'Knighton Fields Primary School', 'id': 61},
    {'lbl': 'Leicester Leys Leisure Centre', 'id': 64},
    {'lbl': 'New Leicester Central Library', 'id': 68},
    {'lbl': 'New Parks Leisure Centre', 'id': 71},
#    {'lbl': 'New Walk Museum', 'id': 75},
    {'lbl': 'Spence Street Leisure Centre', 'id': 78}
]


def is_number_or_cap(s):
    try:
        float(s)
        return True
    except ValueError:
        return s.isupper()

if do_subset:
    datasets = datasets[:do_subset]

for dataset in datasets:
    print('loading %s...' % dataset['lbl'])
    dataset['dataframe'] = adapter.dataframe(dataset['id'], 'all')

print("Doing some calculations")
for dataset in datasets:
    dataset['daily_min'] = dataset['dataframe'].resample('D', how='min')
    dataset['weekly_min'] = dataset['dataframe'].resample('W', how='min')
    dataset['daily_baseload'] = dataset['daily_min'].resample('30T', fill_method='ffill')
    dataset['weekly_baseload'] = dataset['weekly_min'].resample('30T', fill_method='ffill')
    dataset['daily_sum'] = dataset['dataframe'].resample('D', how='sum')
    dataset['weekly_sum'] = dataset['dataframe'].resample('W', how='sum')

    mymin = max(dataset['dataframe'].index.min(), dataset['daily_baseload'].index.min(), dataset['weekly_baseload'].index.min())
    mymax = min(dataset['dataframe'].index.max(), dataset['daily_baseload'].index.max(), dataset['weekly_baseload'].index.max())

    dataset['dataframe'] = dataset['dataframe'].ix[mymin:mymax]
    dataset['daily_baseload'] = dataset['daily_baseload'].ix[mymin:mymax]
    dataset['weekly_baseload'] = dataset['weekly_baseload'].ix[mymin:mymax]
    dataset['daily_sum'] = dataset['daily_sum'].ix[mymin:mymax]
    dataset['weekly_sum'] = dataset['weekly_sum'].ix[mymin:mymax]

for dataset in datasets:
	dataset['daily'] = {}
	dataset['weekly'] = {}
	dataset['weekly']['baseload'] = {
		'min': dataset['weekly_min']['consumption (kWh)'].min() * 7 * 48,
		'mean': dataset['weekly_min']['consumption (kWh)'].mean() * 7 * 48,
		'median': dataset['weekly_min']['consumption (kWh)'].median() * 7 * 48,
		'max': dataset['weekly_min']['consumption (kWh)'].max() * 7 * 48,
	}
	dataset['weekly']['total'] = {
		'min': dataset['weekly_sum']['consumption (kWh)'].min(),
		'mean': dataset['weekly_sum']['consumption (kWh)'].mean(),
		'median': dataset['weekly_min']['consumption (kWh)'].median(),
		'max': dataset['weekly_sum']['consumption (kWh)'].max(),
	}

#	dataset['daily']['baseload%'] = (dataset['daily']['baseload']['mean'] / dataset['daily']['total']['mean']) * 100
	dataset['weekly']['baseload%'] = (dataset['weekly']['baseload']['mean'] / dataset['weekly']['total']['mean']) * 100

#	dataset['baseload_pct'] = (dataset['weekly']['baseload']['mean'] / dataset['weekly']['total']['mean']) * 100
#   dataset['baseload_pct'] = ((dataset['daily_min'].sum()*48*7/ dataset['daily_sum'].sum()) * 100)['consumption (kWh)']
#	print(dataset['baseload_pct'])

output_folder = 'output'
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

raw_data_folder = os.path.join(output_folder, 'raw_data')
if not os.path.exists(raw_data_folder):
    os.makedirs(raw_data_folder)

print("plotting raw data")
for i, dataset in enumerate(datasets):
    df = dataset['dataframe']
    fig, ax = plt.subplots(1, 1, figsize=(7, 4))
    ax.plot(df.index, df['consumption (kWh)'], 'k-', lw=0.15)
    fig.suptitle("%s\n" % dataset['lbl'])
    ax.set_ylabel('consumption\n(kWh)')
    plt.tight_layout()
    plt.savefig(os.path.join(raw_data_folder, "%s.png" % dataset['lbl']))
    plt.close(fig)


fmt = dates.DateFormatter(fmt="%b\n%Y")
loc = dates.MonthLocator(interval=4)

baseload_folder = os.path.join(output_folder, 'baseload')
if not os.path.exists(baseload_folder):
    os.makedirs(baseload_folder)

print("plotting baseload lines")
for i, dataset in enumerate(datasets):
    fig, ax = plt.subplots(1, 1, figsize=(7, 4), sharex=True)
    ax.set_title("%s\n" % dataset['lbl'])
    ax.plot(dataset['dataframe'].index, dataset['dataframe']['consumption (kWh)'], c='black', label="raw", lw=0.2, alpha=0.2)
    ax.plot(dataset['daily_baseload'].index, dataset['daily_baseload']['consumption (kWh)'], c='blue', label="daily", lw=0.5)
    ax.plot(dataset['weekly_baseload'].index, dataset['weekly_baseload']['consumption (kWh)'], c='red', label="weekly", lw=0.8)
    ax.xaxis.set_major_locator(loc)
    ax.xaxis.set_major_formatter(fmt)
    ax.set_ylabel('minimum daily/weekly\nconsumption (kWh)')
    leg = ax.legend(loc=2)
    plt.tight_layout()
    # plt.savefig("%s.png" % dataset['lbl'])
    plt.savefig(os.path.join(baseload_folder, "%s line.png" % dataset['lbl']))
    plt.close(fig)
	
fmt = dates.DateFormatter(fmt="%b\n%Y")
loc = dates.MonthLocator(interval=4)

print("plotting baseload areas")
for i, dataset in enumerate(datasets):
    fig, ax = plt.subplots(1, 1, figsize=(7, 4), sharex=True)
    ax.set_title("%s\n" % dataset['lbl'])
    ax.plot(dataset['dataframe'].index, dataset['dataframe']['consumption (kWh)'], label='total load', color='blue', lw=0.25)
    ax.plot(dataset['daily_baseload'].index, dataset['daily_baseload']['consumption (kWh)'], label='daily baseload', color='yellow', lw=0.25)
    ax.plot(dataset['weekly_baseload'].index, dataset['weekly_baseload']['consumption (kWh)'], label='weekly baseload', color='red', lw=0.25)
    ax.text(0.01, 0.1, "baseload as proportion of total consumption = %3.1f%%" % dataset['weekly']['baseload%'], transform=ax.transAxes)
    ax.fill_between(dataset['daily_baseload'].index, dataset['daily_baseload']['consumption (kWh)'], dataset['dataframe']['consumption (kWh)'], label="occupied load", color='blue', alpha=0.5, lw=0.2)
    ax.fill_between(dataset['daily_baseload'].index, dataset['weekly_baseload']['consumption (kWh)'], dataset['daily_baseload']['consumption (kWh)'], label="occupied load", color='yellow', alpha=0.5, lw=0.2)
    ax.fill_between(dataset['weekly_baseload'].index, dataset['weekly_baseload']['consumption (kWh)'], label="baseload", color='red', alpha=0.5, lw=0.2)
    ax.set_ylim(0, ax.get_ylim()[1])
    ax.xaxis.set_major_locator(loc)
    ax.xaxis.set_major_formatter(fmt)
    ax.set_ylabel('weekly\nconsumption (kWh)')
    leg = ax.legend(loc=2)
    plt.tight_layout()
    plt.savefig(os.path.join(baseload_folder, "%s area.png" % dataset['lbl']))
    plt.close(fig)


hist_folder = os.path.join(output_folder, 'histogram')
if not os.path.exists(hist_folder):
    os.makedirs(hist_folder)

print("plotting histograms")
for i, dataset in enumerate(datasets):    
    fig, ax = plt.subplots(1, 1, figsize=(7, 4), sharex=True)
    # df=DataFrame(dataset['weekly_min']['consumption (kWh)'], dataset['weekly_sum']['consumption (kWh)']) 
    # df.hist(ax=axes, bins=25, stacked=True)  
    n, bins, patches = ax.hist(dataset['dataframe']['consumption (kWh)'], bins=25, label='total load', color='blue', alpha=0.5)
    ax.hist(dataset['weekly_baseload']['consumption (kWh)'], bins=bins, label='baseload', color='red', alpha=0.5)
    ax.set_xlabel('consumption\n(kWh)')
    ax.set_title (dataset['lbl'])
    ax.set_xlim(0, ax.get_xlim()[1])
    plt.tight_layout()
    # plt.savefig("Histogram/%s.png" % dataset['lbl'])	
    plt.savefig(os.path.join(hist_folder, "%s.png" % dataset['lbl']))
    plt.close(fig)

# import csv
# with open('csv/output.csv','wb') as f:
	# writer = csv.writer(f)
	# writer.writerow(['','','Baseload','','','total',''])
	# writer.writerow(['Building','min','mean','median','max','min','mean','median','max','percent'])
	# for i, dataset in enumerate(datasets):
		# b = dataset['weekly']['baseload']
		# t = dataset['weekly']['total']
		# writer.writerow([dataset['lbl'],b['min'],b['mean'],b['median'],b['max'],t['mean'],t['median'],t['min'],t['max'], dataset['baseload_pct']])
		# writer.writerow([dataset['lbl'],dataset['baseload_pct']])

# import csv
# with open('csv/percentile.csv','wb') as f:
    # writer = csv.writer(f)
    # writer.writerow(['','','Baseload','','','total',''])
    # writer.writerow(['Building','min','mean','median','max','min','mean','median','max','percent'])
    # for i, dataset in enumerate(datasets):
        # b = dataset['weekly']['baseload']
        # t = dataset['weekly']['total']
        # prctile(dataset['weekly_min']['consumption (kWh)'], p=(10.0, 25.0, 50.0, 75.0, 100.0), label='baseload')
        # prctile(dataset['weekly_sum']['consumption (kWh)'], p=(10.0, 25.0, 50.0, 75.0, 100.0), label='total load')
        # writer.writerow([dataset['lbl'], dataset['baseload_pct']])

		
# fmt = dates.DateFormatter(fmt="%b\n%Y")
# loc = plt.Locator(interval=datasets)
		
boxdata = []
for i, dataset in enumerate(datasets):
	boxdata.append(dataset['weekly_min']['consumption (kWh)'])

fig, ax = plt.subplots(1, 1, figsize=(7, 4), sharex=True)
#data = ([dataset['lbl'], dataset['weekly']['baseload%']])
ax.boxplot(boxdata)

lbls = [''.join(c for c in d['lbl'] if is_number_or_cap(c)) for d in datasets]

ax.set_labels=lbls#('Queens','H.A','K.b','C.C','J.W','16 N.W','A.C.C','A.L.C','B.L.P.S','Bel C.E',
#'Bel N.C','B.L.C','C.P.S','C.S.S','DMH','E.L.C','F.P.S','I.I.S','I.J.S','K.F.PS','L.Leys','New L.C.','New Parks','New Walk','Spence Strt')
# ax.set_labels=('Queens','H.A','K.b','C.C','J.W','16 N.W','A.C.C','A.L.C','B.L.P.S','Bel C.E',
# 'Bel N.C','B.L.C','C.P.S','C.S.S','DMH','E.L.C','F.P.S')
plt.xticks ([1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25],ax.set_labels, fontsize=6,rotation=60)
# plt.xticks ([1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17],ax.set_labels, fontsize=6,rotation=60)
ax.set_xlabel('Buildings')
# ax.xaxis.set_major_locator(loc)
# ax.xaxis.set_major_formatter(fmt)
ax.set_ylabel('weekly usage (kWh)')	
ax.set_title ('weekly baseload consumption')
plt.tight_layout()
plt.savefig(os.path.join(output_folder, "Box Chart.png"))
# plt.close()	 
