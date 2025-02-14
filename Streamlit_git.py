import streamlit as st
import pandas as pd
from openai import OpenAI
import json

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["api_key"])

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "show_chat" not in st.session_state:
    st.session_state.show_chat = False
if "chat_input" not in st.session_state:
    st.session_state.chat_input = ""

# Load the dropdown dataset
def load_dropdown_data():
    dropdown_file_path = r"Dropdown.csv"
    try:
        df = pd.read_csv(dropdown_file_path, encoding='latin1')
        df.columns = df.columns.str.strip()
        df.columns = df.columns.str.replace("ï»¿", "")
        return df
    except Exception as e:
        st.error(f"Error loading dropdown file: {e}")
        return pd.DataFrame(columns=["Country", "Company"])

# Load the large dataset
def load_large_data():
    large_file_path = r"Final_OP.csv"
    try:
        df = pd.read_csv(large_file_path, encoding='latin1')
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Error loading large dataset: {e}")
        return pd.DataFrame(columns=["DB_Name", "Region", "Country", "Company", "Technology", "Metric", "Definition"])

# ChatGPT API call function
def chat_with_gpt(user_input):
    context_df = st.session_state.get("final_df", pd.DataFrame())
    
    if context_df.empty:
        context_data = "No data selected. Please select countries and providers."
    else:
        context_data = context_df.to_json(orient='records')
    
    messages = [
        {"role": "system", "content": """
This GPT is designed to assist users with queries related to Technology, Media, and Telecommunications (TMT) research by leveraging data strictly from your uploaded CSV file. Before answering any questions, please ensure you have taken enough time to analyze and that the answer is 100 percent accurate.

The uploaded CSV will always have the same structure, the number of rows may vary. The columns are as follows:
DB_Name, Region, Country, Company, Technology, Metric, Definition, and Yearly columns from 1981 to 2030; consider 'Y' as data available and 'N' as data not available

Instructions:
- Provide answers in textual summaries with bullet points.
- Maintain a professional and informative tone, suitable for industry analysts, business strategists, and decision-makers.
- If a query cannot be answered based on the uploaded files, state that the requested information is not available rather than speculate.
- Consider values in columns post 2024 as forecasted figures
- End responses with: "Do you want to draft an E-Mail to RDS for the data request?"
- If prompted Yes, draft a formal email to the RDS team requesting the necessary data basis the queries that have been asked by the user. This should be accurate for the questions and account for all the queries and reflect in the mail. Also, provide the source through which the data is available and ensure that the mail is clearly structured for the RDS team to understand the request.
        """},
        {"role": "user", "content": f"Dataset:\n{context_data}\n\nUser query: {user_input}"}
    ]
    
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )
    
    return completion.choices[0].message.content

def main():
    st.set_page_config(page_title="TMT Data Wizard", layout="wide")
    
    # Display a sample logo with a smaller size
    st.image(r"download.png", caption="", width=100)
    
    st.title("TMT Data Wizard")
    
    dropdown_df = load_dropdown_data()
    large_df = load_large_data()
    
    if dropdown_df.empty or large_df.empty:
        st.warning("Data files are empty or failed to load.")
        return
    
    country_company_map = dropdown_df.groupby("Country")["Company"].apply(list).to_dict()
    
    selected_countries = st.multiselect("Select Countries", list(country_company_map.keys()))
    
    selected_companies = []
    if selected_countries:
        available_companies = sorted(set(company for country in selected_countries for company in country_company_map.get(country, [])))
        selected_companies = st.multiselect("Select Providers", available_companies)
    
    if selected_countries and selected_companies:
        if st.button("Proceed"):
            st.session_state.final_df = large_df[(large_df["Country"].isin(selected_countries)) & (large_df["Company"].isin(selected_companies))]
            st.session_state.chat_history = []
            st.session_state.show_chat = True
            st.session_state.chat_input = ""  # Reset chat input on new selection
    
    if st.session_state.get("show_chat", False):
        st.subheader("Chat with AI")
        chat_container = st.container(height=500)
        for sender, message in st.session_state.get("chat_history", []):
            with chat_container:
                st.markdown(f"<div style='border-radius:10px; padding:10px; margin:5px; background-color:{'#dcf8c6' if sender == 'User' else '#f1f0f0'}'><strong>{sender}:</strong> {message}</div>", unsafe_allow_html=True)
        
        user_input = st.chat_input("Ask about the data:")
        
        col1, col2, col3 = st.columns(3)
        if col1.button("Which unique key metrics are available by data sources?"):
            user_input = "Which unique key metrics are available by data sources?"
        if col2.button("Do we have forecasted figures post 2024?"):
            user_input = "Do we have forecasted figures post 2024?"
        if col3.button("Is the ARPU data available for 2023?"):
            user_input = "Is the ARPU data available for 2023?"
        
        if user_input:
            response = chat_with_gpt(user_input)
            st.session_state.chat_history.append(("User", user_input))
            st.session_state.chat_history.append(("AI", response))
            st.rerun()

if __name__ == "__main__":
    main()
