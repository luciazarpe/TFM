# 🎓 Master Thesis Project — DSMarket

Welcome to the repository of **Lucía, Sandra, Samu, Jorge, and Cristian**! 😎

DSMarket is an end-to-end Machine Learning project built around a retail sales forecasting use case for a fictional supermarket chain operating in New York, Boston, and Philadelphia.

## 📦 What's in this project

- **Exploratory Data Analysis** — sales trends, product popularity, price elasticity and variations across cities and stores
- **Clustering** — product segmentation (4 clusters via K-Means + ABC/XYZ classification) and store segmentation (3 clusters)
- **Sales Forecasting** — 28-day sales forecasting using XGBoost with skforecast, achieving a 54.7% WMAPE improvement over the baseline at chain level
- **BI Dashboard** — interactive Power BI report with 5 tabs for executive-level insights (sales overview, temporal analysis, store performance, product categories, and events impact)
- **Store Replenishment Use Case** — end-to-end MLOps solution including a REST API, Docker deployment, CI/CD pipeline, MLflow model tracking and a web interface for stock replenishment recommendations

## 📓 Notebooks

| Notebook | Description | Open in Colab |
|---|---|---|
| `preprocesamiento.ipynb` | Data cleaning, integration and feature creation | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/luciazarpe/TFM/blob/main/preprocesamiento.ipynb) |
| `eda.ipynb` | Exploratory data analysis | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/luciazarpe/TFM/blob/main/eda.ipynb) |
| `clustering productos.ipynb` | Product clustering | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/luciazarpe/TFM/blob/main/clustering%20productos.ipynb) |
| `clustering tiendas.ipynb` | Store clustering | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/luciazarpe/TFM/blob/main/clustering%20tiendas.ipynb) |
| `modelizacion.ipynb` | Sales forecasting model | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/luciazarpe/TFM/blob/main/modelizacion.ipynb) |

> 💡 We recommend opening the notebooks in Google Colab to view the interactive Plotly charts, which do not render in GitHub's static viewer.

## 🛠️ Tech stack

**Data & Modelling:** Python, pandas, numpy, XGBoost, skforecast, scikit-learn, Optuna, UMAP

**Visualisation:** Plotly, Power BI

**MLOps & Deployment:** FastAPI, Docker, MLflow

**Development:** Jupyter Notebooks, Google Colab, GitHub

## 📊 Key results

| Level | Benchmark WMAPE | Model WMAPE | Improvement |
|---|---|---|---|
| Product × Store | 99.6% | 67.9% | 31.8% |
| Store | 14.3% | 8.4% | 41.3% |
| City | 13.1% | 6.6% | 49.4% |
| Total DSMarket | 12.6% | 5.7% | 54.7% |

## 🏫 Academic context

Master's Degree in Data Science and Artificial Intelligence — Nuclio Digital School, 2026
