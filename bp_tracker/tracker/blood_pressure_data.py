# Blood pressure data based on ranges of
# weight (lbs) , height (ft), and age (years)
blood_pressure_levels = {
    # Test structure
    'default': {'systolic': [90, 120], 'diastolic': [60, 80]},
    (20, 30): {
        (100, 200): {
            (5.0, 6.5): {'systolic': [110, 130], 'diastolic': [70, 90]}
        }
    },
    (30, 40): {
        (150, 250): {
            (5.5, 7.0): {'systolic': [115, 135], 'diastolic': [75, 95]}
        }
    },
}

def get_blood_pressure_range(weight, height, age):
    for age_range, weight_ranges in blood_pressure_levels.items():
        if age_range == 'default':
            continue
        if age_range[0] <= age <= age_range[1]:
            for weight_range, height_ranges in weight_ranges.items():
                if weight_range[0] <= weight <= weight_range[1]:
                    for height_range, bp_values in height_ranges.items():
                        if height_range[0] <= height <= height_range[1]:
                            return bp_values
    return blood_pressure_levels['default']