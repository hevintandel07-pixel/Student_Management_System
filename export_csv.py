import csv
import os


def export_students_to_csv(
    students,
    filename="data/students.csv"
):

    os.makedirs("data", exist_ok=True)

    with open(
        filename,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "Roll No",
            "Name",
            "Branch",
            "Semester",
            "Email",
            "Mobile",
            "Attendance",
            "Club",
            "Permissions"
        ])

        for student in students:

            writer.writerow([
                student["roll_no"],
                student["name"],
                student["branch"],
                student["semester"],
                student["email"],
                student["mobile"],
                student["attendance"],
                student["club"],
                student["permissions"]
            ])

    return filename