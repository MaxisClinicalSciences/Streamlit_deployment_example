from matplotlib import pyplot as plt
import streamlit as st
import requests
import pandas as pd
from langchain import HuggingFaceHub
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import re


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


# Function to update the UI based on selected filter
def update_ui_based_on_filter(df):
    # Filtering the data based on radio button selection
    study_filter = st.radio(
        "Select Studies", ["All", "Pharmacodynamics (PD)", "Pharmacokinetics (PK)"]
    )

    # Filtered data
    if study_filter == "Pharmacodynamics (PD)":
        filtered_df = df[df["Study Type"] == "PD"]
        st.write("### Pharmacodynamics (PD) Studies Data")
        st.dataframe(filtered_df, use_container_width=True)
    elif study_filter == "Pharmacokinetics (PK)":
        filtered_df = df[df["Study Type"] == "PK"]
        st.write("### Pharmacokinetics (PK) Studies Data")
        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.write("### All Studies Data")
        st.dataframe(df, use_container_width=True)


# Function to handle the query input and display results
def handle_query_input():
    query = st.text_area("Ask query to fetched or filtered data")

    if query:
        prompt = (
            """
            1. Use the dataset at 'https://github.com/MaxisClinicalSciences/MCS_AIML_POC/blob/main/clinical_trials_data_complete_new3.csv' to generate the visualization based on the provided query.
            2. Provide a concise answer.
            3. Format your answers in a table when applicable.
            Query: {query}
            """
            + query
        )

        first_input_prompt = PromptTemplate(
            input_variables=[prompt],
            template="Reply this question {first_input_prompt}",
        )

        # Hugging Face model
        llm = HuggingFaceHub(
            huggingfacehub_api_token="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",
            repo_id="mistralai/Mixtral-8x7B-Instruct-v0.1",
            model_kwargs={"temperature": 0.1, "max_new_tokens": 500},
        )

        chain = LLMChain(llm=llm, prompt=first_input_prompt, verbose=True)

        # Button to Submit your query
        if st.button("Submit Query", type="primary"):
            with st.spinner("Generating response..."):
                # Run the chain with the prompt
                response = chain.run(prompt)

                # Process the response
                response = response.replace("<code>", "code", 1)
                response = response.replace("</code>", "code/", 1)

                # Process and display response
                if "<code>" in response and "</code>" in response:
                    start_idx = response.find("<code>") + len("<code>")
                    end_idx = response.find("</code>")
                    code_snippet = response[start_idx:end_idx].strip()

                    # Attempt to execute the code snippet safely
                    try:
                        with st.spinner("Executing code..."):
                            local_vars = {}  # Dictionary to safely execute the code
                            code_snippet = code_snippet.replace("", " ", 1)

                            if "fig" in local_vars:
                                st.pyplot(local_vars["fig"])
                                plot_area = st.empty()
                                plot_area.pyplot(
                                    exec(
                                        code_snippet,
                                        {"st": st, "pd": pd, "plt": plt},
                                        local_vars,
                                    )
                                )
                            else:
                                plot_area = st.empty()
                                plot_area.pyplot(exec(code_snippet))
                                st.write("Code executed but no plot was created.")
                    except Exception as e:
                        st.error(f"Error executing the code: {e}")
                else:
                    # Display response without code snippets
                    st.write(response)


# Streamlit App Layout
st.title("Clinical Trials Data Fetcher")
st.write(
    "Fetch data from clinicalTrials.gov and analyse the data by entering your queries"
)

st.sidebar.image("MaxisLogo.png", use_column_width=True)

# User Inputs
if "data_fetched" not in st.session_state:
    st.session_state.data_fetched = False

# Button to start fetching data
if st.button("Fetch Data"):
    with st.spinner("Fetching data..."):
        base_url = "https://clinicaltrials.gov/api/v2/studies"
        params = {"query.titles": "Diabetes", "pageSize": 100}
        data_list = fetch_data(base_url, params)

        if not data_list:
            st.error("No data fetched. Please check your query or try again later.")
        else:
            # Store data in session state
            df = pd.DataFrame(data_list)

            # Update Study Type based on Phases
            def update_study_type(row):
                if row["Study Type"] == "INTERVENTIONAL":
                    if "PHASE1" in row["Phases"]:
                        return "PK"
                    elif (
                        "PHASE2" in row["Phases"]
                        or "PHASE3" in row["Phases"]
                        or "PHASE4" in row["Phases"]
                    ):
                        return "PD"
                elif row["Study Type"] == "OBSERVATIONAL":
                    if "PHASE1" in row["Phases"]:
                        return "PK"
                return row["Study Type"]

            df["Study Type"] = df.apply(update_study_type, axis=1)

            st.session_state.data_fetched = True
            st.session_state.df = df
            st.success("Data fetched successfully!")
            # Use `st.dataframe` to display the DataFrame and allow scrolling
            st.write("### Full Data")
            st.dataframe(df, use_container_width=True)

            # Optionally, save the DataFrame to a CSV file
            df.to_csv("clinical_trials_data_complete_new3.csv", index=False)

            # Count PK and PD studies
            pk_count = df["Study Type"].value_counts().get("PK", 0)
            pd_count = df["Study Type"].value_counts().get("PD", 0)

            # Display the counts
            st.write(f"### Pharmacokinetics Studies Count: {pk_count}")
            st.write(f"### Pharmacodynamics Studies Count: {pd_count}")

# Conditional display based on whether data is fetched
if st.session_state.data_fetched:
    update_ui_based_on_filter(st.session_state.df)
    handle_query_input()
