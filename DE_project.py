import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error as mse
from math import sqrt
import matplotlib.pyplot as plt
import time
import requests
import json
import datetime
import calendar
import scipy.optimize
import plotly.graph_objects as go
from datetime import date

mean = 0.101018
n_rows=6
md_results = f"The mean is **{mean:.2f}** and there are **{n_rows:,}**.,|   |   | babi |   |   |,|---|---|------|---|---|,|   |   |      |   |   |"
st.markdown(md_results)

st.title('Financial Model')

def run_status():
	latest_iteration = st.empty()
	bar = st.progress(0)
	for i in range(100):
		latest_iteration.text(f'Percent Complete {i+1}')
		bar.progress(i + 1)
		time.sleep(0.01)
		st.empty()


st.sidebar.subheader('Initial Inputs')


syscap= int(st.sidebar.number_input('System Capacity (kWp)',min_value=0,value=100,step=1 ))
capexcost= int(st.sidebar.number_input('Capex Cost (INR/KWp)',min_value=0,value=10000,step=1))
landcost= int(st.sidebar.number_input('Land Cost',min_value=0,value=1,step=1))
# ppa Period
commisiondelay = int(st.sidebar.number_input('Commision Time (Months)',min_value=0,value=1,step=1))
terminal_value_premium = (int(st.sidebar.number_input('Terminal Value Premium (%)',min_value=0,value=1,step=1)))/100 # in decimal, not percentage
#
st.sidebar.subheader(' ')
degradation = (int(st.sidebar.number_input('Degradation (%)',min_value=0,value=1,step=1)))/100 # in decimal, not percentage
st.sidebar.subheader(' ')
#
omcharge= int(st.sidebar.number_input('O&M Charges (%)',min_value=0,value=1,step=1))/100 # in decimal, not percentage
franchise_revenue = int(st.sidebar.number_input('Franchise Fee (% from Revenue)',min_value=0,value=1,step=1))
franchise_asset =int(st.sidebar.number_input('Franchise Fee (% from Asset)',min_value=0,value=1,step=1))
insurance = int(st.sidebar.number_input('Insurance Cost (Rs. Per 1000)',min_value=0,value=1,step=1))
audit = int(st.sidebar.number_input('Audit Cost (Annual)',min_value=0,value=1,step=1))
capexrep= int(st.sidebar.number_input('Capex Replacement (% of Asset)',min_value=0,value=1,step=1))
capexrepyear= int(st.sidebar.number_input('Capex Replacement (year)',min_value=0,value=1,step=1))
#
st.sidebar.subheader(' ')
#
powertarrif= int(st.sidebar.number_input('Power Tariff',min_value=0.0,value=1.0,step=1.0))
powertarrifincr=1 if st.sidebar.number_input('Power Tariff Increase (%/year)',min_value=0,value=1,step=1) else 0
# solar discount (in basic_calculation)
#
st.sidebar.subheader(' ')
#
equitycomp= (int(st.sidebar.number_input('Equity Component (%)',min_value=0,value=1,step=1)))/100 # in decimal, not percentage
loaninterest= (int(st.sidebar.number_input('Term Loan Interest (%)',min_value=0,value=1,step=1)))/100 #percentage
loanperiod= int(st.sidebar.number_input('Loan Period (year)',min_value=0,value=1,step=1))
#
st.sidebar.subheader(' ')
# project cost (in basic_calculation)
generation = st.sidebar.number_input('Generation',min_value=0.0,value=1.0,step=1.0)
solartariff = st.sidebar.number_input('Solar Tariff',min_value=0.0,value=1.0,step=1.0)
# equity (in basic_calculation)
# debt
#  IRR
operation = int(st.sidebar.number_input('Operational Time (year)',min_value=0,max_value=20,value=15,step=1))
startdate = st.sidebar.date_input('Start Date')


def basic_calculation():
	solardiscount = (powertarrif - solartariff)/powertarrif
	projectcost = syscap * capexcost + landcost
	equity = projectcost * equitycomp
	debt = projectcost - equity
	unitsgen = generation #
	opening_balance = debt
	repayment = debt/loanperiod
	closing_balance = opening_balance - repayment
	return solardiscount, projectcost, equity, debt, unitsgen, opening_balance, closing_balance

projectcost =basic_calculation()[1]
insurance_project = projectcost*insurance/1000

repayment = basic_calculation()[3]/loanperiod

def create_data():
	data=basic_calculation()
	data = {
	'Solar Discount':[data[0]],
	'Project Cost':[data[1]],
	'Equity':[data[2]],
	'Debt':[data[3]],
	'Unit Generated':[data[4]]
	}
	data2 = {}
	df2 = 0

	if ppayear != None:
		# ppa year to df
		# st.write(ppayear)
		for year in range(1,ppayear+1):
			data2['Year {}'.format(year)] = []
		df2 = pd.DataFrame(data2)
		# st.dataframe(df2)
	df=pd.DataFrame(data)
	# st.dataframe(df)
	return df, df2, data2

def add_month(orig_date,month_add):
    # orig_date: type datetime , month_add: integer
    new_year = orig_date.year
    new_month = orig_date.month + month_add
    # note: in datetime.date, months go from 1 to 12
    if new_month > 12:
        new_year += 1
        new_month = 12-new_month

    last_day_of_month = calendar.monthrange(new_year, new_month)[1]
    new_day = min(orig_date.day, last_day_of_month)

    return orig_date.replace(year=new_year, month=new_month, day=new_day)

def add_year(orig_date,year_add):
    # orig_date: type datetime , month_add: integer
    new_month = orig_date.month
    new_year = orig_date.year + year_add
    # note: in datetime.date, months go from 1 to 12

    last_day_of_month = calendar.monthrange(new_year, new_month)[1]
    new_day = min(orig_date.day, last_day_of_month)

    return orig_date.replace(year=new_year, month=new_month, day=new_day)

def xnpv(rate, values, dates):
	if rate <= -1.0:
		return float('inf')
	d0 = dates[0]    # or min(dates)
	return sum([ vi / (1.0 + rate)**((di - d0).days / 365.0) for vi, di in zip(values, dates)])

def xirr(values, dates):
	try:
		return scipy.optimize.newton(lambda r: xnpv(r, values, dates), 0.0)
	except RuntimeError:    # Failed to converge?
		return scipy.optimize.brentq(lambda r: xnpv(r, values, dates), -1.0, 1e10)


def year_calculation():
	# calculation
	projectcost =basic_calculation()[1]
	unitsgen = basic_calculation()[4]
	equity_invested = int(basic_calculation()[2])
	firstyear = syscap * unitsgen
	data2 =create_data()[2] # still a dict
	df2 = pd.DataFrame(data2)
	opening_balance= basic_calculation()[5]
	closing_balance = basic_calculation()[6]
	interest_expenses = ((opening_balance+closing_balance)/2 )*loanperiod
	# st.write(ppayear)

	# list initialisation
	calcyear = [firstyear] #units generated
	equity_peryear_list = []
	startyear=add_month(startdate,commisiondelay) # date from input + commision time
	date_years_list = [startyear]
	# dict initialisation
	calcyear_df = {"Year 1":[firstyear]}
	revenue_peryear = {}
	omcharge_peryear = {}
	opex_cashflow_peryear ={}
	equity_peryear = {}
	date_years = {}
	# IRR list
	irr_list_date = [startdate] # dates
	irr_list_equity = [-equity_invested] # values
	for year in range(1,ppayear+1):
		# calculation part
		consecutiveyear = round((calcyear[year-1] * (1-degradation)), 2) #units generated
		unit = round(solartariff * calcyear[year-1], 2) # revenue
		omcharge_year = round(omcharge * unit, 2)
		franchise_fee = unit * franchise_revenue + projectcost * franchise_asset
		if year != capexrepyear:
			opex_cashflow = round(omcharge_year + insurance_project + interest_expenses + audit, 2) # fix name to opex
		else:
			capex = projectcost * capexrep
			opex_cashflow = round(omcharge_year + insurance_project + interest_expenses + audit + capex, 2)
			# 	# year special condition

		equity_peryear_calc = int(round(unit - opex_cashflow - repayment)) # revenue - opex - repayment
		if len(date_years_list) == 1 and len(date_years)==0:
			nextyear_dict = {"Year {}".format(year):[date_years_list[0]]}
			date_years.update(nextyear_dict)
		else:
			nextyear = add_year(date_years_list[year-2],1)
			date_years_list.append(nextyear)
			nextyear_dict = {"Year {}".format(year):[nextyear]}
			date_years.update(nextyear_dict)
		# list appending
		calcyear.append(consecutiveyear)
		equity_peryear_list.append(int(equity_peryear_calc))
		# dict value
		value = {"Year {}".format(year):[calcyear[year-1]]}
		rev = {"Year {}".format(year):[unit]}
		omcharge_year_dict = {"Year {}".format(year):[omcharge_year]}
		opex_cashflow_dict = {"Year {}".format(year):[opex_cashflow]}
		equity_peryear_dict = {"Year {}".format(year):[equity_peryear_calc]}

		# dict update
		calcyear_df.update(value)
		revenue_peryear.update(rev)
		omcharge_peryear.update(omcharge_year_dict)
		opex_cashflow_peryear.update(opex_cashflow_dict)
		equity_peryear.update(equity_peryear_dict)

	# dataframe conversion
	calcyear_df = pd.DataFrame(calcyear_df)
	revenue_peryear=pd.DataFrame(revenue_peryear)
	omcharge_peryear=pd.DataFrame(omcharge_peryear)
	opex_cashflow_peryear=pd.DataFrame(opex_cashflow_peryear)
	equity_peryear=pd.DataFrame(equity_peryear)
	date_years=pd.DataFrame(date_years)
	# appending into main dataframe (df2)
	df2 = df2.append(calcyear_df, ignore_index = True) # unit generated per year
	df2 = df2.append(revenue_peryear, ignore_index = True)
	df2 = df2.append(omcharge_peryear, ignore_index = True)
	df2 = df2.append(opex_cashflow_peryear, ignore_index = True)
	df2 = df2.append(equity_peryear, ignore_index = True)
	df2 = df2.append(date_years, ignore_index = True)
	#
	df2 = df2.rename(index={0:'Units Generated',1:'Revenue',2:'O&M Charges',3:'Opex Cashflow',4:'Equity'})
	#
	# xirr calculation
	irr_list_date = irr_list_date + date_years_list
	irr_list_equity = irr_list_equity + equity_peryear_list
	xirr_value = round(xirr(irr_list_equity, irr_list_date),4)
	xirr_value = xirr(irr_list_equity, irr_list_date)
	# st.write(float(xirr(irr_list_equity, irr_list_date))*100)
	#
	return xirr_value, irr_list_equity,df2, irr_list_date # return xirr_value, irr_list_equity, df2, date_years_list

def terminal_value(): # return terminal_value_list, term_equity_temp_list
	term_xirr_value = year_calculation()[0] # in decimal, not %
	equity_list = year_calculation()[1]
	# st.write(term_xirr_value)
	term_equity_temp_first = equity_list[0]*term_xirr_value + equity_list[1]
	term_equity_temp_list = [term_equity_temp_first]
	terminal_value_list = []
	for year in range(0,ppayear-1): # if ppayear is 15, range is until 14 (index:15)
		if year == 0:
			# first year
			terminal_value_first = - equity_list[0]-(term_equity_temp_list[0] * (1-terminal_value_premium*year/ppayear))
			terminal_value_list.append(terminal_value_first)
		else:
			# second year and above
			# temporary equity
			term_equity_temp = - terminal_value_list[year-1] * term_xirr_value + equity_list[year+1]
			term_equity_temp_list.append(term_equity_temp)
			# terminal value calculation
			terminal_value_years = terminal_value_list[year-1] - term_equity_temp * (1-terminal_value_premium* (year+1)/ppayear)
			terminal_value_list.append(terminal_value_years)

	return terminal_value_list, term_equity_temp_list

def exit_value():
	# last year
	irr_list_equity = year_calculation()[1] # last year
	irr_list_date = year_calculation()[3]
	# list initialisation
	all_year_equity = [irr_list_equity] # list of lists for all years
	# all_year_date
	exit_value_list = [0]
	exit_perkw_list = exit_value_list
	xirr_list = [xirr(irr_list_equity, irr_list_date)]
	string_list_years = ["Year {}".format(ppayear)]
	#
	x = 0
	for year in range(ppayear-1,0,-1): # decrements unti index 1
		# find exit value
		st.write(year)
		# st.write(x)
		# if len(all_year_equity) == 1:
		# 	current_year_list_equity = irr_list_equity
		# else:
		current_year_list_equity = all_year_equity[x].copy()
		# st.write(current_year_list_equity)
		exit = current_year_list_equity[year+1]/(1/1+xirr_list[x]) # ask for feedback due to odd formula
		# exit per kW
		exit_perkw = exit/syscap
		# new equity list
		current_year_list_equity[year+1] = "	"
		current_year_list_equity[year] = current_year_list_equity[year]+exit
		new_equity = current_year_list_equity

		# new date for xirr calculation
		del irr_list_date[year+1]
		# new xirr
		new_xirr = xirr(new_equity, irr_list_date)
		xirr_list.append(new_xirr)
		# list update
		exit_value_list.append(round(exit))
		exit_perkw_list.append(round(exit_perkw))
		all_year_equity.append(new_equity)
		# st.write(all_year_equity)
		string_list_years.append("Year {}".format(year))
		# find cummulutive equity due to exit
		x+= 1
	return all_year_equity, string_list_years

# ppa year selectbox
ppayear = 1
if operation != 0:
	# ppayear = st.selectbox('PPA Options',[*range(1,int(operation)+1)])
	ppayear = st.sidebar.slider('PPA Options',min_value=1, max_value=int(operation),step=1)
	create_data()
	xirr_value, irr_list_equity, data, date_list = year_calculation()
	st.dataframe(data,width=100000, height=100000)
	st.table(data)
	terminal_value_list=terminal_value()[0]
	term_equity_temp_list=terminal_value()[1]
	# xirr display
	xirr_value = xirr_value*100
	# st.write(xirr_value)
	st.markdown(f" IRR : **{xirr_value:.2f}**% (*{ppayear}* years PPA)")
	#
	# st.write(terminal_value_list)
	# st.write(term_equity_temp_list)
	all_year_equity,year_list=exit_value()

	fig = go.Figure(data=[go.Table(
    header=dict(values=year_list[0:6],
                line_color='darkslategray',
                fill_color='lightskyblue',
                align='left'),
    cells=dict(values=all_year_equity[0:6], # 2nd column
               line_color='darkslategray',
               fill_color='lightcyan',
               align='left'))])
	# fig.update_layout(width=10, height=1000)
	st.plotly_chart(fig)
	st.write('babi')
else:
	pass


#
#
# @st.cache
def create_df():
    df=pd
#
# ###############################################################################################
# running part
def run_data():
	#run_status()
	df_models=get_models()[0][0]
	st.write('Given your parameters, the predicted value is **${:.2f}**'.format(df_models))
	df1=map_df(df)
	st.map(df1)
	df1
btn1 = st.sidebar.checkbox("Show Values")
btn = st.sidebar.button("Run Model")

if btn1:
	solardiscount, projectcost, equity, debt, unitsgen, opening_balance, closing_balance = basic_calculation()

	st.markdown(f" Solar Discount : **{int(solardiscount)}**")
	st.markdown(f" Project Cost : **{projectcost}**")
	st.markdown(f" Equity : **{equity}**")
	st.markdown(f" Debt : **{debt:.2f}**")
	st.markdown(f" Unit Generated : **{unitsgen:.2f}**")

if btn:
	run_status()
	# basic_calculation()
	# create_data()
	# display_result()
else:
	pass
