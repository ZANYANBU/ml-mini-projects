# Machine Learning Mini Projects (21CSC305P), Team Cash Guard

Five machine-learning projects, one for each unit of **21CSC305P – Machine Learning** (III Year, V Semester, 2026–2027), SRM Institute of Science and Technology, Kattankulathur.

**Team Cash Guard:** V. Anbu Chelvan (team head) · S. Roopesh · B. Charith Reddy · Y. Rupesh Reddy

Every project uses real, public data and runs end to end. The final report, with all five projects, is in [`report/`](report/).

## The five projects

| Unit | Project | Problem | Method | Headline result |
|---|---|---|---|---|
| 1 | [CashGuard: ATM cash-out prediction](unit-1-cashguard-atm/) | Predict when an ATM will run out of cash and need a refill | Multiple linear regression written from first principles (normal equations, no libraries), turned into a days-to-empty alert | R² **0.666** on unseen days, against 0.483 for "same as today"; 21 of 50 ATMs flagged for refill |
| 2 | [Robust ocean temperature from salinity](unit-2-ocean-temperature-huber/) | Predict ocean temperature from salinity over 72 years so faulty sensor readings do not corrupt the model | Polynomial basis functions with OLS, ridge (MAP), Bayesian linear regression, RANSAC and **Huber** robust regression | With 10% faulty readings, Huber's bias is **0.14 °C** against OLS's 1.11 °C (7.5× smaller); it flags 99.4% of the faults |
| 3 | [Warehouse SKU clustering](unit-3-warehouse-sku-kmeans/) | Group warehouse products by pick frequency, seasonality, size and handling so workers walk less | **K-Means** (elbow and silhouette for k), compared with hierarchical clustering, mixtures of Gaussians and PCA | 383 real SKUs fall into 4 zones; modelled walk per pick drops **27%** (63.8 m → 46.5 m) |
| 4 | [Drone state estimation in turbulent wind](unit-4-drone-state-estimation/) | Recover a drone's true 3-D position and velocity from noisy IMU, altimeter and optical-flow readings | **Linear Dynamical System + Kalman filter**, RTS smoother, EM for the noise levels, a wind state in the model | Position error **0.43 m** against 103.4 m for the IMU alone (**238×** better); the unmeasured wind is recovered to 2.1 m/s |
| 5 | [Climate displacement forecasting](unit-5-climate-displacement/) | Predict how many people an extreme weather event will displace, with an uncertainty range, for emergency planning | **Hybrid Bayesian Model Averaging + Gradient Boosting** | R² **0.520** on 5,600 unseen events (BMA 0.361, boosting 0.517); 94% of outcomes inside the 90% range |

## Repository layout

```
README.md                          this file
report/                            the final project report (all five units)
unit-1-cashguard-atm/              Unit 1 – regression
unit-2-ocean-temperature-huber/    Unit 2 – robust and Bayesian linear regression
unit-3-warehouse-sku-kmeans/       Unit 3 – clustering
unit-4-drone-state-estimation/     Unit 4 – sequential data, Kalman filtering
unit-5-climate-displacement/       Unit 5 – combining models
```

Each unit folder has its own README with the problem statement, the data, how to run it, and the results; its code or notebook; the figures; and the review presentation.

## Review presentations

| Review | Unit | Presentation |
|---|---|---|
| 1 | Unit 1 | [CashGuard_Review1.pptx](unit-1-cashguard-atm/presentation/CashGuard_Review1.pptx) · [PDF](unit-1-cashguard-atm/presentation/CashGuard_Review1.pdf) |
| 2 | Unit 2 | [Unit2_ML_Robust_Ocean_Temperature.pptx](unit-2-ocean-temperature-huber/presentation/Unit2_ML_Robust_Ocean_Temperature.pptx) · [PDF](unit-2-ocean-temperature-huber/presentation/Unit2_ML_Robust_Ocean_Temperature.pdf) |
| 3 | Unit 3 | [kmeans-sku-clustering.pptx](unit-3-warehouse-sku-kmeans/slides/kmeans-sku-clustering.pptx) · [PDF](unit-3-warehouse-sku-kmeans/slides/kmeans-sku-clustering.pdf) |
| 4 | Unit 4 | [Drone_Kalman_Unit4_Presentation.pdf](unit-4-drone-state-estimation/slides/Drone_Kalman_Unit4_Presentation.pdf) · [HTML](unit-4-drone-state-estimation/slides/presentation.html) |
| 5 | Unit 5 | [Climate_Displacement_Presentation.pptx](unit-5-climate-displacement/presentation/Climate_Displacement_Presentation.pptx) |

## Datasets

| Unit | Dataset | Link |
|---|---|---|
| 1 | ATM Cash Demand Forecasting and Management (Kaggle); a generated sample with the same schema and statistics is included | https://www.kaggle.com/datasets/zoya77/atm-cash-demand-forecasting-and-management |
| 2 | CalCOFI Bottle Database, 1949–2021 (895,371 bottle samples) | https://calcofi.org/data/oceanographic-data/bottle-database/ · https://calcofi.io/datasets/calcofi_ctd-cast/ |
| 3 | Brazilian E-Commerce Public Dataset by Olist (99,441 orders) | https://github.com/olist/work-at-olist-data |
| 4 | PX4 flight log (real IMU noise) and Open-Meteo hourly wind archive (real gusts) | https://raw.githubusercontent.com/PX4/pyulog/main/test/sample.ulg · https://open-meteo.com |
| 5 | IDMC disaster displacements (via HDX) and World Bank country indicators | https://data.humdata.org/dataset/idmc-internal-displacements-new-displacements-associated-with-disasters |

## Run in Google Colab

| Unit | Notebook |
|---|---|
| 3 | [warehouse_sku_kmeans.ipynb](https://colab.research.google.com/github/ZANYANBU/ml-mini-projects/blob/main/unit-3-warehouse-sku-kmeans/notebook/warehouse_sku_kmeans.ipynb) |
| 4 | [Drone_Kalman_Unit4.ipynb](https://colab.research.google.com/github/ZANYANBU/ml-mini-projects/blob/main/unit-4-drone-state-estimation/Drone_Kalman_Unit4.ipynb) |
| 5 | [Climate_Displacement_BMA_GradientBoosting.ipynb](https://colab.research.google.com/github/ZANYANBU/ml-mini-projects/blob/main/unit-5-climate-displacement/Climate_Displacement_BMA_GradientBoosting.ipynb) |

Units 1 and 2 are Python scripts; their READMEs say how to run them.

## Team contributions

| Member | Role across the projects |
|---|---|
| V. Anbu Chelvan | Team head: models, implementation, notebooks, demo website, repository, final report |
| S. Roopesh | Problem study and choice of method; data retrieval (PX4 logs, IMU calibration, SQLite database in Unit 4) |
| B. Charith Reddy | Method and data preparation; consistency tests (NEES/NIS) and the GPS study in Unit 4 |
| Y. Rupesh Reddy | Results, graphs and slide decks; EM noise learning figures in Unit 4 |
