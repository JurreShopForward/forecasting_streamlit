import streamlit as st
import hmac
import pandas as pd
from io import StringIO

from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import random



def create_plot(forecast_df, forecast_df_after, forecast_df_before, company_name, variable):
    # TODO insert company name as input variable

    # Plotting
    fig, ax = plt.subplots(figsize=(10, 6))  

    # Plot Clicks
    before = ax.plot(forecast_df_before['date'], forecast_df_before[variable], label=f'{variable}', color = 'royalblue')

    # # Plot Clicks Modified
    # ax.plot(forecast_df_before['date'], forecast_df_before[f'{variable}_modified'], label=f'{variable} Modified', color = 'royalblue')

    # Plot Clicks Dashed
    after_CPS = ax.plot(forecast_df_after['date'], forecast_df_after[f'{variable}_modified'], linestyle = 'dashed', color = 'royalblue', label = 'CPS increase')
    after_noCPS = ax.plot(forecast_df_after['date'], forecast_df_after[variable], linestyle = 'dotted', color = 'royalblue', label = 'No CPS increase')

    lower_CI = ax.fill_between(forecast_df['date'], forecast_df[f'{variable}_lower'], forecast_df[f'{variable}_modified'], color='green', alpha=0.3, label='Lower Confidence Interval')
    upper_CI = ax.fill_between(forecast_df['date'], forecast_df[f'{variable}_upper'], forecast_df[f'{variable}_modified'], color='limegreen', alpha=0.3, label='Upper Confidence Interval')

    if variable == 'Total':
        variable = ' Sales value'

    # Adding title and labels
    # TODO Remove the date and clicks #

    ax.set_title(f'Forecasted {variable} {company_name} after CPS increase')
    ax.set_xlabel('Date')
    ax.set_ylabel(f'{variable}')

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)

    plt.legend()

    # Adding grid lines
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    # Displaying the legend with a customized position
    # plt.legend(loc='upper left', fontsize=12)

    # # Rotating the x-axis labels for better readability
    # ax.xticks(rotation=45)

    # # Displaying the plot
    # ax.plt.tight_layout()
    # Display the plot

    return fig 

def create_forecast(var_array, CPS_percentage, num_new_days, lower_bound, upper_bound):
    # Check if string, this is due nature of csv file
    if var_array.dtype == object:
            for value in range(len(var_array)):
                var_array[value] = var_array[value].replace(',','.')
            var_array = [float(x) if x != 'NaN' else np.nan for x in var_array]
    var_array = np.where(var_array == 0, np.nan, var_array)

    # Convert array to seperate lists
    list_var = var_array.tolist()
    list_modified = var_array.tolist()
    list_upper = var_array.tolist()
    list_lower = var_array.tolist()
    list_no_fluctuation = var_array.tolist()


    factor = 1
    # Indicate the percentage you want the value to increase
    factor_increase = CPS_percentage
    factor_per_iteration = factor_increase / num_new_days
    # TODO decide self or always same confidence bands
    lower_bound_percentage = lower_bound
    upper_bound_percentage = upper_bound
    factor_per_iteration_lower = lower_bound_percentage / num_new_days    
    factor_per_iteration_upper = upper_bound_percentage / num_new_days          
    # TODO make upper and lower input parameter

    # Define upper and lowerbound factor 
    factor_upper = 1.01
    factor_lower = 0.99

    for i in range(1, num_new_days + 1):
        # Append rolling mean

        mean_value = np.nanmean(list_var[-10:])

        # Introduce fluctuations in the factor
        fluctuation = random.uniform(-0.025, 0.025)  # Adjust the range as needed
        fluctuated_factor = factor + fluctuation
        list_var.append(mean_value * (1+fluctuation))

        # Append factor on top of mean
        list_no_fluctuation.append(mean_value * factor)
        list_modified.append(mean_value * fluctuated_factor)
        # Append factors for lower and upper bounds, these necessary for confidence bounds
        list_lower.append(list_no_fluctuation[-1] * factor_lower)
        list_upper.append(list_no_fluctuation[-1] * factor_upper)
        # Add new  factors
        factor += factor_per_iteration
        factor_lower -= factor_per_iteration_lower
        factor_upper += factor_per_iteration_upper

    return list_var,list_modified,list_upper,list_lower

def create_forecast_plot(forecast_data, variable ,forecast_days, CPS_percentage, cutoff_date, company_name, lower_bound, upper_bound):
    # Read data to dataframe
    forecast_data = forecast_data[~forecast_data['Period'].str.contains('Totals')]
    # Convert date to datetime
    forecast_data['date'] = pd.to_datetime(forecast_data['Period'], format = '%d-%m-%Y')
    # Remove today from dataframe 
    forecast_data = forecast_data[forecast_data['date'] != pd.to_datetime('today').normalize()]
    # Variable is the var we are going to forecast, e.g. Clicks or Total
    forecast_data = forecast_data.loc[:, ['date', variable]]
    # Order so dates start with earliest date
    forecast_data = forecast_data.sort_values(by='date')
    # Define last date
    last_date = forecast_data['date'].max()
    # Define new days to forecast 
    num_new_days = forecast_days
    # Create new dates starting from the last date
    new_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=num_new_days, freq='D')
    # extended_date_df = pd.concat([forecast_data['date'], pd.DataFrame({'date':new_dates})], axis = 0)
    extended_date_df = pd.concat([forecast_data['date'], pd.DataFrame(new_dates)])
    # Create series for merging later
    extended_date_df = extended_date_df.iloc[:,0]

    # Create lists for storing predictions
    list_var, list_modified, list_upper, list_lower = create_forecast(forecast_data[variable].values, CPS_percentage, num_new_days, lower_bound, upper_bound)

    # Create dataframe of all lists
    forecast_df = pd.DataFrame({"date":extended_date_df, variable:list_var, f"{variable}_modified": list_modified,f"{variable}_upper": list_upper, f"{variable}_lower": list_lower})
    forecast_df['date'] = pd.to_datetime(forecast_df['date'])
    

    # Cut dateframe date if you want to
    forecast_df = forecast_df[forecast_df['date'] >=  cutoff_date]
    # Add new columns so you can see prognotized columns 
    forecast_df_after = forecast_df[forecast_df['date'] >= last_date]
    forecast_df_before = forecast_df[forecast_df['date'] <= last_date]

    # Insert company_name
    company_name = company_name

    # Print plot
    figure = create_plot(forecast_df, forecast_df_after, forecast_df_before, company_name, variable)
    st.pyplot(figure)

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False


if not check_password():
    st.stop()  # Do not continue if check_password is not True.

uploaded_file = st.file_uploader("Choose a file")
if uploaded_file is not None:

    # Can be used wherever a "file-like" object is accepted:
    dataframe = pd.read_csv(uploaded_file, sep = ';')

    forecast_days = st.number_input('Geef aan tot hoeveel dagen in de toekomst de grafiek moet lopen (bijv 30)', value = 30)
    CPS_percentage = st.number_input('Vul de verhoging / verlaging van CPS percentage in, in hele procenten, bijv, 50', value = 50)
    CPS_percentage = CPS_percentage / 100
    lower_bound = st.number_input('Vul het percentage van de confidence interval voor de daling in. Hoe hoger het percentage des te wijder het interval', value = 20)
    lower_bound = lower_bound / 100
    upper_bound = st.number_input('Vul het percentage van de confidence interval om de stijging in. Hoe hoger het percentage des te wijder het interval', value = 20)
    upper_bound = upper_bound / 100

    cutoff_date = st.text_input("Vul datum in vanaf waar de grafiek moet beginnen (YYYY-MM-DD). Datum moet ingevuld worden")
    if not cutoff_date:
        # Insert random date if no date is filled in so graph is created
        cutoff_date = pd.to_datetime(dataframe['Period'].min())
    company_name = st.text_input("Vul de naam in van het bedrijf waarvoor je forecast wilt maken. Dit is dan te zien in de titel van de grafiek")
    if st.button("Maak forecast grafiek"):
    #   create_forecast_plot(dataframe, forecast_days = 30, CPS_percentage = 0.5, cutoff_date = '2024-05-15', company_name = 'ShopForward')
      create_forecast_plot(dataframe, 'Clicks',  forecast_days = forecast_days, CPS_percentage = CPS_percentage, cutoff_date = cutoff_date, company_name = company_name, lower_bound = lower_bound, upper_bound = upper_bound)
      create_forecast_plot(dataframe, 'Value',  forecast_days = forecast_days, CPS_percentage = CPS_percentage, cutoff_date = cutoff_date, company_name = company_name, lower_bound = lower_bound, upper_bound = upper_bound)
      create_forecast_plot(dataframe, '# Total',  forecast_days = forecast_days, CPS_percentage = CPS_percentage, cutoff_date = cutoff_date, company_name = company_name, lower_bound = lower_bound, upper_bound = upper_bound)