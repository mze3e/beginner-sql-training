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
import plotly.express as px

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
    except duckdb.Error:
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


def dynamic_visualization(df):
    """
    Dynamically visualize a pandas dataframe using Streamlit.

    Parameters:
    - df: pandas.DataFrame - The dataframe to visualize.
    """
    # Ensure the dataframe has the required columns for visualization
    if df is None or df.empty:
        st.write("No data available for visualization.")
        return

    # User selects the type of visualization
    chart_type = st.selectbox(
        "Select the chart type:",
        ("Line Chart", "Bar Chart", "Scatter Plot", "Area Chart")
    )

    # User selects columns for visualization (x and y axis for
    # scatter plot, line chart, and area chart.
    if chart_type in ['Scatter Plot', 'Line Chart', 'Area Chart']:
        x_axis = st.selectbox("Select the X-axis:", options=df.columns)
        y_axis = st.selectbox("Select the Y-axis:", options=df.columns)
    elif chart_type == 'Bar Chart':
        x_axis = st.selectbox("Select the X-axis:", options=df.columns)
        y_axis = st.selectbox("Select the Y-axis:", options=df.columns)

    try:
        # Generate the selected type of visualization
        if chart_type == "Line Chart":
            st.line_chart(df.set_index(x_axis)[y_axis])
        elif chart_type == "Bar Chart":
            st.bar_chart(df.set_index(x_axis)[y_axis])
        elif chart_type == "Scatter Plot":
            st.plotly_chart(px.scatter(df, x=x_axis, y=y_axis))
        elif chart_type == "Area Chart":
            st.area_chart(df.set_index(x_axis)[y_axis])
    except (TypeError, ValueError, KeyError) as e:
        st.error(f"""Try Choose Different Columns for the visualisation.\n\n
                 Error: {e}""")



###################### App Starts Here ######################

st.markdown("# SQL Querying Workshop")

# Example queries dropdown
example_queries = {
    "Select Customers": "SELECT * FROM customers;",
    "Count Orders": "SELECT COUNT(1) FROM orders;",
    "Filter Customers": "SELECT * FROM customers WHERE company = 'AdventureWorks';",
    "Filter Customers (like)":
    "SELECT * FROM customers WHERE company = 'AdventureWorks' and address like '%Paris%'",
    "Insert Customer": 
"""INSERT INTO Customers (FirstName, LastName, Address, Company, Email, Phone)
VALUES ('Ahmed', 'Muzammil', 'Bukit Batok East Avenue 5, Singapore', 
'Bank of Singapore', 'ahmedmuzammil.jamalmohamed@bankofsingapore.com', '94780611')""",
    "Delete Customer": "DELETE FROM customers WHERE customerid = 501;",
    "Order Details (join)":    """select  CustomerName, Address, DatePlaced, DateFilled,
InvoiceNumber, Colour, StandardCost, ListPrice, ListPrice-StandardCost as Profit
from lineitems 
left join orders on (lineitems.orderid = orders.orderid)
left join products on (lineitems.productid = products.productid)
where lineitems.orderid = 9""",
    "Customer Wise Order Counts (join + aggregation)":
"""SELECT orders.customername, orders.address,
count(lineitems.lineitemid) total_line_items,
sum(lineitems.quantity) total_item_count
from orders 
left join lineitems on orders.orderid = lineitems.orderid
group by orders.orderid, orders.customername, orders.address""",
    "Top 10 Profitable Customers (subquery + join + aggregation + ordering + limit)":
"""select customername, sum(profit) profit from (
select  CustomerName, Address, DatePlaced, DateFilled, InvoiceNumber, 
Colour, StandardCost, ListPrice, ListPrice-StandardCost as Profit 
from lineitems 
left join orders on (lineitems.orderid = orders.orderid)
left join products on (lineitems.productid = products.productid)
)x group by customername order by sum(profit) desc limit 10""",
    "Customers Who Ordered For More than $40000 in 2017": 
"""SELECT Customers.FirstName, Customers.LastName, Orders.OrderId,
Orders.DatePlaced, SUM(Products.ListPrice * LineItems.Quantity) AS TotalPrice
FROM Customers
JOIN Orders ON Customers.CustomerId = Orders.CustomerId
JOIN LineItems ON Orders.OrderId = LineItems.OrderId
JOIN Products ON LineItems.ProductId = Products.ProductId
WHERE YEAR(Orders.DatePlaced) = 2017
GROUP BY Orders.OrderId, Customers.FirstName, Customers.LastName, Orders.DatePlaced
HAVING SUM(Products.ListPrice * LineItems.Quantity) > 40000
ORDER BY TotalPrice DESC;"""
}
query = st.selectbox("Example Queries", options=list(example_queries.keys()))

# SQL Query Editor


user_query = st_ace(language='sql',
                    placeholder="Write your SQL query here...",
                    value=example_queries[query],
                    height=200)

with st.spinner("Running Query..."):
    result = run_query(user_query)
    st.markdown("#### Query Results")
    st.info(f"**{result.shape[0]} {'row' if result.shape[0]==1 else 'rows'}** returned.")

    st.dataframe(result)

    if st.checkbox("Visualize Data"):
        dynamic_visualization(result)


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

st.markdown('---')
st.markdown('## Entity Relationship Diagram')
st.markdown('---')
# Create a graphlib graph object
st.graphviz_chart(r'''
    digraph ERDiagram {
                                    
        node [shape=record, style=filled, fillcolor=gray95, margin=0.1, height=0, width=0];
        edge [color=black, arrowhead=crow, arrowtail=none, dir=both]

        Customers [label="{**Customers**|+ CustomerId: INTEGER\l| Address: VARCHAR\l| Company: VARCHAR\l| Email: VARCHAR\l| FirstName: VARCHAR\l| LastName: VARCHAR\l| Phone: VARCHAR\l}"];
        Orders [label="{**Orders**|+ OrderId: INTEGER\l| Address: VARCHAR\l| - CustomerId: INTEGER\l| CustomerName: VARCHAR\l| DateFilled: DATE\l| DatePlaced: DATE\l| InvoiceNumber: VARCHAR\l| PaymentStatus: VARCHAR\l| Status: VARCHAR\l| Term: VARCHAR\l}"];
        LineItems [label="{**LineItems**|+ LineItemId: INTEGER\l| - OrderId: INTEGER\l| - ProductId: INTEGER\l| Quantity: INTEGER\l}"];
        Products [label="{**Products**|+ ProductId: INTEGER\l| Colour: VARCHAR\l| DaysToManufacture: INTEGER\l| Description: VARCHAR\l| ListPrice: DECIMAL(10,2)\l| Name: VARCHAR\l| StandardCost: DECIMAL(10,2)\l| Weight: DECIMAL(10,2)\l}"];

        Orders -> Customers [label="CustomerId", taillabel="1", headlabel="*"];
        LineItems -> Orders [label="OrderId", taillabel="1", headlabel="*"];
        LineItems -> Products [label="ProductId", taillabel="1", headlabel="*"];
    }
''')


st.markdown('---')
st.markdown('## CHEATSHEET: SQL Querying Basics')
st.markdown('---')

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown('### Basic SQL: CRUD Operations')
    st.markdown('[View Detailed Syntax and Examples](#basic-crud-operations)')
    st.markdown("Create, Read, Update, and Delete data in the database.")
    st.markdown("""- Create: **INSERT**
- Read: **SELECT**
- Update: **UPDATE**
- Delete: **DELETE**
""")
    st.markdown('### Filtering Data: **WHERE** Clause')
    st.markdown('[View Detailed Syntax and Examples](#filtering-using-the-where-clause)')
    st.markdown("""- Logical Operators: **AND, OR, NOT**
- Comparison Operators: **=, <>, >, <, BETWEEN**
- List of Values: **IN**
- Wildcard Operator: **LIKE**
- NULL Values: **IS NULL**
""")

with col2:
    st.markdown('### Aggregation')
    st.markdown('[View Detailed Syntax and Examples](#aggregating-data-using-functions)')
    st.markdown("Aggregate data using functions like:")
    st.markdown("""- Count Records: **COUNT(*)**
- Sum of a particular column: **SUM(COLUMN)**
- Column Value: **AVG / MIN / MAX(COLUMN)**
- Slice/Dice by Column: **(GROUP BY) (HAVING)**
""")
    st.markdown('### De-duplication')
    st.markdown('[View Detailed Syntax and Examples](#remove-duplicates-and-find-unique-values)')
    st.markdown("Find the unique list of values:")
    st.markdown("""- **DISTINCT**
- **GROUP BY** + **COUNT** + **HAVING** to find duplicates and their count""")

with col3:
    st.markdown('### Joining Tables')
    st.markdown('[View Detailed Syntax and Examples](#different-ways-to-join-tables)')
    st.markdown("Combine multiple tables:")
    st.markdown("""- **INNER JOIN:** Selects records that have matching values in both tables.
- **LEFT JOIN:** Selects all records from the left table, and the matched records from the right table. The result is NULL on the right side if there is no match.
- **RIGHT JOIN:** Selects all records from the right table, and the matched records from the left table. The result is NULL on the left side if there is no match.
""")

with col4:
    st.markdown('### Sorting/Ordering **ORDER BY**')
    st.markdown('[View Detailed Syntax and Examples](#sorting-and-ordering-data-using-order-by)')
    st.markdown("""Sorts the result set in ascending or descending order.
- **ASC:** Ascending order (default).
- **DESC:** Descending order.""")

    st.markdown('### Subqueries')
    st.markdown('[View Detailed Syntax and Examples](#using-subqueries-within-queries)')
    st.markdown("Use a query within another query. Returns a single value or a table.")

st.markdown('---')
st.markdown('## Detailed SQL Querying Cheatsheet')
st.markdown('---')

st.markdown("""
## Basic CRUD Operations

### Create: `INSERT`
- **Definition:** Adds new rows to a table.
- **Syntax:** `INSERT INTO table_name (column1, column2) VALUES (value1, value2);`
- **Example Query:** 
  ```sql
  INSERT INTO Customers (FirstName, LastName, Email) VALUES ('John', 'Doe', 'john.doe@email.com');
  ```
- **Expected Result Definition:** A new row is added to the `Customers` table with John Doe's details.

### Read: `SELECT`
- **Definition:** Retrieves data from one or more tables.
- **Syntax:** `SELECT column1, column2 FROM table_name WHERE condition;`
- **Example Query:** 
  ```sql
  SELECT FirstName, LastName FROM Customers WHERE CustomerId = 1;
  ```
- **Expected Result Definition:** Displays the first and last name of the customer with `CustomerId` 1.

### Update: `UPDATE`
- **Definition:** Modifies existing records in a table.
- **Syntax:** `UPDATE table_name SET column1 = value1, column2 = value2 WHERE condition;`
- **Example Query:** 
  ```sql
  UPDATE Customers SET Address = '123 New Location' WHERE CustomerId = 1;
  ```
- **Expected Result Definition:** Changes the address of the customer with `CustomerId` 1 to '123 New Location'.

### Delete: `DELETE`
- **Definition:** Removes existing records from a table.
- **Syntax:** `DELETE FROM table_name WHERE condition;`
- **Example Query:** 
  ```sql
  DELETE FROM Customers WHERE CustomerId = 1;
  ```
- **Expected Result Definition:** Deletes the record of the customer with `CustomerId` 1 from the `Customers` table.
Let's expand on the filtering data with `WHERE` clause section, providing more detailed examples for each operator, including logical and comparison operators.

---
            
## Filtering using the `WHERE` Clause

### Logical Operators: `AND`, `OR`, `NOT`

- **`AND` Operator Example:**
  - **Query:** Find all customers who are from "Tech Galaxy" company and live at "123 Space Street".
    ```sql
    SELECT * FROM Customers WHERE Company = 'Tech Galaxy' AND Address = '123 Space Street';
    ```
  - **Expected Result:** Retrieves customer records belonging to "Tech Galaxy" located at "123 Space Street".

- **`OR` Operator Example:**
  - **Query:** Select products that either have "Red" color or weigh more than 20 units.
    ```sql
    SELECT Name FROM Products WHERE Colour = 'Red' OR Weight > 20;
    ```
  - **Expected Result:** Lists names of "Red" products or those weighing over 20 units, possibly including some that meet both conditions.

- **`NOT` Operator Example:**
  - **Query:** Find customers who do not have an email address from "example.com".
    ```sql
    SELECT FirstName, LastName FROM Customers WHERE NOT Email LIKE '%@example.com';
    ```
  - **Expected Result:** Displays first and last names of customers whose email doesn't end with "@example.com".

### Comparison Operators: `=`, `<>`, `>`, `<`, `BETWEEN`

- **`=` Operator Example:**
  - **Query:** Retrieve the list of orders placed by Customer ID 10.
    ```sql
    SELECT OrderId FROM Orders WHERE CustomerId = 10;
    ```
  - **Expected Result:** Shows Order IDs for all orders placed by the customer with ID 10.

- **`<>` Operator Example:**
  - **Query:** Select products that are not colored "Blue".
    ```sql
    SELECT Name FROM Products WHERE Colour <> 'Blue';
    ```
  - **Expected Result:** Lists names of products that are of any color other than "Blue".

- **`>` Operator Example:**
  - **Query:** Find products with a list price greater than 500.
    ```sql
    SELECT Name, ListPrice FROM Products WHERE ListPrice > 500;
    ```
  - **Expected Result:** Retrieves the names and list prices of products priced above 500.

- **`<` Operator Example:**
  - **Query:** Identify customers who have placed less than 3 orders.
    - This example requires a subquery since it involves counting orders per customer.
    ```sql
    SELECT CustomerId, COUNT(OrderId) AS TotalOrders FROM Orders GROUP BY CustomerId HAVING COUNT(OrderId) < 3;
    ```
  - **Expected Result:** Lists Customer IDs along with their total orders, for those having fewer than 3 orders.

- **`BETWEEN` Operator Example:**
  - **Query:** Select all orders placed between January 1, 2023, and March 31, 2023.
    ```sql
    SELECT OrderId FROM Orders WHERE DatePlaced BETWEEN '2023-01-01' AND '2023-03-31';
    ```
  - **Expected Result:** Shows Order IDs for orders placed in the first quarter of 2023.

### List of Values: `IN`
- **Definition:** Specifies multiple values in a `WHERE` clause.
- **Syntax:** `SELECT column1 FROM table_name WHERE column1 IN (value1, value2);`
- **Example Query:** 
  ```sql
  SELECT FirstName, LastName FROM Customers WHERE CustomerId IN (1, 2, 3);
  ```
- **Expected Result Definition:** Selects the names of customers with `CustomerId` 1, 2, or 3.

### Wildcard Operator: `LIKE`
- **Definition:** Searches for a specified pattern in a column.
- **Syntax:** `SELECT column1 FROM table_name WHERE column1 LIKE pattern;`
- **Example Query:** 
  ```sql
  SELECT FirstName FROM Customers WHERE FirstName LIKE 'Jo%';
  ```
- **Expected Result Definition:** Lists first names that start with "Jo".

### NULL Values: `IS NULL`
- **Definition:** Finds rows where the column value is NULL.
- **Syntax:** `SELECT column1 FROM table_name WHERE column1 IS NULL;`
- **Example Query:** 
  ```sql
  SELECT CustomerId FROM Customers WHERE Phone IS NULL;
  ```
- **Expected Result Definition:** Lists `CustomerId`s for customers with no phone number.

## Aggregating Data Using Functions

### Count Records: `COUNT(*)`
- **Definition:** Counts the number of rows in a table or set.
- **Syntax:** `SELECT COUNT(*) FROM table_name WHERE condition;`
- **Example Query:** 
  ```sql
  SELECT COUNT(*) FROM Orders WHERE Status = 'Completed';
  ```
- **Expected Result Definition:** Returns the number of completed orders.

### Sum of a particular column: `SUM(COLUMN)`
- **Definition:** Sums up the numeric values of a specified column.
- **Syntax:** `SELECT SUM(column_name) FROM table_name WHERE condition;`
- **Example Query:** 
  ```sql
  SELECT SUM(Quantity) FROM LineItems WHERE OrderId = 1;
  ```
- **Expected Result Definition:** Totals the quantity of all line items for order with `OrderId` 1.

### Column Value: `AVG / MIN / MAX(COLUMN)`
- **Definition:** Calculates the average, minimum, or maximum value of a specified column.
- **Syntax for AVG:** `SELECT AVG(column_name) FROM table_name WHERE condition;`
- **Syntax for MIN:** `SELECT MIN(column_name) FROM table_name WHERE condition;`
- **Syntax for MAX:** `SELECT MAX(column_name) FROM table_name WHERE condition;`
- **Example Query for AVG:** 
  ```sql
  SELECT AVG(ListPrice) FROM Products;
  ```
- **Expected Result Definition for AVG:** Returns the average list price of all products.
- **Example Query for MIN:** 
  ```sql
  SELECT MIN(ListPrice) FROM Products;
  ```
- **Expected Result Definition for MIN:** Finds the lowest list price among all products.
- **Example Query for MAX:** 
  ```sql
  SELECT MAX(ListPrice) FROM Products;
  ```
- **Expected Result Definition for MAX:** Identifies the highest list price in the product catalog.

### Slice/Dice by Column: `(GROUP BY) (HAVING)`
- **Definition:** Groups rows sharing a property so that an aggregate function can be applied to each group.
- **Syntax:** `SELECT column1, AGG_FUNC(column2) FROM table_name GROUP BY column1 HAVING condition;`
- **Example Query:** 
  ```sql
  SELECT CustomerId, COUNT(OrderId) FROM Orders GROUP BY CustomerId HAVING COUNT(OrderId) > 5;
  ```
- **Expected Result Definition:** Lists customers who have placed more than 5 orders, along with the number of orders they placed.

## Remove Duplicates and Find Unique Values

### DISTINCT
- **Definition:** Returns unique values in the specified column(s).
- **Syntax:** `SELECT DISTINCT column1 FROM table_name;`
- **Example Query:** 
  ```sql
  SELECT DISTINCT Status FROM Orders;
  ```
- **Expected Result Definition:** Lists all unique order statuses.

### GROUP BY + COUNT + HAVING to find duplicates and their count
- **Example Query:** 
  ```sql
  SELECT Email, COUNT(*) FROM Customers GROUP BY Email HAVING COUNT(*) > 1;
  ```
- **Expected Result Definition:** Finds duplicate email addresses in the `Customers` table and shows how many times each appears.

## Different Ways to Join Tables

### INNER JOIN
- **Definition:** Combines rows from two or more tables based on a related column between them.
- **Syntax:** `SELECT table1.column, table2.column FROM table1 INNER JOIN table2 ON table1.common_column = table2.common_column;`
- **Example Query:** 
  ```sql
  SELECT Customers.FirstName, Orders.OrderId FROM Customers INNER JOIN Orders ON Customers.CustomerId = Orders.CustomerId;
  ```
- **Expected Result Definition:** Shows the first name of customers along with their order IDs.

### LEFT JOIN
- **Definition:** Returns all records from the left table, and the matched records from the right table.
- **Syntax:** `SELECT table1.column, table2.column FROM table1 LEFT JOIN table2 ON table1.common_column = table2.common_column;`
- **Example Query:** 
  ```sql
  SELECT Customers.FirstName, Orders.OrderId FROM Customers LEFT JOIN Orders ON Customers.CustomerId = Orders.CustomerId;
  ```
- **Expected Result Definition:** Lists all customers and their orders if they have any. Customers without orders will still appear, with NULL in the `OrderId` column.

### RIGHT JOIN
- **Definition:** Returns all records from the right table, and the matched records from the left table.
- **Syntax:** Similar to LEFT JOIN but with tables reversed.
- **Example Query:** Not commonly used in practice as LEFT JOIN can usually be rearranged to achieve the same result.

## Sorting and Ordering data using `ORDER BY`
- **Definition:** Orders the result set of a query by specified column(s).
- **Syntax:** `SELECT column1 FROM table_name ORDER BY column1 ASC|DESC;`
- **Example Query:** 
  ```sql
  SELECT Name, ListPrice FROM Products ORDER BY ListPrice DESC;
  ```
- **Expected Result Definition:** Lists products in descending order of their list price.

## Using subqueries within queries
- **Definition:** A query nested inside another query.
- **Syntax:** `SELECT column1 FROM (SELECT column1 FROM table_name) AS subquery;`
- **Example Query:** 
  ```sql
  SELECT AVG(Price) FROM (SELECT ListPrice AS Price FROM Products) AS ProductPrices;
  ```
- **Expected Result Definition:** Calculates the average price of all products by treating the list prices as a subquery.

Each of these concepts is foundational in SQL and helps in various data manipulation and retrieval operations. By understanding and applying these operations, one can efficiently work with databases to extract and analyze data.
""")

if st.checkbox("Admin Panel"):
    if st.button("Reset Database"):
        reset_database()
