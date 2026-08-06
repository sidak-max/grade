def calculate_grade(scores):
    """
    Calculate the average of a list of scores (0-100) and return the
    corresponding letter grade.

    A: 90-100
    B: 80-89
    C: 70-79
    D: 60-69
    F: 0-59
    """
    if not scores:
        raise ValueError("scores list cannot be empty")

    average = sum(scores) / len(scores)

    if average >= 90:
        return "A"
    elif average >= 80:
        return "B"
    elif average >= 70:
        return "C"
    elif average >= 60:
        return "D"
    else:
        return "F"


def main():
    """Demonstrate the calculate_grade function with an average."""
    raw = input("Enter scores separated by spaces (e.g. 90 85 78): ")
    scores = [float(token) for token in raw.split()]
    print(f"Average grade: {calculate_grade(scores)}")


if __name__ == "__main__":
    main()
