# Part of RMARaceBench, under BSD-3-Clause License
# See https://github.com/RWTH-HPC/RMARaceBench/LICENSE for license information.
# SPDX-License-Identifier: BSD-3-Clause

import pandas
import argparse

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('results_file', metavar='results_file',
                    help='Results from test runs in CSV format')
parser.add_argument('-o', dest='output_file',
                    help='Results from test runs in CSV format')

disciplines = ['conflict', 'sync', 'atomic']
tools = ['MUST', 'PARCOACH-static', 'PARCOACH-dynamic']

def guarded_div(dividend, divisor):
    if divisor == 0:
        return 0
    else:
        return dividend / divisor

def get_tool_statistics(data, tool):
    if len(data) == 0:
        return
    results = data.value_counts().to_dict()
    #print(results)

    tp = results['TP'] if 'TP' in results else 0
    fp = results['FP'] if 'FP' in results else 0
    tn = results['TN'] if 'TN' in results else 0
    fn = results['FN'] if 'FN' in results else 0
    to = results['TO'] if 'TO' in results else 0

    total = tp + fp + tn + fn
    p = tp + fn
    n = fp + tn

    precision = guarded_div(tp, (tp + fp))
    recall = guarded_div(tp, (tp + fn))
    specificity = guarded_div(tn, n)
    accuracy = guarded_div((tp + tn), total)

    out = {
        (tool, 'TP'): tp,
        (tool, 'FP'): fp,
        (tool, 'TN'): tn,
        (tool, 'FN'): fn,
        (tool, 'TO'): to,
        (tool, 'P'): precision,
        (tool, 'R'): recall,
        (tool, 'A'): accuracy
    }

    return out

def get_derived_metrics(data, tool):
    if len(data) == 0:
        return
    results = data.value_counts().to_dict()
    #print(results)
    #print(results)
    #print(data)
    tp = results['TP'] if 'TP' in results else 0
    fp = results['FP'] if 'FP' in results else 0
    tn = results['TN'] if 'TN' in results else 0
    fn = results['FN'] if 'FN' in results else 0
    to = results['TO'] if 'TO' in results else 0

    total = tp + fp + tn + fn
    p = tp + fn
    n = fp + tn

    precision = guarded_div(tp, (tp + fp))
    recall = guarded_div(tp, (tp + fn))
    specificity = guarded_div(tn, n)
    accuracy = guarded_div((tp + tn), total)

    out = {
       'Precision': precision,
       'Recall': recall,
       'Accuracy': accuracy
    }

    return out

def get_tool_table(df, tool):
    return pandas.DataFrame.from_dict({
            'Conflict': get_tool_statistics(df.loc[df['discipline'] == "conflict"][tool], tool),
            'Sync': get_tool_statistics(df.loc[df['discipline'] == "sync"][tool], tool),
            'Atomic': get_tool_statistics(df.loc[df['discipline'] == "atomic"][tool], tool),
            'Hybrid': get_tool_statistics(df.loc[df['discipline'] == "hybrid"][tool], tool),
            'Total': get_tool_statistics(df[tool], tool),
            },
            orient='index')

def get_discipline_statistics(df):
    retmust = get_tool_table(df, "MUST")
    retparcoachs = get_tool_table(df, "PARCOACH-dynamic")
    retparcoachd = get_tool_table(df, "PARCOACH-static")
    return pandas.concat([retmust, retparcoachs, retparcoachd], axis=1)

def get_statistics(df):
    return pandas.DataFrame([get_tool_statistics(df['MUST'], "MUST"), 
                             get_tool_statistics(df['PARCOACH-dynamic'], "PARCOACH-dynamic"),
                             get_tool_statistics(df['PARCOACH-static'], "PARCOACH-static")])


args = parser.parse_args()

df = pandas.read_csv(args.results_file, index_col=0)

print(df.to_string())
print(
    pandas.DataFrame.from_dict({tool : get_derived_metrics(df[tool], tool) for tool in ['MUST', 'PARCOACH-dynamic', 'PARCOACH-static']} ,orient='index').to_string(float_format="%.3f" )
)

print(get_discipline_statistics(df).to_string(float_format="%.2f"))

# LaTeX tables
# with pandas.option_context("max_colwidth", 1000):
#     print(df.drop(columns=['discipline']).to_latex(index_names=False))
#     print(get_discipline_statistics(df).to_latex(float_format="%.2f"))