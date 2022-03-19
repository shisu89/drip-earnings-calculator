from bokeh.plotting import output_file
from bokeh.layouts import column
from bokeh.models.widgets import Paragraph
from bokeh.models import ColumnDataSource, TableColumn, DataTable, Div
import pandas as pd
import pandas_bokeh

'''
Code written by Shi Su
The user inputs should be modified as per the user's requirements.
The script first calculates the deposit growth depending on the hydration
frequency and period during which hydration is performed.
The daily interest at the end of the hydration period is then taken to
generate income during the earnings period.
Gas fees incurred by hydration are considered and reported.
A dashboard is then created using Bokeh to display some KPIs and charts of
deposit and interest growth during the hydration period,
as well as the earnings accumulation during the earnings period.
'''

#############
#User inputs#
#############
output_file('DRIP_calculations.html')

#Deposit to start calculations from, in DRIP
INITIAL_DEPOSIT=20

#Average gas fee, in BNB
GAS_FEE=0.00125

#Token prices, in USD
BNB_PRICE=370
DRIP_PRICE=20

#Time periods for calculating the deposit accumulation and earnings, in days
PERIOD=365*2
EARNINGS_PERIOD=365

#Frequency of hydration process, in days
HYDRATION_FREQUENCY=1

#Current claimed amount, in DRIP
claimed=0

####################
#End of user inputs#
####################

max_payout=min(INITIAL_DEPOSIT*3.65,100000)

TAX_HYDRATION=5/100
ACCUMULATION_INTEREST=1/100
CLAIM_TAX=10/100

PERIOD=int(PERIOD)
EARNINGS_PERIOD=int(EARNINGS_PERIOD)

column_header=['Days','Deposit','Claimed','MaxPayout','Hydration Interest',
              'Interest','Available','Total Gas Fees in BNB']
dataframe_content=[[0],[INITIAL_DEPOSIT],[claimed],[max_payout],[0],[0],[0],[0]]
available=0
deposit=INITIAL_DEPOSIT
total_gas_fees=0
for current_day in range(1,PERIOD+1):
    dataframe_content[0].append(current_day)
    if current_day%HYDRATION_FREQUENCY==0:
        interest=ACCUMULATION_INTEREST*deposit
        hydration_interest=(available+interest)*(1-TAX_HYDRATION)
        deposit+=hydration_interest
        claimed+=hydration_interest
        max_payout=deposit*3.65
        available=0
        total_gas_fees+=GAS_FEE
    else:
        hydration_interest=0
        interest=ACCUMULATION_INTEREST*deposit
        deposit+=0
        claimed+=0
        max_payout=deposit*3.65
        available+=interest
        total_gas_fees+=0
    dataframe_content[1].append(deposit)
    dataframe_content[2].append(claimed)
    dataframe_content[3].append(min(max_payout,100000))
    dataframe_content[4].append(hydration_interest)
    dataframe_content[5].append(interest)
    dataframe_content[6].append(available)
    dataframe_content[7].append(total_gas_fees)

df=pd.DataFrame(dict(zip(column_header,dataframe_content)))
df['Total Gas Fees in USD']=df['Total Gas Fees in BNB']*BNB_PRICE

remaining_possible_earnings=df['MaxPayout'].iloc[-1]-df['Claimed'].iloc[-1]

cumulative_earnings=0
earnings_after_end_period=[]
for i in range(EARNINGS_PERIOD+1):
    earnings_after_end_period.append(cumulative_earnings)
    cumulative_earnings+=df['Interest'].iloc[-1]*(1-CLAIM_TAX)
    cumulative_earnings=min(cumulative_earnings,remaining_possible_earnings)

days_earnings=list(range(EARNINGS_PERIOD+1))

df_earnings=pd.DataFrame()
df_earnings['Days']=days_earnings
df_earnings['Cumulative Earnings, DRIP']=earnings_after_end_period
df_earnings['Cumulative Earnings, USD']=df_earnings['Cumulative Earnings, DRIP']*DRIP_PRICE

plot_deposit=df.plot_bokeh(
    kind='line',
    x='Days',
    y=['Deposit'],
    xlabel='Days',
    ylabel='Deposit [DRIP]',
    title='Total deposit in DRIP',
    legend='top_left',
    disable_scientific_axes="y",
    show_figure=False
    )

plot_interest=df.plot_bokeh(
    kind='line',
    x='Days',
    y=['Interest'],
    xlabel='Days',
    ylabel='Interest [DRIP/day]',
    title='Daily Interest in DRIP/day',
    legend='top_left',
    line_color='green',
    disable_scientific_axes="y",
    show_figure=False
    )

plot_earnings_DRIP=df_earnings.plot_bokeh(
    kind='line',
    x='Days',
    y=['Cumulative Earnings, DRIP'],
    xlabel='Days',
    ylabel='Cumulative Earnings [DRIP]',
    ylim=(0,df_earnings['Cumulative Earnings, DRIP'].max()*1.1),
    title='Cumulative Earnings in DRIP',
    legend='top_left',
    disable_scientific_axes="y",
    show_figure=False
    )

plot_earnings_USD=df_earnings.plot_bokeh(
    kind='line',
    x='Days',
    y=['Cumulative Earnings, USD'],
    xlabel='Days',
    ylabel='Cumulative Earnings [USD]',
    title='Cumulative Earnings in USD',
    legend='top_left',
    line_color='red',
    disable_scientific_axes="y",
    show_figure=False
    )

day_hydration='day'
day_period='day'
day_earnings='day'

if HYDRATION_FREQUENCY>1:
    day_hydration+='s'
if PERIOD>1:
    day_period+='s'
if EARNINGS_PERIOD>1:
    day_earnings+='s'

property_hydration=[
    "BNB price considered",
    "DRIP price considered",
    "",
    "Hydration frequency",
    "Hydration period considered",
    "",
    "Daily interest at the end of the period in DRIP",
    "Daily interest at the end of the period in USD",
    "",
    "Total gas fees in BNB",
    "Total gas fees in USD"
    ]
data_hydration=[
    f"{BNB_PRICE} USD",
    f"{DRIP_PRICE} USD",
    "",
    f"{HYDRATION_FREQUENCY} {day_hydration}",
    f"{PERIOD} {day_period}",
    "",
    f"{round(df['Interest'].iloc[-1],2)} DRIP/day",
    f"{round(df['Interest'].iloc[-1]*DRIP_PRICE,2)} USD/day",
    "",
    f"{round(df['Total Gas Fees in BNB'].iloc[-1],2)} BNB",
    f"{round(df['Total Gas Fees in USD'].iloc[-1],2)} USD"
    ]

df_hydration=pd.DataFrame()
df_hydration['Property']=property_hydration
df_hydration['Data']=data_hydration

property_earnings=[
    "Earnings Period",
    "Claimable DRIP to reach maximum payout",
    "Maximum payout",
    "DRIP already claimed at the end of the hydration period",
    "",
    "Total earnings at the end of the period in DRIP",
    "Total earnings at the end of earnings period in USD"
    ]

data_earnings=[
    f"{EARNINGS_PERIOD} {day_earnings}",
    f"{round(remaining_possible_earnings,2)} DRIP",
    f"{round(df['MaxPayout'].iloc[-1],2)} DRIP",
    f"{round(df['Claimed'].iloc[-1],2)} DRIP",
    "",
    f"{round(cumulative_earnings,2)} DRIP",
    f"{round(cumulative_earnings*DRIP_PRICE,2)} USD"
    ]

df_earnings=pd.DataFrame()
df_earnings['Property']=property_earnings
df_earnings['Data']=data_earnings

source_hydration=ColumnDataSource(df_hydration)
columns_hydration = [
        TableColumn(field="Property", title="Property"),
        TableColumn(field="Data", title="Data"),
    ]
data_table_hydration=(DataTable(source=source_hydration,
                                columns=columns_hydration,
                                autosize_mode='fit_viewport'))

source_earnings=ColumnDataSource(df_earnings)
columns_earnings = [
        TableColumn(field="Property", title="Property"),
        TableColumn(field="Data", title="Data"),
    ]
data_table_earnings=(DataTable(source=source_earnings,
                               columns=columns_earnings,
                               autosize_mode='fit_viewport'))

title = Div(text='<h1 style="text-align: center">DRIP Interest and Earnings Calculator</h1>')

box_earnings_note=Paragraph(
    text="""Note: Earnings only start after the end of the hydration period.
    The earnings accumulation stops when the maximum payout is reached.""",
    width_policy='min')


plot_data_hydration=column(title,data_table_hydration)
plot_data_earnings=column(box_earnings_note,data_table_earnings)

col1=column(title,data_table_hydration,box_earnings_note,data_table_earnings)
col2=column(plot_deposit,plot_earnings_DRIP)
col3=column(plot_interest,plot_earnings_USD)

pandas_bokeh.plot_grid([
      [col1,col2,col3],
      ]
      )
