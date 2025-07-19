import clickhouse_connect

def get_client():
    """
    Create and return a ClickHouse client instance.
    
    Returns:
        clickhouse_connect.Client: A ClickHouse client connected to the specified host and port.
    """
    return clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='')

def run_query(query):
    """
    Execute a ClickHouse query and return the result.
    
    Args:
        query (str): The SQL query to execute.
        
    Returns:
        list: The result of the query as a list of dictionaries.
    """
    client = get_client()
    return client.query_df(query)