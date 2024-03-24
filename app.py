"""
===Streamlit App for SQL Querying with DuckDB Database===
This app allows users to write and execute SQL queries on a DuckDB database.
The app provides example queries, a SQL editor, and buttons to run and reset the database.
This is a code repository for a streamlit based sql playground to practice basic sql skills. 
Part of the workshop conducted by Ahmed Muzammil.
"""

import os
import streamlit as st
import duckdb
import pandas as pd
from streamlit_ace import st_ace

# Set page config to wide layout
st.set_page_config(layout="wide")

# Initialize connection to DuckDB
@st.cache_resource()
def get_connection():
    """
    Establishes a connection to the 'sample.db' database.

    Returns:
        Connection: A connection object to the database.
    """
    conn = duckdb.connect(database='sample.db', read_only=False)
    return conn

# Function to execute SQL query
def run_query(sql_query):
    """
    Executes the given SQL query and returns the result as a DataFrame.

    Args:
        sql_query (str): The SQL query to be executed.

    Returns:
        pandas.DataFrame: The result of the SQL query as a DataFrame.

    """
    try:
        df_result = get_connection().execute(sql_query).fetchdf()
        return df_result
    except duckdb.Error as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

def reset_database():
    """
    Resets the database by deleting all records from a table 
    and re-importing the data from a backup table.
    """
    try:
        get_connection().close()
    except Exception:
        pass

    if os.path.exists("sample.db"):
        os.remove("sample.db")

    get_connection.clear()
    conn = get_connection()
    conn.execute("IMPORT DATABASE 'backup_data';")


    # with open("contoso_db.sql", "r", encoding="utf-8") as f:
    #     sql_script = f.read()
    #     conn.execute(sql_script)
    st.success("Database reset to original state!")


st.markdown("# SQL Querying Workshop")


# Example queries dropdown
example_queries = {
    "Select Customers": "SELECT * FROM customers;",
    "Select Orders": "SELECT * FROM orders;",
    "Select Products": "SELECT * FROM products;",
    "Count Orders": "SELECT COUNT(1) FROM orders;",
    "Filter Customers": "SELECT * FROM customers WHERE company = 'AdventureWorks';",
    "Select OrderDetails":    """select  CustomerName, Address, DatePlaced, DateFilled,
InvoiceNumber, Colour, StandardCost, ListPrice, ListPrice-StandardCost as Profit
from lineitems 
left join orders on (lineitems.orderid = orders.orderid)
left join products on (lineitems.productid = products.productid)
where lineitems.orderid = 9""",
    "Select Order Counts": """SELECT orders.customername, orders.address,
count(lineitems.lineitemid) total_line_items,
sum(lineitems.quantity) total_item_count
from orders 
left join lineitems on orders.orderid = lineitems.orderid
group by orders.orderid, orders.customername, orders.address""",
    "List Profitable Customers": """select customername, sum(profit) profit from (
select  CustomerName, Address, DatePlaced, DateFilled, InvoiceNumber, Colour, StandardCost, ListPrice, ListPrice-StandardCost as Profit from lineitems 
left join orders on (lineitems.orderid = orders.orderid)
left join products on (lineitems.productid = products.productid)
)x group by customername order by sum(profit) desc"""
}
query = st.selectbox("Example Queries", options=list(example_queries.keys()))

# SQL Query Editor


user_query = st_ace(language='sql',
                    placeholder="Write your SQL query here...",
                    value=example_queries[query],
                    height=150)

with st.spinner("Running Query..."):
    result = run_query(user_query)
    st.markdown("#### Query Results")
    st.info(f"**{result.shape[0]} {'row' if result.shape[0]==1 else 'rows'}** returned.")

    st.dataframe(result)


tables = run_query("SELECT table_name FROM information_schema.tables order by table_name;")
col0, col1, col2 = st.columns([2, 1, 2])
# Display the tables and their columns in the database with st.expander

if tables.shape[0] == 0:
    st.warning("No tables found in the database!")
    with st.spinner("Resetting database..."):
        reset_database()
    st.rerun()

with col0:
    # Display instructions or documentation to the user
    st.markdown("""
    ## Instructions
    - Use the SQL editor above to write and execute your SQL queries.
    - Select from the dropdown for example queries.
    - Click **Run Query** to execute your SQL and see the results.
    - If you make a mistake or want to start over, click **Reset Database**.
    """)


col1.markdown("## Tables")
with col1:
    SQL_QUERY = ""
    for index, row in tables.iterrows():
        SQL_QUERY += f"""select '{row['table_name']}' as 'Table Name',
                         count(1) as 'Row Count' from {row['table_name']}
                         UNION ALL """
    SQL_QUERY = SQL_QUERY[:-11] #to remove the last UNION ALL
    table_counts = run_query(SQL_QUERY)
    st.dataframe(table_counts, hide_index=True)

col2.markdown("## Columns")
with col2:
    for index, row in tables.iterrows():
        with st.expander(f"{row['table_name']}", expanded=False):
            columns = run_query(f"""SELECT ordinal_position as 'Ordinal Position',
                                column_name as 'Column Name',
                                data_type as 'Data Type'
                                FROM information_schema.columns
                                WHERE table_name = '{row['table_name']}';""")
            st.dataframe(columns, hide_index=True)

if st.checkbox("Admin Panel"):
    if st.button("Reset Database"):
        reset_database()
