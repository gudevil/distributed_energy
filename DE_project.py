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
from datetime import date
import calendar
import scipy.optimize
import plotly.graph_objects as go
import base64
# import openpyxl
from io import BytesIO
from datetime import date

# mean = 0.101018
# n_rows=6
# md_results = f"The mean is **{mean:.2f}** and there are **{n_rows:,}**.,|   |   | babi |   |   |,|---|---|------|---|---|,|   |   |      |   |   |"
# st.markdown(md_results)

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


syscap= int(st.sidebar.number_input('System Capacity (kWp)',min_value=0,value=200,step=100 ))
capexcost= int(st.sidebar.number_input('Capex Cost (INR/KWp)',min_value=0,value=35000,step=1))
landcost= int(st.sidebar.number_input('Land Cost',min_value=0,value=0,step=1))
operation = int(st.sidebar.number_input('PPA year',min_value=0,max_value=25,value=15,step=1))
# ppa Period
commisiondelay = int(st.sidebar.number_input('Commision Time (Months)',min_value=0,value=2,step=1))
terminal_value_premium = (int(st.sidebar.number_input('Terminal Value Premium (%)',min_value=0,value=0,step=1)))/100 # in decimal, not percentage
#
st.sidebar.subheader(' ')
degradation = (int(st.sidebar.number_input('Degradation (%)',min_value=0,value=1,step=1)))/100 # in decimal, not percentage
st.sidebar.subheader(' ')
#
omcharge= int(st.sidebar.number_input('O&M Charges (%)',min_value=0,value=20,step=2))/100 # in decimal, not percentage
franchise_revenue = int(st.sidebar.number_input('Franchise Fee (% from Revenue)',min_value=0,value=0,step=1))/100
franchise_asset =int(st.sidebar.number_input('Franchise Fee (% from Asset)',min_value=0,value=0,step=1))/100
insurance = int(st.sidebar.number_input('Insurance Cost (Rs. Per 1000)',min_value=0,value=1,step=1))
audit = int(st.sidebar.number_input('Audit Cost (Annual)',min_value=0,value=0,step=1))
capexrep= int(st.sidebar.number_input('Capex Replacement (% of Asset)',min_value=0,value=10,step=1))/100

capexrepyear= int(st.sidebar.number_input('Capex Replacement (year)',min_value=2,value=10,step=1))
#
st.sidebar.subheader(' ')
#
powertarrif= st.sidebar.number_input('Power Tariff',min_value=0.0,value=6.35,step=1.0) #%d %e %f %g %i %u
powertarrifincr= st.sidebar.number_input('Power Tariff Increase (%/year)',min_value=0,value=0,step=1)/100
# solar discount (in basic_calculation)
#
st.sidebar.subheader(' ')
#
equitycomp= (int(st.sidebar.number_input('Equity Component (%)',min_value=0,value=100,step=1)))/100 # in decimal, not percentage
loaninterest= (int(st.sidebar.number_input('Term Loan Interest (%)',min_value=0,value=10,step=1)))/100 #percentage
loanperiod= int(st.sidebar.number_input('Loan Period (year)',min_value=0,value=7,step=1))
#
st.sidebar.subheader(' ')
# project cost (in basic_calculation)
generation = st.sidebar.number_input('Generation',min_value=0.0,value=1500.0,step=1.0)
solartariff = st.sidebar.number_input('Solar Tariff',min_value=0.0,value=5.25,step=1.0)
# equity (in basic_calculation)
# debt
#  IRR
startdate = st.sidebar.date_input('Start Date', value = date(2000, 1, 1))

input_list = [syscap
,capexcost
,landcost
,operation
,commisiondelay
,(terminal_value_premium*100)
,(degradation*100)
,(omcharge*100)
,(franchise_revenue*100)
,(franchise_asset*100)
,insurance
,audit
,(capexrep*100)
,capexrepyear
,powertarrif
,(powertarrifincr*100)
,(equitycomp*100)
,(loaninterest*100)
,loanperiod
,generation
,solartariff
]
#
input_string_list = ['System Capacity (kWp)',
'Capex Cost (INR/KWp)',
'Land Cost',
'PPA year',
'Commision Time (Months)',
'Terminal Value Premium (%)',
'Degradation (%)',
'O&M Charges (%)',
'Franchise Fee (% from Revenue)',
'Franchise Fee (% from Asset)',
'Insurance Cost (Rs. Per 1000)',
'Audit Cost (Annual)',
'Capex Replacement (% of Asset)',
'Capex Replacement (year)',
'Power Tariff',
'Power Tariff Increase (%/year)',
'Equity Component (%)',
'Term Loan Interest (%)',
'Loan Period (year)',
'Generation',
'Solar Tariff'
]
# st.write(input_list)

def basic_calculation():
	solardiscount = (powertarrif - solartariff)/powertarrif

	projectcost = syscap * capexcost + landcost
	equity = projectcost * equitycomp
	debt = projectcost - equity
	unitsgen = generation #

	return solardiscount, projectcost, equity, debt, unitsgen

projectcost =basic_calculation()[1]
insurance_project = projectcost*insurance/1000

repayment = basic_calculation()[3]/loanperiod

def create_df_input(list,string_list):
	# list(list)
	# st.write(list)
	for i in range(len(list)):
		input_list.append(list[i])
		input_string_list.append(string_list[i])
	df_input = pd.DataFrame(zip(input_string_list, input_list),
			   columns =['Name', 'Value'])
	df_input = df_input.set_index('Name')
	# st.write(list)
	return df_input


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

# def append_to_df():


def to_excel(df, bool):
	output = BytesIO()
	writer = pd.ExcelWriter(output, engine='xlsxwriter')
	df.to_excel(writer, sheet_name='Sheet1',index=bool)
	writer.save()
	processed_data = output.getvalue()
	return processed_data

def to_excel_sheets(df_list, bool):
	"""
	Make sure that both df_list and bool (contains whether index is added or ignored) is a list
	"""
	output = BytesIO()
	writer = pd.ExcelWriter(output, engine='xlsxwriter')
	# string_list =['Input','']
	num = 0
	for df in df_list:
		df.to_excel(writer, sheet_name='Sheet {}'.format(num+1),index=bool[num])
		num += 1
	writer.save()
	processed_data = output.getvalue()
	return processed_data

def get_table_download_link(df,string,bool):
	"""Generates a link allowing the data in a given panda dataframe to be downloaded
	in:  dataframe
	out: href string
	"""
	if type(df) == list:
		val = to_excel_sheets(df,bool)
	else:
		val = to_excel(df,bool)
	b64 = base64.b64encode(val)  # val looks like b'...'
	return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="{string}.xlsx">Download {string} Excel file</a>' # decode b'abc' => ab





def year_calculation():
	# if powertarrif != 0:

	# calculation
	projectcost =basic_calculation()[1]
	unitsgen = basic_calculation()[4]
	debt = basic_calculation()[3]
	equity_invested = int(basic_calculation()[2])
	firstyear = syscap * unitsgen
	data2 =create_data()[2] # still a dict
	df2 = pd.DataFrame(data2)
	# opening_balance= basic_calculation()[5]
	# closing_balance = basic_calculation()[6]
	opening_balance = [debt]
	repayment = debt/loanperiod
	closing_balance = []
	for period in range(0,ppayear):
		if period <= loanperiod:
			new_closing_balance = opening_balance[period] - repayment
			# st.write(new_closing_balance)
			if period < loanperiod:
				opening_balance.append(new_closing_balance)
				closing_balance.append(new_closing_balance)
		else:
			closing_balance.append(0)
			opening_balance.append(0)

	closing_balance.append(0)


	# list initialisation
	calcyear = [firstyear] #units generated
	equity_peryear_list = []
	startyear=add_month(startdate,commisiondelay) # date from input + commision time
	date_years_list = [startyear]
	solartariff_list = [solartariff]
	repayment_list = []
	interest_expenses_list = []
	# dict initialisation
	calcyear_df = {"Year 1":[firstyear]}
	solartariff_peryear = {}
	opening_balance_peryear = {}
	repayment_peryear = {}
	closing_balance_peryear = {}
	revenue_peryear = {}
	#
	omcharge_peryear = {}
	interest_expenses_peryear = {}
	franchise_fee_peryear = {}
	insurance_peryear = {}
	audit_peryear = {}
	capex_peryear = {}
	opex_cashflow_peryear ={}
	equity_peryear = {}
	date_years = {}
	# IRR list
	irr_list_date = [startdate] # dates
	irr_list_equity = [-equity_invested] # values
	for year in range(1,ppayear+1):
		# calculation part
		interest_expenses = (np.mean([opening_balance[year-1],closing_balance[year-1]]) )*loaninterest
		if year == 1:
			solartariff_peryear.update({"Year {}".format(year):[solartariff_list[0]]})
			unit = round(solartariff_list[year-1] * calcyear[year-1], 2) # revenue
		else:
			solartariff_new = solartariff_list[-1] * (1 + powertarrifincr)
			solartariff_list.append(solartariff_new)
			solartariff_peryear.update({"Year {}".format(year):[round(solartariff_new,3)]})
			# solartariff_list.append(round(solartariff_new, 3))
			unit = round(solartariff_list[year-1] * calcyear[year-1], 2)

		#
		consecutiveyear = round((calcyear[year-1] * (1-degradation)), 2) #units generated

		omcharge_year = round(omcharge * unit, 2)
		franchise_fee_rev = unit * franchise_revenue
		franchise_fee_ass = projectcost * franchise_asset
		franchise_fee_total = franchise_fee_rev + franchise_fee_ass
		capex = 0
		if year != capexrepyear:
			if franchise_asset != 0 and year == 1:
					if franchise_revenue != 0:
						opex_cashflow = round(omcharge_year + insurance_project + interest_expenses + audit + franchise_fee_ass + franchise_fee_rev, 2)
						franchise_fee = franchise_fee_total
					else:
						opex_cashflow = round(omcharge_year + insurance_project + interest_expenses + audit + franchise_fee_ass, 2)
						franchise_fee = franchise_fee_ass
			elif franchise_revenue != 0:
				opex_cashflow = round(omcharge_year + insurance_project + interest_expenses + audit + franchise_fee_rev, 2) # fix name to opex
				franchise_fee = franchise_fee_rev
			else:
				opex_cashflow = round(omcharge_year + insurance_project + interest_expenses + audit, 2)
				franchise_fee = 0
		elif year == capexrepyear:
			capex = projectcost * capexrep
			if year == 1:
				st.write("Capex Replacement Year Must Be Above The First Year")
			elif franchise_revenue != 0:
				opex_cashflow = round(omcharge_year + insurance_project + interest_expenses + audit + franchise_fee_rev + capex, 2)
			else:
				opex_cashflow = round(omcharge_year + insurance_project + interest_expenses + audit + capex, 2)

			# 	# year special condition
		if year <= loanperiod:
			equity_peryear_calc = (unit - opex_cashflow - repayment)# revenue - opex - repayment
			repayment_list.append(repayment)
			repayment_peryear.update({"Year {}".format(year):[round(repayment)]})
		else:
			equity_peryear_calc = unit - opex_cashflow
			repayment_list.append(0)
			repayment_peryear.update({"Year {}".format(year):[0]})
		if len(date_years_list) == 1 and len(date_years)==0:
			nextyear_dict = {"Year {}".format(year):[date_years_list[0].strftime('%m/%d/%Y')]}
			date_years.update(nextyear_dict)
		else:
			nextyear = add_year(date_years_list[year-2],1)
			date_years_list.append(nextyear)
			nextyear_dict = {"Year {}".format(year):[nextyear.strftime('%m/%d/%Y')]}
			date_years.update(nextyear_dict)
		# list appending
		calcyear.append(consecutiveyear)
		equity_peryear_list.append(round(equity_peryear_calc))
		# dict value
		value = {"Year {}".format(year):[calcyear[year-1]]} # units generated
		# in the conditional above # solar Tariff
		#
		# term loan - 1. opening_balance 2. repayment 3. closing closing_balance
		opening_balance_peryear.update({"Year {}".format(year):[round(opening_balance[year-1])]})

		closing_balance_peryear.update({"Year {}".format(year):[round(closing_balance[year-1])]})
		#
		opex_cashflow_dict = {"Year {}".format(year):[round(opex_cashflow)]}
		omcharge_year_dict = {"Year {}".format(year):[round(omcharge_year)]}
		# interest_expenses, franchise_fee , insurance, audit , terminal_value of land (not needed), capex(at specific year)
		interest_expenses_list.append(interest_expenses)
		interest_expenses_peryear.update({"Year {}".format(year):[round(interest_expenses)]})
		franchise_fee_peryear.update({"Year {}".format(year):[round(franchise_fee)]})
		insurance_peryear.update({"Year {}".format(year):[insurance_project]})
		audit_peryear.update({"Year {}".format(year):[audit]})
		capex_peryear.update({"Year {}".format(year):[capex]})
		#
		equity_peryear_dict = {"Year {}".format(year):[round(equity_peryear_calc)]} # capex cashflow (same as equity) , xirr
		# dict update
		calcyear_df.update(value)
		revenue_peryear.update({"Year {}".format(year):[round(unit)]})
		omcharge_peryear.update(omcharge_year_dict)
		opex_cashflow_peryear.update(opex_cashflow_dict)
		equity_peryear.update(equity_peryear_dict)

	# dataframe conversion
	calcyear_df = pd.DataFrame(calcyear_df)
	solartariff_peryear = pd.DataFrame(solartariff_peryear)
	opening_balance_peryear = pd.DataFrame(opening_balance_peryear)
	repayment_peryear = pd.DataFrame(repayment_peryear)
	closing_balance_peryear = pd.DataFrame(closing_balance_peryear)
	revenue_peryear=pd.DataFrame(revenue_peryear)
	omcharge_peryear=pd.DataFrame(omcharge_peryear)
	interest_expenses_peryear=pd.DataFrame(interest_expenses_peryear)
	franchise_fee_peryear=pd.DataFrame(franchise_fee_peryear)
	insurance_peryear=pd.DataFrame(insurance_peryear)
	audit_peryear=pd.DataFrame(audit_peryear)
	opex_cashflow_peryear=pd.DataFrame(opex_cashflow_peryear)
	equity_peryear=pd.DataFrame(equity_peryear)
	date_years=pd.DataFrame(date_years)
	# appending into main dataframe (df2)
	df2 = df2.append(calcyear_df, ignore_index = True) # unit generated per year
	df2 = df2.append(solartariff_peryear, ignore_index = True)
	df2 = df2.append(opening_balance_peryear, ignore_index = True)
	df2 = df2.append(repayment_peryear, ignore_index = True)
	df2 = df2.append(closing_balance_peryear, ignore_index = True)
	df2 = df2.append(revenue_peryear, ignore_index = True)
	df2 = df2.append(omcharge_peryear, ignore_index = True)
	df2 = df2.append(interest_expenses_peryear, ignore_index = True)
	df2 = df2.append(franchise_fee_peryear, ignore_index = True)
	df2 = df2.append(insurance_peryear, ignore_index = True)
	df2 = df2.append(audit_peryear, ignore_index = True)
	df2 = df2.append(pd.DataFrame(capex_peryear), ignore_index = True)
	df2 = df2.append(opex_cashflow_peryear, ignore_index = True)
	df2 = df2.append(equity_peryear, ignore_index = True)
	df2 = df2.append(date_years, ignore_index = True)
	#
	df2 = df2.rename(index=
	{0:'Units Generated',1:'Solar Tariff',2:'Opening Balance',3:'Repayment',
	4:'Closing Balance',5:'Revenue',6:'O&M Charges'
	,7:'Interest Expenses',8:'Franchise Fee',9:'Insurance',10:'Account & Audit'
	,11:'Capex', 12:'Opex Cashflow',13:'Equity/Capex Cashflow',14:'Dates',
	15:' ',16:'Terminal Value'})
	#
	# st.write(repayment)
	# st.write(revenue_peryear)
	# st.write(opex_cashflow_peryear)
	# xirr calculation
	irr_list_date = irr_list_date + date_years_list
	irr_list_equity = irr_list_equity + equity_peryear_list
	# st.write(irr_list_equity)
	xirr_value = round(xirr(irr_list_equity, irr_list_date),4)
	xirr_value = xirr(irr_list_equity, irr_list_date)
	# st.write(solartariff_list)
	#
	return xirr_value, irr_list_equity,df2, irr_list_date, closing_balance, interest_expenses_list, repayment_list # return xirr_value, irr_list_equity, df2, date_years_list

def terminal_value(): # return terminal_value_list, term_equity_temp_list
	term_xirr_value = year_calculation()[0] # in decimal, not %
	equity_list = year_calculation()[1]
	closing_balance = year_calculation()[4] # list of closing balance

	term_equity_temp_first = equity_list[0]*term_xirr_value + equity_list[1]
	term_equity_temp_list = [round(term_equity_temp_first)]
	terminal_value_list = []
	temp_terminal_value_list = []
	for year in range(0,ppayear): # if ppayear is 15, range is until 14 (index:15)
		if year == 0:
			# first year
			terminal_value_first = - equity_list[0]-(term_equity_temp_list[0] * (1-terminal_value_premium*(year+1)/ppayear))
			temp_terminal_value_list.append(terminal_value_first)
			#
			terminal_value_first = terminal_value_first + closing_balance[0]*1.02
			terminal_value_list.append(round(terminal_value_first))
		else:
			# second year and above
			# temporary equity
			term_equity_temp = - temp_terminal_value_list[year-1] * term_xirr_value + equity_list[year+1]
			term_equity_temp_list.append(round(term_equity_temp))
			# terminal value calculation
			if year != ppayear-1:
				terminal_value_years = temp_terminal_value_list[year-1] - term_equity_temp * (1-terminal_value_premium* (year+1)/ppayear)
				temp_terminal_value_list.append(terminal_value_years)
				#
				terminal_value_years = terminal_value_years + closing_balance[year]*1.02
				terminal_value_list.append(round(terminal_value_years))
			else:
				temp_terminal_value_list.append(0)
				terminal_value_list.append(0)

	return terminal_value_list, term_equity_temp_list

def exit_value():
	# last year
	irr_list_equity = year_calculation()[1] # last year
	irr_list_date = year_calculation()[3].copy()
	repayment_list = year_calculation()[6].copy()
	interest_expenses_list = year_calculation()[5].copy()
	# list initialisation
	all_year_equity = [irr_list_equity] # list of lists for all years
	# all_year_date
	exit_value_list = [0]
	exit_perkw_list = exit_value_list.copy()
	xirr_list = [xirr(irr_list_equity, irr_list_date)]
	string_list_years = ["Year {}".format(ppayear)]
	#
	x = 0
	total_payment = repayment_list[ppayear-1] + interest_expenses_list[ppayear-1]
	for year in range(ppayear-1,0,-1): # decrements unti index 1
		# special case for debt
		total_payment += repayment_list[year-1] + interest_expenses_list[year-1]
		#
		current_year_list_equity = all_year_equity[x].copy()
		exit = current_year_list_equity[year+1]/(1/1+xirr_list[x])  # ask for feedback due to odd formula
		exit_temp = exit + total_payment
		# exit per kW
		exit_perkw = exit/syscap
		# new equity list
		current_year_list_equity[year+1] = "	"
		current_year_list_equity[year] = current_year_list_equity[year]+round(exit)
		new_equity = current_year_list_equity
		# new date for xirr calculation
		del irr_list_date[year+1]
		# new xirr
		new_xirr = xirr(new_equity, irr_list_date)
		xirr_list.append(new_xirr)
		# st.write("Year {}".format(year))
		# st.write(total_payment)
		# st.write(exit)
		# list update
		exit_value_list.append(round(exit_temp))
		exit_perkw_list.append(round(exit_perkw))
		all_year_equity.append(new_equity)
		string_list_years.append("Year {}".format(year))
		# find cummulutive equity due to exit
		x+= 1
	# st.write(xirr_list)
	# st.write(exit_perkw_list)
	return all_year_equity, string_list_years, xirr_list, exit_value_list, exit_perkw_list

btn2 = st.sidebar.checkbox("PPA slider")

btn3 = st.sidebar.checkbox("Show Individual Download Link")

# ppa year selectbox
ppayear = 1
if operation != 0:
	# chnage this to df into new sheet
	templist = list(basic_calculation())
	templist[0] = templist[0]*100
	df_input = create_df_input(templist, ['Solar Discount', 'Project Cost', 'Equity', 'Debt', 'Unit Generated'])
	st.dataframe(df_input ,width=100000, height=100000)
	if btn3:
		st.markdown(get_table_download_link(df_input, "Sheet 1",bool=True), unsafe_allow_html=True)
	solardiscount, projectcost, equity, debt, unitsgen = basic_calculation()
	new_list = [solardiscount,projectcost,equity,debt]
	new_list_string = ['Solar Discount','Project Cost','Equity','Debt']
	input_list = input_list.copy() + new_list
	input_string_list = input_string_list.copy() + new_list_string
	# st.write(input_string_list)
	if btn2:
		ppayear = st.sidebar.slider('PPA Options',min_value=1, max_value=int(operation), value =int(operation) ,step=1)
	else:
		ppayear = int(operation)
	create_data()
	#
	dict_terminal_value = {}
	dict_equity_temp = {}
	year_list = exit_value()[1]
	terminal_value_list, term_equity_temp_list=terminal_value()
	# st.write(terminal_value_list)
	for year in range(ppayear):
		dict_terminal_value.update({year_list[ppayear-1-year]:[terminal_value_list[year]]})
		dict_equity_temp.update({year_list[ppayear-1-year]:[term_equity_temp_list[year]]})

	# st.write(dict_terminal_value)
	dict_terminal_value = pd.DataFrame(dict_terminal_value)
	dict_equity_temp = pd.DataFrame(dict_equity_temp)
	#
	xirr_value, irr_list_equity, df_2, date_list, closing_balance, interest_expenses_list, repayment_list = year_calculation()
	df_2 = df_2.append(dict_equity_temp, ignore_index = True)
	df_2 = df_2.append(dict_terminal_value, ignore_index = True)
	df_2 = df_2.rename(index=
	{0:'Units Generated',1:'Solar Tariff',2:'Opening Balance',3:'Repayment',
	4:'Closing Balance',5:'Revenue',6:'O&M Charges'
	,7:'Interest Expenses',8:'Franchise Fee',9:'Insurance',10:'Account & Audit'
	,11:'Capex', 12:'Opex Cashflow',13:'Equity/Capex Cashflow',14:'Dates',
	15:' ',16:'Terminal Value'})
	st.dataframe(df_2,width=100000, height=100000)
	#
	if btn3:
		st.markdown(get_table_download_link(df_2, "Sheet2",bool=True), unsafe_allow_html=True)
	#
	# xirr display
	xirr_value = xirr_value*100
	# st.write(xirr_value)
	st.markdown(f" IRR : **{xirr_value:.2f}**% (*{ppayear}* years PPA)")
	#
	# btn1 = st.sidebar.checkbox("Show Values")
	# if btn1:
	# solardiscount, projectcost, equity, debt, unitsgen, opening_balance, closing_balance = basic_calculation()

	all_year_equity,year_list, xirr_list, exit_value_list, exit_perkw_list = exit_value()
	dict_exit_value = {}
	irr_list_date_terminal = year_calculation()[3].copy()
	irr_list_date_terminal[0] = irr_list_date_terminal[0].strftime('%m/%d/%Y')
	for i in range(ppayear):
		all_year_equity[i].append(exit_value_list[i])
		all_year_equity[i].append(exit_perkw_list[i])
		all_year_equity[i].append(round(xirr_list[i]*100,3))
		dict_exit_value.update({year_list[i]:all_year_equity[i]})
		irr_list_date_terminal[i+1] = irr_list_date_terminal[i+1].strftime('%m/%d/%Y')
	irr_list_date_terminal= irr_list_date_terminal.copy()+['Exit Value','Exit Value per kW','IRR each Year']

	df_terminal_val = pd.DataFrame(dict_exit_value, index=irr_list_date_terminal)
	st.dataframe(df_terminal_val,width=100000, height=100000)
	if btn3:
		st.markdown(get_table_download_link(df_terminal_val, "Sheet3",bool=True), unsafe_allow_html=True)
	#
	# for excel export for all DataFrame
	df_master_list = [df_input, df_2 ,df_terminal_val]
	df_master_bool = [True, True, True]
	st.markdown(get_table_download_link(df_master_list, "Full_Ouput",df_master_bool), unsafe_allow_html=True)

else:
	pass




def create_df():
	df=pd

def run_data():
	#run_status()
	df_models=get_models()[0][0]
	st.write('Given your parameters, the predicted value is **${:.2f}**'.format(df_models))
	df1=map_df(df)
	st.map(df1)
	df1


# btn = st.sidebar.button("Run Model")
# if btn:
# 	run_status()
# 	# basic_calculation()
# 	# create_data()
# 	# display_result()
# else:
# 	pass
