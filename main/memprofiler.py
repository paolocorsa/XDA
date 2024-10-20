import tracemalloc
import warnings
import numpy as np
import pandas as pd
from colorama import Fore, Style
from sklearn.model_selection import train_test_split
from CustomPlanner import CustomPlanner
from SHAPCustomPlanner import SHAPCustomPlanner
from FICustomPlanner import FICustomPlanner
from FITEST import FitestPlanner
from NSGA3Planner import NSGA3Planner
from model.ModelConstructor import constructModel
from RandomCustomPlanner import RandomPlanner
from util import vecPredictProba


def profile_memory(func, *args, **kwargs):
    tracemalloc.start()
    func(*args, **kwargs)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(peak / (1024 ** 2))
    return peak / (1024 ** 2)


def successScore(adaptation, reqClassifiers, targetSuccessProba):
    return np.sum(vecPredictProba(reqClassifiers, [adaptation])[0] - targetSuccessProba)


def normalizeAdaptation(adaptation, domains, nFeatures):
    new_adaptation = []
    for index in range(nFeatures):
        new_adaptation.append(((adaptation[index] - domains[index][0]) / (domains[index][1] - domains[index][0])) * 100)

    return new_adaptation

# provided optimization score function (based on the ideal controllable feature assignment)
def optimizationScore(adaptation, domains, n_controllableFeatures):
    adaptation = normalizeAdaptation(adaptation, domains, n_controllableFeatures)
    #return 400 - (100 - adaptation[0] + adaptation[1] + adaptation[2] + adaptation[3]) #robot
    #return 300 - (100 - adaptation[0] + 100 - adaptation[1] + adaptation[2]) #uav
    #return 100 - (100 - adaptation[0]) #drive
    #return 800 - (100 - adaptation[0] + adaptation[1] + adaptation[2] + adaptation[3] +
     #+ 100 - adaptation[4] + adaptation[5] + adaptation[6] + 100 - adaptation[7]) #robotDouble
    #return 600 - (100 - adaptation[0] + 100 - adaptation[1] + adaptation[2] + 100 - adaptation[3] +
     #+ 100 - adaptation[4] + 100 - adaptation[5]) #uavDouble
    return 200 - (100 - adaptation[0] + adaptation[1]) #driveDouble


def main():
    warnings.filterwarnings("ignore")

    ds = pd.read_csv('../datasets/drivev3.csv')
    featureNames = ['car_speed','p_x','p_y','orientation','weather','road_shape']
    controllableFeaturesNames = featureNames[0:2]
    externalFeaturesNames = featureNames[2:6]
    controllableFeatureIndices = [0, 1]

    # for simplicity, we consider all the ideal points to be 0 or 100
    # so that we just need to consider ideal directions instead
    # -1 => minimize, 1 => maximize
    optimizationDirections = [1, -1]

    reqs = ['req_0','req_1','req_2']

    n_reqs = len(reqs)
    n_neighbors = 10
    n_startingSolutions = 10
    n_controllableFeatures = len(controllableFeaturesNames)

    targetConfidence = np.full((1, n_reqs), 0.8)[0]

    # split the dataset
    X = ds.loc[:, featureNames]
    y = ds.loc[:, reqs]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.4, random_state=42
    )

    models = []
    for req in reqs:
        print(Fore.RED + "Requirement: " + req + "\n" + Style.RESET_ALL)
        """
        ds_req = pd.read_csv(f'bilanciato_{req}.csv')
        X_req = ds_req.loc[:, featureNames]
        y_req = ds_req.loc[:, req]
        X_req_train, X_req_test, y_req_train, y_req_test = train_test_split(
            X_req, y_req, test_size=0.4, random_state=42
        )
        """
        models.append(constructModel(X_train.values,
                                     X_test.values,
                                     np.ravel(y_train.loc[:, req]),
                                     np.ravel(y_test.loc[:, req])))
        print("=" * 100)

    controllableFeatureDomains = np.array([[5.0, 50.0], [0.0, 10.0]])
    discreteIndices = []

    customPlanner = CustomPlanner(X_train, n_neighbors, n_startingSolutions, models, targetConfidence,
                                  controllableFeaturesNames, controllableFeatureIndices, controllableFeatureDomains,
                                  optimizationDirections, optimizationScore, 1, "../explainability_plots")

    nsga3Planner = NSGA3Planner(models, targetConfidence, controllableFeatureIndices, controllableFeatureDomains,
                                optimizationDirections, successScore, optimizationScore)

    SHAPcustomPlanner = SHAPCustomPlanner(X_train, n_neighbors, n_startingSolutions, models, targetConfidence,
                                          controllableFeaturesNames, controllableFeatureIndices,
                                          controllableFeatureDomains,
                                          optimizationDirections, optimizationScore, 1, "../explainability_plots")

    FIcustomPlanner = FICustomPlanner(X_train, y_train, n_neighbors, n_startingSolutions, models, targetConfidence,
                                      controllableFeaturesNames, controllableFeatureIndices, controllableFeatureDomains,
                                      optimizationDirections, optimizationScore, 1, "../explainability_plots")

    pop_size = nsga3Planner.algorithm.pop_size

    Fitest_planner = FitestPlanner(models, targetConfidence,
                                   controllableFeatureIndices, controllableFeatureDomains, optimizationScore,
                                   successScore, pop_size, discreteIndices, 3,
                                   [0.8, 0.8, 0.8])

    Random_Planner = RandomPlanner(controllableFeatureIndices, controllableFeatureDomains, discreteIndices, models,
                                   optimizationScore)

    data_time = {
        'PDPTime': [customPlanner.PDPtime],
        'SPDPTime': [customPlanner.SPDPtime],
        'SHAPTime': [SHAPcustomPlanner.rankingTime],
        'FITime': [FIcustomPlanner.rankingTime]
    }

    data_memory = {
        'CustomMemory': [],
        'SHAPMemory': [],
        'FIMemory': [],
        'FitestMemory': [],
        'RandomMemory': [],
        'NSGA3Memory': [],
    }

    testNum = 200
    for k in range(1, testNum + 1):
        rowIndex = k - 1
        row = X_test.iloc[rowIndex, :].to_numpy()

        print(Fore.BLUE + "Test " + str(k) + ":" + Style.RESET_ALL)
        print("Row " + str(rowIndex) + ":\n" + str(row))
        print("-" * 100)

        customMemUsage = profile_memory(customPlanner.findAdaptation, row)
        SHAPcustomMemUsage = profile_memory(SHAPcustomPlanner.findAdaptation, row)
        FICustomMemUsage = profile_memory(FIcustomPlanner.findAdaptation, row)
        FitestMemUsage = profile_memory(Fitest_planner.run_search, row)
        RandomMemUsage = profile_memory(Random_Planner.findAdaptation, row)
        externalFeatures = row[n_controllableFeatures:]
        nsga3MemUsage = profile_memory(nsga3Planner.findAdaptation, externalFeatures)

        data_memory['CustomMemory'].append(customMemUsage)
        data_memory['SHAPMemory'].append(SHAPcustomMemUsage)
        data_memory['FIMemory'].append(FICustomMemUsage)
        data_memory['FitestMemory'].append(FitestMemUsage)
        data_memory['RandomMemory'].append(RandomMemUsage)
        data_memory['NSGA3Memory'].append(nsga3MemUsage)

        print("-" * 100)

    df_memory = pd.DataFrame(data_memory)
    df_time = pd.DataFrame(data_time)

    path = "../results/"

    df_memory.to_csv(path + "/memory_results.csv", index=False)
    df_time.to_csv(path + "/time_results.csv", index=False)


#print(df_memory)
#print(df_time)


if __name__ == '__main__':
    main()
