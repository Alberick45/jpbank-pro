-- Create Service Requests Table
CREATE TABLE tbl_service_requests_086 (
    request_id INT IDENTITY(1,1) PRIMARY KEY,
    customer_id INT NOT NULL,
    request_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    priority VARCHAR(10) DEFAULT 'Medium',
    status VARCHAR(20) DEFAULT 'Pending',
    created_by INT NOT NULL,
    created_at DATETIME NOT NULL,
    completed_by INT,
    completed_at DATETIME,
    FOREIGN KEY (customer_id) REFERENCES tbl_customers_086(cus_id),
    FOREIGN KEY (created_by) REFERENCES tbl_users_086(usr_idpk),
    FOREIGN KEY (completed_by) REFERENCES tbl_users_086(usr_idpk)
);
