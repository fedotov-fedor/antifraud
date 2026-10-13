import pandas as pd


def find_nan_groups(df: pd.DataFrame) -> dict:
    nan_group = {}

    for col in df.columns:
        current_group = df[col].isna().sum()
        nan_group.setdefault(current_group, []).append(col)

    return nan_group


def find_correlated_groups(
    df: pd.DataFrame,
    columns: list,
    threshold: float = 0.75,
    method: str = "pearson",
    min_periods: int = 30,
) -> list[list]:
    correlation_matrix = df[columns].corr(
        method=method,
        min_periods=min_periods,
    ).abs()

    connections = correlation_matrix.gt(threshold).fillna(False)

    for column in columns:
        connections.loc[column, column] = False

    visited = set()
    groups = []
    column_positions = {
        column: position
        for position, column in enumerate(columns)
    }

    for start_column in columns:
        if start_column in visited:
            continue

        stack = [start_column]
        visited.add(start_column)
        current_group = []

        while stack:
            current_column = stack.pop()
            current_group.append(current_column)

            connected_columns = connections.columns[
                connections.loc[current_column]
            ]

            for connected_column in connected_columns:
                if connected_column not in visited:
                    visited.add(connected_column)
                    stack.append(connected_column)

        current_group.sort(key=column_positions.get)
        groups.append(current_group)

    return groups


def reduce_groups(df: pd.DataFrame, groups: list[list]) -> list:
    reduced_groups = []

    for group in groups:
        max_unique = 0
        best_element = group[0]

        for element in group:
            unique_elements = df[element].nunique()

            if unique_elements > max_unique:
                max_unique = unique_elements
                best_element = element

        reduced_groups.append(best_element)

    return reduced_groups
