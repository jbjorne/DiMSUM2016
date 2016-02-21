University of Turku in SemEval 2016 Task 10: DiMSUM
===================================================

This code implements the experiments of the University of Turku IT Department for [SemEval 2016 Task 10](http://dimsum16.github.io/), Detecting Minimal Semantic Units and their Meanings (DiMSUM).

Experiment Results
------------------
Our submitted DiMSUM task results can be found under `data/results`. The three packages correspond to the three conditions of the DiMSUM task.

Required Libraries and Data
---------------------------

### Dependencies
The dependencies are listed in `requirements.txt`. Except for scikit-learn, other versions of the libraries may also work. The specific version 0.16.0 of scikit-learn is required for our extensions to work with it.

### Data files
Data files used in our experiments, a copy of the DiMSUM corpus and our submitted results can be found in the `data` directory.

> NOTE: You cannot run the experiments for tasks 2 and 3 unless you get the [YELP academic dataset](https://www.yelp.com/academic_dataset). To get the dataset first apply for a permission from Yelp. Once you have the permission, download the dataset and use `setupYelp.py` to build the database, e.g. `python setupYelp.py -i yelp_academic_dataset.json.gz`.

* `dimsum-data-1.5`: A copy of the [DiMSUM 2016 shared task data](https://github.com/dimsum16/dimsum-data/releases/tag/1.5).
* `wikipedia`: Data files derived from the English Wikipedia, used in our entry for the open condition.
* `yelp`: A placeholder for the YELP database generated from the YELP academic dataset. To access the YELP academic dataset request a license from the [YELP website](https://www.yelp.com/academic_dataset)
* `results`: Our submitted results for the DiMSUM challenge.

Running the Experiments
-----------------------
The DiMSUM task consists of three subtasks, 1) the supervised closed condition, 2) the semi-supervised closed condition and 3) the open condition. For more information on these tasks please see the [DiMSUM home page](http://dimsum16.github.io/). For running our experimental code for the three tasks, please use the following command: 

`python run.py -e [TASK] -o [OUTPUT] -c ensemble.ExtraTreesClassifier -r "n_estimators=[2];random_state=[1]" --hidden`

When running an experiment, replace `[OUTPUT]` with your own output directory and replace `[TASK]` with one of the experiments: `Task1`, `Task2`, or `Task3`.

The Experiment System
---------------------
All experiments can be run using the program `run.py`. The experimental code uses a three-step system. One or more of these actions can be performed using the command line option `--action` or `--a`.

### Generating examples for machine learning
Examples are generated using the `build` action. A class is derived from src.Experiment to define the rules and limits for example generation. Classes for the experiments described in the paper are defined in the file `experiments.py`.

### Classification
Examples are classified using the `classify` action. A class can be derived from src.Classification to customize the overall approach for classifying the examples. For most experiments, src.Classification can be used as is. For defining the scikit-learn classifier and its parameters, the  `--classifier` and `--classifierArguments` of `run.py` can be used.

### Analyses
Classified examples can be used for various analyses with the `analyse` action. Analysis classes can be derived from src.analyse.Analysis to define such analyses, and the `--analyses` options of `run.py` can be used to choose which analyses to run for the experiment.