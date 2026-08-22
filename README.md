# Customer Churn & Revenue Risk Intelligence Platform

An end-to-end machine learning project for predicting SaaS customer churn, estimating revenue at risk, and exploring customer risk through an interactive dashboard.

The project combines customer telemetry, classification models, survival analysis, and revenue calculations to answer a practical question:

> **Which customers are most likely to churn, how much revenue is at risk, and what can be done about it?**

---

## Overview

Customer churn is easier to address when it can be identified before the customer leaves.

This project uses customer-level SaaS data such as login activity, support interactions, NPS scores, payment failures, contract type, and recurring revenue to build a churn prediction pipeline.

The output is used to:

* Predict the probability of customer churn
* Identify the factors associated with higher churn risk
* Estimate customer lifetime and time-to-churn patterns
* Calculate annual revenue exposed to churn
* Explore how changes in customer behaviour affect predicted risk
* Suggest possible retention actions based on the customer's risk factors

---

## Project Highlights

### Churn Prediction

Built a classification pipeline using `scikit-learn` to preprocess customer data, engineer behavioural features, and compare multiple models:

* Logistic Regression
* Random Forest
* Gradient Boosting

The selected Logistic Regression model achieved a **0.80 ROC-AUC** on the test set.

### Survival Analysis

Kaplan-Meier survival curves are used to study how long customers remain subscribed and how survival differs between:

* Basic
* Pro
* Enterprise

This provides a different view of churn beyond a simple yes/no prediction.

### Revenue at Risk

Each customer's predicted churn probability is combined with their recurring revenue to estimate potential annual revenue exposure:

```text
Revenue at Risk = Churn Probability × MRR × 12
```

Across the generated customer dataset, the estimated exposure is **$1.4M+ ARR**.

### What-If Simulator

The dashboard includes an interactive simulator where users can change customer attributes such as:

* Login activity
* Support tickets
* NPS
* Payment failures
* Other behavioural signals

The model then updates the estimated churn risk, allowing users to explore how different customer situations affect the prediction.

### Retention Recommendations

The dashboard also maps important risk factors to potential actions.

For example:

| Risk Signal              | Possible Action               |
| ------------------------ | ----------------------------- |
| High support workload    | Escalate unresolved tickets   |
| Declining login activity | CSM check-in                  |
| Low NPS                  | Customer feedback / follow-up |
| Payment failures         | Billing review                |
| Low product engagement   | Product onboarding session    |

These recommendations are rule-based and are intended as decision-support rather than automated decisions.

---

## Model Results

The models were evaluated using an 80/20 stratified train-test split.

| Model                   |  ROC-AUC | Precision |   Recall |       F1 |
| ----------------------- | -------: | --------: | -------: | -------: |
| **Logistic Regression** | **0.80** |  **0.66** | **0.27** | **0.38** |
| Random Forest           |     0.78 |      0.86 |     0.12 |     0.22 |
| Gradient Boosting       |     0.75 |      0.61 |     0.25 |     0.35 |

Logistic Regression was selected because it provided the best overall ROC-AUC while also being relatively easy to interpret.

The relatively low recall highlights an important limitation of the current model: improving detection of potential churners would be a useful next step.

---

## Important Churn Signals

The analysis identified several variables that were particularly useful for predicting churn:

1. **Login decay rate**
   A decline in recent product usage is a strong signal of disengagement.

2. **Support workload**
   A combination of ticket volume and resolution time can indicate customer friction.

3. **Payment failures**
   Repeated payment problems can contribute to involuntary churn.

4. **NPS score**
   Lower satisfaction scores are associated with higher churn risk.

5. **Contract type**
   Monthly customers show higher churn risk compared with customers on annual contracts in the generated dataset.

> These relationships are based on the project's dataset and should not be interpreted as universal SaaS benchmarks.

---

## Tech Stack

**Data & Machine Learning**

* Python
* Pandas
* NumPy
* Scikit-learn
* Kaplan-Meier survival analysis

**Frontend**

* HTML
* CSS
* JavaScript
* Chart.js

**Other**

* Pickle
* JSON
* CSV

---

## Project Structure

```text
churn-revenue-intelligence/
│
├── data/
│   ├── generate_data.py
│   └── saas_churn_telemetry.csv
│
├── src/
│   └── train_model.py
│
├── models/
│   ├── churn_pipeline.pkl
│   └── model_metrics.json
│
├── web/
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   └── dashboard_data.json
│
└── README.md
```

### What each part does

**`data/generate_data.py`**
Generates the synthetic SaaS customer telemetry dataset.

**`src/train_model.py`**
Handles feature engineering, preprocessing, model training, evaluation, survival analysis, and exporting the results.

**`models/`**
Contains the trained model pipeline and evaluation metrics.

**`web/`**
Contains the dashboard and the data required to display predictions, metrics, charts, and the simulator.

---

## Dataset

The project uses a synthetic dataset containing **5,000+ SaaS customer records**.

Example variables include:

* Customer ID
* Subscription tier
* Contract type
* MRR
* Login activity
* Login decay
* Support tickets
* Average resolution time
* NPS
* Payment failures
* Tenure
* Churn status

The dataset is generated locally using `generate_data.py`, so no real customer information is used.

---

## Running the Project

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd churn-revenue-intelligence
```

### 2. Install dependencies

```bash
pip install pandas numpy scikit-learn
```

### 3. Generate the dataset

```bash
python data/generate_data.py
```

### 4. Train the models

```bash
python src/train_model.py
```

This generates the trained model, evaluation metrics, and dashboard data.

### 5. Start the dashboard

From the project root:

```bash
python -m http.server 8000 --directory web
```

Open:

```text
http://localhost:8000
```

---

## Dashboard

The dashboard provides:

* Overall churn statistics
* Revenue-at-risk metrics
* Churn probability distribution
* Customer risk breakdown
* Survival curves
* Churn driver analysis
* Customer-level filtering
* What-if risk simulation
* Suggested retention actions

---

## Future Improvements

Some areas that could be explored in future versions:

* XGBoost / LightGBM comparison
* SHAP-based model explanations
* Probability calibration
* Better handling of class imbalance
* Time-based validation instead of a random split
* Real customer telemetry integration
* Automated model retraining
* API backend for real-time predictions
* Customer-level alerting
* A/B testing of retention strategies
* More robust survival models such as Cox Proportional Hazards

---

## Disclaimer

This project uses **synthetically generated data** and is intended for educational and portfolio purposes.

The revenue-at-risk figures, churn relationships, and model performance should not be treated as real-world SaaS benchmarks.

---

## Author

**Rahul Gaharwar**

B.Tech. Computer Science & Engineering

Built as a portfolio project to explore machine learning, predictive analytics, survival analysis, and business intelligence.
