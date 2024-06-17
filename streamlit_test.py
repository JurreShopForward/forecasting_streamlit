import streamlit as st
import pandas as pd
from io import StringIO

from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import random



def create_plot(forecast_df, forecast_df_after, forecast_df_before, company_name):
    # TODO insert company name as input variable

    # Plotting
    fig, ax = plt.subplots(figsize=(10, 6))  

    # Plot Clicks
    ax.plot(forecast_df_before['date'], forecast_df_before['clicks'], label='Clicks', color = 'royalblue')

    # Plot Clicks Modified
    ax.plot(forecast_df_before['date'], forecast_df_before['clicks_modified'], label='Clicks Modified', color = 'royalblue')


    # Plot Clicks Dashed
    ax.plot(forecast_df_after['date'], forecast_df_after['clicks_modified'], linestyle = 'dashed', color = 'royalblue')
    ax.plot(forecast_df_after['date'], forecast_df_after['clicks'], linestyle = 'dashed', color = 'royalblue')

    ax.fill_between(forecast_df['date'], forecast_df['clicks_lower'], forecast_df['clicks_modified'], color='red', alpha=0.3, label='Confidence Band')
    ax.fill_between(forecast_df['date'], forecast_df['clicks_upper'], forecast_df['clicks_modified'], color='green', alpha=0.3, label='Confidence Band')

    # Adding title and labels
    ax.set_title(f'Forecasted clicks {company_name} after CPS increase')
    ax.set_xlabel('Date')
    ax.set_ylabel('Number of Clicks')

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

def create_forecast(forecast_data, CPS_percentage, num_new_days):
    click_array = forecast_data['Clicks'].values
    click_list = click_array.tolist()

    click_list_modified = click_array.tolist()
    click_list_upper = click_array.tolist()
    click_list_lower = click_array.tolist()

    factor = 1
    # Indicate the percentage you want the value to increase
    factor_increase = CPS_percentage
    factor_per_iteration = factor_increase / num_new_days
    # TODO decide self or always same confidence bands
    factor_lower_upper = 0.2
    factor_per_iteration_lower_upper = factor_lower_upper / num_new_days            
    # Define upper and lowerbound factor 
    factor_upper = 1.01
    factor_lower = 0.99

    for i in range(1, num_new_days + 1):
        # Append rolling mean
        mean_value = np.mean(click_list[-10:])
        # Introduce fluctuations in the factor
        fluctuation = random.uniform(-0.025, 0.025)  # Adjust the range as needed
        fluctuated_factor = factor + fluctuation
        click_list.append(mean_value * (1+fluctuation))

        # Append factor on top of mean
        click_list_modified.append(mean_value * fluctuated_factor)
        # Append factors for lower and upper bounds, these necessary for confidence bounds
        click_list_lower.append(click_list_modified[-1] * factor_lower)
        click_list_upper.append(click_list_modified[-1] * factor_upper)
        # Add new  factors
        factor += factor_per_iteration
        factor_lower -= factor_per_iteration_lower_upper
        factor_upper += factor_per_iteration_lower_upper
    return click_list,click_list_modified,click_list_upper,click_list_lower

def create_forecast_plot(forecast_data, forecast_days, CPS_percentage, cutoff_date, company_name):
    # Read data to dataframe
    # forecast_data = pd.read_csv(file)
    forecast_data = forecast_data.dropna()
    # Convert date to datetime
    forecast_data['date'] = pd.to_datetime(forecast_data['Period'], format = '%d/%m/%Y')
    forecast_data = forecast_data.loc[:, ['date', 'Clicks']]
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
    click_list, click_list_modified, click_list_upper, click_list_lower = create_forecast(forecast_data, CPS_percentage, num_new_days)

    # Create dataframe of all lists
    forecast_df = pd.DataFrame({"date":extended_date_df, "clicks":click_list, "clicks_modified": click_list_modified,"clicks_upper": click_list_upper, "clicks_lower": click_list_lower})
    forecast_df['date'] = pd.to_datetime(forecast_df['date'])

    # Cut dateframe date if you want to
    forecast_df = forecast_df[forecast_df['date'] >=  cutoff_date]
    # Add new columns so you can see prognotized columns 
    forecast_df_after = forecast_df[forecast_df['date'] >= last_date]
    forecast_df_before = forecast_df[forecast_df['date'] <= last_date]

    # Insert company_name
    company_name = company_name
    # Print plot
    figure = create_plot(forecast_df, forecast_df_after, forecast_df_before, company_name)
    st.pyplot(figure)

uploaded_file = st.file_uploader("Choose a file")
if uploaded_file is not None:

    # Can be used wherever a "file-like" object is accepted:
    dataframe = pd.read_csv(uploaded_file)

    # forecast_days = st.number_input('Enter the forecast horizon must be integer', value = 1)
    # CPS_percentage = st.number_input('Vul de verhoging / verlaging van CPS percentage in, in hele procenten, bijv, 50', value = 1)
    # CPS_percentage = CPS_percentage / 100
    # cutoff_date = st.text_input("Vul datum in vanaf waar de grafiek moet beginnen (YYYY-MM-DD)")
    # company_name = st.text_input("Vul de naam in van het bedrijf waarvoor je forecast wilt maken")
    if st.button("Maak forecast grafiek"):
      create_forecast_plot(dataframe, forecast_days = 30, CPS_percentage = 0.5, cutoff_date = '2024-05-15', company_name = 'ShopForward')
      # create_forecast_plot(dataframe, forecast_days = forecast_days, CPS_percentage = CPS_percentage, cutoff_date = cutoff_date, company_name = company_name)

  
