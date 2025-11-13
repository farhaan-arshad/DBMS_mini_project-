-- gym_enhanced_fixed.sql

DROP DATABASE IF EXISTS GYM;
CREATE DATABASE GYM CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE GYM;

-- -----------------------
-- 0. Utilities / Audit
-- -----------------------
CREATE TABLE Audit_Log (
    Audit_ID INT AUTO_INCREMENT PRIMARY KEY,
    Table_Name VARCHAR(64),
    Action VARCHAR(10), -- INSERT, UPDATE, DELETE, ADD
    Key_Info VARCHAR(255),
    Changed_By VARCHAR(64), -- app username
    Changed_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Details JSON NULL
);

-- -----------------------
-- 1. GYM
-- -----------------------
CREATE TABLE Gym (
    Gym_ID INT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Location VARCHAR(150),
    Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_gym_name ON Gym(Name);

INSERT INTO Gym (Gym_ID, Name, Location) VALUES 
(1, 'FitZone', 'Bangalore'),
(2, 'PowerHouse', 'Mysore');

-- -----------------------
-- 2. TRAINERS
-- -----------------------
CREATE TABLE Trainers (
    Trainer_ID INT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Email VARCHAR(100) UNIQUE,
    Specialization VARCHAR(80),
    Gym_ID INT NOT NULL,
    Active BOOLEAN DEFAULT TRUE,
    Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (Gym_ID) REFERENCES Gym(Gym_ID) ON DELETE CASCADE
);
CREATE INDEX idx_trainers_gym ON Trainers(Gym_ID);

INSERT INTO Trainers (Trainer_ID, Name, Email, Specialization, Gym_ID, Active, Created_At) VALUES
(101, 'Dhriti Kumar', 'rajesh@fitzone.com','Strength Training', 1, TRUE, NOW()),
(102, 'Anita Sharma', 'anita@fitzone.com','Yoga', 1, TRUE, NOW()),
(103, 'Karan Patel', 'karan@powerhouse.com','Cardio', 2, TRUE, NOW());

-- -----------------------
-- 2a. TRAINER_PHONE
-- -----------------------
CREATE TABLE Trainer_Phone (
    Trainer_ID INT,
    Phone VARCHAR(20),
    PRIMARY KEY (Trainer_ID, Phone),
    FOREIGN KEY (Trainer_ID) REFERENCES Trainers(Trainer_ID) ON DELETE CASCADE
);
INSERT INTO Trainer_Phone (Trainer_ID, Phone) VALUES
(101, '9001112233'),
(101, '9887766554'),
(102, '9001114455'),
(103, '9112233445'),
(103, '9332211000');

-- -----------------------
-- 3. CLASSES
-- -----------------------
CREATE TABLE Classes (
    Class_ID INT PRIMARY KEY,
    Name VARCHAR(80),
    Schedule VARCHAR(80),
    Trainer_ID INT,
    Capacity INT DEFAULT 20,
    Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (Trainer_ID) REFERENCES Trainers(Trainer_ID) ON DELETE SET NULL
);
INSERT INTO Classes (Class_ID, Name, Schedule, Trainer_ID, Capacity, Created_At) VALUES
(201, 'Morning Yoga', 'Mon-Wed-Fri 7AM', 102, 25, NOW()),
(202, 'HIIT Training', 'Tue-Thu 6PM', 101, 30, NOW()),
(203, 'Zumba', 'Sat-Sun 5PM', 103, 40, NOW());

-- -----------------------
-- 4. MEMBERS
-- -----------------------
CREATE TABLE Members (
    Member_ID INT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    DOB DATE,
    Age INT,
    Type_of_Membership ENUM('Monthly','Quarterly','Annual','Trial') DEFAULT 'Monthly',
    Fee DECIMAL(10,2),
    Gym_ID INT,
    Membership_Start DATE,
    Membership_End DATE,
    Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (Gym_ID) REFERENCES Gym(Gym_ID) ON DELETE SET NULL
);
CREATE INDEX idx_members_gym ON Members(Gym_ID);

INSERT INTO Members (Member_ID, Name, DOB, Age, Type_of_Membership, Fee, Gym_ID, Membership_Start, Membership_End, Created_At, Active) VALUES
(301, 'Arjun Mehta', '1999-05-10', 26, 'Annual', 12000, 1, '2025-01-01','2025-12-31', NOW(), TRUE),
(302, 'Priya Singh', '2001-11-21', 23, 'Monthly', 1500, 1, '2025-02-01','2025-02-28', NOW(), TRUE),
(303, 'Rohit Verma', '1998-03-14', 27, 'Annual', 10000, 2, '2025-02-10','2026-02-09', NOW(), TRUE);

-- -----------------------
-- 5. FAMILY_MEMBERS
-- -----------------------
CREATE TABLE Family_Members (
    Fam_ID INT PRIMARY KEY,
    Name VARCHAR(100),
    Relationship VARCHAR(30),
    Member_ID INT,
    FOREIGN KEY (Member_ID) REFERENCES Members(Member_ID) ON DELETE CASCADE
);
INSERT INTO Family_Members (Fam_ID, Name, Relationship, Member_ID) VALUES
(401, 'Neha Mehta', 'Sister', 301),
(402, 'Amit Singh', 'Brother', 302);

-- -----------------------
-- 6. WORKOUT_PLAN
-- -----------------------
CREATE TABLE Workout_Plan (
    Plan_ID INT PRIMARY KEY,
    Name VARCHAR(80),
    Duration VARCHAR(40),
    Trainer_ID INT,
    Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (Trainer_ID) REFERENCES Trainers(Trainer_ID) ON DELETE SET NULL
);
INSERT INTO Workout_Plan (Plan_ID, Name, Duration, Trainer_ID, Created_At) VALUES
(501, 'Fat Loss Plan', '3 Months', 103, NOW()),
(502, 'Muscle Gain Plan', '6 Months', 101, NOW()),
(503, 'Flexibility Plan', '2 Months', 102, NOW());

-- -----------------------
-- 7. EXERCISE
-- -----------------------
CREATE TABLE Exercise (
    Ex_ID INT PRIMARY KEY,
    Name VARCHAR(80),
    Type VARCHAR(40),
    Calories INT,
    Plan_ID INT,
    FOREIGN KEY (Plan_ID) REFERENCES Workout_Plan(Plan_ID) ON DELETE CASCADE
);
INSERT INTO Exercise (Ex_ID, Name, Type, Calories, Plan_ID) VALUES
(601, 'Squats', 'Strength', 100, 502),
(602, 'Push-ups', 'Strength', 80, 502),
(603, 'Running', 'Cardio', 200, 501),
(604, 'Surya Namaskar', 'Yoga', 120, 503);

-- -----------------------
-- 8. PAYMENTS
-- -----------------------
CREATE TABLE Payments (
    Payment_ID INT AUTO_INCREMENT PRIMARY KEY,
    Method VARCHAR(20),
    Date DATE,
    Amount DECIMAL(10,2),
    Member_ID INT,
    Receipt_No VARCHAR(100),
    FOREIGN KEY (Member_ID) REFERENCES Members(Member_ID) ON DELETE CASCADE
);

INSERT INTO Payments (Payment_ID, Method, Date, Amount, Member_ID, Receipt_No) VALUES
(701, 'UPI', '2025-01-10', 12000, 301, 'R-20250110-701'),
(702, 'Cash', '2025-02-01', 1500, 302, 'R-20250201-702'),
(703, 'Card', '2025-03-05', 10000, 303, 'R-20250305-703');

CREATE INDEX idx_payments_member ON Payments(Member_ID);

-- -----------------------
-- 9. GYM_CONTACT
-- -----------------------
CREATE TABLE Gym_Contact (
    Gym_ID INT,
    Contact VARCHAR(20),
    PRIMARY KEY (Gym_ID, Contact),
    FOREIGN KEY (Gym_ID) REFERENCES Gym(Gym_ID) ON DELETE CASCADE
);
INSERT INTO Gym_Contact (Gym_ID, Contact) VALUES
(1, '9876543210'),
(1, '9900112233'),
(2, '9123456780'),
(2, '9345678901');

-- -----------------------
-- 10. ASSIGNS (M:N: members - trainers - plan)
-- -----------------------
CREATE TABLE Assigns (
    Member_ID INT,
    Trainer_ID INT,
    Plan_ID INT,
    Assigned_Date DATE,
    PRIMARY KEY (Member_ID, Trainer_ID, Plan_ID),
    FOREIGN KEY (Member_ID) REFERENCES Members(Member_ID) ON DELETE CASCADE,
    FOREIGN KEY (Trainer_ID) REFERENCES Trainers(Trainer_ID) ON DELETE CASCADE,
    FOREIGN KEY (Plan_ID) REFERENCES Workout_Plan(Plan_ID) ON DELETE CASCADE
);
INSERT INTO Assigns (Member_ID, Trainer_ID, Plan_ID, Assigned_Date) VALUES
(301, 101, 502, '2025-01-15'),
(302, 102, 503, '2025-02-01'),
(303, 103, 501, '2025-02-10'),
(301, 102, 503, '2025-02-20');

-- -----------------------
-- 11. USERS (for app-level auth)
-- -----------------------
-- Passwords stored as SHA2(...) for demo. In production use bcrypt + salted hashing.
CREATE TABLE App_Users (
    User_ID INT AUTO_INCREMENT PRIMARY KEY,
    Username VARCHAR(50) UNIQUE NOT NULL,
    Password_Hash VARCHAR(128) NOT NULL, -- SHA2('password', 256)
    Role ENUM('admin','staff','member','viewer') DEFAULT 'member',
    Linked_Member_ID INT NULL,
    Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Last_Login TIMESTAMP NULL,
    FOREIGN KEY (Linked_Member_ID) REFERENCES Members(Member_ID) ON DELETE SET NULL
);

-- seed an admin row (password will be set using procedure below)
INSERT INTO App_Users (Username, Password_Hash, Role) VALUES ('admin', '', 'admin');

-- -----------------------
-- 12. FUNCTIONS & PROCEDURES
-- -----------------------
DELIMITER $$

CREATE FUNCTION total_payment(memberId INT)
RETURNS DECIMAL(12,2)
DETERMINISTIC
BEGIN
    DECLARE total DECIMAL(12,2) DEFAULT 0;
    SELECT IFNULL(SUM(Amount),0) INTO total FROM Payments WHERE Member_ID = memberId;
    RETURN total;
END$$

CREATE PROCEDURE add_member(
    IN p_id INT,
    IN p_name VARCHAR(100),
    IN p_dob DATE,
    IN p_type VARCHAR(20),
    IN p_fee DECIMAL(10,2),
    IN p_gym INT,
    IN p_start DATE,
    IN p_end DATE,
    IN changed_by VARCHAR(64)
)
BEGIN
    DECLARE calc_age INT;
    SET calc_age = TIMESTAMPDIFF(YEAR, p_dob, CURDATE());
    INSERT INTO Members(Member_ID, Name, DOB, Age, Type_of_Membership, Fee, Gym_ID, Membership_Start, Membership_End)
    VALUES (p_id, p_name, p_dob, calc_age, p_type, p_fee, p_gym, p_start, p_end);

    -- audit
    INSERT INTO Audit_Log (Table_Name, Action, Key_Info, Changed_By, Details)
    VALUES ('Members','INSERT', CONCAT('Member_ID=', p_id), changed_by, JSON_OBJECT('Name', p_name));
END$$

CREATE PROCEDURE set_user_password(
    IN p_username VARCHAR(50),
    IN p_plain_password VARCHAR(255)
)
BEGIN
    UPDATE App_Users
    SET Password_Hash = SHA2(p_plain_password,256)
    WHERE Username = p_username;
END$$

CREATE PROCEDURE add_audit(
    IN tname VARCHAR(64),
    IN act VARCHAR(10),
    IN kinfo VARCHAR(255),
    IN who VARCHAR(64),
    IN details_json JSON
)
BEGIN
    INSERT INTO Audit_Log (Table_Name, Action, Key_Info, Changed_By, Details)
    VALUES (tname, act, kinfo, who, details_json);
END$$

DELIMITER ;

-- set admin password using procedure
CALL set_user_password('admin','adminpass');

-- seed a readonly app user for the web app
INSERT INTO App_Users (Username, Password_Hash, Role)
VALUES ('readonly', SHA2('readonly123',256), 'viewer');



-- -----------------------
-- 13. TRIGGERS
-- -----------------------
DELIMITER $$

CREATE TRIGGER trg_members_age_insert
BEFORE INSERT ON Members
FOR EACH ROW
BEGIN
    IF NEW.DOB IS NOT NULL THEN
        SET NEW.Age = TIMESTAMPDIFF(YEAR, NEW.DOB, CURDATE());
    ELSE
        SET NEW.Age = NULL;
    END IF;
END$$

CREATE TRIGGER trg_members_age_update
BEFORE UPDATE ON Members
FOR EACH ROW
BEGIN
    IF NEW.DOB <> OLD.DOB OR NEW.Membership_Start <> OLD.Membership_Start THEN
        SET NEW.Age = IF(NEW.DOB IS NOT NULL, TIMESTAMPDIFF(YEAR, NEW.DOB, CURDATE()), NULL);
    END IF;
END$$

CREATE TRIGGER trg_payments_insert
AFTER INSERT ON Payments
FOR EACH ROW
BEGIN
    CALL add_audit('Payments','INSERT', CONCAT('Payment_ID=', NEW.Payment_ID), 'system', JSON_OBJECT('Amount', NEW.Amount, 'Member_ID', NEW.Member_ID));
END$$

CREATE TRIGGER trg_trainers_audit_update
AFTER UPDATE ON Trainers
FOR EACH ROW
BEGIN
    CALL add_audit('Trainers','UPDATE', CONCAT('Trainer_ID=', NEW.Trainer_ID), 'system', JSON_OBJECT('old', JSON_OBJECT('Name', OLD.Name, 'Email', OLD.Email), 'new', JSON_OBJECT('Name', NEW.Name, 'Email', NEW.Email)));
END$$

CREATE TRIGGER trg_members_delete
AFTER DELETE ON Members
FOR EACH ROW
BEGIN
    CALL add_audit('Members','DELETE', CONCAT('Member_ID=', OLD.Member_ID), 'system', JSON_OBJECT('Name', OLD.Name));
END$$


CREATE TRIGGER trg_add_member_payment
AFTER INSERT ON Members
FOR EACH ROW
BEGIN
  -- insert an initial payment record using the new member's fee and start date
  INSERT INTO Payments (Method, Date, Amount, Member_ID, Receipt_No)
  VALUES (
    'Initial',
    NEW.Membership_Start,
    NEW.Fee,
    NEW.Member_ID,
    CONCAT('AUTO-', NEW.Member_ID, '-', DATE_FORMAT(NEW.Membership_Start, '%Y%m%d'))
  );
  -- audit the automatic payment
  CALL add_audit('Payments','INSERT', CONCAT('Member_ID=', NEW.Member_ID), 'system', JSON_OBJECT('auto_payment_for_member', NEW.Member_ID));
END$$

DELIMITER ;

-- -----------------------
-- 14. VIEWS
-- -----------------------
CREATE VIEW vw_member_payments AS
SELECT M.Member_ID, M.Name, M.Gym_ID, IFNULL(total_payment(M.Member_ID),0) AS Total_Paid, M.Membership_End
FROM Members M;

-- -----------------------
-- 15. OS-LEVEL DB USERS (optional; run as root)
-- -----------------------
CREATE USER IF NOT EXISTS 'readonly_user'@'localhost' IDENTIFIED BY 'readonly123';
GRANT SELECT ON GYM.* TO 'readonly_user'@'localhost';
FLUSH PRIVILEGES;

-- -----------------------
-- Done.
-- -----------------------

SELECT* FROM MEMBERS;
SELECT * FROM TRAINERS;


-- Join Query:

SELECT 
    M.Member_ID,
    M.Name AS Member_Name,
    T.Name AS Trainer_Name,
    WP.Name AS Plan_Name,
    G.Name AS Gym_Name,
    A.Assigned_Date
FROM Assigns A
JOIN Members M ON A.Member_ID = M.Member_ID
JOIN Trainers T ON A.Trainer_ID = T.Trainer_ID
JOIN Workout_Plan WP ON A.Plan_ID = WP.Plan_ID
JOIN Gym G ON M.Gym_ID = G.Gym_ID
ORDER BY M.Member_ID;

-- Nested Join Query: 

SELECT 
    T.Trainer_ID,
    T.Name AS Trainer_Name,
    G.Name AS Gym_Name,
    IFNULL(SUM(P.Total_Amount), 0) AS Total_Member_Payments
FROM Trainers T
JOIN Gym G ON T.Gym_ID = G.Gym_ID
LEFT JOIN (
    SELECT 
        A.Trainer_ID,
        A.Member_ID,
        SUM(P.Amount) AS Total_Amount
    FROM Assigns A
    JOIN Payments P ON A.Member_ID = P.Member_ID
    GROUP BY A.Trainer_ID, A.Member_ID
) AS P ON T.Trainer_ID = P.Trainer_ID
GROUP BY T.Trainer_ID, T.Name, G.Name
ORDER BY Total_Member_Payments DESC;


-- Aggregate Query
SELECT 
    G.Gym_ID,
    G.Name AS Gym_Name,
    COUNT(M.Member_ID) AS Total_Members,
    AVG(M.Fee) AS Avg_Fee,
    SUM(P.Amount) AS Total_Revenue
FROM Gym G
LEFT JOIN Members M ON G.Gym_ID = M.Gym_ID
LEFT JOIN Payments P ON M.Member_ID = P.Member_ID
GROUP BY G.Gym_ID, G.Name
ORDER BY Total_Revenue DESC;

