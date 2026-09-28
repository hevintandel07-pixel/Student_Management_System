def calculate_grade(percentage):

    if percentage >= 90:
        return "A+"
    elif percentage >= 80:
        return "A"
    elif percentage >= 70:
        return "B"
    elif percentage >= 60:
        return "C"
    elif percentage >= 50:
        return "D"
    else:
        return "F"


def calculate_result(percentage):

    if percentage >= 40:
        return "PASS"

    return "FAIL"


def validate_marks(marks):

    for mark in marks:

        if mark < 0 or mark > 100:
            raise ValueError(
                "Marks must be between 0 and 100."
            )

    return True


def calculate_attendance(total_days, present_days):

    if total_days <= 0:
        raise ValueError(
            "Total days must be greater than 0."
        )

    if present_days < 0:
        raise ValueError(
            "Present days cannot be negative."
        )

    if present_days > total_days:
        raise ValueError(
            "Present days cannot be greater than total days."
        )

    return round(
        (present_days / total_days) * 100,
        2
    )