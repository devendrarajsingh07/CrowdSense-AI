import csv

def get_analytics():

    try:

        people_values = []

        with open(
            "data/crowd_history.csv",
            "r"
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:

                people_values.append(
                    int(row["People"])
                )

        if len(people_values) == 0:

            return {
                "peak": 0,
                "average": 0,
                "records": 0
            }

        peak = max(people_values)

        average = round(
            sum(people_values)
            /
            len(people_values),
            2
        )

        records = len(
            people_values
        )

        return {

            "peak": peak,
            "average": average,
            "records": records

        }

    except:

        return {

            "peak": 0,
            "average": 0,
            "records": 0

        }