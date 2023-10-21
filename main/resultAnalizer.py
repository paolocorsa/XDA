import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import ticker

from util import readFromCsv, evaluateAdaptations


def personalizedBoxPlot(data, name, columnNames=None, rotation=0, path=None):
    columns = data.columns
    nColumns = len(columns)
    fig = plt.figure()#plt.figure(figsize=(10, 10 * nColumns/2))
    ax1 = fig.add_subplot(111)#(nColumns, 1, 1)

    # Creating axes instance
    bp = ax1.boxplot(data, patch_artist=True,
                     notch='True', vert=True)

    colors = plt.cm.Spectral(np.linspace(.1, .9, 2))
    #colors = np.append(colors[0::2], colors[1::2], axis=0)
    c = np.copy(colors)
    for i in range(nColumns//2):
        c = np.append(c, colors, axis=0)

    colors = c

    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)

    # changing color and linewidth of
    # whiskers
    for whisker in bp['whiskers']:
        whisker.set(color='#8B008B',
                    linewidth=1.5,
                    linestyle=":")

    # changing color and linewidth of
    # caps
    for cap in bp['caps']:
        cap.set(color='#8B008B',
                linewidth=2)

    # changing color and linewidth of
    # medians
    for median in bp['medians']:
        median.set(color='red',
                   linewidth=3)

    # changing style of fliers
    for flier in bp['fliers']:
        flier.set(marker='D',
                  color='#e7298a',
                  alpha=0.5)

    # x-axis labels

    if columnNames is not None:
        ax1.xaxis.set_ticks(np.arange(1.5, len(columnNames) * 2, step=2), columnNames, rotation=rotation)
    else:
        plt.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)

    #legend
    box = ax1.get_position()
    ax1.set_position([box.x0, box.y0 + box.height * 0.1,
                     box.width, box.height * 0.9])
    ax1.legend([bp["boxes"][0], bp["boxes"][1]], ["nsga3", "custom"],
               ncol=2, loc='upper center', bbox_to_anchor=(0.5, -0.1))

    # Adding title
    plt.title(name)

    # Removing top axes and right axes
    # ticks
    ax1.get_xaxis().tick_bottom()
    ax1.get_yaxis().tick_left()

    """
    for i in range(int(nColumns/2)):
        i2 = i + int(nColumns/2)
        axn = fig.add_subplot(nColumns, 1, i + 2)
        subset = data[[columns[i], columns[i2]]]
        subset = subset.sort_values(columns[i2])
        subset = subset.reset_index(drop=True)
        # axn.title.set_text(columns[i] + ' | ' + columns[i + int(nColumns/2)])
        subset.plot(ax=axn, color=colors[[i, i2]])
    """

    if path is not None:
        plt.savefig(path + name)

    fig.show()

def personalizedBarChart(data, name, path=None):
    colors = plt.cm.Spectral(np.linspace(.1, .9, 2))
    # colors = np.append(colors[0::2], colors[1::2], axis=0)
    c = np.copy(colors)
    for i in range(len(data.values) // 2):
        c = np.append(c, colors, axis=0)

    colors = c

    data.plot.bar(title=name, color=colors)

    if len(data.index) > 1:
        plt.xticks(rotation=0)
    else:
        plt.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)

    if path is not None:
        plt.savefig(path + name)

    plt.show()

os.chdir(sys.path[0])
evaluate = False

pathToResults = '../results/1ss/allReqs/'

featureNames = ["cruise speed",
                    "image resolution",
                    "illuminance",
                    "controls responsiveness",
                    "power",
                    "smoke intensity",
                    "obstacle size",
                    "obstacle distance",
                    "firm obstacle"]

reqs = ["req_0", "req_1", "req_2", "req_3"]

# read dataframe from csv
results = readFromCsv(pathToResults + 'results.csv')
nReqs = len(results["nsga3_confidence"][0])
reqs = reqs[:nReqs]
targetConfidence = np.full((1, nReqs), 0.8)[0]

if evaluate:
    evaluateAdaptations(results, featureNames)

#read outcomes from csv
customOutcomes = pd.read_csv(pathToResults + 'customDataset.csv')
nsga3Outcomes = pd.read_csv(pathToResults + 'nsga3Dataset.csv')

#build indices arrays
nsga3ConfidenceNames = ['nsga3_confidence_' + req for req in reqs]
nsga3OutcomeNames = ['nsga3_outcome_' + req for req in reqs]
customConfidenceNames = ['custom_confidence_' + req for req in reqs]
customOutcomeNames = ['custom_outcome_' + req for req in reqs]

#outcomes dataframe
outcomes = pd.concat([nsga3Outcomes[reqs], customOutcomes[reqs]], axis=1)
outcomes.columns = np.append(nsga3OutcomeNames, customOutcomeNames)
outcomes = outcomes[list(sum(zip(nsga3OutcomeNames, customOutcomeNames), ()))]

# decompose arrays columns into single values columns
nsga3Confidences = pd.DataFrame(results['nsga3_confidence'].to_list(),
                                columns=nsga3ConfidenceNames)
customConfidences = pd.DataFrame(results['custom_confidence'].to_list(),
                                 columns=customConfidenceNames)

# select sub-dataframes to plot
confidences = pd.concat([nsga3Confidences, customConfidences], axis=1)
confidences = confidences[list(sum(zip(nsga3Confidences.columns, customConfidences.columns), ()))]
scores = results[["nsga3_score", "custom_score"]]
times = results[["nsga3_time", "custom_time"]]

#plots
plotPath = pathToResults + 'plots/'
if not os.path.exists(plotPath):
    os.makedirs(plotPath)

personalizedBoxPlot(confidences, "Confidences comparison", reqs, path=plotPath)
personalizedBoxPlot(scores, "Score comparison", path=plotPath)
personalizedBoxPlot(times, "Execution time comparison", path=plotPath)

#mapping
bothSuccesful = pd.concat([confidences[nsga3ConfidenceNames] > targetConfidence, confidences[customConfidenceNames] > targetConfidence], axis=1).all(axis=1)
onlyNsga3Succesful = pd.concat([confidences[nsga3ConfidenceNames] > targetConfidence, (confidences[customConfidenceNames] <= targetConfidence).any(axis=1)], axis=1).all(axis=1)
onlyCustomSuccesful = pd.concat([(confidences[nsga3ConfidenceNames] <= targetConfidence).any(axis=1), confidences[customConfidenceNames] > targetConfidence], axis=1).all(axis=1)
noneSuccesful = pd.concat([(confidences[nsga3ConfidenceNames] <= targetConfidence).any(axis=1), (confidences[customConfidenceNames] <= targetConfidence).any(axis=1)], axis=1).all(axis=1)

#results
averages = pd.concat([outcomes[bothSuccesful].mean(),
                      outcomes[onlyNsga3Succesful].mean(),
                      outcomes[onlyCustomSuccesful].mean(),
                      outcomes[noneSuccesful].mean()], axis=1)
averages.columns = ['both', 'nsga3_only', 'custom_only', 'none']

print(str(averages) + "\n")

#predicted successful adaptations
nsga3PredictedSuccessful = (confidences[nsga3ConfidenceNames] > targetConfidence).all(axis=1)
customPredictedSuccessful = (confidences[customConfidenceNames] > targetConfidence).all(axis=1)

print("nsga3 predicted success rate: " + "{:.2%}".format(nsga3PredictedSuccessful.sum() / nsga3PredictedSuccessful.shape[0]))
print(str(nsga3Confidences.mean()) + "\n")
print("custom predicted success rate:  " + "{:.2%}".format(customPredictedSuccessful.sum() / customPredictedSuccessful.shape[0]))
print(str(customConfidences.mean()) + "\n")

print("nsga3 predicted success mean probas: \n" + str(nsga3Confidences[nsga3PredictedSuccessful].mean()) + '\n')
print("custom predicted success mean probas: \n" + str(customConfidences[customPredictedSuccessful].mean()) + '\n')

#predicted successful adaptations
nsga3Successful = outcomes[nsga3OutcomeNames].all(axis=1)
customSuccessful = outcomes[customOutcomeNames].all(axis=1)

nsga3SuccessRate = nsga3Successful.sum() / nsga3Successful.shape[0]
customSuccessRate = customSuccessful.sum() / customSuccessful.shape[0]

#outcomes analysis
print("nsga3 success rate: " + "{:.2%}".format(nsga3SuccessRate))
print(str(outcomes[nsga3OutcomeNames].mean()) + "\n")
print("custom success rate:  " + "{:.2%}".format(customSuccessRate))
print(str(outcomes[customOutcomeNames].mean()) + "\n")

successRate = pd.concat([outcomes[nsga3OutcomeNames].rename(columns=dict(zip(nsga3OutcomeNames, reqs))).mean(),
                        outcomes[customOutcomeNames].rename(columns=dict(zip(customOutcomeNames, reqs))).mean()], axis=1)
successRate.columns = ['nsga3', 'custom']

personalizedBarChart(successRate, "Success Rate", plotPath)