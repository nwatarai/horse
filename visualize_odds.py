import pandas as pd
import sys
import os
import datetime
import numpy as np
import seaborn as sns; sns.set()
sns.set(style="whitegrid")
import matplotlib.pyplot as plt
import argparse
import warnings
warnings.simplefilter('ignore', UserWarning)

def parser_setting():
    parser = argparse.ArgumentParser()
    parser.add_argument('csv',
                        action='store',
                        type=str,
                        help='csv')
    parser.add_argument('-r', '--ratio',
                        action='store_true',
                        dest="ratio",
                        help='Taking ratio')
    parser.set_defaults(ratio=False)
    args = parser.parse_args()
    return vars(args)

def string_to_date(string):
    return datetime.datetime.strptime(string, '%H:%M:%S')

def date_to_integer(timedelta):
    return timedelta.seconds

def date_difference(index):
    d_index = index.map(string_to_date)
    return (d_index - d_index[0]).map(date_to_integer)

def ratio(df):
    a = df.iloc[:, 1:]
    #b = df.iloc[:, :-1]
    b = np.transpose([df.mean(axis=1).values for i in range(df.shape[1] - 1)])
    ratio = a.values / b
    return pd.DataFrame(data=ratio, columns=df.columns[1:], index=df.index)

def main(args):
    df = pd.read_csv(args["csv"], header=0, index_col=0)
    approval = 1.0 / df.iloc[:, 1:]
    approval.columns = date_difference(approval.columns)
    if args["ratio"]:
        approval = ratio(approval)
    data = []
    columns = ["No.", "timepoint", "odds"]
    for i in approval.index:
        for j in approval.loc[i, :].index:
            data.append([i, j, approval.loc[i, j]])
    data_df = pd.DataFrame(data, columns=columns)
    p1 = sns.lineplot(x="timepoint", y="odds", hue="No.", data=data_df,
                palette=sns.color_palette("hls", df.shape[0]),  hue_order=approval.index)
    ex = data_df.loc[data_df["timepoint"] == data_df["timepoint"].max(), :]
    for i in ex.index:
        p1.text(ex.loc[i, "timepoint"], ex.loc[i, "odds"], ex.loc[i, "No."], fontsize=8)
    plt.legend(loc=3, frameon=True, edgecolor="black")
    plt.show()

if __name__ == '__main__':
    main(parser_setting())
