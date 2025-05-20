def get_options_dropdown(table, column):
    sorted_values = sorted(table[column].dropna().unique())
    return [{"label": x, "value": x} for x in sorted_values]