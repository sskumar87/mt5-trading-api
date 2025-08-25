import pandas as pd

def merge_ranges(range_df):
    range_df['time'] = pd.to_datetime(range_df['time'], format='%d-%m-%Y %H:%M')
    range_df['end_time'] = pd.to_datetime(range_df['end_time'], format='%d-%m-%Y %H:%M')
    merged = []
    group_rows = [range_df.iloc[0]]

    for idx in range(1, len(range_df)):
        row = range_df.iloc[idx]
        last = group_rows[-1]
        if last['time'] <= row['time'] <= last['end_time']:
            group_rows.append(row)
        else:
            group_df = pd.DataFrame(group_rows)
            merged_row = group_rows[0].copy()
            merged_row['end_time'] = group_df['end_time'].max()
            merged_row['top'] = group_df['top'].max()
            merged_row['bottom'] = group_df['bottom'].min()
            merged_row['duration_bars'] = group_df['duration_bars'].sum()
            merged_row['range_value'] = round(merged_row['top'] - merged_row['bottom'], 2)
            merged_row['mid'] = round((merged_row['top'] + merged_row['bottom']) / 2, 2)
            merged.append(merged_row)
            group_rows = [row]
    # Handle last group
    group_df = pd.DataFrame(group_rows)
    merged_row = group_rows[0].copy()
    merged_row['end_time'] = group_df['end_time'].max()
    merged_row['top'] = group_df['top'].max()
    merged_row['bottom'] = group_df['bottom'].min()
    merged_row['duration_bars'] = group_df['duration_bars'].sum()
    merged_row['range_value'] = round(merged_row['top'] - merged_row['bottom'], 2)
    merged_row['mid'] = round((merged_row['top'] + merged_row['bottom']) / 2, 2)
    merged.append(merged_row)

    result = pd.DataFrame(merged)
    result['time'] = result['time'].dt.strftime('%d-%m-%Y %H:%M')
    result['end_time'] = result['end_time'].dt.strftime('%d-%m-%Y %H:%M')
    result = result.iloc[::-1]
    result.to_csv(f"data/{range_df['symbol'].iloc[0]}_merged_body_ranges.csv", index=False, mode='w')
    return result



# df = pd.read_csv('data/body_ranges.csv')
# merged_df = merge_ranges(df)
# print(merged_df)
#
# # Print merged DataFrame
# print(merged_df)