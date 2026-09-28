from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_file
)

from database import get_db_connection, create_tables

from student_utils import (
    calculate_grade,
    calculate_result,
    validate_marks,
    calculate_attendance
)

from export_csv import export_students_to_csv

import pandas as pd
import numpy as np

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import seaborn as sns

from scipy import stats

from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score

from bs4 import BeautifulSoup

import pickle
import os


app = Flask(__name__)

create_tables()


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    connection = get_db_connection()

    total_students = connection.execute(
        "SELECT COUNT(*) AS count FROM students"
    ).fetchone()["count"]

    total_marks = connection.execute(
        "SELECT COUNT(*) AS count FROM marks"
    ).fetchone()["count"]

    total_attendance = connection.execute(
        "SELECT COUNT(*) AS count FROM attendance"
    ).fetchone()["count"]

    connection.close()

    return render_template(
        "index.html",
        total_students=total_students,
        total_marks=total_marks,
        total_attendance=total_attendance
    )


# =========================================================
# STUDENTS
# =========================================================

@app.route("/students")
def students():

    search = request.args.get("search", "")

    connection = get_db_connection()

    if search:

        students = connection.execute("""
            SELECT *
            FROM students
            WHERE roll_no LIKE ?
               OR name LIKE ?
               OR branch LIKE ?
            ORDER BY id DESC
        """, (
            f"%{search}%",
            f"%{search}%",
            f"%{search}%"
        )).fetchall()

    else:

        students = connection.execute(
            "SELECT * FROM students ORDER BY id DESC"
        ).fetchall()

    connection.close()

    return render_template(
        "students.html",
        students=students,
        search=search
    )


# =========================================================
# ADD STUDENT
# =========================================================

@app.route("/add-student", methods=["GET", "POST"])
def add_student():

    if request.method == "POST":

        roll_no = request.form["roll_no"]
        name = request.form["name"]
        branch = request.form["branch"]
        semester = request.form["semester"]
        email = request.form["email"]
        mobile = request.form["mobile"]
        attendance = request.form.get("attendance", 0)
        club = request.form.get("club", "None")

        permissions = 0

        if request.form.get("read_permission"):
            permissions |= 1

        if request.form.get("write_permission"):
            permissions |= 2

        if request.form.get("delete_permission"):
            permissions |= 4

        connection = get_db_connection()

        try:

            connection.execute("""
                INSERT INTO students
                (
                    roll_no,
                    name,
                    branch,
                    semester,
                    email,
                    mobile,
                    attendance,
                    club,
                    permissions
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                roll_no,
                name,
                branch,
                semester,
                email,
                mobile,
                attendance,
                club,
                permissions
            ))

            connection.commit()

        except Exception as error:

            print("Error:", error)

        finally:

            connection.close()

        return redirect(url_for("students"))

    return render_template("add_student.html")


# =========================================================
# EDIT STUDENT
# =========================================================

@app.route("/edit-student/<int:student_id>", methods=["GET", "POST"])
def edit_student(student_id):

    connection = get_db_connection()

    if request.method == "POST":

        roll_no = request.form["roll_no"]
        name = request.form["name"]
        branch = request.form["branch"]
        semester = request.form["semester"]
        email = request.form["email"]
        mobile = request.form["mobile"]
        attendance = request.form.get("attendance", 0)
        club = request.form.get("club", "None")

        permissions = 0

        if request.form.get("read_permission"):
            permissions |= 1

        if request.form.get("write_permission"):
            permissions |= 2

        if request.form.get("delete_permission"):
            permissions |= 4

        connection.execute("""
            UPDATE students
            SET
                roll_no = ?,
                name = ?,
                branch = ?,
                semester = ?,
                email = ?,
                mobile = ?,
                attendance = ?,
                club = ?,
                permissions = ?
            WHERE id = ?
        """, (
            roll_no,
            name,
            branch,
            semester,
            email,
            mobile,
            attendance,
            club,
            permissions,
            student_id
        ))

        connection.commit()
        connection.close()

        return redirect(url_for("students"))

    student = connection.execute(
        "SELECT * FROM students WHERE id = ?",
        (student_id,)
    ).fetchone()

    connection.close()

    return render_template(
        "edit_student.html",
        student=student
    )


# =========================================================
# DELETE STUDENT
# =========================================================

@app.route("/delete-student/<int:student_id>")
def delete_student(student_id):

    connection = get_db_connection()

    connection.execute(
        "DELETE FROM marks WHERE student_id = ?",
        (student_id,)
    )

    connection.execute(
        "DELETE FROM attendance WHERE student_id = ?",
        (student_id,)
    )

    connection.execute(
        "DELETE FROM students WHERE id = ?",
        (student_id,)
    )

    connection.commit()
    connection.close()

    return redirect(url_for("students"))


# =========================================================
# MARKS
# =========================================================

@app.route("/marks", methods=["GET", "POST"])
def marks():

    connection = get_db_connection()

    students = connection.execute(
        "SELECT * FROM students ORDER BY roll_no"
    ).fetchall()

    if request.method == "POST":

        student_id = request.form["student_id"]

        try:

            subject1 = float(request.form["subject1"])
            subject2 = float(request.form["subject2"])
            subject3 = float(request.form["subject3"])
            subject4 = float(request.form["subject4"])
            subject5 = float(request.form["subject5"])

            validate_marks([
                subject1,
                subject2,
                subject3,
                subject4,
                subject5
            ])

        except ValueError as error:

            connection.close()

            return f"""
            <h3>Error: {error}</h3>
            <a href="/marks">Go Back</a>
            """

        total = (
            subject1 +
            subject2 +
            subject3 +
            subject4 +
            subject5
        )

        percentage = total / 5

        grade = calculate_grade(percentage)
        result = calculate_result(percentage)

        connection.execute("""
            INSERT INTO marks
            (
                student_id,
                subject1,
                subject2,
                subject3,
                subject4,
                subject5,
                total,
                percentage,
                grade,
                result
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            student_id,
            subject1,
            subject2,
            subject3,
            subject4,
            subject5,
            total,
            percentage,
            grade,
            result
        ))

        connection.commit()
        connection.close()

        return redirect(url_for("marks"))

    marks_data = connection.execute("""
        SELECT
            marks.*,
            students.roll_no,
            students.name
        FROM marks
        JOIN students
        ON marks.student_id = students.id
        ORDER BY marks.id DESC
    """).fetchall()

    connection.close()

    return render_template(
        "marks.html",
        students=students,
        marks_data=marks_data
    )


# =========================================================
# ATTENDANCE
# =========================================================

@app.route("/attendance", methods=["GET", "POST"])
def attendance():

    connection = get_db_connection()

    students = connection.execute(
        "SELECT * FROM students ORDER BY roll_no"
    ).fetchall()

    if request.method == "POST":

        student_id = request.form["student_id"]

        try:

            total_days = int(request.form["total_days"])
            present_days = int(request.form["present_days"])

            attendance_percentage = calculate_attendance(
                total_days,
                present_days
            )

        except ValueError as error:

            connection.close()

            return f"""
            <h3>Error: {error}</h3>
            <a href="/attendance">Go Back</a>
            """

        connection.execute("""
            UPDATE students
            SET attendance = ?
            WHERE id = ?
        """, (
            attendance_percentage,
            student_id
        ))

        connection.execute("""
            INSERT INTO attendance
            (
                student_id,
                total_days,
                present_days,
                attendance_percentage
            )
            VALUES (?, ?, ?, ?)
        """, (
            student_id,
            total_days,
            present_days,
            attendance_percentage
        ))

        connection.commit()
        connection.close()

        return redirect(url_for("attendance"))

    attendance_data = connection.execute("""
        SELECT
            attendance.*,
            students.roll_no,
            students.name
        FROM attendance
        JOIN students
        ON attendance.student_id = students.id
        ORDER BY attendance.id DESC
    """).fetchall()

    connection.close()

    return render_template(
        "attendance.html",
        students=students,
        attendance_data=attendance_data
    )


# =========================================================
# CSV EXPORT
# =========================================================

@app.route("/export-csv")
def export_csv():

    connection = get_db_connection()

    students = connection.execute(
        "SELECT * FROM students ORDER BY roll_no"
    ).fetchall()

    connection.close()

    filename = export_students_to_csv(students)

    return send_file(
        filename,
        as_attachment=True,
        download_name="students.csv"
    )


# =========================================================
# TEXT EXPORT
# =========================================================

@app.route("/export-text")
def export_text():

    connection = get_db_connection()

    students = connection.execute(
        "SELECT * FROM students ORDER BY roll_no"
    ).fetchall()

    connection.close()

    os.makedirs("data", exist_ok=True)

    filename = "data/students.txt"

    with open(filename, "w", encoding="utf-8") as file:

        for student in students:

            file.write(
                f"Roll No: {student['roll_no']}\n"
            )

            file.write(
                f"Name: {student['name']}\n"
            )

            file.write(
                f"Branch: {student['branch']}\n"
            )

            file.write(
                f"Semester: {student['semester']}\n"
            )

            file.write(
                f"Email: {student['email']}\n"
            )

            file.write(
                f"Mobile: {student['mobile']}\n"
            )

            file.write(
                f"Attendance: {student['attendance']}%\n"
            )

            file.write("-" * 40 + "\n")

    return send_file(
        filename,
        as_attachment=True,
        download_name="students.txt"
    )


# =========================================================
# PICKLE BACKUP
# =========================================================

@app.route("/backup")
def backup():

    connection = get_db_connection()

    students = connection.execute(
        "SELECT * FROM students"
    ).fetchall()

    connection.close()

    student_records = [
        dict(student)
        for student in students
    ]

    os.makedirs("data", exist_ok=True)

    filename = "data/students_backup.pkl"

    with open(filename, "wb") as file:

        pickle.dump(
            student_records,
            file
        )

    return send_file(
        filename,
        as_attachment=True,
        download_name="students_backup.pkl"
    )


# =========================================================
# ANALYTICS
# =========================================================

@app.route("/analytics")
def analytics():

    connection = get_db_connection()

    data = connection.execute("""
        SELECT
            students.roll_no,
            students.name,
            students.branch,
            students.attendance,
            marks.subject1,
            marks.subject2,
            marks.subject3,
            marks.subject4,
            marks.subject5,
            marks.total,
            marks.percentage,
            marks.grade,
            marks.result
        FROM marks
        JOIN students
        ON marks.student_id = students.id
    """).fetchall()

    connection.close()

    if len(data) == 0:

        return render_template(
            "analytics.html",
            total_students=0,
            average=0,
            highest=0,
            lowest=0,
            pass_count=0,
            fail_count=0,
            std_dev=0,
            variance=0,
            skewness=0,
            kurtosis=0,
            confidence_low=0,
            confidence_high=0,
            pass_probability=0,
            sample_mean=0,
            sample_size=0,
            t_stat=0,
            p_value=0,
            t_test_result="No data",
            univariate_mean=0,
            univariate_median=0,
            univariate_mode=0,
            correlation=0,
            students_data=[]
        )

    df = pd.DataFrame(
        [dict(row) for row in data]
    )

    percentages = np.array(
        df["percentage"],
        dtype=float
    )

    average = round(np.mean(percentages), 2)
    highest = round(np.max(percentages), 2)
    lowest = round(np.min(percentages), 2)

    std_dev = round(
        float(stats.tstd(percentages)),
        2
    )

    variance = round(
        float(stats.tvar(percentages)),
        2
    )

    skewness = round(
        float(stats.skew(percentages)),
        2
    )

    kurtosis = round(
        float(stats.kurtosis(percentages)),
        2
    )

    if len(percentages) > 1:

        confidence = stats.t.interval(
            0.95,
            len(percentages) - 1,
            loc=np.mean(percentages),
            scale=stats.sem(percentages)
        )

    else:

        confidence = (
            np.mean(percentages),
            np.mean(percentages)
        )

    confidence_low = round(
        float(confidence[0]),
        2
    )

    confidence_high = round(
        float(confidence[1]),
        2
    )

    pass_count = int(
        (df["result"] == "PASS").sum()
    )

    fail_count = int(
        (df["result"] == "FAIL").sum()
    )

    total_students = len(df)

    pass_probability = round(
        (pass_count / total_students) * 100,
        2
    )

    sample_size = min(
        5,
        len(percentages)
    )

    sample = df["percentage"].sample(
        n=sample_size,
        random_state=42
    )

    sample_mean = round(
        float(sample.mean()),
        2
    )

    if len(percentages) > 1:

        t_result = stats.ttest_1samp(
            percentages,
            40
        )

        t_stat = round(
            float(t_result.statistic),
            4
        )

        p_value = round(
            float(t_result.pvalue),
            4
        )

        if p_value < 0.05:

            t_test_result = (
                "Statistically significant "
                "difference from 40"
            )

        else:

            t_test_result = (
                "No statistically significant "
                "difference from 40"
            )

    else:

        t_stat = 0
        p_value = 0
        t_test_result = "Not enough data"

    numeric_columns = [
        "subject1",
        "subject2",
        "subject3",
        "subject4",
        "subject5",
        "percentage"
    ]

    df[numeric_columns] = (
        df[numeric_columns]
        .apply(pd.to_numeric, errors="coerce")
    )

    df[numeric_columns] = (
        df[numeric_columns]
        .fillna(df[numeric_columns].mean())
    )

    df = df.drop_duplicates()

    min_value = df["percentage"].min()
    max_value = df["percentage"].max()

    if max_value != min_value:

        df["normalized_percentage"] = (
            (df["percentage"] - min_value)
            /
            (max_value - min_value)
        )

    else:

        df["normalized_percentage"] = 0

    os.makedirs("static", exist_ok=True)

    chart_path = os.path.join(
        "static",
        "performance_chart.png"
    )

    plt.figure(figsize=(9, 5))

    plt.bar(
        df["name"],
        df["percentage"]
    )

    plt.title("Student Performance")
    plt.xlabel("Students")
    plt.ylabel("Percentage")

    plt.xticks(
        rotation=30,
        ha="right"
    )

    plt.ylim(0, 100)

    plt.tight_layout()
    plt.savefig(chart_path)
    plt.close()

    correlation_path = os.path.join(
        "static",
        "subject_analysis.png"
    )

    plt.figure(figsize=(8, 6))

    sns.heatmap(
        df[
            [
                "subject1",
                "subject2",
                "subject3",
                "subject4",
                "subject5"
            ]
        ].corr(),
        annot=True,
        fmt=".2f"
    )

    plt.title("Subject Correlation Analysis")

    plt.tight_layout()
    plt.savefig(correlation_path)
    plt.close()

    univariate_mean = round(
        float(df["subject1"].mean()),
        2
    )

    univariate_median = round(
        float(df["subject1"].median()),
        2
    )

    mode_values = df["subject1"].mode()

    univariate_mode = (
        mode_values.iloc[0]
        if not mode_values.empty
        else 0
    )

    if len(df) > 1:

        correlation = round(
            float(
                df[
                    ["subject1", "subject2"]
                ].corr().iloc[0, 1]
            ),
            2
        )

    else:

        correlation = 0

    return render_template(
        "analytics.html",
        total_students=total_students,
        average=average,
        highest=highest,
        lowest=lowest,
        pass_count=pass_count,
        fail_count=fail_count,
        std_dev=std_dev,
        variance=variance,
        skewness=skewness,
        kurtosis=kurtosis,
        confidence_low=confidence_low,
        confidence_high=confidence_high,
        pass_probability=pass_probability,
        sample_mean=sample_mean,
        sample_size=sample_size,
        t_stat=t_stat,
        p_value=p_value,
        t_test_result=t_test_result,
        univariate_mean=univariate_mean,
        univariate_median=univariate_median,
        univariate_mode=univariate_mode,
        correlation=correlation,
        students_data=df.to_dict("records")
    )


# =========================================================
# BEAUTIFULSOUP
# =========================================================

@app.route("/scrape")
def scrape():

    html = """
    <html>
        <body>

            <div class="student">
                <span class="roll">101</span>
                <span class="name">Rahul</span>
                <span class="branch">Computer</span>
            </div>

            <div class="student">
                <span class="roll">102</span>
                <span class="name">Priya</span>
                <span class="branch">Computer</span>
            </div>

        </body>
    </html>
    """

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    scraped_students = []

    for student in soup.select(".student"):

        scraped_students.append({

            "roll_no":
                student.select_one(
                    ".roll"
                ).text,

            "name":
                student.select_one(
                    ".name"
                ).text,

            "branch":
                student.select_one(
                    ".branch"
                ).text
        })

    return render_template(
        "students.html",
        students=scraped_students,
        search="",
        scraped=True
    )


# =========================================================
# MACHINE LEARNING
# =========================================================

@app.route(
    "/prediction",
    methods=["GET", "POST"]
)
def prediction():

    prediction_result = None
    accuracy = None

    connection = get_db_connection()

    data = connection.execute("""
        SELECT
            subject1,
            subject2,
            subject3,
            subject4,
            subject5,
            attendance,
            result
        FROM marks
        JOIN students
        ON marks.student_id = students.id
    """).fetchall()

    connection.close()

    if len(data) >= 5:

        df = pd.DataFrame(
            [dict(row) for row in data]
        )

        df["pass"] = (
            df["result"] == "PASS"
        ).astype(int)

        features = [
            "subject1",
            "subject2",
            "subject3",
            "subject4",
            "subject5",
            "attendance"
        ]

        X = df[features]
        y = df["pass"]

        if len(y.unique()) >= 2:

            X_train, X_test, y_train, y_test = (
                train_test_split(
                    X,
                    y,
                    test_size=0.2,
                    random_state=42,
                    stratify=y
                )
            )

            model = DecisionTreeClassifier(
                random_state=42
            )

            model.fit(
                X_train,
                y_train
            )

            predictions = model.predict(
                X_test
            )

            accuracy = round(
                accuracy_score(
                    y_test,
                    predictions
                ) * 100,
                2
            )

            os.makedirs(
                "data",
                exist_ok=True
            )

            with open(
                "data/student_model.pkl",
                "wb"
            ) as file:

                pickle.dump(
                    model,
                    file
                )

            if request.method == "POST":

                input_data = [[

                    float(
                        request.form["subject1"]
                    ),

                    float(
                        request.form["subject2"]
                    ),

                    float(
                        request.form["subject3"]
                    ),

                    float(
                        request.form["subject4"]
                    ),

                    float(
                        request.form["subject5"]
                    ),

                    float(
                        request.form["attendance"]
                    )
                ]]

                result = model.predict(
                    input_data
                )[0]

                prediction_result = (
                    "PASS"
                    if result == 1
                    else "FAIL"
                )

    return render_template(
        "prediction.html",
        prediction_result=prediction_result,
        accuracy=accuracy
    )


# =========================================================
# FLASK TECHNOLOGY / ARCHITECTURE
# =========================================================

@app.route("/flask-info")
def flask_info():

    return render_template(
        "flask_info.html"
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    app.run(debug=True)