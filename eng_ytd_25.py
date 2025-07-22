# =================================== IMPORTS ================================= #
import csv, sqlite3
import numpy as np 
import pandas as pd 
import seaborn as sns 
import matplotlib.pyplot as plt 
import plotly.figure_factory as ff
import plotly.graph_objects as go
from geopy.geocoders import Nominatim
from folium.plugins import MousePosition
import plotly.express as px
from datetime import datetime
import folium
import os
import sys
from collections import Counter
# ------
import json
import base64
import gspread
from oauth2client.service_account import ServiceAccountCredentials
# ------
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
from dash.development.base_component import Component

# 'data/~$bmhc_data_2024_cleaned.xlsx'
# print('System Version:', sys.version)
# -------------------------------------- DATA ------------------------------------------- #

current_dir = os.getcwd()
current_file = os.path.basename(__file__)
script_dir = os.path.dirname(os.path.abspath(__file__))
# data_path = 'data/Engagement_March_2025.xlsx'
# file_path = os.path.join(script_dir, data_path)
# data = pd.read_excel(file_path)
# df = data.copy()

# Define the Google Sheets URL
sheet_url = "https://docs.google.com/spreadsheets/d/1D0oOioAfJyNCHhJhqFuhxxcx3GskP9L-CIL1DcOyhug/edit?resourcekey=&gid=1261604285#gid=1261604285"

# Define the scope
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Load credentials
encoded_key = os.getenv("GOOGLE_CREDENTIALS")

if encoded_key:
    json_key = json.loads(base64.b64decode(encoded_key).decode("utf-8"))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(json_key, scope)
else:
    creds_path = r"C:\Users\CxLos\OneDrive\Documents\BMHC\Data\bmhc-timesheet-4808d1347240.json"
    if os.path.exists(creds_path):
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    else:
        raise FileNotFoundError("Service account JSON file not found and GOOGLE_CREDENTIALS is not set.")

# Authorize and load the sheet
client = gspread.authorize(creds)
sheet = client.open_by_url(sheet_url)
data = pd.DataFrame(client.open_by_url(sheet_url).sheet1.get_all_records())
df = data.copy()

# Strip whitespace from column names and string values
for col in df.columns:
    if df[col].dtype == 'object':
        df[col] = df[col].map(lambda x: x.strip() if isinstance(x, str) else x)


# Define a discrete color sequence
# color_sequence = px.colors.qualitative.Plotly

# Filtered df where 'Date of Activity:' is between October 1, 2024 to September 30, 2025
df['Date of Activity'] = pd.to_datetime(df['Date of Activity'], format='%m/%d/%Y', errors='coerce')
df = df[(df['Date of Activity'] >= '2024-10-01') & (df['Date of Activity'] <= '2025-09-30')]

# Get the reporting month:
report_year = datetime(2025, 1, 1).strftime("%Y")

# print(df.head(20))
# print('Total Marketing Events: ', len(df))
# print('Column Names: \n', df.columns.tolist())
# print('DF Shape:', df.shape)
# print('Dtypes: \n', df.dtypes)
# print('Info:', df.info())
# print("Amount of duplicate rows:", df.duplicated().sum())
# print('Current Directory:', current_dir)
# print('Script Directory:', script_dir)
# print('Path to data:',file_path)

# ================================= Columns ================================= #

columns = [
    'Timestamp',
    'Date of Activity', 
    'Person submitting this form:',
    'Activity Duration (minutes):', 
    'Care Network Activity:', 
    'Entity name:', 
    'Brief Description:', 
    'Activity Status:', 
    'BMHC Administrative Activity:', 
    'Total travel time (minutes):', 
    'Community Outreach Activity:', 
    'Number engaged at Community Outreach Activity:', 
    'Any recent or planned changes to BMHC lead services or programs?'
]

# =============================== Missing Values ============================ #

# missing = df.isnull().sum()
# print('Columns with missing values before fillna: \n', missing[missing > 0])

# ============================== Data Preprocessing ========================== #

# Check for duplicate columns
# duplicate_columns = df.columns[df.columns.duplicated()].tolist()
# print(f"Duplicate columns found: {duplicate_columns}")
# if duplicate_columns:
#     print(f"Duplicate columns found: {duplicate_columns}")

# Rename columns
df.rename(
    columns={
        "Activity Duration (minutes):": "Activity Duration",
        "Total travel time (minutes):": "Travel",
        "Person submitting this form:": "Person",
        "Activity Status:": "Activity Status",
        "Entity name:": "Entity",
        "Care Network Activity:": "Care Activity",
        "BMHC Administrative Activity:": "Admin Activity",
        "Community Outreach Activity:": "Outreach Activity",
        "Number engaged at Community Outreach Activity:": "Number Engaged",
    }, 
inplace=True)

# df_larry = df[df['Person'] == 'Larry Wallace Jr.']

# ========================= Total Engagements ========================== #

# Total number of engagements:
total_engagements = len(df)
# print('Total Engagements:', total_engagements)
# print("Person length before:", len(df['Person']))

# -------------------------- Engagement Hours -------------------------- #

# Sum of 'Activity Duration (minutes):' dataframe converted to hours:

# Convert 'Activity Duration (minutes):' to numeric
df['Activity Duration'] = pd.to_numeric(df['Activity Duration'], errors='coerce')
engagement_hours = df['Activity Duration'].sum()/60
engagement_hours = round(engagement_hours)

# -------------------------- Total Travel Time ------------------------ #

df['Travel'] = (
    df['Travel']
    .astype(str)
    .str.strip()
    .replace({
        'Sustainable Food Center + APH Health Education Strategy Meeting & Planning Activities': 0
        })
)
df['Travel'] = pd.to_numeric(df['Travel'], errors='coerce').fillna(0)

# Sum travel time in hours and round
total_travel_time = round(df['Travel'].sum() / 60)
# print(total_travel_time)

# travel time value counts
# print(df['Total travel time (minutes):'].value_counts())

# ---------------------------- Activity Status ----------------------- #

df_activity_status = df.groupby('Activity Status').size().reset_index(name='Count')

status_bar=px.bar(
    df_activity_status,
    x='Activity Status',
    y='Count',
    color='Activity Status',
    text='Count',
).update_layout(
    height=460, 
    width=780,
    title=dict(
        text='Activity Status',
        x=0.5, 
        font=dict(
            size=25,
            family='Calibri',
            color='black',
            )
    ),
    font=dict(
        family='Calibri',
        size=18,
        color='black'
    ),
    xaxis=dict(
        tickangle=0,  # Rotate x-axis labels for better readability
        tickfont=dict(size=18),  # Adjust font size for the tick labels
        title=dict(
            # text=None,
            text="Status",
            font=dict(size=20),  # Font size for the title
        ),
        # showticklabels=False  # Hide x-tick labels
        showticklabels=True  # Hide x-tick labels
    ),
    yaxis=dict(
        title=dict(
            text='Count',
            font=dict(size=20),  # Font size for the title
        ),
    ),
    legend=dict(
        # title='Support',
        title_text='',
        orientation="v",  # Vertical legend
        x=1.05,  # Position legend to the right
        y=1,  # Position legend at the top
        xanchor="left",  # Anchor legend to the left
        yanchor="top",  # Anchor legend to the top
        # visible=False
        visible=True
    ),
    hovermode='closest', # Display only one hover label per trace
    bargap=0.08,  # Reduce the space between bars
    bargroupgap=0,  # Reduce space between individual bars in groups
).update_traces(
    textposition='auto',
    hovertemplate='<b>Status:</b> %{label}<br><b>Count</b>: %{y}<extra></extra>'
)

status_pie = px.pie(
    df_activity_status,
    names='Activity Status',
    values='Count',
).update_layout(
    title='Activity Status',
    height=450,
    title_x=0.5,
    font=dict(
        family='Calibri',
        size=17,
        color='black'
    ),
    margin=dict(t=70, r=50, b=30, l=40),
).update_traces(
    rotation=0,
    texttemplate='%{value}<br>(%{percent:.2%})',
    hovertemplate='<b>%{label}</b>: %{value}<extra></extra>'
)

# ----------------------------- Admin Activity --------------------------- #

# print("Admin Unique Before: \n", df["Admin Activity"].unique().tolist())
# print("Admin Value Counts: \n", df["Admin Activity"].value_counts())

admin_uique = [
'Record Keeping & Documentation', '', 'Community engagement and Partnership', 'Communication & Correspondence', 'Research & Planning', 'Meeting with Kensington Property Admin and tour of the remodeled property', 'weekly COA meeting and BOLO review', 'HR Support', 'HAP monthly meeting', 'email composition and scheduling for needed zoom to precede with move ins to Kensington', 'Compliance & Policy Enforcement', 'CHECK HMIS FOR SHARED CLIENT', 'Financial & Budgetary Management', 'IT', 'Community partnership', 'Outreach and community engagement', 'Office Management', 'Community Engagement', 'Engagement /Outreach', 'biweekly psh review with Doc', 'Emergency Management Training', 'PSH Meeting', '1 to 1 Strategy Meeting', 'EOW 1 to 1 Performance Review', 'Meeting with LINC for shared cases (Kevin)'
]

admin_categories = [
    
    "Financial & Budgetary Management",
    "Communication & Correspondence",
    "Compliance & Policy Enforcement",
    "HR Support",
    "Office Management",
    "Record Keeping & Documentation",
    "Research & Planning",
]

admin_activity = df[df['Admin Activity'].notnull()]
admin_activity = admin_activity[admin_activity['Admin Activity'].str.strip() != '']

admin_activity['Admin Activity'] = (
    admin_activity['Admin Activity']
    .str.strip()
    .replace({
        'Record Keeping & Documentation': 'Record Keeping & Documentation',
        'Community engagement and Partnership': 'Communication & Correspondence',
        'Communication & Correspondence': 'Communication & Correspondence',
        'Research & Planning': 'Research & Planning',
        'Meeting with Kensington Property Admin and tour of the remodeled property': 'Communication & Correspondence',
        'weekly COA meeting and BOLO review': 'Communication & Correspondence',
        'HR Support': 'HR Support',
        'HAP monthly meeting': 'Communication & Correspondence',
        'email composition and scheduling for needed zoom to precede with move ins to Kensington': 'Communication & Correspondence',
        'Compliance & Policy Enforcement': 'Compliance & Policy Enforcement',
        'CHECK HMIS FOR SHARED CLIENT': 'Record Keeping & Documentation',
        'Financial & Budgetary Management': 'Financial & Budgetary Management',
        'IT': 'Office Management',
        'Community partnership': 'Communication & Correspondence',
        'Outreach and community engagement': 'Communication & Correspondence',
        'Office Management': 'Office Management',
        'Community Engagement': 'Communication & Correspondence',
        'Engagement /Outreach': 'Communication & Correspondence',
        'biweekly psh review with Doc': 'Record Keeping & Documentation',
        'Emergency Management Training': 'Compliance & Policy Enforcement',
        'PSH Meeting': 'Record Keeping & Documentation',
        '1 to 1 Strategy Meeting': 'Communication & Correspondence',
        'EOW 1 to 1 Performance Review': 'Communication & Correspondence',
        'Meeting with LINC for shared cases (Kevin)': 'Communication & Correspondence'
    })
)

# Identify unexpected/unapproved categories
admin_unexpected = admin_activity[~admin_activity['Admin Activity'].isin(admin_categories)]
# print("Admin Unexpected: \n", admin_unexpected['Admin Activity'].unique().tolist())

normalized_categories = {cat.lower().strip(): cat for cat in admin_categories}

counter = Counter()
for entry in df['Admin Activity']:
    
    # Split and clean each category
    items = [i.strip().lower() for i in entry.split(",")]
    for item in items:
        if item in normalized_categories:
            counter[normalized_categories[item]] += 1

# Display the result
# for category, count in counter.items():
#     print(f"Support Counts: \n {category}: {count}")

admin_activity = pd.DataFrame(counter.items(), columns=['Admin Activity', 'Count']).sort_values(by='Count', ascending=False)

# Group by the renamed 'admin_activity' column
# admin_activity = admin_activity.groupby('Admin Activity').size().reset_index(name='Count')
# print(admin_activity.head(10))

admin_bar=px.bar(
    admin_activity,
    x="Admin Activity",
    y='Count',
    color="Admin Activity",
    text='Count',
).update_layout(
    height=850, 
    width=1900,
    title=dict(
        text='Admin Activity Bar Chart',
        x=0.5, 
        font=dict(
            size=25,
            family='Calibri',
            color='black',
            )
    ),
    font=dict(
        family='Calibri',
        size=18,
        color='black'
    ),
    xaxis=dict(
        tickangle=-20,  # Rotate x-axis labels for better readability
        tickfont=dict(size=18),  # Adjust font size for the tick labels
        title=dict(
            # text=None,
            text="Admin Activity",
            font=dict(size=20),  # Font size for the title
        ),
        showticklabels=False
    ),
    yaxis=dict(
        title=dict(
            text='Count',
            font=dict(size=20),  # Font size for the title
        ),
    ),
    legend=dict(
        title='',
        orientation="v",  # Vertical legend
        x=1.05,  # Position legend to the right
        y=1,  # Position legend at the top
        xanchor="left",  # Anchor legend to the left
        yanchor="top",  # Anchor legend to the top
        visible=True
        # visible=False
    ),
    hovermode='closest', # Display only one hover label per trace
    bargap=0.08,  # Reduce the space between bars
    bargroupgap=0,  # Reduce space between individual bars in groups
).update_traces(
    textposition='auto',
    hovertemplate='<b></b> %{label}<br><b>Count</b>: %{y}<extra></extra>'
)

admin_pie=px.pie(
    admin_activity,
    names="Admin Activity",
    values='Count'
).update_layout(
    height=850,
    width=1700,
    # showlegend=False,
    showlegend=True,
    title='Admin Activity Pie Chart',
    title_x=0.5,
    font=dict(
        family='Calibri',
        size=17,
        color='black'
    )
).update_traces(
    rotation=130,
    texttemplate='%{value}<br>(%{percent:.2%})',
    # textinfo='none',
    hovertemplate='<b>%{label}</b>: %{value}<extra></extra>',
    # pull = [0.1 if v < 5 else 0.01 + (v / max(admin_activity["Count"]) * 0.05) for v in admin_activity["Count"]]

    # pull=[0.15 if v < 5 else 0.04 for v in admin_activity["Count"]]  # Pull out small slices more, and others slightly
    #  pull=[0.1 if v < 5 else 0 for v in admin_activity["Count"]]  # Pull out small slices more, no pull for large ones
)

# -------------------------- Care Network Activity ----------------------- #

# print("Care Network Unique Before: \n", df["Care Activity"].unique().tolist())
# print("Care Netowrk Activities: \n", care_network_activity.value_counts())

care_uique = [
    'Work Force Development', '', 'client engagement and referrals', 'SDoH Provider', 'Clinical Provider', 'Academic', 'ECHO PSH PILOT PROGRAM', 'ECHO PSH', 'Referral service/community engagement', 'Outreach', 'Outreach/awareness', 'Community Engagement', 'Community Event for Networking', 'Religious', 'Give Back Program', 'ECHO Pilot PSH Program', 'ECHO', 'PSH PILOT', 'ECHO PILOT PROGRAM', 'Community Outreach/Awareness', 'Government'
]

care_categories = [
    "Academic",
    "Clinical Provider",
    "Give Back Program",
    "Government",
    "Religious",
    "SDoH Provider",
    "Work Force Development",
]

care_activity = df[df['Care Activity'].notnull()]
care_activity = care_activity[care_activity['Care Activity'].str.strip() != '']
care_activity = care_activity.copy()  # Avoid SettingWithCopyWarning

care_activity['Care Activity'] = (
    care_activity['Care Activity']
    .str.strip()
    .replace({
        'client engagement and referrals': 'SDoH Provider',
        'SDoH Provider': 'SDoH Provider',
        'Clinical Provider': 'Clinical Provider',
        'Academic': 'Academic',
        'ECHO PSH PILOT PROGRAM': 'Government',
        'ECHO PSH': 'Government',
        'ECHO Pilot PSH Program': 'Government',
        'ECHO': 'Government',
        'PSH PILOT': 'Government',
        'ECHO PILOT PROGRAM': 'Government',
        'Referral service/community engagement': 'SDoH Provider',
        'Outreach': 'SDoH Provider',
        'Outreach/awareness': 'SDoH Provider',
        'Community Engagement': 'SDoH Provider',
        'Community Event for Networking': 'SDoH Provider',
        'Religious': 'Religious',
        'Give Back Program': 'Give Back Program',
        'Community Outreach/Awareness': 'SDoH Provider',
        'Government': 'Government',
        'Work Force Development': 'Work Force Development',
    })
)

# Identify unexpected/unapproved categories
care_unexpected = care_activity[~care_activity['Care Activity'].isin(care_categories)]

# Group by the renamed 'Care_activity' column
care_network_activity = care_activity.groupby('Care Activity').size().reset_index(name='Count')

care_bar=px.bar(
    care_network_activity,
    x="Care Activity",
    y='Count',
    color="Care Activity",
    text='Count',
).update_layout(
    height=850, 
    width=1800,
    title=dict(
        text='Care Network Activity Bar Chart',
        x=0.5, 
        font=dict(
            size=25,
            family='Calibri',
            color='black',
            )
    ),
    font=dict(
        family='Calibri',
        size=18,
        color='black'
    ),
    xaxis=dict(
        tickangle=-20,  # Rotate x-axis labels for better readability
        tickfont=dict(size=18),  # Adjust font size for the tick labels
        title=dict(
            # text=None,
            text="Care Network Activity",
            font=dict(size=20),  # Font size for the title
        ),
        showticklabels = False
    ),
    yaxis=dict(
        title=dict(
            text='Count',
            font=dict(size=20),  # Font size for the title
        ),
    ),
    legend=dict(
        title='',
        orientation="v",  # Vertical legend
        x=1.05,  # Position legend to the right
        y=1,  # Position legend at the top
        xanchor="left",  # Anchor legend to the left
        yanchor="top",  # Anchor legend to the top
        # visible=False
    ),
    hovermode='closest', # Display only one hover label per trace
    bargap=0.08,  # Reduce the space between bars
    bargroupgap=0,  # Reduce space between individual bars in groups
).update_traces(
    textposition='auto',
    hovertemplate='<b></b> %{label}<br><b>Count</b>: %{y}<extra></extra>'
)

# Insurance Status Pie Chart
care_pie=px.pie(
    care_network_activity,
    names="Care Activity",
    values='Count'
).update_layout(
    height=850,
    width=1700,
    # showlegend=False,
    title='Care Network Activity Pie Chart',
    title_x=0.5,
    font=dict(
        family='Calibri',
        size=17,
        color='black'
    )
).update_traces(
    rotation=70,
    # texttemplate='%{value}<br>(%{percent:.2%})',
    textinfo='none',
    hovertemplate='<b>%{label}</b>: %{value}<extra></extra>',
    # pull=[0.15 if v < 5 else 0.04 for v in admin_activity["Count"]]  # Pull out small slices more, and others slightly
)

# --------------------------Community Outreach Activity ---------------------- #

# print("Outreach Unique Before: \n", df['Outreach Activity'].unique().tolist())

outreach_unique = [
    'Mental HealthTraining', 'Presentation', 'Advocacy, Presentation', 'Advocacy', 'Tabling Event',
    'Action planning', 'Mental Health First Aid Training', 'Presentation, Mental Training',
    'Team meeting, training, and meeting with Dominique', 'Presentation,  Mental Health First Aid Training',
    'HR onboarding', 'HR Onboarding', 'Training', 'Advocacy, Participant outreach',
    'Advocacy, data collection', 'Onsite Outreach', 'Presentation, Tabling Event',
    'Advocacy, Meeting/partnership', 'Community engagement',
    'Team huddle,  meeting with Cameron, meeting with Misha and Arie to best determine coverage for the remainder of the week. Also sure we are on the same page on form submission',
    'Navigation Huddle', 'CUC/MONTHLY MEETING', 'tour/partnership', 'tour and partnership',
    'Followed up 22 contacts collected throughout the week.  Impact and engagement forms. Follow up  calls',
    'Schedule appointments', 'Partnership Building', 'Capacity Building', 'Client navigation',
    'Advocacy, Presentation, Tabling Event', 'CUC MEETING', 'scheduling meeting/ tour',
    'Advocacy,', 'Advocacy, Tabling Event', 'meeting', 'administrative',
    'Follow up on unhoused contacts,  team meeting,  newsletter submissions,  return calls'
]

outreach_categories = [
    "Advocacy",
    "Event (virtual)",
    "Event (In-person)",
    "Presentation",
    "Tabling Event",
    "Health Event",
    "Scheduling",
]

# Replacement map with lowercase keys
replacement_map = {
    # Health Events
    'mental healthtraining': 'Health Event',
    'mental health first aid training': 'Health Event',
    'movement is medicine': 'Health Event',

    # Presentations
    'presentation': 'Presentation',
    'continuous education/training': 'Presentation',

    # Tabling
    'tabling event': 'Tabling Event',
    'tabling': 'Tabling Event',

    # Advocacy-related
    'advocacy': 'Advocacy',
    'onsite outreach': 'Advocacy',
    'client navigation': 'Advocacy',
    'capacity building': 'Advocacy',
    'partnership building': 'Advocacy',
    'community engagement': 'Advocacy',
    'community engagement /outreach networking': 'Advocacy',
    'outreach & navigation': 'Advocacy',
    'participant outreach': 'Advocacy',
    'data collection': 'Advocacy',
    'meeting/partnership': 'Advocacy',
    'schedule appointments': 'Advocacy',
    'follow up on unhoused contacts': 'Advocacy',
    'followed up 22 contacts collected throughout the week. impact and engagement forms. follow up calls': 'Advocacy',
    'team huddle': 'Advocacy',

    # Event (virtual)
    'cuc/monthly meeting': 'Event (virtual)',
    'cuc meeting': 'Event (virtual)',
    'tour/partnership': 'Event (virtual)',
    'tour and partnership': 'Event (virtual)',
    'training': 'Event (virtual)',
    'team meeting': 'Event (virtual)',
    'navigation huddle': 'Event (virtual)',
    'huddle': 'Event (virtual)',
    'scheduling meeting/ tour': 'Event (virtual)',
    'hr onboarding': 'Event (virtual)',
    'administrative': 'Event (virtual)',
    'meeting': 'Event (virtual)',
    'event (virtual)': 'Event (virtual)',
}

# Filter DataFrame
outreach_activity = df[df['Outreach Activity'].notnull()]
outreach_activity = outreach_activity[outreach_activity['Care Activity'].str.strip() != '']
outreach_activity = outreach_activity.copy()

# print("Outreach Length:", len(outreach_activity))

# Count occurrences after cleaning + replacing
counter = Counter()

for entry in outreach_activity['Outreach Activity']:
    items = [i.strip().lower() for i in entry.split(",") if i.strip()]
    for item in items:
        normalized = replacement_map.get(item, item.title())  # fallback to title-case original
        counter[normalized] += 1

# Convert to DataFrame
community_outreach_activity = (
    pd.DataFrame(counter.items(), columns=['Outreach Activity', 'Count'])
    .sort_values(by='Count', ascending=False)
)

# print(community_outreach_activity)

community_bar=px.bar(
    community_outreach_activity,
    x="Outreach Activity",
    y='Count',
    color="Outreach Activity",
    text='Count',
).update_layout(
    height=850, 
    width=1800,
    title=dict(
        text='Community Outreach Activity Bar Chart',
        x=0.5, 
        font=dict(
            size=25,
            family='Calibri',
            color='black',
            )
    ),
    font=dict(
        family='Calibri',
        size=18,
        color='black'
    ),
    xaxis=dict(
        tickangle=-20,  # Rotate x-axis labels for better readability
        tickfont=dict(size=18),  # Adjust font size for the tick labels
        title=dict(
            # text=None,
            text="Community Outreach Activity",
            font=dict(size=20),  # Font size for the title
        ),
        showticklabels=False
        # showticklabels=True 
    ),
    yaxis=dict(
        title=dict(
            text="Count",
            font=dict(size=20),  # Font size for the title
        ),
    ),
    legend=dict(
        title="",
        orientation="v",  # Vertical legend
        x=1.05,  # Position legend to the right
        y=1,  # Position legend at the top
        xanchor="left",  # Anchor legend to the left
        yanchor="top",  # Anchor legend to the top
        visible=True
        # visible=False
    ),
    hovermode='closest', # Display only one hover label per trace
    bargap=0.08,  # Reduce the space between bars
    bargroupgap=0,  # Reduce space between individual bars in groups
).update_traces(
    textangle=0,
    textposition='auto',
    hovertemplate='<b></b> %{label}<br><b>Count</b>: %{y}<extra></extra>'
)

# Insurance Status Pie Chart
community_pie=px.pie(
    community_outreach_activity,
    names="Outreach Activity",
    values='Count'
).update_layout(
    height=850,
    width=1700,
    title='Community Outreach Activity Pie Chart',
    title_x=0.5,
    font=dict(
        family='Calibri',
        size=17,
        color='black'
    )
).update_traces(
    rotation=80,
    textinfo='none',
    # texttemplate='%{value}<br>(%{percent:.2%})',
    hovertemplate='<b>%{label}</b>: %{value}<extra></extra>',
    # The code is creating a list called `pull` using a list comprehension. For each value `v` in the
    # "Count" column of the `admin_activity` DataFrame (assuming it's a pandas DataFrame), it assigns
    # 0.15 to the corresponding element in `pull` if `v` is less than 5, and 0.05 if `v` is greater
    # than or equal to 5. This code is essentially adjusting the values based on the condition
    # provided.
    # pull=[0.15 if v < 5 else 0.05 for v in admin_activity["Count"]]  # Pull out small slices more, and others slightly
)

# ------------------------ Person Submitting Form -------------------- #

# print("Person length", len(df['Person']))
# print("Person Unique Before: \n", df["Person"].unique().tolist())
# print("Person Value Counts Before: \n", df["Person"].value_counts())

person_unique =[
'Larry Wallace Jr.', 'Cameron Morgan', 'Jordan Calbert', 'Eric Roberts', 'Michael Lambert', 'Dominique Street', 'Jaqueline Oviedo', 'Sonya Hosey', 'Kimberly Holiday', 'Antonio Montgomery', 'Arianna Williams', 'Toya Craney', 'Steve Kemgang, Toya Craney', 'Kiounis Williams', 'Steve Kemgang', 'Jaqueline Oviedo, Viana Varela', 'Arianna Williams, Cameron Morgan', 'Jaqueline Oviedo, Viviana Varela'
]

person_categories = [
    "Antonio Montgomery",
    'Arianna Williams', 
    "Azaniah Israel",
    "Cameron Morgan",
    "Dominique Street",
    "Eric Roberts",
    "Jaqueline Oviedo",
    "Jordan Calbert",
    "Kimberly Holiday",
    "Kiounis Williams",
    "Michael Lambert",
    "Larry Wallace Jr.",
    "Sonya Hosey",
    "Steve Kemgang",
    "Toya Craney",
]

# person df
df_person = df[df['Person'].notnull()]
df_person = df_person[df_person['Person'].str.strip() != '']


df_person['Person'] = (
    df_person['Person']
    .astype(str)  # ensure string type
    .str.strip()
    .replace({
        "Larry Wallace Jr": "Larry Wallace Jr.", 
        "Antonio Montggery": "Antonio Montgomery",
        "Kim Holiday" : "Kimberly Holiday",
        "Eric roberts" : "Eric Roberts",
        "Eric Robert" : "Eric Roberts",
    }, regex=False)
)

person_unexpected = df_person[~df_person['Person'].isin(person_categories)]
# print("Person Unexpected: \n", person_unexpected['Person'].unique().tolist())

person_normalized = {cat.lower().strip(): cat for cat in person_categories}
counter = Counter()
for entry in df_person['Person']:
    items = [i.strip().lower() for i in entry.split(",")]
    for item in items:
        if item in person_normalized:
            counter[person_normalized[item]] += 1
            
df_person = pd.DataFrame(counter.items(), columns=['Person', 'Count']).sort_values(by='Count', ascending=False)

person_bar=px.bar(
    df_person,
    x='Person',
    y='Count',
    color='Person',
    text='Count',
).update_layout(
    height=700, 
    width=950,
    title=dict(
        text='People Submitting Forms',
        x=0.5, 
        font=dict(
            size=25,
            family='Calibri',
            color='black',
            )
    ),
    font=dict(
        family='Calibri',
        size=18,
        color='black'
    ),
    xaxis=dict(
        tickangle=-15,  # Rotate x-axis labels for better readability
        tickfont=dict(size=18),  # Adjust font size for the tick labels
        title=dict(
            # text=None,
            text="Name",
            font=dict(size=20),  # Font size for the title
        ),
        showticklabels=False  # Hide x-tick labels
        # showticklabels=True  # Hide x-tick labels
    ),
    yaxis=dict(
        title=dict(
            text='Count',
            font=dict(size=20),  # Font size for the title
        ),
    ),
    legend=dict(
        # title='Support',
        title_text='',
        orientation="v",  # Vertical legend
        x=1.05,  # Position legend to the right
        y=1,  # Position legend at the top
        xanchor="left",  # Anchor legend to the left
        yanchor="top",  # Anchor legend to the top
        # visible=False
        visible=True
    ),
    hovermode='closest', # Display only one hover label per trace
    bargap=0.08,  # Reduce the space between bars
    bargroupgap=0,  # Reduce space between individual bars in groups
).update_traces(
    textposition='outside',
    hovertemplate='<b>Name:</b> %{label}<br><b>Count</b>: %{y}<extra></extra>'
)

# Person Pie Chart
person_pie=px.pie(
    df_person,
    names="Person",
    values='Count'  # Specify the values parameter
).update_layout(
    height=700, 
    title='Ratio of People Filling Out Forms',
    title_x=0.5,
    font=dict(
        family='Calibri',
        size=17,
        color='black'
    )
).update_traces(
    rotation=90,
    textposition='auto',
    texttemplate='%{value}<br>(%{percent:.2%})',
    hovertemplate='<b>%{label} Status</b>: %{value}<extra></extra>',
    # pull = [0.1 if v < 5 else 0.01 + (v / max(admin_activity["Count"]) * 0.05) for v in admin_activity["Count"]]
)

# # ========================== DataFrame Table ========================== #

# Engagement Table
engagement_table = go.Figure(data=[go.Table(
    # columnwidth=[50, 50, 50],  # Adjust the width of the columns
    header=dict(
        values=list(df.columns),
        fill_color='paleturquoise',
        align='center',
        height=30,  # Adjust the height of the header cells
        # line=dict(color='black', width=1),  # Add border to header cells
        font=dict(size=12)  # Adjust font size
    ),
    cells=dict(
        values=[df[col] for col in df.columns],
        fill_color='lavender',
        align='left',
        height=25,  # Adjust the height of the cells
        # line=dict(color='black', width=1),  # Add border to cells
        font=dict(size=12)  # Adjust font size
    )
)])

engagement_table.update_layout(
    margin=dict(l=50, r=50, t=30, b=40),  # Remove margins
    height=700,
    # width=1500,  # Set a smaller width to make columns thinner
    paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
    plot_bgcolor='rgba(0,0,0,0)'  # Transparent plot area
)

# Group by 'Entity name:' dataframe
entity_name_group = df.groupby('Entity').size().reset_index(name='Count')

# Entity Name Table
entity_name_table = go.Figure(data=[go.Table(
    header=dict(
        values=list(entity_name_group.columns),
        fill_color='paleturquoise',
        align='center',
        height=30,
        font=dict(size=12)
    ),
    cells=dict(
        values=[entity_name_group[col] for col in entity_name_group.columns],
        fill_color='lavender',
        align='left',
        height=25,
        font=dict(size=12)
    )
)])

entity_name_table.update_layout(
    margin=dict(l=50, r=50, t=30, b=40),
    height=900,
    width=780,
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)'
)

# ============================== Dash Application ========================== #

import dash
import dash_core_components as dcc
import dash_html_components as html

app = dash.Dash(__name__)
server = app.server

app.layout = html.Div(
    children=[ 
        html.Div(
            className='divv', 
            children=[ 
                html.H1('Partner Engagement Report', className='title'),
                html.H1(f'{report_year} 2025', className='title2'),
                html.Div(
                    className='btn-box', 
                    children=[
                        html.A(
                            'Repo',
                            href=f'https://github.com/CxLos/Eng_YTD_{report_year}',
                            className='btn'
                        )
                    ]
                )
            ]
        ),
        
        # Data Table
        # html.Div(
        #     className='row0',
        #     children=[
        #         html.Div(
        #             className='table',
        #             children=[
        #                 html.H1(
        #                     className='table-title',
        #                     children='Engagement Data Table'
        #                 )
        #             ]
        #         ),
        #         html.Div(
        #             className='table2', 
        #             children=[
        #                 dcc.Graph(
        #                     className='data',
        #                     figure=engagement_table
        #                 )
        #             ]
        #         )
        #     ]
        # ),

        # Row 1: Engagements and Hours
        html.Div(
            className='row1',
            children=[
                html.Div(
                    className='graph11',
                    children=[
                        html.Div(className='high1', children=[f'{report_year} Engagements:']),
                        html.Div(
                            className='circle1',
                            children=[
                                html.Div(
                                    className='hilite',
                                    children=[html.H1(className='high2', children=[total_engagements])]
                                )
                            ]
                        )
                    ]
                ),
                html.Div(
                    className='graph22',
                    children=[
                        html.Div(className='high3', children=[f'{report_year} Engagement Hours:']),
                        html.Div(
                            className='circle2',
                            children=[
                                html.Div(
                                    className='hilite',
                                    children=[html.H1(className='high4', children=[engagement_hours])]
                                )
                            ]
                        ) 
                    ]
                )
            ]
        ),

        # Row 1: Engagements and Hours
        html.Div(
            className='row1',
            children=[
                html.Div(
                    className='graph11',
                    children=[
                        html.Div(className='high5', children=[f'{report_year} Travel Hours']),
                        html.Div(
                            className='circle1',
                            children=[
                                html.Div(
                                    className='hilite',
                                    children=[html.H1(className='high6', children=[total_travel_time])]
                                )   
                            ]
                        )
                    ]
                ),
                html.Div(
                    className='graph22',
                    children=[
                        dcc.Graph(
                            # figure=status_pie
                        )
                    ]
                )
            ]
        ),

        # Row 1: Engagements and Hours
        html.Div(
            className='row1',
            children=[
                html.Div(
                    className='graph1',
                    children=[
                        dcc.Graph(
                            figure=status_bar
                        )
                    ]
                ),
                html.Div(
                    className='graph2',
                    children=[
                        dcc.Graph(
                            figure=status_pie
                        )
                    ]
                )
            ]
        ),
        
        html.Div(
            className='row3',
            children=[
                html.Div(
                    className='graph33',
                    children=[
                        dcc.Graph(
                            figure=admin_bar
                        )
                    ]
                ),
            ]
        ),   
        
        html.Div(
            className='row3',
            children=[
                html.Div(
                    className='graph33',
                    children=[
                        dcc.Graph(
                            figure=admin_pie
                        )
                    ]
                ),
            ]
        ),   

        html.Div(
            className='row3',
            children=[
                html.Div(
                    className='graph33',
                    children=[
                        dcc.Graph(
                            figure=care_bar
                        )
                    ]
                ),
            ]
        ),   

        html.Div(
            className='row3',
            children=[
                html.Div(
                    className='graph33',
                    children=[
                        dcc.Graph(
                            figure=care_pie
                        )
                    ]
                ),
            ]
        ),   

        html.Div(
            className='row3',
            children=[
                html.Div(
                    className='graph33',
                    children=[
                        dcc.Graph(
                            figure=community_bar
                        )
                    ]
                ),
            ]
        ),   

        html.Div(
            className='row3',
            children=[
                html.Div(
                    className='graph33',
                    children=[
                        dcc.Graph(
                            figure=community_pie
                        )
                    ]
                ),
            ]
        ),   

        # html.Div(
        #     className='row3',
        #     children=[
        #         html.Div(
        #             className='graph1',
        #             children=[
        #                 dcc.Graph(
        #                     figure=community_bar
        #                 )
        #             ]
        #         ),
        #         html.Div(
        #             className='graph2',
        #             children=[
        #                 dcc.Graph(
        #                     figure=community_pie
        #                 )
        #             ]
        #         )
        #     ]
        # ),   

        html.Div(
            className='row3',
            children=[
                html.Div(
                    className='graph1',
                    children=[
                        dcc.Graph(
                            figure=person_bar
                        )
                    ]
                ),
                html.Div(
                    className='graph2',
                    children=[
                        dcc.Graph(
                            figure=person_pie
                        )
                    ]
                )
            ]
        ),   
        
# ROW 2
# html.Div(
#     className='row2',
#     children=[
#         html.Div(
#             className='graph3',
#             children=[
#                 html.Div(
#                     className='table',
#                     children=[
#                         html.H1(
#                             className='table-title',
#                             children='Entity Name Table'
#                         )
#                     ]
#                 ),
#                 html.Div(
#                     className='table2', 
#                     children=[
#                         dcc.Graph(
#                             className='data',
#                             # figure=entity_name_table
#                         )
#                     ]
#                 )
#             ]
#         ),
#         html.Div(
#             className='graph4',
#             children=[                
#               html.Div(
#                     className='table',
#                     children=[
#                         html.H1(
#                             className='table-title',
#                             children=''
#                         )
#                     ]
#                 ),
#                 html.Div(
#                     className='table2', 
#                     children=[
#                         dcc.Graph(
                            
#                         )
#                     ]
#                 )
   
#             ]
#         )
#     ]
# ),

        html.Div(
            className='row3',
            children=[
                html.Div(
                    className='graph33',
                    children=[
                        dcc.Graph(
                            figure=entity_name_table
                        )
                    ]
                ),
            ]
        ),   
])

print(f"Serving Flask app '{current_file}'! 🚀")

if __name__ == '__main__':
    app.run_server(debug=
                    True)
                    # False)
# =================================== Updated Database ================================= #

# updated_path1 = 'data/service_tracker_q4_2024_cleaned.csv'
# data_path1 = os.path.join(script_dir, updated_path1)
# df.to_csv(data_path1, index=False)
# print(f"DataFrame saved to {data_path1}")

# updated_path = f'data/Engagement_{current_month}_{report_year}.xlsx'
# # updated_path = f'data/engagement_larry_wallace_jr.xlsx'
# data_path = os.path.join(script_dir, updated_path)

# with pd.ExcelWriter(data_path, engine='xlsxwriter') as writer:
#     df.to_excel(
#             writer, 
#             sheet_name=f'Engagement {current_month} {report_year}', 
#             startrow=1, 
#             index=False
#         )

#     # Access the workbook and each worksheet
#     workbook = writer.book
#     sheet1 = writer.sheets['Engagement April 2025']
    
#     # Define the header format
#     header_format = workbook.add_format({
#         'bold': True, 
#         'font_size': 13, 
#         'align': 'center', 
#         'valign': 'vcenter',
#         'border': 1, 
#         'font_color': 'black', 
#         'bg_color': '#B7B7B7',
#     })
    
#     # Set column A (Name) to be left-aligned, and B-E to be right-aligned
#     left_align_format = workbook.add_format({
#         'align': 'left',  # Left-align for column A
#         'valign': 'vcenter',  # Vertically center
#         'border': 0  # No border for individual cells
#     })

#     right_align_format = workbook.add_format({
#         'align': 'right',  # Right-align for columns B-E
#         'valign': 'vcenter',  # Vertically center
#         'border': 0  # No border for individual cells
#     })
    
#     # Create border around the entire table
#     border_format = workbook.add_format({
#         'border': 1,  # Add border to all sides
#         'border_color': 'black',  # Set border color to black
#         'align': 'center',  # Center-align text
#         'valign': 'vcenter',  # Vertically center text
#         'font_size': 12,  # Set font size
#         'font_color': 'black',  # Set font color to black
#         'bg_color': '#FFFFFF'  # Set background color to white
#     })

#     # Merge and format the first row (A1:E1) for each sheet
#     sheet1.merge_range('A1:N1', f'Engagement Report {current_month} {report_year}', header_format)

#     # Set column alignment and width
#     # sheet1.set_column('A:A', 20, left_align_format)   

#     print(f"Engagement Excel file saved to {data_path}")

# -------------------------------------------- KILL PORT ---------------------------------------------------

# netstat -ano | findstr :8050
# taskkill /PID 24772 /F
# npx kill-port 8050

# ---------------------------------------------- Host Application -------------------------------------------

# 1. pip freeze > requirements.txt
# 2. add this to procfile: 'web: gunicorn impact_11_2024:server'
# 3. heroku login
# 4. heroku create
# 5. git push heroku main

# Create venv 
# virtualenv venv 
# source venv/bin/activate # uses the virtualenv

# Update PIP Setup Tools:
# pip install --upgrade pip setuptools

# Install all dependencies in the requirements file:
# pip install -r requirements.txt

# Check dependency tree:
# pipdeptree
# pip show package-name

# Remove
# pypiwin32
# pywin32
# jupytercore

# ----------------------------------------------------

# Name must start with a letter, end with a letter or digit and can only contain lowercase letters, digits, and dashes.

# Heroku Setup:
# heroku login
# heroku create mc-impact-11-2024
# heroku git:remote -a mc-impact-11-2024
# git push heroku main

# Clear Heroku Cache:
# heroku plugins:install heroku-repo
# heroku repo:purge_cache -a mc-impact-11-2024

# Set buildpack for heroku
# heroku buildpacks:set heroku/python

# Heatmap Colorscale colors -----------------------------------------------------------------------------

#   ['aggrnyl', 'agsunset', 'algae', 'amp', 'armyrose', 'balance',
            #  'blackbody', 'bluered', 'blues', 'blugrn', 'bluyl', 'brbg',
            #  'brwnyl', 'bugn', 'bupu', 'burg', 'burgyl', 'cividis', 'curl',
            #  'darkmint', 'deep', 'delta', 'dense', 'earth', 'edge', 'electric',
            #  'emrld', 'fall', 'geyser', 'gnbu', 'gray', 'greens', 'greys',
            #  'haline', 'hot', 'hsv', 'ice', 'icefire', 'inferno', 'jet',
            #  'magenta', 'magma', 'matter', 'mint', 'mrybm', 'mygbm', 'oranges',
            #  'orrd', 'oryel', 'oxy', 'peach', 'phase', 'picnic', 'pinkyl',
            #  'piyg', 'plasma', 'plotly3', 'portland', 'prgn', 'pubu', 'pubugn',
            #  'puor', 'purd', 'purp', 'purples', 'purpor', 'rainbow', 'rdbu',
            #  'rdgy', 'rdpu', 'rdylbu', 'rdylgn', 'redor', 'reds', 'solar',
            #  'spectral', 'speed', 'sunset', 'sunsetdark', 'teal', 'tealgrn',
            #  'tealrose', 'tempo', 'temps', 'thermal', 'tropic', 'turbid',
            #  'turbo', 'twilight', 'viridis', 'ylgn', 'ylgnbu', 'ylorbr',
            #  'ylorrd'].

# rm -rf ~$bmhc_data_2024_cleaned.xlsx
# rm -rf ~$bmhc_data_2024.xlsx
# rm -rf ~$bmhc_q4_2024_cleaned2.xlsx