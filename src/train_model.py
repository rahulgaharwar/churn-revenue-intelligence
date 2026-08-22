import os
import json
import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, precision_recall_fscore_support, confusion_matrix, classification_report

def run_ml_pipeline():
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "saas_churn_telemetry.csv")
    df = pd.read_csv(data_path)
    
    print(f"[INFO] Loaded dataset with shape: {df.shape}")
    
    # 1. Feature Engineering
    df["support_workload_index"] = df["support_tickets_90d"] * df["avg_ticket_res_hrs"]
    df["user_engagement_density"] = df["login_frequency_30d"] / df["active_users"].replace(0, 1)
    df["mrr_per_user"] = df["mrr"] / df["active_users"].replace(0, 1)
    
    feature_cols_num = [
        "mrr", "tenure_months", "active_users", "login_frequency_30d",
        "login_decay_rate", "feature_adoption_score", "support_tickets_90d",
        "avg_ticket_res_hrs", "payment_failures_12m", "nps_score",
        "support_workload_index", "user_engagement_density", "mrr_per_user"
    ]
    
    feature_cols_cat = ["plan_tier", "contract_type"]
    
    X = df[feature_cols_num + feature_cols_cat]
    y = df["churn_status"]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42, stratify=y)
    
    # 2. Preprocessing Transformer
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), feature_cols_num),
            ('cat', OneHotEncoder(drop='first', sparse_output=False), feature_cols_cat)
        ]
    )
    
    # 3. Train Models
    models = {
        "Logistic Regression": LogisticRegression(random_state=42, max_iter=1000),
        "Random Forest": RandomForestClassifier(n_estimators=150, max_depth=8, random_state=42),
        "Gradient Boosting": GradientBoostingClassifier(n_estimators=150, learning_rate=0.08, max_depth=5, random_state=42)
    }
    
    best_model_name = ""
    best_auc = 0
    best_pipeline = None
    results = {}
    
    for name, clf in models.items():
        pipe = Pipeline([
            ('preprocessor', preprocessor),
            ('classifier', clf)
        ])
        pipe.fit(X_train, y_train)
        
        y_pred = pipe.predict(X_test)
        y_prob = pipe.predict_proba(X_test)[:, 1]
        
        auc = roc_auc_score(y_test, y_prob)
        prec, rec, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='binary')
        cm = confusion_matrix(y_test, y_pred).tolist()
        
        results[name] = {
            "roc_auc": round(float(auc), 4),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1_score": round(float(f1), 4),
            "confusion_matrix": cm
        }
        
        print(f"[{name}] AUC: {auc:.4f} | F1: {f1:.4f} | Precision: {prec:.4f} | Recall: {rec:.4f}")
        
        if auc > best_auc:
            best_auc = auc
            best_model_name = name
            best_pipeline = pipe

    print(f"\n[WINNER] Selected Best Model: {best_model_name} with ROC-AUC = {best_auc:.4f}")
    
    # Save best model pipeline
    models_dir = os.path.join(os.path.dirname(__file__), "..", "models")
    os.makedirs(models_dir, exist_ok=True)
    model_file = os.path.join(models_dir, "churn_pipeline.pkl")
    with open(model_file, "wb") as f:
        pickle.dump(best_pipeline, f)
        
    metrics_file = os.path.join(models_dir, "model_metrics.json")
    with open(metrics_file, "w") as f:
        json.dump(results, f, indent=2)
        
    # 4. Feature Importance Extraction
    cat_encoder = best_pipeline.named_steps['preprocessor'].named_transformers_['cat']
    cat_feature_names = cat_encoder.get_feature_names_out(feature_cols_cat).tolist()
    all_feature_names = feature_cols_num + cat_feature_names
    
    classifier = best_pipeline.named_steps['classifier']
    if hasattr(classifier, 'feature_importances_'):
        importances = classifier.feature_importances_
    else:
        importances = np.abs(classifier.coef_[0])
        
    feature_importance_list = [
        {"feature": name.replace("cat__", "").replace("num__", ""), "importance": round(float(imp), 4)}
        for name, imp in sorted(zip(all_feature_names, importances), key=lambda x: x[1], reverse=True)
    ]
    
    # 5. Score Entire Dataset & Business Analytics Computation
    full_probs = best_pipeline.predict_proba(X)[:, 1]
    df["churn_probability"] = np.round(full_probs, 4)
    
    # Define Risk Tiers
    def get_risk_tier(p):
        if p >= 0.65:
            return "High"
        elif p >= 0.35:
            return "Medium"
        else:
            return "Low"
            
    df["risk_tier"] = df["churn_probability"].apply(get_risk_tier)
    df["expected_revenue_loss"] = np.round(df["mrr"] * 12 * df["churn_probability"], 2)
    
    # Strategic Action Generator based on features
    def recommend_action(row):
        actions = []
        if row["login_decay_rate"] < -0.2:
            actions.append("Schedule CSM Re-engagement Call")
        if row["support_tickets_90d"] >= 4 and row["avg_ticket_res_hrs"] > 24:
            actions.append("Escalate Open Support Tickets")
        if row["payment_failures_12m"] > 0:
            actions.append("Audit Billing / Update Credit Card")
        if row["feature_adoption_score"] < 45:
            actions.append("Enroll in Product Onboarding Webinar")
        if row["nps_score"] <= 5:
            actions.append("Executive Outbound Outreach")
        if not actions:
            actions.append("Send Monthly Product Digest & Usage Insights")
        return " | ".join(actions)

    df["recommended_action"] = df.apply(recommend_action, axis=1)

    # Key Business Metrics
    total_arr = float(df["mrr"].sum() * 12)
    high_risk_df = df[df["risk_tier"] == "High"]
    med_risk_df = df[df["risk_tier"] == "Medium"]
    
    revenue_at_risk_arr = float(df["expected_revenue_loss"].sum())
    high_risk_arr = float(high_risk_df["mrr"].sum() * 12)
    high_risk_count = int(len(high_risk_df))
    med_risk_count = int(len(med_risk_df))
    low_risk_count = int(len(df[df["risk_tier"] == "Low"]))
    overall_churn_rate = float(df["churn_status"].mean())

    # 6. Survival Analysis Curves (Kaplan-Meier Style Estimation by Plan Tier)
    max_tenure = int(df["tenure_months"].max())
    tenure_timeline = list(range(1, max_tenure + 1))
    
    survival_curves = {}
    for plan in ["Basic", "Pro", "Enterprise"]:
        plan_sub = df[df["plan_tier"] == plan]
        surv_probs = []
        for t in tenure_timeline:
            # Fraction of users remaining at tenure t
            at_risk = len(plan_sub[plan_sub["tenure_months"] >= t])
            churned_by_t = len(plan_sub[(plan_sub["tenure_months"] >= t) & (plan_sub["churn_status"] == 1)])
            prob = 1.0 - (churned_by_t / (at_risk + 1e-5))
            surv_probs.append(round(float(max(0.2, prob)), 3))
        survival_curves[plan] = surv_probs

    # 7. Cohort Matrix Data (Tenure Bucket vs Plan Retention %)
    cohort_data = []
    tenure_buckets = [
        ("1-6 Mos", 1, 6),
        ("7-12 Mos", 7, 12),
        ("13-24 Mos", 13, 24),
        ("25+ Mos", 25, 60)
    ]
    for label, min_t, max_t in tenure_buckets:
        row_dict = {"bucket": label}
        for plan in ["Basic", "Pro", "Enterprise"]:
            sub = df[(df["plan_tier"] == plan) & (df["tenure_months"] >= min_t) & (df["tenure_months"] <= max_t)]
            if len(sub) > 0:
                retention = round(float((1 - sub["churn_status"].mean()) * 100), 1)
            else:
                retention = 100.0
            row_dict[plan] = retention
        cohort_data.append(row_dict)

    # 8. Export JSON for Web Dashboard
    dashboard_data = {
        "kpi": {
            "total_arr": round(total_arr, 2),
            "revenue_at_risk_arr": round(revenue_at_risk_arr, 2),
            "high_risk_arr": round(high_risk_arr, 2),
            "total_customers": len(df),
            "high_risk_count": high_risk_count,
            "medium_risk_count": med_risk_count,
            "low_risk_count": low_risk_count,
            "observed_churn_rate": round(overall_churn_rate * 100, 2),
            "model_best": best_model_name,
            "model_auc": results[best_model_name]["roc_auc"],
            "model_f1": results[best_model_name]["f1_score"]
        },
        "model_comparison": results,
        "feature_importance": feature_importance_list,
        "survival_curves": {
            "timeline": tenure_timeline,
            "curves": survival_curves
        },
        "cohort_matrix": cohort_data,
        "customer_sample": df.sort_values(by="churn_probability", ascending=False).head(300).to_dict(orient="records")
    }

    web_dir = os.path.join(os.path.dirname(__file__), "..", "web")
    os.makedirs(web_dir, exist_ok=True)
    json_out_path = os.path.join(web_dir, "dashboard_data.json")
    
    with open(json_out_path, "w") as f:
        json.dump(dashboard_data, f, indent=2)
        
    print(f"[SUCCESS] Web dashboard data artifact exported to: {json_out_path}")
    print(f"Total ARR: ${total_arr:,.2f} | Revenue at Risk: ${revenue_at_risk_arr:,.2f}")
    print(f"High Risk Accounts: {high_risk_count} (${high_risk_arr:,.2f} ARR)")

if __name__ == "__main__":
    run_ml_pipeline()
