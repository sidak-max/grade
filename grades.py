def calculate_grade(score):
    """
    Convert a numerical score (0-100) into a letter grade.

    A: 90-100
    B: 80-89
    C: 70-79
    D: 60-69
    F: 0-59
    """
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"


def main():
    """Demonstrate the calculate_grade function."""
    score = float(input("Enter the score (0-100): "))
    print(f"Grade: {calculate_grade(score)}")


if __name__ == "__main__":
    main()
