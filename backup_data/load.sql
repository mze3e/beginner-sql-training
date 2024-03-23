COPY Products FROM 'new_data/products_.csv' (FORMAT 'csv', quote '"', delimiter ',', header 1);
COPY Customers FROM 'new_data/customers_.csv' (FORMAT 'csv', quote '"', delimiter ',', header 1);
COPY Orders FROM 'new_data/orders_.csv' (FORMAT 'csv', quote '"', delimiter ',', header 1);
COPY LineItems FROM 'new_data/lineitems_.csv' (FORMAT 'csv', quote '"', delimiter ',', header 1);