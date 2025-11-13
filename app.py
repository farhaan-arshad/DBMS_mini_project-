from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import mysql.connector
import hashlib
from functools import wraps
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "supersecret-key")

# =====================================================
# DATABASE CONFIG
# =====================================================
DB_CONFIG_ADMIN = {
    "user": "root",
    "password": "Warlord@1503",
    "host": "127.0.0.1",
    "database": "GYM"
}

DB_CONFIG_VIEWER = {
    "user": "readonly_user",
    "password": "readonly123",
    "host": "127.0.0.1",
    "database": "GYM"
}

# =====================================================
# HELPERS
# =====================================================
def sha256(pw):
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def get_db():
    """Return DB connection based on user role."""
    role = session.get("role")
    if role == "viewer":
        return mysql.connector.connect(**DB_CONFIG_VIEWER)
    return mysql.connector.connect(**DB_CONFIG_ADMIN)

# =====================================================
# LOGIN DECORATOR
# =====================================================
def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "user" not in session:
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                return "Access denied", 403
            return f(*args, **kwargs)
        return wrapper
    return decorator

# =====================================================
# LOGIN / LOGOUT
# =====================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = mysql.connector.connect(**DB_CONFIG_ADMIN)
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM App_Users WHERE Username=%s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and user["Password_Hash"] == sha256(password):
            session["user"] = user["Username"]
            session["role"] = user["Role"]
            return redirect(url_for("dashboard"))

        return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# =====================================================
# DASHBOARD
# =====================================================
@app.route("/")
@app.route("/dashboard")
@login_required()
def dashboard():
    conn = get_db()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT COUNT(*) AS total_members FROM Members")
    total_members = cur.fetchone()["total_members"]

    cur.execute("SELECT IFNULL(SUM(Amount), 0) AS total_revenue FROM Payments")
    total_revenue = cur.fetchone()["total_revenue"]

    cur.execute("""
        SELECT IFNULL(SUM(M.Fee - IFNULL(SUM_P.total, 0)), 0) AS pending
        FROM Members M
        LEFT JOIN (
            SELECT Member_ID, SUM(Amount) AS total FROM Payments GROUP BY Member_ID
        ) AS SUM_P ON M.Member_ID = SUM_P.Member_ID
    """)
    pending = cur.fetchone()["pending"]

    cur.close()
    conn.close()

    return render_template("dashboard.html", members=total_members, revenue=total_revenue, pending=pending)

# =====================================================
# MEMBERS
# =====================================================
@app.route("/members")
@login_required()
def members_page():
    return render_template("members.html")


@app.route("/api/member_payments", methods=["GET"])
@login_required()
def api_get_member_payments():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT 
            M.Member_ID,
            M.Name,
            M.Type_of_Membership,
            M.Fee,
            IFNULL(SUM(P.Amount), 0) AS Total_Paid,
            (M.Fee - IFNULL(SUM(P.Amount), 0)) AS Pending_Balance,
            DATE_FORMAT(M.Membership_Start, '%Y-%m-%d') AS Membership_Start,
            DATE_FORMAT(M.Membership_End, '%Y-%m-%d') AS Membership_End,
            CASE 
                WHEN M.Membership_End >= CURDATE() THEN 'Active'
                ELSE 'Expired'
            END AS Status
        FROM Members M
        LEFT JOIN Payments P ON M.Member_ID = P.Member_ID
        GROUP BY 
            M.Member_ID, M.Name, M.Type_of_Membership, M.Fee, 
            M.Membership_Start, M.Membership_End
        ORDER BY M.Member_ID
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(rows)


@app.route("/api/members", methods=["POST"])
@login_required()
def api_add_member():
    if session.get("role") == "viewer":
        return jsonify({"error": "Read-only users cannot add members"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid data"}), 400

    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Members 
            (Member_ID, Name, DOB, Type_of_Membership, Fee, Gym_ID, Membership_Start, Membership_End)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data["Member_ID"],
            data["Name"],
            data["DOB"],
            data["Type_of_Membership"],
            data["Fee"],
            data["Gym_ID"],
            data["Membership_Start"],
            data["Membership_End"]
        ))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/members/<int:member_id>", methods=["POST"])
@login_required()
def api_update_member(member_id):
    if session.get("role") == "viewer":
        return jsonify({"error": "Read-only users cannot edit members"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid data"}), 400

    fields = ["Name", "Type_of_Membership", "Fee", "Membership_Start", "Membership_End"]
    updates, values = [], []

    for f in fields:
        if f in data:
            val = data[f]
            if f in ["Membership_Start", "Membership_End"]:
                try:
                    if val:
                        val = datetime.strptime(val[:10], "%Y-%m-%d").date()
                except Exception:
                    return jsonify({"error": f"Invalid date format for {f}"}), 400
            updates.append(f"{f}=%s")
            values.append(val)

    if not updates:
        return jsonify({"error": "No fields to update"}), 400

    values.append(member_id)

    try:
        conn = get_db()
        cur = conn.cursor()
        sql = f"UPDATE Members SET {', '.join(updates)} WHERE Member_ID=%s"
        cur.execute(sql, values)
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/assign_member", methods=["POST"])
@login_required()
def api_assign_member():
    """Assign a trainer and workout plan to a member"""
    if session.get("role") == "viewer":
        return jsonify({"error": "Read-only users cannot assign members"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid data"}), 400

    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Check if assignment already exists
        cur.execute("""
            SELECT 1 FROM Assigns 
            WHERE Member_ID=%s AND Trainer_ID=%s AND Plan_ID=%s
        """, (data["Member_ID"], data["Trainer_ID"], data["Plan_ID"]))
        
        if cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({"success": True, "message": "Assignment already exists"})
        
        # Insert new assignment
        cur.execute("""
            INSERT INTO Assigns (Member_ID, Trainer_ID, Plan_ID, Assigned_Date)
            VALUES (%s, %s, %s, %s)
        """, (data["Member_ID"], data["Trainer_ID"], data["Plan_ID"], data.get("Assigned_Date")))
        conn.commit()
        
        # Log to audit
        cur.execute("""
            INSERT INTO Audit_Log (Table_Name, Action, Key_Info, Changed_By)
            VALUES ('Assigns', 'INSERT', %s, %s)
        """, (f'Member_ID={data["Member_ID"]}, Trainer_ID={data["Trainer_ID"]}', session["user"]))
        conn.commit()
        
        cur.close()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =====================================================
# TRAINERS
# =====================================================
@app.route("/trainers")
@login_required()
def trainers_page():
    return render_template("trainers.html")


# ✅ GET all trainers
@app.route("/api/trainers", methods=["GET"])
@login_required()
def api_get_trainers():
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM Trainers ORDER BY Trainer_ID")
        rows = cur.fetchall()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()


# ✅ ADD new trainer (auto-generates Trainer_ID)
@app.route("/api/trainers", methods=["POST"])
@login_required()
def api_add_trainer():
    if session.get("role") == "viewer":
        return jsonify({"error": "Read-only users cannot add trainers"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid input"}), 400

    try:
        conn = get_db()
        cur = conn.cursor()

        # 🔹 Auto-generate next Trainer_ID
        cur.execute("SELECT IFNULL(MAX(Trainer_ID), 100) + 1 FROM Trainers")
        next_id = cur.fetchone()[0]

        sql = """
            INSERT INTO Trainers (Trainer_ID, Name, Email, Specialization, Gym_ID, Active)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cur.execute(sql, (
            next_id,
            data.get("Name"),
            data.get("Email"),
            data.get("Specialization"),
            data.get("Gym_ID"),
            int(data.get("Active", 1))  # default Active=1 if missing
        ))
        conn.commit()

        # 🔹 Log to audit
        cur.execute("""
            INSERT INTO Audit_Log (Table_Name, Action, Key_Info, Changed_By)
            VALUES ('Trainers', 'ADD', %s, %s)
        """, (f'Trainer_ID={next_id}', session["user"]))
        conn.commit()

        return jsonify({"success": True, "Trainer_ID": next_id})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()


# ✅ UPDATE existing trainer
@app.route("/api/trainers/<int:trainer_id>", methods=["POST"])
@login_required()
def api_update_trainer(trainer_id):
    if session.get("role") == "viewer":
        return jsonify({"error": "Read-only users cannot edit trainers"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid data"}), 400

    fields = ["Name", "Email", "Specialization", "Gym_ID", "Active"]
    updates, values = [], []

    for f in fields:
        if f in data:
            updates.append(f"{f}=%s")
            values.append(data[f])

    if not updates:
        return jsonify({"error": "No fields to update"}), 400

    values.append(trainer_id)

    try:
        conn = get_db()
        cur = conn.cursor()
        sql = f"UPDATE Trainers SET {', '.join(updates)} WHERE Trainer_ID=%s"
        cur.execute(sql, values)
        conn.commit()

        # 🔹 Log to audit
        cur.execute("""
            INSERT INTO Audit_Log (Table_Name, Action, Key_Info, Changed_By)
            VALUES ('Trainers', 'UPDATE', %s, %s)
        """, (f'Trainer_ID={trainer_id}', session["user"]))
        conn.commit()

        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()


# =====================================================
# PAYMENTS
# =====================================================
@app.route("/payments")
@login_required()
def payments_page():
    return render_template("payments.html")

@app.route("/api/payments", methods=["GET"])
@login_required()
def api_get_payments():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT p.Payment_ID, p.Method, p.Date, p.Amount, p.Member_ID, p.Receipt_No, m.Name AS MemberName
        FROM Payments p
        JOIN Members m ON p.Member_ID = m.Member_ID
        ORDER BY Payment_ID
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(rows)

@app.route("/api/payments", methods=["POST"])
@login_required()
def api_add_payment():
    if session.get("role") == "viewer":
        return jsonify({"error": "Read-only users cannot add payments"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid input"}), 400

    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Payments (Method, Date, Amount, Member_ID, Receipt_No)
            VALUES (%s, %s, %s, %s, %s)
        """, (data["Method"], data["Date"], data["Amount"], data["Member_ID"], data["Receipt_No"]))
        conn.commit()

        cur.execute("""
            INSERT INTO Audit_Log (Table_Name, Action, Key_Info, Changed_By)
            VALUES ('Payments', 'ADD', %s, %s)
        """, (f'Member_ID={data["Member_ID"]}', session["user"]))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()
    return jsonify({"success": True})

# =====================================================
# ADVANCED QUERIES (JOIN, NESTED, AGGREGATE)
# =====================================================
@app.route("/queries")
@login_required()
def queries_page():
    if session.get("role") == "viewer":
        return "Access denied. Advanced Queries are not available for read-only users.", 403
    return render_template("queries.html")



# ✅ JOIN Query: Member-Trainer-Plan-Gym Details
@app.route("/api/queries/join", methods=["GET"])
@login_required()
def api_join_query():
    """
    JOIN Query: Displays member assignments with trainer, plan, and gym details
    """
    if session.get("role") == "viewer":
        return jsonify({"error": "Access denied. Advanced Queries are not available for read-only users."}), 403
    
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT 
                A.Member_ID,
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
            ORDER BY M.Member_ID
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ NESTED Query: Trainer Performance with Member Payments
@app.route("/api/queries/nested", methods=["GET"])
@login_required()
def api_nested_query():
    """
    NESTED Query: Shows trainer performance based on members' payments
    Includes subquery with aggregate functions
    """
    if session.get("role") == "viewer":
        return jsonify({"error": "Access denied. Advanced Queries are not available for read-only users."}), 403
    
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT 
                T.Trainer_ID,
                T.Name AS Trainer_Name,
                G.Name AS Gym_Name,
                T.Specialization,
                IFNULL(SUM(P.Total_Amount), 0) AS Total_Member_Payments,
                IFNULL(COUNT(DISTINCT A.Member_ID), 0) AS Total_Members_Assigned
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
            LEFT JOIN Assigns A ON T.Trainer_ID = A.Trainer_ID
            GROUP BY T.Trainer_ID, T.Name, G.Name, T.Specialization
            ORDER BY Total_Member_Payments DESC
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ AGGREGATE Query: Gym Performance Summary
@app.route("/api/queries/aggregate", methods=["GET"])
@login_required()
def api_aggregate_query():
    """
    AGGREGATE Query: Provides gym-level statistics including member count,
    average fees, and total revenue
    """
    if session.get("role") == "viewer":
        return jsonify({"error": "Access denied. Advanced Queries are not available for read-only users."}), 403
    
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT 
                G.Gym_ID,
                G.Name AS Gym_Name,
                G.Location,
                COUNT(DISTINCT M.Member_ID) AS Total_Members,
                IFNULL(AVG(M.Fee), 0) AS Avg_Fee,
                IFNULL(SUM(P.Amount), 0) AS Total_Revenue,
                COUNT(DISTINCT T.Trainer_ID) AS Total_Trainers,
                ROUND(IFNULL(SUM(P.Amount), 0) / NULLIF(COUNT(DISTINCT M.Member_ID), 0), 2) AS Revenue_Per_Member
            FROM Gym G
            LEFT JOIN Members M ON G.Gym_ID = M.Gym_ID
            LEFT JOIN Payments P ON M.Member_ID = P.Member_ID
            LEFT JOIN Trainers T ON G.Gym_ID = T.Gym_ID
            GROUP BY G.Gym_ID, G.Name, G.Location
            ORDER BY Total_Revenue DESC
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =====================================================
# AUDIT LOG
# =====================================================
@app.route("/audit")
@login_required(role="admin")
def audit_page():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM Audit_Log ORDER BY Changed_At DESC LIMIT 200")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("audit.html", audits=rows)

# =====================================================
# RUN
# =====================================================
if __name__ == "__main__":
    app.run(debug=True, port=5000)
