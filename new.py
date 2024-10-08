import streamlit as st
import requests
import pandas as pd


# Function to fetch data from ClinicalTrials.gov API
def fetch_data(base_url, params):
    data_list = []
    while True:
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            data = response.json()
            studies = data.get("studies", [])
            for study in studies:
                nctId = study["protocolSection"]["identificationModule"].get(
                    "nctId", "Unknown"
                )
                overallStatus = study["protocolSection"]["statusModule"].get(
                    "overallStatus", "Unknown"
                )
                startDate = (
                    study["protocolSection"]["statusModule"]
                    .get("startDateStruct", {})
                    .get("date", "Unknown Date")
                )
                conditions = ", ".join(
                    study["protocolSection"]["conditionsModule"].get(
                        "conditions", ["No conditions listed"]
                    )
                )
                acronym = study["protocolSection"]["identificationModule"].get(
                    "acronym", "Unknown"
                )

                interventions_list = (
                    study["protocolSection"]
                    .get("armsInterventionsModule", {})
                    .get("interventions", [])
                )
                interventions = (
                    ", ".join(
                        [
                            intervention.get("name", "No intervention name listed")
                            for intervention in interventions_list
                        ]
                    )
                    if interventions_list
                    else "No interventions listed"
                )

                locations_list = (
                    study["protocolSection"]
                    .get("contactsLocationsModule", {})
                    .get("locations", [])
                )
                locations = (
                    ", ".join(
                        [
                            f"{location.get('city', 'No City')} - {location.get('country', 'No Country')}"
                            for location in locations_list
                        ]
                    )
                    if locations_list
                    else "No locations listed"
                )

                primaryCompletionDate = (
                    study["protocolSection"]["statusModule"]
                    .get("primaryCompletionDateStruct", {})
                    .get("date", "Unknown Date")
                )
                studyFirstPostDate = (
                    study["protocolSection"]["statusModule"]
                    .get("studyFirstPostDateStruct", {})
                    .get("date", "Unknown Date")
                )
                lastUpdatePostDate = (
                    study["protocolSection"]["statusModule"]
                    .get("lastUpdatePostDateStruct", {})
                    .get("date", "Unknown Date")
                )
                studyType = study["protocolSection"]["designModule"].get(
                    "studyType", "Unknown"
                )
                phases = ", ".join(
                    study["protocolSection"]["designModule"].get(
                        "phases", ["Not Available"]
                    )
                )

                data_list.append(
                    {
                        "NCT ID": nctId,
                        "Acronym": acronym,
                        "Overall Status": overallStatus,
                        "Start Date": startDate,
                        "Conditions": conditions,
                        "Interventions": interventions,
                        "Locations": locations,
                        "Primary Completion Date": primaryCompletionDate,
                        "Study First Post Date": studyFirstPostDate,
                        "Last Update Post Date": lastUpdatePostDate,
                        "Study Type": studyType,
                        "Phases": phases,
                    }
                )

            nextPageToken = data.get("nextPageToken")
            if nextPageToken:
                params["pageToken"] = nextPageToken
            else:
                break
        else:
            st.error(f"Failed to fetch data. Status code: {response.status_code}")
            break

    return data_list


# Streamlit App Layout
st.title("Clinical Trials Data Fetcher")

# User Inputs
search_query = st.text_input("Enter the study title query:", "Diabetes")
page_size = st.number_input(
    "Enter the number of results per page:",
    min_value=10,
    max_value=1000,
    value=100,
    step=10,
)

# Initial URL for the first API call
base_url = "https://clinicaltrials.gov/api/v2/studies"
params = {"query.titles": search_query, "pageSize": page_size}

# Button to start fetching data
if st.button("Fetch Data"):
    with st.spinner("Fetching data..."):
        data_list = fetch_data(base_url, params)

        # Create a DataFrame from the list of dictionaries
        df = pd.DataFrame(data_list)

        # Update Study Type based on Phases
        def update_study_type(row):
            if row["Study Type"] == "INTERCONVETIONAL":
                if (
                    "PHASE2" in row["Phases"]
                    or "PHASE3" in row["Phases"]
                    or "PHASE4" in row["Phases"]
                ):
                    return "PD"
            elif row["Study Type"] == "OBSERVATIONAL":
                if "PHASE1" in row["Phases"]:
                    return "PK"
            return row["Study Type"]

        # Apply the function to update the Study Type
        df["Study Type"] = df.apply(update_study_type, axis=1)

        # Display the DataFrame in Streamlit
        if not df.empty:
            st.success("Data fetched successfully!")
            st.write(df)
            # Optionally, save the DataFrame to a CSV file
            df.to_csv("clinical_trials_data_complete_new1.csv", index=False)
            st.info("Data saved to clinical_trials_data_complete_new1.csv")
        else:
            st.warning("No data found.")
