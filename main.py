"""
Student Attendance & Performance Tracker
PS No. 44 | Python 3

CSV columns: Name, Classes_Held, Classes_Attended, Marks
At Risk: attendance below 75% OR marks below 40.
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


REQUIRED_COLUMNS = ["Name", "Classes_Held", "Classes_Attended", "Marks"]
ATTENDANCE_LIMIT = 75
MARKS_LIMIT = 40


def load_and_clean_csv(file_path):
    """Load a CSV file, validate records, and return clean data + skipped rows."""
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"CSV file not found: {path}")

    raw_df = pd.read_csv(path)
    raw_df.columns = raw_df.columns.str.strip()

    missing = [column for column in REQUIRED_COLUMNS if column not in raw_df.columns]
    if missing:
        raise ValueError("Missing required CSV column(s): " + ", ".join(missing))

    # Keep only the required columns and normalize text.
    df = raw_df[REQUIRED_COLUMNS].copy()
    df["Name"] = df["Name"].astype("string").str.strip()

    # Convert numeric columns; non-numeric values become NaN and are rejected below.
    for column in ["Classes_Held", "Classes_Attended", "Marks"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    valid_rows = []
    skipped_rows = []

    for row_number, row in df.iterrows():
        reasons = []

        if pd.isna(row["Name"]) or not str(row["Name"]).strip():
            reasons.append("missing student name")

        numeric_values = ["Classes_Held", "Classes_Attended", "Marks"]
        if any(pd.isna(row[column]) for column in numeric_values):
            reasons.append("invalid or missing numeric value")
        else:
            held = float(row["Classes_Held"])
            attended = float(row["Classes_Attended"])
            marks = float(row["Marks"])

            if held <= 0:
                reasons.append("classes held must be greater than 0")
            if attended < 0:
                reasons.append("classes attended cannot be negative")
            if attended > held:
                reasons.append(f"attended ({attended:g}) cannot exceed held ({held:g})")
            if not 0 <= marks <= 100:
                reasons.append("marks must be between 0 and 100")

        if reasons:
            skipped_rows.append({
                "CSV Row": row_number + 2,
                "Name": str(row["Name"]) if not pd.isna(row["Name"]) else "(blank)",
                "Reason": "; ".join(reasons)
            })
        else:
            valid_rows.append(row)

    clean_df = pd.DataFrame(valid_rows, columns=REQUIRED_COLUMNS)
    if not clean_df.empty:
        clean_df["Classes_Held"] = clean_df["Classes_Held"].astype(int)
        clean_df["Classes_Attended"] = clean_df["Classes_Attended"].astype(int)
        clean_df["Marks"] = clean_df["Marks"].astype(float)
        clean_df["Attendance_Percentage"] = (
            clean_df["Classes_Attended"] / clean_df["Classes_Held"] * 100
        ).round(2)

    return clean_df, skipped_rows


def create_student_dictionary(row):
    """Represent one student's information using a Python dictionary."""
    attendance = float(row["Attendance_Percentage"])
    marks = float(row["Marks"])
    at_risk = attendance < ATTENDANCE_LIMIT or marks < MARKS_LIMIT

    return {
        "name": str(row["Name"]),
        "attendance": attendance,
        "marks": marks,
        "status": "At Risk" if at_risk else "OK",
        "risk_reason": get_risk_reason(attendance, marks)
    }


def get_risk_reason(attendance, marks):
    reasons = []
    if attendance < ATTENDANCE_LIMIT:
        reasons.append("attendance below 75%")
    if marks < MARKS_LIMIT:
        reasons.append("marks below 40")
    return ", ".join(reasons) if reasons else "None"


def analyse_students(df):
    """Use Pandas columns and boolean filtering to analyse students."""
    if df.empty:
        return [], None

    # Boolean filtering: a student is at risk if either condition is true.
    risk_mask = (
        (df["Attendance_Percentage"] < ATTENDANCE_LIMIT)
        | (df["Marks"] < MARKS_LIMIT)
    )
    at_risk_df = df[risk_mask]

    # Dictionaries store the final student-wise information.
    student_records = [create_student_dictionary(row) for _, row in df.iterrows()]
    risk_names = at_risk_df["Name"].astype(str).tolist()

    summary = {
        "total_students": len(df),
        "average_attendance": round(float(df["Attendance_Percentage"].mean()), 2),
        "average_marks": round(float(df["Marks"].mean()), 2),
        "at_risk_count": len(at_risk_df),
        "at_risk_names": risk_names
    }
    return student_records, summary


def show_report(df, skipped_rows):
    """Print attendance, marks, risk status, averages, and skipped rows."""
    records, summary = analyse_students(df)

    print("\n" + "=" * 68)
    print("             STUDENT ATTENDANCE & PERFORMANCE REPORT")
    print("=" * 68)

    if summary is None:
        print("No valid data to analyse.")
        print_skipped_rows(skipped_rows)
        return

    print(f"{'Name':<18}{'Attendance':>14}{'Marks':>12}{'Status':>14}")
    print("-" * 58)
    for student in records:
        print(
            f"{student['name']:<18}"
            f"{student['attendance']:>13.2f}%"
            f"{student['marks']:>12.2f}"
            f"{student['status']:>14}"
        )
        if student["status"] == "At Risk":
            print(f"   Reason: {student['risk_reason']}")

    print("-" * 58)
    print(f"Average attendance : {summary['average_attendance']:.2f}%")
    print(f"Average marks      : {summary['average_marks']:.2f}")
    print(f"At Risk students   : {summary['at_risk_count']}")
    if summary["at_risk_names"]:
        print("At Risk names      : " + ", ".join(summary["at_risk_names"]))
    else:
        print("At Risk names      : None")

    print_skipped_rows(skipped_rows)


def print_skipped_rows(skipped_rows):
    if skipped_rows:
        print("\nInvalid rows skipped:")
        for item in skipped_rows:
            print(
                f"  Row {item['CSV Row']} ({item['Name']}): {item['Reason']}"
            )


def show_charts(df):
    """Display a bar chart and a scatter chart using Matplotlib."""
    if df.empty:
        print("No valid data to analyse. Charts cannot be displayed.")
        return

    # Chart 1: Student attendance and marks (bar chart).
    chart_df = df.set_index("Name")[["Attendance_Percentage", "Marks"]]
    chart_df.plot(kind="bar", figsize=(10, 5), width=0.75)
    plt.title("Student Attendance and Marks")
    plt.xlabel("Students")
    plt.ylabel("Percentage / Marks")
    plt.xticks(rotation=0)
    plt.legend(["Attendance (%)", "Marks"])
    plt.tight_layout()
    plt.savefig("attendance_marks_bar_chart.png", dpi=150)
    plt.show()
    plt.close()

    # Chart 2: Attendance vs Marks (scatter chart).
    plt.figure(figsize=(8, 5))
    plt.scatter(
        df["Attendance_Percentage"],
        df["Marks"],
        s=90,
        alpha=0.8,
        label="Students"
    )
    for _, row in df.iterrows():
        plt.annotate(
            str(row["Name"]),
            (row["Attendance_Percentage"], row["Marks"]),
            xytext=(5, 5),
            textcoords="offset points"
        )
    plt.axvline(ATTENDANCE_LIMIT, linestyle="--", label="75% attendance limit")
    plt.axhline(MARKS_LIMIT, linestyle=":", label="40 marks limit")
    plt.title("Attendance vs Marks")
    plt.xlabel("Attendance Percentage (%)")
    plt.ylabel("Marks (out of 100)")
    plt.legend()
    plt.grid(True, alpha=0.25)
    plt.tight_layout()
    plt.savefig("attendance_vs_marks_scatter_chart.png", dpi=150)
    plt.show()
    plt.close()

    print("Charts saved as:")
    print("  attendance_marks_bar_chart.png")
    print("  attendance_vs_marks_scatter_chart.png")


def main():
    print("=" * 58)
    print("       STUDENT ATTENDANCE & PERFORMANCE TRACKER")
    print("=" * 58)

    file_path = input("Enter CSV file path [students.csv]: ").strip()
    if not file_path:
        file_path = "students.csv"

    try:
        students_df, skipped_rows = load_and_clean_csv(file_path)
    except FileNotFoundError as error:
        print(f"\nError: {error}")
        print("Keep students.csv in the same folder or enter its full path.")
        return
    except (ValueError, pd.errors.ParserError, UnicodeDecodeError) as error:
        print(f"\nUnable to process CSV: {error}")
        return
    except Exception as error:
        print(f"\nUnexpected error: {error}")
        return

    print(f"\nValid students loaded: {len(students_df)}")
    print(f"Invalid rows skipped : {len(skipped_rows)}")

    while True:
        print("\n--------------- MAIN MENU ---------------")
        print("1. Report")
        print("2. Visualisation (Bar chart and Scatter chart)")
        print("3. Exit")
        choice = input("Enter your choice (1-3): ").strip()

        if choice == "1":
            show_report(students_df, skipped_rows)
        elif choice == "2":
            show_charts(students_df)
        elif choice == "3":
            print("Thank you for using Student Attendance & Performance Tracker.")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")


if __name__ == "__main__":
    main()
